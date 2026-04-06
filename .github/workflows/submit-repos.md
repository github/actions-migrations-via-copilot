---
name: Submit Repositories for Migration
description: >
  Iterates over repositories in configured organizations, reads each
  repository's GH_MIGRATION_TYPE custom property, matches it against
  MIGRATION_TYPE_PROMPTS, and hands off migration work to the Copilot
  coding agent in the target repository.
on:
  schedule:
    weekly
  workflow_dispatch:
timeout-minutes: 60
concurrency:
  group: submit-repos
  cancel-in-progress: false
permissions:
  contents: read
  issues: read
steps:
  - name: Generate GitHub App token
    id: app-token
    uses: actions/create-github-app-token@v3
    with:
      app-id: ${{ vars.GH_APP_ID }}
      private-key: ${{ secrets.GH_APP_PEM }}
      owner: ${{ github.repository_owner }}
  - name: Load configuration
    run: |
      set -euo pipefail
      mkdir -p /tmp/gh-aw/submit-repos
      echo '${{ vars.ORGANIZATIONS }}' > /tmp/gh-aw/submit-repos/organizations.json
      echo '${{ vars.MIGRATION_TYPE_PROMPTS }}' > /tmp/gh-aw/submit-repos/migration-type-prompts.json
      echo '${{ vars.BATCH_SIZE }}' > /tmp/gh-aw/submit-repos/batch-size.txt
    env:
      GH_TOKEN: ${{ steps.app-token.outputs.token }}
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
    - "uniq"
    - "wc"
    - "date"
    - "mkdir:*"
    - "base64:*"
    - "gh:*"
    - "jq:*"
  github:
    github-token: ${{ steps.app-token.outputs.token }}
    toolsets: [repos, issues]
    allowed-repos:
      - "*/*"
network:
  allowed:
    - defaults
    - github
safe-outputs:
  github-token: ${{ secrets.ISSUE_SUBMIT_TOKEN }}
  create-issue:
    title-prefix: "[Actions Migration] "
    labels: [automation, migration]
    close-older-issues: true
    assignees: [copilot]
    target-repo: "*"
    max: 100
  create-issue:
    title-prefix: "[migration-report] "
    labels: [automation, report]
    close-older-issues: true
    group-by-day: true
    max: 1
  noop:
---

# Submit Repositories for Migration

You are an orchestrator that scans repositories across organizations and submits
eligible ones for CI/CD migration to GitHub Actions.

## Configuration

Read the following configuration files from `/tmp/gh-aw/submit-repos/`:

1. **`organizations.json`** — JSON array of GitHub organization names to scan
2. **`migration-type-prompts.json`** — JSON object mapping migration type to agent prompt filename (e.g., `{"Jenkins": "jenkins-migrator.md", "GitLab": "gitlab-migrator.md", ...}`)
3. **`batch-size.txt`** — Maximum repositories to process per organization

Also read the agent prompt files from the checked-out repository under `agents/` to have the full prompt text available for each migration type.

## Process

For each organization in `organizations.json`:

1. **List repositories** using `gh api --paginate "/orgs/<org>/repos?per_page=100&type=all"`. Skip archived repos and forks.

2. **For each repository**, read the `GH_MIGRATION_TYPE` custom property:
   ```
   gh api "/repos/<org>/<repo>/properties/values" --jq '.[] | select(.property_name=="GH_MIGRATION_TYPE") | .value'
   ```

3. **Skip the repository if:**
   - `GH_MIGRATION_TYPE` is `"None"`, empty, or unset
   - No matching key exists in the migration type prompts mapping
   - An open migration issue already exists (search: `repo:<org>/<repo> is:issue is:open "gh-aw-workflow-id:" in:body "[Actions Migration]" in:title`)

4. **For eligible repositories:**
   - Look up the agent prompt filename from the mapping (e.g., `Jenkins` → `jenkins-migrator.md`)
   - Read the agent file contents from `agents/<filename>`
   - Create an issue in the target repository using `create_issue` with:
     - `repo`: `<org>/<repo>`
     - `title`: `Migrate <MigrationType> CI/CD to GitHub Actions`
     - `body`: The full contents of the agent prompt file
     - The issue will be automatically assigned to Copilot via the `assignees: [copilot]` configuration

5. **Track results** — maintain a running tally of:
   - Repositories scanned
   - Migrations submitted
   - Repositories skipped (and reason: already has open issue, no migration type, type is "None")
   - Errors encountered

6. **Respect batch size** — stop processing an organization after reaching the batch size limit.

## After Processing All Organizations

Create a summary report issue using the second `create_issue` (with `[migration-report]` prefix) containing:

```markdown
## Migration Submission Report - <YYYY-MM-DD>

| Metric | Count |
|--------|-------|
| Organizations scanned | N |
| Repositories scanned | N |
| Migrations submitted | N |
| Repositories skipped | N |
| Errors encountered | N |

### Submissions

| Repository | Migration Type | Agent | Status |
|------------|---------------|-------|--------|
| org/repo   | Jenkins       | jenkins-migrator.md | Submitted |

### Skipped

| Repository | Reason |
|------------|--------|
| org/repo   | Already has open migration issue |
| org/repo2  | GH_MIGRATION_TYPE is "None" |
```

## If No Repositories Require Migration

You MUST call the `noop` tool with a message explaining why:
```json
{"noop": {"message": "No action needed: no eligible repositories found across N organizations (M repositories scanned, all either already submitted or have no migration type set)"}}
```

Do NOT skip calling noop — the workflow will fail if no safe output tool is called.
