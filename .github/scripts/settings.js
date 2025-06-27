module.exports = async ({ github, context, core, process, fs, yaml }) => {
  try {
    // Read and parse the config.yaml file
    const configPath = '.github/settings/config.yaml'
    const configContent = fs.readFileSync(configPath, 'utf8')
    const config = yaml.load(configContent)

    core.info('Parsed configuration file successfully')

    // Extract values from config
    const ghAppId = config.gh_app_id
    const ghMigrationType = config.gh_migration_type
    const migrationTypePrompts = config.migration_type_prompts
    const organizations = config.organizations

    // Validate required fields
    if (
      !ghAppId ||
      !ghMigrationType ||
      !migrationTypePrompts ||
      !organizations
    ) {
      throw new Error('Missing required configuration fields')
    }

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

    // 3. Create custom property for each organization
    core.info('Creating custom properties for organizations...')

    // Prepare the allowed values array (default_value + other_values)
    const allowedValues = [
      ghMigrationType.default_value,
      ...ghMigrationType.other_values,
    ]
    // Remove duplicates
    const uniqueAllowedValues = [...new Set(allowedValues)]

    for (const org of organizations) {
      core.info(`Creating custom property for organization: ${org}`)

      try {
        await github.request(
          'PUT /orgs/{org}/properties/schema/{custom_property_name}',
          {
            org: org,
            custom_property_name: 'GH_MIGRATION_TYPE',
            value_type: 'single_select',
            description: ghMigrationType.description,
            default_value: ghMigrationType.default_value,
            allowed_values: uniqueAllowedValues,
            required: true,
            values_editable_by: 'org_and_repo_actors',
          }
        )
        core.info(
          `✅ Created/updated GH_MIGRATION_TYPE custom property for ${org}`
        )
      } catch (error) {
        core.warning(
          `Failed to create custom property for ${org}: ${error.message}`
        )
        // Continue with other organizations even if one fails
      }
    }

    // 4. Create or update repository variable for organizations list
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

    // 5. Create or update repository variable for batch size
    core.info('Creating/updating repository variable for batch size...')
    const batchSize = config.batch_size || 100
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

    core.info('🎉 All configuration setup completed successfully!')
  } catch (error) {
    core.setFailed(`Configuration setup failed: ${error.message}`)
    throw error
  }
}
