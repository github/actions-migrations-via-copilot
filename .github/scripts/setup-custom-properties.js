/**
 * Creates custom properties for organizations
 */
module.exports = async ({ github, core, config }) => {
    try {
        // Parse config if it's a string
        const parsedConfig = typeof config === 'string' ? JSON.parse(config) : config

        const ghMigrationType = parsedConfig.gh_migration_type
        const organizations = parsedConfig.organizations

        core.info('Creating custom properties for organizations...')

        // Prepare the allowed values array (default_value + other_values + 'None')
        const allowedValues = [
            ghMigrationType.default_value,
            ...ghMigrationType.other_values,
            'None',
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

        core.info('🎉 Custom properties setup completed successfully!')
    } catch (error) {
        core.setFailed(`Custom properties setup failed: ${error.message}`)
        throw error
    }
}
