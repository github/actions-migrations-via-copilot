module.exports = async ({ github, core, process }) => {
    const org = process.env.ORG
    const batchSize = parseInt(process.env.BATCH_SIZE) || 100

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
    let totalRepos = 0
    let skippedNoType = 0
    let skippedExisting = 0
    let skippedArchived = 0

    core.info(`Scanning organization: ${org}`)

    let repos
    try {
        repos = await withRetry(
            () => github.paginate(github.rest.repos.listForOrg, { org, per_page: 100, type: 'all' }),
            `listForOrg(${org})`
        )
    } catch (err) {
        core.setFailed(`Failed to list repos for ${org}: ${err.message}`)
        return []
    }

    core.info(`Found ${repos.length} repositories in ${org}`)

    for (const repo of repos) {
        totalRepos++
        if (repo.archived || repo.fork) {
            skippedArchived++
            continue
        }
        if (repo.name === '.github-private') continue

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
        } catch (err) { }

        if (!migrationType || migrationType === 'None') {
            skippedNoType++
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
                skippedExisting++
                continue
            }
        } catch (err) {
            core.warning(`Search failed for ${org}/${repo.name}: ${err.message}`)
        }

        eligible.push({ repo: repo.name, type: migrationType })
        if (eligible.length >= batchSize) {
            core.info(`Batch size ${batchSize} reached`)
            break
        }
    }

    const byType = eligible.reduce((acc, r) => {
        acc[r.type] = (acc[r.type] || 0) + 1
        return acc
    }, {})

    core.info(`--- Scan Summary: ${org} ---`)
    core.info(`Total repositories:    ${totalRepos}`)
    core.info(`Skipped (archived/fork): ${skippedArchived}`)
    core.info(`Skipped (no migration type): ${skippedNoType}`)
    core.info(`Skipped (existing migration): ${skippedExisting}`)
    core.info(`Eligible for migration: ${eligible.length}`)
    if (eligible.length > 0) {
        core.info('Breakdown by type:')
        for (const [type, count] of Object.entries(byType)) {
            core.info(`  ${type}: ${count}`)
        }
    }

    return eligible
}
