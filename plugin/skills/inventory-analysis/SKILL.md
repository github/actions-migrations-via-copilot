---
name: inventory-analysis
description: Clustering heuristics, scoring rules, output schemas, sampling strategy, and `REPORT.md` template for the `inventory-analysis` agent. Load when analyzing a `inventory/<run-id>/` snapshot produced by `repo-scan.yml` to group repositories by technology similarity, score consolidation confidence, and write the `analysis/clusters.json|csv|REPORT.md` outputs.
---

# Inventory Analysis Skill

This skill is the analytical brain of the `inventory-analysis` agent. It defines:

1. The clustering algorithm (cluster key derivation, scoring, refinement).
2. The output file schemas.
3. The sampling rules for representative pipelines.
4. The `REPORT.md` template.

## Inputs (read-only)

The agent operates on a snapshot directory `inventory/<run-id>/` produced by the Stage 1 workflow. The relevant files are:

| File | Required | Purpose |
| --- | --- | --- |
| `manifest.json` | yes | Snapshot metadata (inputs, counts, run-id). |
| `repos.csv` | yes | Per-repo canonical labels. Columns documented in `docs/repo-scan.md#reposcsv-columns`. |
| `dependencies.csv` | no | Per-(repo, source-file, CI dependency) rows extracted from captured pipeline files (reusable workflows, actions, shared libraries, includes, templates, orbs, pipes, plugin images). Columns documented in `docs/repo-scan.md#dependenciescsv-columns`. |
| `pipelines/<org>/<repo>/...` | yes | Raw pipeline files; used for sampling. |
| `manifests/<org>/<repo>/...` | no | Raw manifest files; used opportunistically for tiebreakers. |
| `raw/<org>__<repo>.json` | yes | Detailed per-repo signal dump; used to surface truncation flags in `REPORT.md`. |

## Canonical taxonomy

Every label that appears in a cluster key, cluster name, or recommendation MUST come from one of the tables below. These values mirror the canonical labels that the Stage 1 scripts emit into `repos.csv`. When Stage 1 starts emitting a new label, add a row to the appropriate table here so the agent knows what it means.

### CI platforms

`GitHubActions`, `Jenkins`, `AzureDevOps`, `GitLabCI`, `CircleCI`, `TravisCI`, `Bamboo`, `BitbucketPipelines`, `DroneCI`

### Languages

Values come verbatim from the GitHub Languages API (e.g. `JavaScript`, `TypeScript`, `Python`, `Java`, `Go`, `Ruby`, `C#`, `Rust`, `Kotlin`, `Swift`, `PHP`, `Shell`, `HCL`, `Dockerfile`). The taxonomy does not constrain language names.

### Build tools / package managers

`Maven`, `Gradle`, `npm`, `Yarn`, `pnpm`, `Pip`, `Poetry`, `Setuptools`, `GoModules`, `CargoCrate`, `Bundler`, `DotNet`, `Make`, `Bazel`, `SBT`, `Mix`, `Composer`

For ecosystems where the build tool and package manager are the same (`Maven`, `Gradle`, `SBT`, `DotNet`), the label appears in both `build_tools` and `package_managers`.

### Container & runtime

`Docker`, `DockerCompose`, `Buildpacks`

`has_dockerfile` is `true` whenever any `Docker` signal is present.

### Infrastructure as Code

`Terraform`, `OpenTofu`, `Pulumi`, `Helm`, `Kustomize`, `CloudFormation`, `Bicep`, `ARM`, `Ansible`, `Chef`, `Puppet`

`has_helm` is `true` whenever any `Helm` signal is present.

### Deploy targets

| Cloud | Labels |
| --- | --- |
| AWS | `AWS-S3`, `AWS-Lambda`, `AWS-ECS`, `AWS-EKS`, `AWS-CloudFront`, `AWS-Beanstalk` |
| Azure | `Azure-WebApp`, `Azure-Functions`, `Azure-AKS`, `Azure-StaticWebApps`, `Azure-ContainerApps` |
| GCP | `GCP-CloudRun`, `GCP-GKE`, `GCP-AppEngine`, `GCP-CloudFunctions` |
| Generic | `Kubernetes`, `Heroku`, `Netlify`, `Vercel`, `GitHubPages`, `Cloudflare-Pages`, `Cloudflare-Workers` |
| Container registries | `DockerHub`, `GHCR`, `ECR`, `GCR`, `ACR` |
| Package registries | `NPMRegistry`, `MavenCentral`, `PyPI`, `NuGet`, `RubyGems` |

`deploy_targets` in `repos.csv` may contain multiple semicolon-separated values.

## Cluster key derivation

For each row in `repos.csv`, compute a **cluster key** as a 4-tuple:

```text
(primary_language, top_build_tool, top_ci_platform, top_deploy_target)
```

Where:

- `primary_language` is taken verbatim from the column.
- `top_build_tool` = first (alphabetical, case-insensitive) value in `build_tools` (semicolon-separated). Empty if `build_tools` is empty.
- `top_ci_platform` = first (alphabetical) value in `ci_platforms`.
- `top_deploy_target` = first (alphabetical) value in `deploy_targets`. If empty, use `none`.

Repos with the same 4-tuple form a tentative cluster.

## Scoring (HIGH / MEDIUM / LOW)

For each tentative cluster, count how many of the four dimensions are non-empty for **every** member:

| Matching non-empty dimensions | Confidence |
| --- | --- |
| 4 | `HIGH` |
| 2–3 | `MEDIUM` |
| 0–1 | `LOW` — discard; members go to "unclustered" |

Singleton clusters (one member) are emitted with confidence reduced by one tier (HIGH → MEDIUM, MEDIUM → LOW) — a cluster of one is rarely actionable.

## Refinement via CI dependency overlap (optional)

If `dependencies.csv` exists it contains CI-side dependencies — reusable workflows, marketplace actions, shared libraries, includes, templates, orbs, pipes, plugin images. Repos in the same cluster that share the same CI building blocks are stronger consolidation candidates; repos that pull in idiosyncratic dependencies are weaker candidates.

1. For each repo in a cluster, collect the set of `dependency_ref` values (ignore `version`).
2. Compute the cluster centroid = the union of all member dependency sets.
3. For each member, compute Jaccard similarity (`|A ∩ B| / |A ∪ B|`) between its dependency set and the centroid.
4. Members with similarity < 0.2 (or with an empty dependency set in a cluster where the centroid is non-empty) are flagged `outlier: true` in `clusters.json` but remain in the cluster.
5. When most members share a specific external reference (e.g. `my-org/shared-ci-templates`, `circleci/aws-cli`), surface it in the cluster's `recommendation` — it's the existing reusable building block to start from.

If 3+ outliers share a refined sub-key, you MAY split them into a sub-cluster with the same key plus a numeric suffix (e.g. `Java|Maven|Jenkins|AWS-ECS:2`).

## Representative pipelines

For each emitted cluster:

1. Collect every pipeline file under `inventory/<run-id>/pipelines/<owner>/<repo>/` for cluster members.
2. Sort by `loc` (descending) — read this from `raw/<owner>__<repo>.json`.
3. Take up to **3** files. Record their snapshot-relative paths in `clusters.json[*].representative_pipelines`.

## Output schemas

### `analysis/clusters.json`

```json
{
  "snapshot": "inventory/1234567890",
  "generated_at": "2026-05-29T14:00:00Z",
  "input_repo_count": 42,
  "clustered_repo_count": 35,
  "unclustered_repo_count": 7,
  "clusters": [
    {
      "cluster_id": "cluster-001",
      "key": "Java|Maven|Jenkins|AWS-ECS",
      "label": "Java + Maven + Jenkins → AWS-ECS",
      "confidence": "HIGH",
      "dimensions": {
        "primary_language": "Java",
        "top_build_tool": "Maven",
        "top_ci_platform": "Jenkins",
        "top_deploy_target": "AWS-ECS"
      },
      "member_count": 8,
      "members": [
        { "org": "my-org-a", "repo": "service-foo", "outlier": false },
        { "org": "my-org-a", "repo": "service-bar", "outlier": true }
      ],
      "representative_pipelines": [
        "pipelines/my-org-a/service-foo/Jenkinsfile",
        "pipelines/my-org-a/service-bar/Jenkinsfile",
        "pipelines/my-org-b/service-qux/Jenkinsfile"
      ],
      "recommendation": "Strong candidate for `reusable-java-maven-ecs.yml`."
    }
  ],
  "unclustered": [
    { "org": "my-org-c", "repo": "experimental", "reason": "LOW confidence: only primary_language populated" }
  ]
}
```

### `analysis/clusters.csv`

Flat per-(cluster, repo) rows for spreadsheet review:

```csv
cluster_id,key,confidence,org,repo,outlier
cluster-001,Java|Maven|Jenkins|AWS-ECS,HIGH,my-org-a,service-foo,false
cluster-001,Java|Maven|Jenkins|AWS-ECS,HIGH,my-org-a,service-bar,true
```

Unclustered repos appear with `cluster_id=`, `confidence=UNCLUSTERED`.

### `analysis/REPORT.md`

Use this template verbatim (fill in the bracketed sections):

```markdown
# Inventory Analysis — [snapshot path]

**Generated:** [ISO timestamp]
**Snapshot inputs:** [echo `manifest.json#/inputs`]
**Repositories:** [N] scanned · [N] clustered · [N] unclustered

## Top 5 clusters

| Rank | Cluster | Confidence | Members | Recommendation |
| --- | --- | --- | --- | --- |
| 1 | [label] | HIGH | 12 | [one-line recommendation] |
| ... | ... | ... | ... | ... |

## Cluster details

### [cluster-001] [label]

- **Confidence:** HIGH
- **Members ([N]):** `org-a/repo-x`, `org-a/repo-y`, ...
- **Outliers:** `org-a/repo-z` (Jaccard 0.14)
- **Representative pipelines:**
  - [`pipelines/org-a/repo-x/Jenkinsfile`](../pipelines/org-a/repo-x/Jenkinsfile)
  - ...
- **Recommendation:** [text]

[Repeat per cluster — sorted by member_count desc, then confidence desc]

## Unclustered repositories

| Repo | Reason |
| --- | --- |
| `org-c/experimental` | LOW confidence: only primary_language populated |
| ... | ... |

## Truncation warnings

[List any repos where `raw/<repo>.json#truncated == true`, with the suspected reason.]

## Suggested next actions

1. **Build reusable workflows** for clusters: [list HIGH-confidence cluster labels with 3+ members].
2. **Re-scan if `dependencies.csv` looks sparse** [list any clusters whose members captured pipelines but no CI deps — likely a missing path pattern in `extract.js`].
3. **Expand the taxonomy** for these unmapped signals: [list any unrecognized labels seen in `signals_json`].
```

## CLI examples

```bash
# Analyze the latest snapshot (the most common case)
copilot --agent inventory-analysis "Analyze inventory/latest"

# Analyze a specific historical snapshot
copilot --agent inventory-analysis "Analyze inventory/1717000000"

# Apply a filter
copilot --agent inventory-analysis "Analyze inventory/latest. Focus on repos with deploy_targets including AWS-*."
```

## Validation checklist

Before finishing, verify:

- [ ] All three output files exist under `inventory/<run-id>/analysis/`.
- [ ] No files were created or modified outside that directory.
- [ ] Every `cluster_id` is unique.
- [ ] Every member `(org, repo)` exists as a row in `repos.csv`.
- [ ] Every `representative_pipelines[*]` path resolves to a file in the snapshot.
- [ ] Every cluster label uses canonical taxonomy values.
- [ ] The sum of `clustered_repo_count + unclustered_repo_count` equals `input_repo_count`.
