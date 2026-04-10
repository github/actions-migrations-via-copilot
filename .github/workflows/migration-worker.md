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
env:
  MIGRATION_TYPE_PROMPTS: ${{ vars.MIGRATION_TYPE_PROMPTS }}
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
    owner: ${{ inputs.target_repo_owner }}
    repositories: ["*"]
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

- **Target repository:** `${{ inputs.target_repo }}` (checked out as your workspace via `current: true`)
- **Migration type:** `${{ inputs.migration_type }}`
- **Knowledge base:** Available at `./knowledge/`
- **Agent prompts:** Available at `./agents/`

## Instructions

1. **Determine the agent file** — the repository variable `MIGRATION_TYPE_PROMPTS`
   contains a JSON mapping of migration types to agent filenames. Parse it and
   look up `${{ inputs.migration_type }}` to get the agent file path under
   `./knowledge/agents/`.

   If no matching entry exists, call `noop` with message:
   "No migration agent found for type: ${{ inputs.migration_type }}"

2. **Read the agent file** — use `cat` to read the full contents of the matched
   agent file. This file contains the specialized migration prompt, knowledge
   base references, platform-specific expertise, and step-by-step process.

3. **Read knowledge base documents** referenced in the agent file — the agent
   file will reference documents under `./knowledge/` (migration
   workflow, standards, guardrails, action mappings, patterns, report templates).
   Read them with `cat` as needed — they are all available locally.

4. **Execute the migration** by following the agent file's instructions exactly.
   The agent file defines the full migration process including:
   - Source file identification
   - Pipeline analysis
   - GitHub Actions workflow creation
   - Original file archival
   - Migration report generation
   - Pull request creation (title, body, and content)

5. **Report status** — if a tracking issue was provided (${{ inputs.tracking_issue }}),
   post a comment via `add_comment`:
   - On success: `✅ ${{ inputs.target_repo }}: PR opened — [migration summary]`
   - On failure/no changes: `❌ ${{ inputs.target_repo }}: [reason]`

## Rules

- Do NOT modify application source code — only create/modify files in `.github/`
- Do NOT create custom actions — use verified marketplace actions only
- Do NOT use `permissions: write-all` — declare least-privilege permissions
- Do NOT leave placeholder text (TODO, FIXME, CHANGEME) in output files
- EVERY action must be pinned to a 40-char commit SHA
- ALWAYS follow the agent file's instructions — it is the authoritative source
  for platform-specific migration logic
