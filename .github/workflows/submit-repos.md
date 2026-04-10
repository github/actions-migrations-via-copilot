---
name: Submit Repositories for Migration
description: >
  Deterministic orchestrator: scans repos for GH_MIGRATION_TYPE custom
  property, creates a tracking issue, and dispatches migration-worker.md
  for each eligible repository.
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
jobs:
  scan:
    runs-on: ubuntu-latest
    outputs:
      app_token: ${{ steps.app-token.outputs.token }}
    steps:
      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v3
        with:
          app-id: ${{ vars.GH_APP_ID }}
          private-key: ${{ secrets.GH_APP_PEM }}
          owner: ${{ github.repository_owner }}
      - name: Checkout
        uses: actions/checkout@v6
        with:
          token: ${{ steps.app-token.outputs.token }}
      - name: Scan repositories
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

            async function withRetry(fn, label, maxRetries = 3) {
              for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                  return await fn()
                } catch (err) {
                  const status = err.status || err.response?.status
                  if ((status === 403 || status === 429) && attempt < maxRetries) {
                    const retryAfter = parseInt(err.response?.headers?.['retry-after'] || '60', 10)
                    core.warning(`Rate limited on ${label} (attempt ${attempt}/${maxRetries}), waiting ${retryAfter}s`)
                    await new Promise(r => setTimeout(r, retryAfter * 1000))
                    continue
                  }
                  throw err
                }
              }
            }

            const eligible = []
            const skipped = []
            const errors = []
            let totalScanned = 0

            for (const org of orgs) {
              let submitted = 0
              core.info(`Scanning organization: ${org}`)

              let repos
              try {
                repos = await withRetry(
                  () => github.paginate(github.rest.repos.listForOrg, { org, per_page: 100, type: 'all' }),
                  `listForOrg(${org})`
                )
              } catch (err) {
                errors.push({ org, error: err.message })
                continue
              }

              for (const repo of repos) {
                if (repo.archived || repo.fork) continue
                if (repo.name === '.github-private') continue
                totalScanned++

                let migrationType = null
                try {
                  const { data: props } = await withRetry(
                    () => github.request(
                      'GET /repos/{owner}/{repo}/properties/values',
                      { owner: org, repo: repo.name }
                    ),
                    `properties(${org}/${repo.name})`
                  )
                  const prop = props.find(p => p.property_name === 'GH_MIGRATION_TYPE')
                  migrationType = prop?.value
                } catch (err) {}

                if (!migrationType || migrationType === 'None') {
                  skipped.push({ repo: `${org}/${repo.name}`, reason: 'No migration type or set to None' })
                  continue
                }

                if (!prompts[migrationType]) {
                  skipped.push({ repo: `${org}/${repo.name}`, reason: `Unknown migration type: ${migrationType}` })
                  continue
                }

                try {
                  const { data: search } = await withRetry(
                    () => github.rest.search.issuesAndPullRequests({
                      q: `repo:${org}/${repo.name} is:open "[Actions Migration]" in:title`
                    }),
                    `search(${org}/${repo.name})`
                  )
                  if (search.total_count > 0) {
                    skipped.push({ repo: `${org}/${repo.name}`, reason: 'Open migration issue/PR already exists' })
                    continue
                  }
                } catch (err) {
                  core.warning(`Search failed for ${org}/${repo.name}: ${err.message}`)
                }

                eligible.push({ repo: `${org}/${repo.name}`, migrationType })
                submitted++
                if (submitted >= batchSize) {
                  core.info(`Batch size ${batchSize} reached for ${org}`)
                  break
                }
              }
            }

            const results = { eligible, skipped, errors, totalScanned, orgs: orgs.length }
            fs.mkdirSync('/tmp/gh-aw/agent', { recursive: true })
            fs.writeFileSync('/tmp/gh-aw/agent/scan-results.json', JSON.stringify(results, null, 2))
            core.info(`Scan complete: ${eligible.length} eligible, ${skipped.length} skipped, ${errors.length} errors out of ${totalScanned} repos`)
      - name: Upload scan results
        uses: actions/upload-artifact@v4
        with:
          name: scan-results
          path: /tmp/gh-aw/agent/scan-results.json
steps:
  - name: Download scan results
    uses: actions/download-artifact@v4
    with:
      name: scan-results
      path: /tmp/gh-aw/agent/
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
    title-prefix: "[Migration Batch] "
    labels: [automation, migration, tracking]
    max: 1
  dispatch-workflow:
    workflows: [migration-worker]
    max: 50
  noop:
---

# Dispatch Migration Workers from Pre-Computed Scan Results

The deterministic scan has already run in the `steps:` phase. All repo scanning,
property reading, and idempotency checks are done. Your job is to create a
tracking issue and dispatch workers.

## Instructions

1. **Read** `/tmp/gh-aw/agent/scan-results.json`. It contains:
   - `eligible`: repos needing migration (`repo`, `migrationType`)
   - `skipped`: repos skipped (`repo`, `reason`)
   - `errors`: errors during scanning
   - `totalScanned`: total repos scanned
   - `orgs`: number of organizations

2. **If `eligible` is empty**, call `noop`:

   ```json
   {"noop": {"message": "No action needed: 0 eligible repos out of <totalScanned> scanned across <orgs> organizations"}}
   ```

3. **Create a tracking issue** via `create_issue` with title `<date> - <count> repos` and body:

   ```markdown
   ## Migration Batch - <YYYY-MM-DD>

   | Metric | Count |
   |--------|-------|
   | Organizations scanned | <orgs> |
   | Repositories scanned | <totalScanned> |
   | Migrations dispatched | <eligible.length> |
   | Repositories skipped | <skipped.length> |
   | Errors | <errors.length> |

   ### Dispatched

   | Repository | Migration Type | Status |
   |------------|---------------|--------|
   | <repo> | <migrationType> | 🔄 Dispatched |

   ### Skipped

   | Repository | Reason |
   |------------|--------|
   | <repo> | <reason> |

   Workers will report back to this issue as they complete.
   ```

4. **For each entry in `eligible`**, call `dispatch_workflow` with:
   - `workflow`: `migration-worker`
   - `inputs`:
     - `target_repo`: `eligible[i].repo`
     - `migration_type`: `eligible[i].migrationType`
     - `tracking_issue`: the issue number from step 3

Do NOT scan repositories yourself. Do NOT call GitHub API to list repos or read
properties. Everything was computed deterministically. Read the JSON, create
the tracking issue, dispatch workers, done.
