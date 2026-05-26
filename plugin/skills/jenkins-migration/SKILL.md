---
name: jenkins-migration
description: Jenkins migration to GitHub Actions — syntax mappings and the migration report template for Pipelines (declarative + scripted), shared libraries, Groovy scripts, credential bindings, agent labels, parallel stages, plugin replacements. Load with `migration-core` when migrating Jenkins sources to GitHub Actions.
---

# Jenkins Migration

## Files in this skill

- `mapping.md` — syntax/command mappings from Jenkins to GitHub Actions, including how this platform's secret/credential references translate to `${{ secrets.* }}` / `${{ vars.* }}`.
- `pipeline.md` — declarative and scripted pipeline conversion patterns.
- `groovy.md` — Groovy script and shared-library expansion patterns.
- `report-template.md` — migration report template (fill placeholders, deliver as PR body and `.github/ci-archive/MIGRATION-README.md`).

## How to use

Always pair with `migration-core` and `actionlint`. Read `mapping.md` before generating workflows; use `report-template.md` for the migration report.
