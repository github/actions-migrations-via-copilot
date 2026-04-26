/**
 * Loads and parses the config.yaml file
 * Returns the configuration as a JSON string for use by other steps
 */
module.exports = async ({ core, process, fs, yaml }) => {
    try {
        // Read and parse the config.yaml file
        const configPath = '.github/settings/config.yaml'
        const configContent = fs.readFileSync(configPath, 'utf8')
        const config = yaml.load(configContent)

        core.info('Parsed configuration file successfully')

        // Validate required fields
        if (
            !config.gh_app_id ||
            !config.gh_migration_type ||
            !config.migration_type_prompts ||
            !config.organizations
        ) {
            throw new Error('Missing required configuration fields')
        }

        // Output the configuration as JSON for other steps
        const configJson = JSON.stringify(config)
        core.setOutput('config', configJson)

        core.info('✅ Configuration loaded and validated successfully')

        return config
    } catch (error) {
        core.setFailed(`Failed to load configuration: ${error.message}`)
        throw error
    }
}
