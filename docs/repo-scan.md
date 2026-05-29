# Repo Pipeline Scan — Stage 1 Operator Guide

The `repo-scan.yml` workflow is the deterministic Stage 1 of the repo pipeline inventory feature. It enumerates configured organizations and explicit repositories, captures their CI/CD pipeline and manifest files, classifies each repo against a canonical taxonomy, and commits the resulting snapshot to this repository under `inventory/<run-id>/` via a pull request.

The (separate) Stage 2 analysis is documented in [`inventory-analysis.md`](inventory-analysis.md).

## Prerequisites

| Requirement                              | Notes                                                                                                                                     |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub App installed on every target org | Same app used by `submit-repos.yml`. Set `vars.GH_APP_ID` and `secrets.GH_APP_PEM` in this repo.                                          |
| App permissions                          | `Contents: read`, `Metadata: read`.                                                                                                       |
| Branch protection                        | The workflow opens a PR; merging it lands the snapshot under `inventory/`. Reviewers should diff `repos.csv` and spot-check `pipelines/`. |

## Running a scan

1. Open the **Actions** tab → **Repo Pipeline Scan** → **Run workflow**.
2. Fill in the inputs:

| Input           | Type                       | Required          | Example                     | Notes                                                                                       |
| --------------- | -------------------------- | ----------------- | --------------------------- | ------------------------------------------------------------------------------------------- |
| `organizations` | JSON array of strings      | No                | `["my-org-a","my-org-b"]`   | Every non-archived, non-disabled, non-fork repo in each org is scanned.                     |
| `repositories`  | JSON array of `owner/repo` | No                | `["other-org/repo-1"]`      | Explicit repos to include in addition to the org scan.                                      |
| `excludes`      | JSON array of `owner/repo` | No                | `["my-org-a/legacy-thing"]` | Applied after enumeration.                                                                  |
| `retention`     | integer                    | No (default `12`) | `12`                        | Keep the most recent N snapshots under `inventory/`; older ones are deleted in the same PR. |

At least one of `organizations` or `repositories` must be provided.

3. The workflow runs a matrix job per organization (plus one synthetic job for the explicit repositories), then an aggregator job that opens a PR titled `inventory: repo-scan snapshot run-<run-id>`.

4. Review the PR. Confirm:
   - `inventory/<run-id>/manifest.json` reflects the inputs you supplied.
   - `repos.csv` row count matches `manifest.json#counts.repositories_scanned`.
   - Spot-check 2–3 entries against the captured `pipelines/<org>/<repo>/...` files.
   - The `inventory/latest` pointer was updated.

5. Merge the PR. Once merged, the snapshot is available to Stage 2.

## Snapshot layout

Every run writes to `inventory/<run-id>/` where `<run-id>` is the GitHub Actions run ID:

```text
inventory/
├── latest                                # pointer file containing the most recent <run-id>
└── <run-id>/
    ├── manifest.json                     # inputs, timestamp, counts, truncation flags
    ├── repos.csv                         # per-repo classification (Stage 1)
    ├── dependencies.csv                  # CI-side dependencies referenced by captured pipeline files (Stage 1)
    ├── pipelines/<org>/<repo>/...        # raw CI/CD config files preserved with original paths
    ├── manifests/<org>/<repo>/...        # raw manifest files (package.json, pom.xml, etc.)
    ├── raw/<org>__<repo>.json            # per-repo extracted signals
    └── analysis/                         # Stage 2 outputs (added by the inventory-analysis agent)
        ├── clusters.json
        ├── clusters.csv
        └── REPORT.md
```

### `repos.csv` columns

| Column                | Description                                                                          |
| --------------------- | ------------------------------------------------------------------------------------ |
| `org`                 | Owner login                                                                          |
| `repo`                | Repository name                                                                      |
| `default_branch`      | Default branch at scan time                                                          |
| `primary_language`    | Largest language by bytes (Languages API)                                            |
| `secondary_languages` | Semicolon-separated list of additional languages                                     |
| `build_tools`         | Semicolon-separated canonical build tools                                            |
| `package_managers`    | Semicolon-separated canonical package managers                                       |
| `ci_platforms`        | Semicolon-separated CI/CD platforms detected via pipeline files                      |
| `deploy_targets`      | Semicolon-separated canonical deploy targets                                         |
| `container`           | `true` if a `Dockerfile` or container build file was found                           |
| `iac`                 | Semicolon-separated infrastructure-as-code tools detected (e.g. `Terraform`, `Helm`) |
| `has_dockerfile`      | `true`/`false`                                                                       |
| `has_helm`            | `true`/`false`                                                                       |
| `pipeline_file_count` | Number of pipeline files captured under `pipelines/<org>/<repo>/`                    |
| `total_loc_pipeline`  | Combined line count across captured pipeline files                                   |
| `signals_json`        | JSON blob of raw signal hits for downstream analysis                                 |

The canonical label vocabulary used in these columns is defined in [`plugin/skills/inventory-analysis/SKILL.md`](../plugin/skills/inventory-analysis/SKILL.md#canonical-taxonomy).

### `dependencies.csv` columns

This file captures **CI-side dependencies** — references that a captured pipeline file makes to artifacts *outside the source repository* (reusable workflows, marketplace actions, shared libraries, included pipeline files, templates, orbs, pipes, plugin images). It does **not** capture application-code package dependencies (npm, Maven, pip, etc.); use GitHub's Dependency Graph for that.

| Column            | Description                                                                                                                                                                                                                                                 |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `org`             | Owner login                                                                                                                                                                                                                                                 |
| `repo`            | Repository name                                                                                                                                                                                                                                             |
| `ci_platform`     | Canonical CI platform the source file belongs to (`GitHubActions`, `GitLabCI`, `AzureDevOps`, `Jenkins`, `CircleCI`, `BitbucketPipelines`, `DroneCI`, `TravisCI`)                                                                                           |
| `source_path`     | Path of the pipeline file that declares the dependency (relative to the repo root)                                                                                                                                                                          |
| `dependency_kind` | One of `Action`, `ReusableWorkflow`, `GitLabIncludeProject`, `GitLabIncludeRemote`, `GitLabIncludeTemplate`, `AzureTemplate`, `AzureRepoResource`, `JenkinsSharedLibrary`, `CircleCIOrb`, `BitbucketPipe`, `BitbucketImport`, `DronePlugin`, `TravisImport` |
| `dependency_ref`  | The referenced identifier (action name, workflow path, library name, orb, pipe, plugin image, etc.)                                                                                                                                                         |
| `version`         | Ref/version pin if specified, otherwise empty                                                                                                                                                                                                               |

Local references (e.g. `uses: ./.github/actions/...` in GitHub Actions, `include: local: ...` in GitLab CI, sibling-file `template:` references in Azure DevOps) are intentionally excluded.

### `manifest.json`

```json
{
  "run_id": "1234567890",
  "started_at": "2026-05-29T12:00:00Z",
  "finished_at": "2026-05-29T12:14:32Z",
  "inputs": {
    "organizations": ["my-org-a"],
    "repositories": [],
    "excludes": [],
    "retention": 12
  },
  "counts": {
    "repositories_scanned": 42,
    "pipelines_captured": 187,
    "repositories_with_pipelines": 38,
    "repositories_truncated": 2
  }
}
```

## Caps & truncation

To bound API usage and snapshot size:

| Cap                     | Default         | Override                                               |
| ----------------------- | --------------- | ------------------------------------------------------ |
| Pipeline files per repo | 25              | Edit `MAX_PIPELINE_FILES_PER_REPO` in `repo-scan.yml`. |
| Pipeline bytes per repo | 524288 (512 KB) | Edit `MAX_PIPELINE_BYTES_PER_REPO` in `repo-scan.yml`. |

Repos that hit a cap are recorded with `truncated: true` in their `raw/<owner>__<repo>.json`, and counted in `manifest.json#counts.repositories_truncated`. The Stage 2 agent surfaces these in its `REPORT.md`.

## Adding signals

Detection logic lives entirely in code — there is no separate config file. When you need to recognize a new build tool, deploy target, or IaC platform:

1. Add a regex entry to the appropriate array in [`.github/scripts/repo-scan/extract.js`](../.github/scripts/repo-scan/extract.js): `PIPELINE_PATTERNS`, `MANIFEST_PATTERNS`, or `PATH_ONLY_PATTERNS`.
2. For deploy targets detected via pipeline file content, add a regex entry to `DEPLOY_TARGET_CUES` in [`.github/scripts/repo-scan/classify.js`](../.github/scripts/repo-scan/classify.js).
3. Add the canonical label to the taxonomy block in [`plugin/skills/inventory-analysis/SKILL.md`](../plugin/skills/inventory-analysis/SKILL.md#canonical-taxonomy) so the Stage 2 agent knows what it means.
4. Run a scan against one or two known repos and verify the new label appears in `repos.csv`.

## Running Stage 2

After Stage 1 has produced a snapshot (and `inventory/latest` is updated), run the agent locally:

```bash
copilot --agent inventory-analysis "Analyze inventory/latest"
```

See [`inventory-analysis.md`](inventory-analysis.md) for the full operator guide.

## Troubleshooting

| Symptom                                                           | Likely cause                                                                                      | Fix                                                            |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `At least one of organizations or repositories must be provided.` | Both inputs are empty.                                                                            | Provide at least one.                                          |
| `Input ... is not valid JSON.`                                    | A bare string was passed instead of a JSON array.                                                 | Use `["my-org"]`, not `my-org`.                                |
| Many repos with empty `ci_platforms`                              | App lacks `Contents: read` on those repos, or the repo uses a CI pattern not yet in `extract.js`. | Check app installation; consider adding signals.               |
| `dependencies.csv` is empty for a repo that clearly uses actions  | The repo's pipeline files were not captured (no matching path pattern in `extract.js`).           | Add the missing path pattern and re-scan.                      |
| Aggregator job opens a PR with no changes                         | Every shard failed enumeration.                                                                   | Check shard logs in the matrix; usually a token-scoping issue. |

## Related

- [`inventory-analysis.md`](inventory-analysis.md) — Stage 2 (cluster the snapshot).
- [`extending.md`](extending.md) — how to extend the broader project.
