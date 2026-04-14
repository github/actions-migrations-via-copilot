module.exports = async ({ github, core, context, org, repos, trackingIssue }) => {
    let dispatched = 0

    for (const entry of repos) {
        const repoValue = typeof entry.repo === 'string' ? entry.repo.trim() : ''
        const [targetOwner, targetRepoName] = repoValue.includes('/')
            ? repoValue.split('/', 2)
            : [org, repoValue]

        if (!targetOwner || !targetRepoName) {
            core.error(`Skipping invalid repository entry: ${JSON.stringify(entry)}`)
            continue
        }

        const targetRepo = `${targetOwner}/${targetRepoName}`

        try {
            await github.rest.actions.createWorkflowDispatch({
                owner: context.repo.owner,
                repo: context.repo.repo,
                workflow_id: 'migration-worker.lock.yml',
                ref: context.ref || 'main',
                inputs: {
                    target_repo: targetRepo,
                    migration_type: entry.type,
                    tracking_issue: trackingIssue,
                    target_repo_owner: targetOwner
                }
            })
            dispatched++
            core.info(`Dispatched migration for ${targetRepo} (${entry.type})`)
        } catch (err) {
            core.error(`Failed to dispatch migration for ${targetRepo}: ${err.message}`)
        }
    }

    core.info(`Dispatched ${dispatched}/${repos.length} migration workers for ${org}`)
}
