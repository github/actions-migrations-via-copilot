module.exports = async ({ github, core, context, orgEntry }) => {
    const { org, repos } = orgEntry
    const date = new Date().toISOString().split('T')[0]

    const byType = repos.reduce((acc, r) => {
        acc[r.type] = (acc[r.type] || 0) + 1
        return acc
    }, {})

    const typeBreakdown = Object.entries(byType)
        .map(([type, count]) => `| ${type} | ${count} |`)
        .join('\n')

    const repoRows = repos
        .map(r => `| \`${org}/${r.repo}\` | ${r.type} | 🔄 Dispatched |`)
        .join('\n')

    const body = `# Migration Batch — ${org}

> **Date:** ${date}
> **Organization:** \`${org}\`
> **Total dispatched:** ${repos.length}

---

### Summary by Migration Type

| Type | Count |
|------|-------|
${typeBreakdown}

### Repositories

| Repository | Migration Type | Status |
|------------|---------------|--------|
${repoRows}

---

_Workers will update this issue as they complete._`

    const issue = await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `[Migration Batch] ${date} - ${org} - ${repos.length} repos`,
        body,
        labels: ['automation', 'migration', 'tracking']
    })

    core.info(`Created tracking issue #${issue.data.number}`)

    let dispatched = 0
    for (const entry of repos) {
        try {
            await github.rest.actions.createWorkflowDispatch({
                owner: context.repo.owner,
                repo: context.repo.repo,
                workflow_id: 'migration-worker.lock.yml',
                ref: context.ref || 'main',
                inputs: {
                    target_repo: `${org}/${entry.repo}`,
                    migration_type: entry.type,
                    tracking_issue: String(issue.data.number),
                    target_repo_owner: org
                }
            })
            dispatched++
            core.info(`Dispatched migration for ${org}/${entry.repo} (${entry.type})`)
        } catch (err) {
            core.error(`Failed to dispatch migration for ${org}/${entry.repo}: ${err.message}`)
        }
    }

    core.info(`Dispatched ${dispatched}/${repos.length} migration workers for ${org}`)
    core.setOutput('dispatched', dispatched)
    core.setOutput('tracking_issue', issue.data.number)
}
