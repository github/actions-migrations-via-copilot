# Plan: Repo Pipeline Inventory & Similarity Categorization

Two independent stages for inventorying CI/CD pipelines across organizations and grouping repositories by technology similarity:

- **Stage 1 — Deterministic scanner** (traditional GH Actions workflow + Node scripts): enumerates repos from orgs/lists/excludes, downloads manifests + source pipeline files, queries GitHub Dependency Graph API, applies rule-based classification, and **commits the resulting CSVs and raw files back to this repository** under `inventory/<run-id>/`.
- **Stage 2 — Inventory Analysis agent** (plugin agent, run locally via Copilot CLI): the user runs the agent from a clone of this repo; the agent reads `inventory/<run-id>/repos.csv` + `dependencies.csv` from the filesystem, samples `pipelines/`, and produces `clusters.json` / `clusters.csv` + a summary report.

The two stages run **independently** — Stage 1 is a scheduled/on-demand CI workflow; Stage 2 is an on-demand local agent invocation against whatever inventory snapshot the user picks.

## Phases

### Phase 1 — Shared taxonomy & config
1. `knowledge/repo-scan/taxonomy.md` — canonical vocabulary (CI platforms, languages, build tools, deploy targets, IaC, containers). Drives both classifier rules and the Inventory Analysis agent prompt.
   - **Consumed by:** Step 8 (`classify.js` reads it to emit canonical label values into `repos.csv`); Step 11 (`agents/inventory-analysis.md` reads it so cluster names and recommendations use the same vocabulary as the CSV).
2. `knowledge/repo-scan/signals.md` — manifest/path → signal mapping (e.g. `pom.xml`→Maven/Java, `Jenkinsfile`→Jenkins, `azure-pipelines.yml`→Azure DevOps, `terraform/*.tf`→Terraform).
   - **Consumed by:** Step 6 (`extract.js` reads it to know which manifest/pipeline paths to fetch per repo); Step 8 (`classify.js` reads it for path→label rules applied to extracted signals).
3. `knowledge/repo-scan/README.md` — input format docs (contributor-facing only).
   - **Consumed by:** Step 15 (`docs/repo-scan.md` operator guide links to it) and Step 16 (`docs/extending.md` references it for adding new signals/taxonomy entries).

### Phase 2 — Stage 1: Deterministic scanner (depends on Phase 1)
4. `.github/workflows/repo-scan.yml` — `workflow_dispatch` inputs: `organizations`, `repositories`, `excludes`, `scan_depth` (`shallow`|`with-deps`). Matrix per org + synthetic "explicit" entry. Reuses the `actions/create-github-app-token@v3` pattern from [.github/workflows/submit-repos.yml](.github/workflows/submit-repos.yml).
5. `.github/scripts/repo-scan/enumerate.js` — resolves orgs+repos+excludes → flat list (non-archived/disabled/fork).
6. `.github/scripts/repo-scan/extract.js` — per-repo: Languages API + Contents API for manifests + download up to N pipeline files (`Jenkinsfile`, `.gitlab-ci.yml`, `azure-pipelines*.yml`, `.circleci/config.yml`, `bitbucket-pipelines.yml`, `.drone.yml`, `bamboo-specs/*`, `.travis.yml`, `.github/workflows/*.yml`). Writes `inventory/<run-id>/pipelines/<org>/<repo>/...`, `inventory/<run-id>/manifests/...`, `inventory/<run-id>/raw/<org>__<repo>.json`.
7. `.github/scripts/repo-scan/deps.js` — Dependency Graph via GraphQL (`repository.dependencyGraphManifests`) → `inventory/<run-id>/dependencies.csv`.
8. `.github/scripts/repo-scan/classify.js` — rule-based classifier from signals/taxonomy → `inventory/<run-id>/repos.csv` (org, repo, primary_language, build_tools, ci_platforms, deploy_targets, container, iac, …).
9. Final workflow step: aggregate per-org outputs into a single `inventory/<run-id>/` tree (with a `manifest.json` recording inputs, timestamp, and counts), update `inventory/latest` symlink/pointer file, and **open a PR back to this repo** committing the new `inventory/<run-id>/` directory. Also write a step summary with counts.

### Phase 3 — Stage 2: Inventory Analysis agent (independent of Phase 2 — run on demand against a committed snapshot)
10. `agents/inventory-analysis.md` — agent prompt invoked locally via Copilot CLI from a clone of this repo. Accepts an optional `inventory/<run-id>` path (defaults to `inventory/latest`). Reads `repos.csv` + `dependencies.csv` from the filesystem, samples `pipelines/`, builds similarity clusters (lang+build+deploy+CI; secondary dep-overlap), scores reusable-workflow candidates (HIGH ≥4, MEDIUM 2–3). Writes:
    - `inventory/<run-id>/analysis/clusters.json` — structured clusters with members, rationale, shared signals, recommended reusable workflows.
    - `inventory/<run-id>/analysis/clusters.csv` — flattened one-row-per-(cluster, repo).
    - `inventory/<run-id>/analysis/REPORT.md` — human-readable summary with top recommendations.
11. `plugin/agents/inventory-analysis.agent.md` — plugin wrapper mirroring existing `plugin/agents/*.agent.md` so the agent is discoverable from Copilot CLI and chat.
12. `plugin/skills/inventory-analysis/SKILL.md` — packages clustering heuristics, taxonomy reference, output schemas, and CLI invocation examples.
13. Add entry to `plugin/plugin.json` registering the new agent + skill.

### Phase 4 — Docs
14. `docs/repo-scan.md` — operator guide for Stage 1 (running the workflow, reviewing the inventory PR).
15. `docs/inventory-analysis.md` — operator guide for Stage 2 (installing the plugin, running the agent via Copilot CLI against an `inventory/<run-id>` snapshot, interpreting `clusters.json`/`REPORT.md`).
16. Update [docs/extending.md](docs/extending.md) — adding signals/taxonomy entries.
17. Update [README.md](README.md) features list.

## Verification

1. `actionlint` clean on `repo-scan.yml`.
2. Stage 1 dry-run against 1 org + 3–5 explicit repos covering ≥3 CI platforms; verify a PR is opened containing the full `inventory/<run-id>/` tree.
3. Schema-check `repos.csv` columns from Step 8.
4. Merge the inventory PR; confirm `inventory/latest` points to the new snapshot.
5. Stage 2: clone repo, install the plugin, run the Inventory Analysis agent via Copilot CLI against `inventory/latest`; validate `clusters.json` against inline schema (members ⊆ `repos.csv`, unique `cluster_id`) and that `REPORT.md` lists top recommendations.
6. Re-run Stage 2 against a prior `inventory/<run-id>` snapshot; confirm it produces an `analysis/` subfolder scoped to that snapshot without touching others.
7. Manually inspect one HIGH cluster's raw pipeline files to confirm shared build/deploy.

## Decisions

- Two independent stages (no `workflow_run` chaining): Stage 1 produces a committed snapshot; Stage 2 is a separate, on-demand local agent run.
- Stage 1 outputs are **committed to the repo** under `inventory/<run-id>/` via PR; `inventory/latest` tracks the most recent.
- Stage 2 is delivered as a **plugin agent** (`inventory-analysis`), invoked through the Copilot CLI — not a gh-aw workflow.
- Inputs accept orgs OR repo list OR mix with excludes.
- Dependency depth = manifests + Dependency Graph API (no SBOM).
- Shared taxonomy authored first so deterministic labels and analysis cluster names align.
- Reusable-workflow YAML generation stays with the existing `reusable-workflow-builder` agent — it can consume `clusters.json` as input later.

## Further Considerations

1. **Dependency Graph permission.** GraphQL `dependencyGraphManifests` needs `Dependency graph: read` on the GitHub App. Options: **A) Add the permission to the existing app** (recommended), B) Use a separate `DEP_GRAPH_TOKEN` PAT only when `scan_depth=with-deps`, C) Graceful skip when missing.
2. **Pipeline file caps.** Default to 25 files / 512 KB per repo, record `truncated: true` in `raw/*.json` when hit; overridable via workflow inputs. **Recommend** these defaults.
3. **Inventory snapshot retention.** Committing every scan grows the repo. Options: A) Keep all snapshots (simple, full history; repo grows), B) Keep last N (e.g. 12) and prune older directories in the same PR, C) Move snapshots to a sibling `*-inventory` repo. **Recommend B** with `N=12` as a default workflow input.
4. **Stage 2 model selection.** The Copilot CLI invocation will use whatever model the user's CLI is configured for. Document recommended models in `docs/inventory-analysis.md` and note that analysis quality scales with model context window (large inventories may need a long-context model).
