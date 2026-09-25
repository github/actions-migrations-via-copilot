---
name: migration-core
description: 5-phase migration process, security guardrails, deliverables, archival protocol, and the 10-item completion checklist for any CI/CD migration to GitHub Actions. Load at the start of every migration.
---

# Migration Core

## 5-Phase Workflow

All migrations follow these phases **in order** — skipping any phase is a completion failure.

### Phase 1 — Source

- **REQUIRE** actual source CI/CD files from the user. Refuse to proceed without them.
- **NEVER** invent workflows from descriptions, requirements, or assumptions.
- Common filenames: `Jenkinsfile`, `azure-pipelines.yml`, `.circleci/config.yml`, `.gitlab-ci.yml`, `.travis.yml`, `bitbucket-pipelines.yml`, `bamboo-specs.yml`, `.drone.yml` (and any included/referenced files).

### Phase 2 — Analyze

Examine the source thoroughly. Identify:

- Pipeline/job/stage structure and dependencies
- Triggers, conditions, branching strategy
- Agents/executors/containers → GitHub runner mapping
- Credential bindings, secrets, env vars
- Caching, artifacts, matrix builds, parallelism
- Platform-specific features with no direct Actions equivalent (see the platform skill's `mapping.md`)

### Phase 3 — Convert

- Convert **only** what's in the source — no added functionality.
- Use the platform skill's `mapping.md` for syntax translations.
- Use only marketplace actions from verified creators (see Guardrails below).
- Translate triggers, conditional logic, env/secrets references, services, artifacts, caches.
- Expand all platform-specific includes/templates/shared-libraries inline.
- Add comments explaining non-obvious conversion choices.

### Phase 4 — Validate

Load and follow the `actionlint` skill: install the tool if needed, run it against all generated workflows, resolve every finding, and capture the real output for the report.

### Phase 5 — Document

Before writing or publishing any report, follow **Safe Migration Reports** below.
Review validation output and examples for credential values; report only names
and references, not values.

1. Write `.github/ci-archive/MIGRATION-README.md` using the platform skill's `report-template.md`, filled with real data — no placeholders, real actionlint output.
2. **MOVE** original CI/CD files into `.github/ci-archive/` and **DELETE** them from their original locations (see Archival below).
3. Deliver the report via PR: update an existing PR on the branch if present; otherwise create a new one. If PR creation/update is unavailable, the `MIGRATION-README.md` is the sole report.

---

## Guardrails

### ❌ Never do

- Create workflows without a real source CI/CD file.
- Generate pipelines from descriptions or assumptions.
- Add functionality not in the source.
- Write custom actions, scripts, or bespoke integrations — find a marketplace action.
- Use unverified, community, or deprecated actions.
- Skip validation, leave originals in their original location, or ship placeholder text in the PR/report.

### ✅ Always do

- Work exclusively from the provided source files.
- Use only **verified creators** on the [GitHub Marketplace](https://github.com/marketplace) — e.g. `actions/*`, `azure/*`, `aws-actions/*`, `google-github-actions/*`.
- Use the **latest stable version** of each action.
- **Pin every action to a commit SHA** (never a tag/branch); add a comment with the SHA→version mapping.
- Apply **least-privilege** `permissions:` blocks.
- Document every secret and variable the migrated workflow requires.

### Action version verification

> **Never emit a commit SHA that is not present verbatim in the output of a
> command you ran in this session.** A fabricated SHA either fails at dispatch
> time or resolves to an unintended commit.

**Step 1 — check the shipped catalog first.** `pinned-actions.json` in this skill
directory holds verified SHAs for the actions this product emits most often. It
ships with the plugin, so it works with no network at all:

```bash
grep -A2 '"actions/checkout"' plugin/skills/migration-core/pinned-actions.json
```

If the action is in the catalog, use that SHA and move on. Check `resolved_on`
in the file — if it is more than about six months old, say so in the report so
the user knows the pins are due a refresh.

**Step 2 — capability probe.** Only for actions the catalog does not cover.
Network access is not guaranteed; offline and air-gapped installs are supported.
Run this and branch on the result:

```bash
gh auth status >/dev/null 2>&1 && echo NETWORK_OK || echo NETWORK_UNAVAILABLE
```

**Step 3a — if `NETWORK_OK`.** Resolve the latest release tag, then resolve that
tag to a commit SHA:

```bash
gh api repos/OWNER/REPO/releases/latest --jq .tag_name
gh api repos/OWNER/REPO/commits/TAG --jq .sha
```

Use `commits/TAG` rather than `git/ref/tags/TAG` — for an annotated tag the
latter returns the tag object SHA, not the commit SHA.

If the repository publishes no releases, take the default-branch head:

```bash
gh api "repos/OWNER/REPO/commits?per_page=1" --jq '.[0].sha'
```

**Step 3b — if `NETWORK_UNAVAILABLE`.** Do not guess, and do not write a workflow
step you cannot pin. Stop and tell the user which actions need resolving, so they
can either grant network access or confirm the pin themselves. An unpinned action
is a real defect — the quality gate will flag it, and it should.

A fully resolved pin looks like this:

```yaml
# actions/checkout v7.0.1
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
```

### Secrets and variables

- `${{ secrets.NAME }}` — sensitive credentials; never log or echo, never put values in workflow files.
- `${{ vars.NAME }}` — non-sensitive configuration.
- Org-level for shared values; repo-level for project-specific values.
- Platform-specific secret syntax mappings live in the platform skill's `mapping.md`.

### Safe Migration Reports

- Document secret and variable names, purpose, scope, and `${{ secrets.NAME }}` / `${{ vars.NAME }}` references, never credential values.
- Before writing the report, review all prose, tables, examples, and validation output. Remove credential values and use `[REDACTED]` when an omission must be shown; redaction is not an unfinished placeholder.
- Use the same reviewed content for the report file, PR body, comments, and final response. Do not paste raw source files or logs containing credentials.
- If a suspected credential cannot be safely removed, stop report publication and warn without repeating the value. Do not claim the migration is complete while publication is blocked.
- Never disable secret scanning or push protection to deliver a report. If a value may already have been exposed, advise revocation or rotation and follow the repository's incident process.

---

## Deliverables and Archival

### Required deliverables

1. Runnable `.github/workflows/*.yml` replicating source functionality.
2. All required secrets/variables documented with names and purpose.
3. Conversion explanations as comments in workflows and notes in the report.
4. Real `actionlint` output pasted into the report (see `actionlint` skill).
5. Source files archived and deleted from original locations.
6. `.github/ci-archive/MIGRATION-README.md` — complete, no placeholders.
7. Pull Request with the report as its body (or `MIGRATION-README.md` as fallback).

### Archival protocol

```bash
mkdir -p .github/ci-archive/
```

**MOVE** (don't copy) source CI/CD files. Examples:

| Original | Archive destination |
|---|---|
| `Jenkinsfile` | `.github/ci-archive/Jenkinsfile` |
| `azure-pipelines.yml` | `.github/ci-archive/azure-pipelines.yml` |
| `.circleci/config.yml` | `.github/ci-archive/circleci-config.yml` (delete `.circleci/` dir) |
| `.gitlab-ci.yml` | `.github/ci-archive/.gitlab-ci.yml` |
| `.travis.yml` | `.github/ci-archive/.travis.yml` |
| `.drone.yml` | `.github/ci-archive/.drone.yml` |
| `bitbucket-pipelines.yml` | `.github/ci-archive/bitbucket-pipelines.yml` |
| `bamboo-specs.yml` | `.github/ci-archive/bamboo-specs.yml` |

Verify nothing remains in the original locations.

---

## Completion Checklist (10 items)

Migration is **NOT COMPLETE** until all 10 are true:

1. Source file(s) provided and analyzed
2. Workflow(s) accurately replicate source functionality
3. Only verified marketplace actions used, latest stable versions, pinned to SHAs
4. `actionlint` executed per the `actionlint` skill; real output captured
5. All required secrets and variables documented
6. Original CI/CD files moved to `.github/ci-archive/` and deleted from original locations
7. `.github/ci-archive/MIGRATION-README.md` written from the platform's `report-template.md`, no placeholders
8. Migration report delivered via PR (existing PR updated, or new PR created) where possible
9. All guardrails above satisfied
10. Response ends with:

> Migration complete. MIGRATION-README.md created and Pull Request updated/created with migration report.

(If PR was unavailable: *Migration complete. MIGRATION-README.md created in .github/ci-archive/*)
