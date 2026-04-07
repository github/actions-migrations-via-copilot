---
name: Submit Repositories for Migration
description: >
  Hybrid orchestrator: deterministic JS scans repos and computes eligible
  migrations (steps), then a minimal agent creates issues via safe outputs.
  Combines reliability of code with gh-aw write guardrails.
on:
  schedule:
    weekly
  workflow_dispatch:
timeout-minutes: 360
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

  - name: Scan repositories and compute eligible migrations
    id: scan
    uses: actions/github-script@v8.0.0
    env:
      MIGRATION_TYPE_PROMPTS: ${{ vars.MIGRATION_TYPE_PROMPTS }}
      BATCH_SIZE_VAR: ${{ vars.BATCH_SIZE }}
      ORGANIZATIONS: ${{ vars.ORGANIZATIONS }}
    with:
      github-token: ${{ steps.app-token.outputs.token }}
      script: |
        const fs = require('fs')
        const path = require('path')

        const orgs = JSON.parse(process.env.ORGANIZATIONS)
        const prompts = JSON.parse(process.env.MIGRATION_TYPE_PROMPTS)
        const batchSize = parseInt(process.env.BATCH_SIZE_VAR) || 100

        const eligible = []
        const skipped = []
        const errors = []
        let totalScanned = 0

        for (const org of orgs) {
          let submitted = 0
          core.info(`Scanning organization: ${org}`)

          let repos
          try {
            repos = await github.paginate(github.rest.repos.listForOrg, {
              org, per_page: 100, type: 'all'
            })
          } catch (err) {
            errors.push({ org, error: err.message })
            continue
          }

          for (const repo of repos) {
            if (repo.archived || repo.fork) continue
            if (repo.name === '.github-private') continue
            totalScanned++

            // Read custom property
            let migrationType = null
            try {
              const { data: props } = await github.request(
                'GET /repos/{owner}/{repo}/properties/values',
                { owner: org, repo: repo.name }
              )
              const prop = props.find(p => p.property_name === 'GH_MIGRATION_TYPE')
              migrationType = prop?.value
            } catch (err) {
              // Property not set or not accessible
            }

            if (!migrationType || migrationType === 'None') {
              skipped.push({ repo: `${org}/${repo.name}`, reason: 'No migration type or set to None' })
              continue
            }

            if (!prompts[migrationType]) {
              skipped.push({ repo: `${org}/${repo.name}`, reason: `Unknown migration type: ${migrationType}` })
              continue
            }

            // Idempotency: skip if open migration issue exists
            try {
              const { data: search } = await github.rest.search.issuesAndPullRequests({
                q: `repo:${org}/${repo.name} is:issue is:open "[Actions Migration]" in:title`
              })
              if (search.total_count > 0) {
                skipped.push({ repo: `${org}/${repo.name}`, reason: 'Open migration issue already exists' })
                continue
              }
            } catch (err) {
              core.warning(`Search failed for ${org}/${repo.name}: ${err.message}`)
            }

            // Read agent prompt file
            const agentFile = prompts[migrationType]
            const agentPath = path.join(process.env.GITHUB_WORKSPACE, 'agents', agentFile)
            let agentPrompt
            try {
              agentPrompt = fs.readFileSync(agentPath, 'utf8')
            } catch (err) {
              errors.push({ repo: `${org}/${repo.name}`, error: `Agent file not found: ${agentFile}` })
              continue
            }

            eligible.push({ repo: `${org}/${repo.name}`, migrationType, agentFile, agentPrompt })
            submitted++
            if (submitted >= batchSize) {
              core.info(`Batch size ${batchSize} reached for ${org}`)
              break
            }
          }
        }

        // Write results for agent consumption
        const results = { eligible, skipped, errors, totalScanned, orgs: orgs.length }
        fs.mkdirSync('/tmp/gh-aw/agent', { recursive: true })
        fs.writeFileSync('/tmp/gh-aw/agent/scan-results.json', JSON.stringify(results, null, 2))
        core.info(`Scan complete: ${eligible.length} eligible, ${skipped.length} skipped, ${errors.length} errors out of ${totalScanned} repos`)

tools:
  bash:
    - "cat"
    - "jq:*"
network:
  allowed:
    - defaults
    - github
safe-outputs:
  github-token: ${{ secrets.ISSUE_SUBMIT_TOKEN }}
  create-issue:
    title-prefix: "[Actions Migration] "
    labels: [automation, migration]
    assignees: [copilot]
    target-repo: "*"
    max: 100
  add-comment:
    target: "*"
    max: 1
  noop:
---

# Create Migration Issues from Pre-Computed Scan Results

The deterministic scan has already run in the `steps:` phase. All repo scanning,
property reading, idempotency checks, and prompt loading are done. Your job is
to read the results and create issues via safe outputs.

## Instructions

1. **Read** `/tmp/gh-aw/agent/scan-results.json`. It contains:
   - `eligible`: repos needing migration (`repo`, `migrationType`, `agentFile`, `agentPrompt`)
   - `skipped`: repos skipped (`repo`, `reason`)
   - `errors`: errors during scanning
   - `totalScanned`: total repos scanned
   - `orgs`: number of organizations

2. **If `eligible` is empty**, call `noop`:
   ```json
   {"noop": {"message": "No action needed: 0 eligible repos out of <totalScanned> scanned across <orgs> organizations"}}
   ```

3. **For each entry in `eligible`**, call `create_issue`:
   - `repo`: `eligible[i].repo`
   - `title`: `Migrate <migrationType> CI/CD to GitHub Actions`
   - `body`: `eligible[i].agentPrompt` (pass exactly as-is, do not modify)

4. **After all issues created**, post a summary via `add_comment` on the last
   created issue:

   ```markdown
   ## Migration Submission Report

   | Metric | Count |
   |--------|-------|
   | Organizations scanned | <orgs> |
   | Repositories scanned | <totalScanned> |
   | Migrations submitted | <eligible.length> |
   | Repositories skipped | <skipped.length> |
   | Errors | <errors.length> |
   ```

Do NOT scan repositories yourself. Do NOT call GitHub API to list repos or read
properties. Everything was computed deterministically. Read the JSON, create
issues, done.
