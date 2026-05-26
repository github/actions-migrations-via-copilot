---
name: circleci-migration
description: CircleCI migration to GitHub Actions — syntax mappings and the migration report template for Workflows, jobs, Orbs, executors, contexts, parameters, matrix jobs, approval gates. Load with `migration-core` when migrating CircleCI sources to GitHub Actions.
---

# CircleCI Migration

## Files in this skill

- `mapping.md` — syntax/command mappings from CircleCI to GitHub Actions, including how this platform's secret/credential references translate to `${{ secrets.* }}` / `${{ vars.* }}`.
- `report-template.md` — migration report template (fill placeholders, deliver as PR body and `.github/ci-archive/MIGRATION-README.md`).

## How to use

Always pair with `migration-core`. Read `mapping.md` before generating workflows; use `report-template.md` for the migration report.
