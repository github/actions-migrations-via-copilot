---
name: azure-devops-migration
description: Azure DevOps migration to GitHub Actions — syntax mappings and the migration report template for YAML pipelines, templates, variable groups, service connections, deployment jobs, stages, conditional logic. Load with `migration-core` when migrating Azure DevOps sources to GitHub Actions.
---

# Azure DevOps Migration

## Files in this skill

- `mapping.md` — syntax/command mappings from Azure DevOps to GitHub Actions, including how this platform's secret/credential references translate to `${{ secrets.* }}` / `${{ vars.* }}`.
- `report-template.md` — migration report template (fill placeholders, deliver as PR body and `.github/ci-archive/MIGRATION-README.md`).

## How to use

Always pair with `migration-core`. Read `mapping.md` before generating workflows; use `report-template.md` for the migration report.
