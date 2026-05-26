---
name: bamboo-migration
description: Bamboo migration to GitHub Actions — syntax mappings and the migration report template for Build plans, deployment projects, tasks, requirements, variables, plan branches. Load with `migration-core` when migrating Bamboo sources to GitHub Actions.
---

# Bamboo Migration

## Files in this skill

- `mapping.md` — syntax/command mappings from Bamboo to GitHub Actions, including how this platform's secret/credential references translate to `${{ secrets.* }}` / `${{ vars.* }}`.
- `report-template.md` — migration report template (fill placeholders, deliver as PR body and `.github/ci-archive/MIGRATION-README.md`).

## How to use

Always pair with `migration-core` and `actionlint`. Read `mapping.md` before generating workflows; use `report-template.md` for the migration report.
