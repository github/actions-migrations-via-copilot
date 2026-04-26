/**
 * Creates or updates repository variables based on configuration
 */
module.exports = async ({ github, context, core, config }) => {
  try {
    // Parse config if it's a string
    const parsedConfig = typeof config === 'string' ? JSON.parse(config) : config

    const ghAppId = parsedConfig.gh_app_id
    const migrationTypePrompts = parsedConfig.migration_type_prompts
    const organizations = parsedConfig.organizations
    const batchSize = parsedConfig.batch_size || 100

    core.info('Creating/updating repository variables...')

    // 1. Create or update repository variable for gh_app_id
    core.info('Creating/updating repository variable for GitHub App ID...')
    try {
      await github.rest.actions.createRepoVariable({
        owner: context.repo.owner,
        repo: context.repo.repo,
        name: 'GH_APP_ID',
        value: ghAppId,
      })
      core.info('✅ Created GH_APP_ID repository variable')
    } catch (error) {
      if (error.status === 409) {
        // Variable already exists, update it
        await github.rest.actions.updateRepoVariable({
          owner: context.repo.owner,
          repo: context.repo.repo,
          name: 'GH_APP_ID',
          value: ghAppId,
        })
        core.info('✅ Updated GH_APP_ID repository variable')
      } else {
        throw error
      }
    }

    // 2. Create or update repository variable for migration_type_prompts as JSON string
    core.info(
      'Creating/updating repository variable for migration type prompts...'
    )
    const migrationTypePromptsJson = JSON.stringify(migrationTypePrompts)
    try {
      await github.rest.actions.createRepoVariable({
        owner: context.repo.owner,
        repo: context.repo.repo,
        name: 'MIGRATION_TYPE_PROMPTS',
        value: migrationTypePromptsJson,
      })
      core.info('✅ Created MIGRATION_TYPE_PROMPTS repository variable')
    } catch (error) {
      if (error.status === 409) {
        // Variable already exists, update it
        await github.rest.actions.updateRepoVariable({
          owner: context.repo.owner,
          repo: context.repo.repo,
          name: 'MIGRATION_TYPE_PROMPTS',
          value: migrationTypePromptsJson,
        })
        core.info('✅ Updated MIGRATION_TYPE_PROMPTS repository variable')
      } else {
        throw error
      }
    }

    // 3. Create or update repository variable for organizations list
    core.info('Creating/updating repository variable for organizations...')
    const organizationsJson = JSON.stringify(organizations)
    try {
      await github.rest.actions.createRepoVariable({
        owner: context.repo.owner,
        repo: context.repo.repo,
        name: 'ORGANIZATIONS',
        value: organizationsJson,
      })
      core.info('✅ Created ORGANIZATIONS repository variable')
    } catch (error) {
      if (error.status === 409) {
        // Variable already exists, update it
        await github.rest.actions.updateRepoVariable({
          owner: context.repo.owner,
          repo: context.repo.repo,
          name: 'ORGANIZATIONS',
          value: organizationsJson,
        })
        core.info('✅ Updated ORGANIZATIONS repository variable')
      } else {
        throw error
      }
    }

    // 4. Create or update repository variable for batch size
    core.info('Creating/updating repository variable for batch size...')
    try {
      await github.rest.actions.createRepoVariable({
        owner: context.repo.owner,
        repo: context.repo.repo,
        name: 'BATCH_SIZE',
        value: batchSize.toString(),
      })
      core.info('✅ Created BATCH_SIZE repository variable')
    } catch (error) {
      if (error.status === 409) {
        // Variable already exists, update it
        await github.rest.actions.updateRepoVariable({
          owner: context.repo.owner,
          repo: context.repo.repo,
          name: 'BATCH_SIZE',
          value: batchSize.toString(),
        })
        core.info('✅ Updated BATCH_SIZE repository variable')
      } else {
        throw error
      }
    }

    core.info('🎉 Repository variables setup completed successfully!')
  } catch (error) {
    core.setFailed(`Repository variables setup failed: ${error.message}`)
    throw error
  }
}

