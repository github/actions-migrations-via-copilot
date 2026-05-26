---
name: bitbucket-migration
description: Bitbucket Pipelines migration to GitHub Actions — syntax mappings and the migration report template for Pipelines, Pipes, parallel steps, branch/pull-request workflows, deployments, variables. Load with `migration-core` when migrating Bitbucket Pipelines sources to GitHub Actions.
---

# Bitbucket Pipelines Migration

## Files in this skill

- `mapping.md` — syntax/command mappings from Bitbucket Pipelines to GitHub Actions, including how this platform's secret/credential references translate to `${{ secrets.* }}` / `${{ vars.* }}`.
- `report-template.md` — migration report template (fill placeholders, deliver as PR body and `.github/ci-archive/MIGRATION-README.md`).

## How to use

Always pair with `migration-core`. Read `mapping.md` before generating workflows; use `report-template.md` for the migration report.
