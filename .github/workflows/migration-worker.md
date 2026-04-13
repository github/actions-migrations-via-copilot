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
        required: true
        type: string
      target_repo_owner:
        description: "Organization that owns the target repository"
        required: true
        type: string
timeout-minutes: 60
concurrency:
  group: migration-worker-${{ inputs.target_repo }}
  cancel-in-progress: false
permissions:
  contents: read
  issues: read
checkout:
  - repository: ${{ inputs.target_repo }}
    github-app:
      app-id: ${{ vars.GH_APP_ID }}
      private-key: ${{ secrets.GH_APP_PEM }}
      owner: ${{ inputs.target_repo_owner }}
    current: true
  - path: ./knowledge
    sparse-checkout: |
      knowledge/
      agents/
env: {}
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
    github-app:
      app-id: ${{ vars.GH_APP_ID }}
      private-key: ${{ secrets.GH_APP_PEM }}
      owner: ${{ inputs.target_repo_owner }}
      repositories: ["*"]
    toolsets: [repos]
network:
  allowed:
    - defaults
    - github
safe-outputs:
  github-app:
    app-id: ${{ vars.GH_APP_ID }}
    private-key: ${{ secrets.GH_APP_PEM }}
  create-pull-request:
    target-repo: ${{ inputs.target_repo }}
    title-prefix: "[Actions Migration] "
    labels: [automation, migration]
    draft: true
    max: 1
  add-comment:
    target: ${{ inputs.tracking_issue }}
    discussions: false
    max: 1
  noop:
---

# CI/CD Migration Worker

Migrate the CI/CD pipeline in `${{ inputs.target_repo }}` from
**${{ inputs.migration_type }}** to GitHub Actions.

## Context

| Key | Value |
|-----|-------|
| Target repository | `${{ inputs.target_repo }}` checked out as workspace root |
| Calling repository | Sparse-checked out at `./knowledge/` (agents and knowledge dirs) |
| Migration type | `${{ inputs.migration_type }}` |
| Tracking issue | #${{ inputs.tracking_issue }} |
| Agent file | `./knowledge/agents/${{ inputs.migration_type }}-migrator.md` |
| Knowledge base | `./knowledge/knowledge/` |

## Instructions

1. **Read the agent file** at `./knowledge/agents/${{ inputs.migration_type }}-migrator.md`.
   If it does not exist, call `noop` with message:
   "No migration agent found for type: ${{ inputs.migration_type }}"

2. **Read knowledge base documents** referenced in the agent file — they are
   all available locally under `./knowledge/knowledge/`.

3. **Execute the migration** following the agent file's instructions against
   the target repository at the workspace root. It defines the full process:
   source file identification, pipeline analysis, workflow creation, file
   archival, report generation, and PR creation. All new/modified files go
   under `.github/`.

4. **Create a pull request** on `${{ inputs.target_repo }}` via `create_pull_request`
   (uses the GH App token to push to the target repo).

5. **Report status** to tracking issue #${{ inputs.tracking_issue }} via `add_comment`
   (uses the default GITHUB_TOKEN on the calling repo):
   - Success: `✅ ${{ inputs.target_repo }}: PR opened — [summary]`
   - Failure: `❌ ${{ inputs.target_repo }}: [reason]`

## Rules

- Only create/modify files in `.github/` — do NOT touch application source code
- Use verified marketplace actions only — no custom actions
- Pin every action to a 40-char commit SHA
- Declare least-privilege permissions — never use `permissions: write-all`
- No placeholder text (TODO, FIXME, CHANGEME) in output files
- The agent file is authoritative — follow its instructions exactly
