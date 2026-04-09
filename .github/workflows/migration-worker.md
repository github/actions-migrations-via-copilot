---
name: Migration Worker
description: >
  Agentic workflow that migrates a single repository's CI/CD pipeline
  to GitHub Actions. Runs from .github-private, checks out the target
  repo, performs the migration, and opens a cross-repo PR.
on:
  workflow_dispatch:
    inputs:
      target_repo:
        description: "Target repository (owner/repo format)"
        required: true
        type: string
      migration_type:
        description: "CI platform to migrate from (Jenkins, GitLab, etc.)"
        required: true
        type: string
      tracking_issue:
        description: "Parent tracking issue number for status reporting"
        required: false
        type: string
timeout-minutes: 60
concurrency:
  group: migration-worker-${{ inputs.target_repo }}
  cancel-in-progress: false
permissions:
  contents: read
  issues: read
jobs:
  checkout-target:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout target repository
        uses: actions/checkout@v6
        with:
          repository: ${{ inputs.target_repo }}
          token: ${{ secrets.ISSUE_SUBMIT_TOKEN }}
          path: target-repo
      - name: Upload target repo as artifact
        uses: actions/upload-artifact@v4
        with:
          name: target-repo
          path: target-repo/
steps:
  - name: Download target repo
    uses: actions/download-artifact@v4
    with:
      name: target-repo
      path: ./
tools:
  bash:
    - "cat"
    - "echo"
    - "ls:*"
    - "pwd"
    - "find:*"
    - "grep:*"
    - "head"
    - "tail"
    - "sort"
    - "wc"
    - "date"
    - "mkdir:*"
    - "base64:*"
    - "jq:*"
  github:
    github-token: ${{ secrets.ISSUE_SUBMIT_TOKEN }}
    toolsets: [repos]
network:
  allowed:
    - defaults
    - github
safe-outputs:
  github-token: ${{ secrets.ISSUE_SUBMIT_TOKEN }}
  create-pull-request:
    target-repo: ${{ inputs.target_repo }}
    title-prefix: "[Actions Migration] "
    labels: [automation, migration]
    draft: true
    max: 1
  add-comment:
    target: ${{ inputs.tracking_issue }}
    max: 1
  noop:
---

# CI/CD Migration Worker

You are a CI/CD migration agent. Your job is to migrate the CI/CD pipeline in
this repository from **${{ inputs.migration_type }}** to GitHub Actions.

## Context

- **Target repository:** `${{ inputs.target_repo }}` (checked out as your workspace)
- **Migration type:** `${{ inputs.migration_type }}`
- **Knowledge base:** Available at `./knowledge/` in the `.github-private` repo (read via GitHub API if needed)

## Migration Process

1. **Identify CI source files** in the workspace. Look for:
   - `Jenkinsfile`, `*.jenkinsfile` (Jenkins)
   - `.gitlab-ci.yml` (GitLab)
   - `.circleci/config.yml` (CircleCI)
   - `.travis.yml` (Travis CI)
   - `azure-pipelines.yml` (Azure DevOps)
   - `.drone.yml` (Drone CI)
   - `bitbucket-pipelines.yml` (Bitbucket)
   - `bamboo-specs/*.yml` (Bamboo)

   If no CI source files are found, call `noop` with message: "No CI source files found in ${{ inputs.target_repo }}"

2. **Analyze the pipeline** — understand stages, steps, triggers, environment variables, secrets, and deployment targets.

3. **Create the GitHub Actions workflow** at `.github/workflows/ci.yml`:
   - Map all stages/steps to equivalent Actions
   - Pin ALL actions to 40-character commit SHAs (not version tags)
   - Add a version comment next to each SHA (e.g., `# v4.2.0`)
   - Declare least-privilege `permissions:` at the top level
   - Use GitHub Actions secrets syntax (e.g., `secrets.MY_SECRET`) for all credentials — never hardcode
   - Document any secrets the workflow requires

4. **Archive the original CI files** — move them to `.github/ci-archive/`

5. **Create a migration report** at `.github/ci-archive/MIGRATION-README.md` containing:
   - What was migrated and from which platform
   - Mapping table: original step → Actions equivalent
   - Required secrets and variables
   - Any manual steps needed post-migration
   - Validation results (if actionlint is available)

6. **Open a pull request** via `create_pull_request` with:
   - Title: `Migrate ${{ inputs.migration_type }} pipeline to GitHub Actions`
   - Body: The migration report content (summary of changes, secrets needed, validation results)

7. **Report status** — if a tracking issue was provided (${{ inputs.tracking_issue }}), post a comment via `add_comment`:
   - On success: `✅ ${{ inputs.target_repo }}: PR opened — [migration summary]`
   - On failure/no changes: `❌ ${{ inputs.target_repo }}: [reason]`

## Rules

- Do NOT modify application source code — only create/modify files in `.github/`
- Do NOT create custom actions — use verified marketplace actions only
- Do NOT use `permissions: write-all` — declare least-privilege permissions
- Do NOT leave placeholder text (TODO, FIXME, CHANGEME) in output files
- EVERY action must be pinned to a 40-char commit SHA
