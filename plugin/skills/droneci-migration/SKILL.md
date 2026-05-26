---
name: droneci-migration
description: Drone CI migration to GitHub Actions — syntax mappings and the migration report template for Pipelines, plugins, services, secrets, triggers, multi-platform pipelines. Load with `migration-core` when migrating Drone CI sources to GitHub Actions.
---

# Drone CI Migration

## Files in this skill

- `mapping.md` — syntax/command mappings from Drone CI to GitHub Actions, including how this platform's secret/credential references translate to `${{ secrets.* }}` / `${{ vars.* }}`.
- `report-template.md` — migration report template (fill placeholders, deliver as PR body and `.github/ci-archive/MIGRATION-README.md`).

## How to use

Always pair with `migration-core` and `actionlint`. Read `mapping.md` before generating workflows; use `report-template.md` for the migration report.
