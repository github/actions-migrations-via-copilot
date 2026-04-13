module.exports = async ({ github, core, context, org, repos, trackingIssue }) => {
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
                    tracking_issue: trackingIssue,
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
}
