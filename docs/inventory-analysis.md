# Inventory Analysis — Stage 2 Operator Guide

The `inventory-analysis` agent is Stage 2 of the repo pipeline inventory feature. It reads a snapshot produced by the [`repo-scan.yml`](../.github/workflows/repo-scan.yml) workflow (Stage 1) and groups repositories into technology-similarity clusters, then writes the analysis back into the same snapshot directory.

> Stage 1 setup and snapshot layout are documented in [`repo-scan.md`](repo-scan.md).

## Prerequisites

| Requirement                                                     | Notes                                                                                     |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Stage 1 snapshot merged to default branch                       | At least `inventory/<run-id>/manifest.json` + `repos.csv` + `pipelines/` must be present. |
| Local checkout of this repo                                     | The agent operates on local files; it does not call any API.                              |
| GitHub Copilot CLI with the `actions-migrator` plugin installed | See [`plugin/README.md`](../plugin/README.md).                                            |

## Running the analysis

From the repo root, in an interactive Copilot CLI session or via the CLI directly:

```bash
# Analyze the most recent snapshot (recommended)
copilot --agent inventory-analysis "Analyze inventory/latest"

# Analyze a specific historical snapshot
copilot --agent inventory-analysis "Analyze inventory/1717000000"

# Apply a filter
copilot --agent inventory-analysis "Analyze inventory/latest. Focus on repos with deploy_targets including AWS-*."
```

The agent resolves `inventory/latest` (a text file containing the most recent `<run-id>`) and reads everything under that snapshot directory. It then writes three files:

```text
inventory/<run-id>/analysis/
├── clusters.json   # machine-readable
├── clusters.csv    # flat per-(cluster, repo) rows for spreadsheets
└── REPORT.md       # human-readable executive summary
```

## What the agent does

1. **Resolve** the snapshot path and parse `manifest.json` + `repos.csv` (plus `dependencies.csv` when present).
2. **Cluster** every repo by a 4-tuple key: `(primary_language, top_build_tool, top_ci_platform, top_deploy_target)`.
3. **Score** each cluster `HIGH` / `MEDIUM` / `LOW` based on how many of the four dimensions are populated for every member. `LOW` clusters are dissolved; their members appear in the `unclustered` list.
4. **Refine** (if `dependencies.csv` exists) — Jaccard similarity on the top 50 packages flags outliers within each cluster.
5. **Sample** up to 3 representative pipeline files per cluster (largest by LOC).
6. **Write** the three output files under `analysis/`.

See [`plugin/skills/inventory-analysis/SKILL.md`](../plugin/skills/inventory-analysis/SKILL.md) for the full algorithm and output schemas.

## Committing the analysis

The analysis files are committed separately from the snapshot — typically the user reviews `REPORT.md` first and opens a PR with just the `analysis/` directory:

```bash
git checkout -b inventory-analysis/run-<run-id>
git add inventory/<run-id>/analysis/
git commit -m "analysis: cluster repo-scan snapshot run-<run-id>"
git push -u origin HEAD
gh pr create --fill
```

## What to do with the report

The top-of-report "Suggested next actions" block typically recommends:

1. **Build reusable workflows** — for each `HIGH`-confidence cluster with 3+ members, invoke the [`reusable-workflow-builder`](../agents/reusable-workflow-builder.md) agent with the cluster's member repos as the scope.
2. **Re-scan with `scan_depth=with-deps`** — if the current snapshot is shallow, more refinement is unlocked by Dependency Graph data.
3. **Extend the taxonomy** — for any unrecognized signals surfaced in the report.

## Troubleshooting

| Symptom                                    | Likely cause                                                                          | Fix                                                                                                 |
| ------------------------------------------ | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Agent refuses with "snapshot not found"    | `inventory/latest` is missing or points at a deleted run-id.                          | Re-run Stage 1 or pass an explicit `inventory/<run-id>` path.                                       |
| Almost every repo lands in `unclustered`   | `repos.csv` rows have only `primary_language` populated (no CI/build/deploy signals). | Extend signals (see Stage 1 guide) and re-scan.                                                     |
| `REPORT.md` lists many truncation warnings | Stage 1 hit the file/byte caps for monorepos.                                         | Raise `MAX_PIPELINE_FILES_PER_REPO` / `MAX_PIPELINE_BYTES_PER_REPO` in `repo-scan.yml` and re-scan. |
| Singletons everywhere                      | Cluster keys are too specific because deploy_targets are heterogeneous.               | Re-run the agent with a filter (e.g. `Focus on AWS-* deploys only.`) to constrain the universe.     |

## Related

- [`repo-scan.md`](repo-scan.md) — Stage 1 (produce the snapshot).
- [`../plugin/skills/inventory-analysis/SKILL.md`](../plugin/skills/inventory-analysis/SKILL.md) — algorithm + output schemas.
- [`../agents/reusable-workflow-builder.md`](../agents/reusable-workflow-builder.md) — natural next step for HIGH-confidence clusters.
