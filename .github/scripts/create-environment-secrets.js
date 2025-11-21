/**
 * Creates the 'copilot' environment and sets the COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN secret
 * for all repositories in the organizations
 */

/**
 * Gets all repositories in an organization
 * @param {object} github - GitHub API client
 * @param {object} core - GitHub Actions core utilities
 * @param {string} org - Organization name
 * @returns {object[]} Array of repositories
 */
const getAllRepositories = async (github, core, org) => {
    core.info(`Fetching all repositories in organization: ${org}`)

    try {
        const repositories = await github.paginate(github.rest.repos.listForOrg, {
            org: org,
            per_page: 100,
        })

        core.info(`Found ${repositories.length} repositories in ${org}`)

        return repositories.map((repo) => ({
            name: repo.name,
            owner: org,
        }))
    } catch (error) {
        core.warning(`Failed to fetch repositories for ${org}: ${error.message}`)
        return []
    }
}

/**
 * Creates or updates the 'copilot' environment in a repository
 * @param {object} github - GitHub API client
 * @param {object} core - GitHub Actions core utilities
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @returns {string|null} Environment name if successful, null otherwise
 */
const createEnvironment = async (github, core, owner, repo) => {
    try {
        core.info(`Creating/updating 'copilot' environment in ${owner}/${repo}`)

        await github.rest.repos.createOrUpdateEnvironment({
            owner: owner,
            repo: repo,
            environment_name: 'copilot',
        })

        core.info(`✅ Environment 'copilot' ready in ${owner}/${repo}`)
        return 'copilot'
    } catch (error) {
        core.warning(
            `Failed to create environment in ${owner}/${repo}: ${error.message}`
        )
        return null
    }
}

/**
 * Creates or updates the environment secret
 * @param {object} github - GitHub API client
 * @param {object} core - GitHub Actions core utilities
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {string} environmentName - Environment name
 * @param {string} secretValue - Secret value to set
 */
const createEnvironmentSecret = async (
    github,
    core,
    owner,
    repo,
    environmentName,
    secretValue
) => {
    try {
        // Get the repository's public key for encryption
        const { data: publicKey } = await github.rest.actions.getEnvironmentPublicKey({
            repository_id: (await github.rest.repos.get({ owner, repo })).data.id,
            environment_name: environmentName,
        })

        // Encrypt the secret value using libsodium
        const sodium = require('libsodium-wrappers')
        await sodium.ready

        const binkey = sodium.from_base64(publicKey.key, sodium.base64_variants.ORIGINAL)
        const binsec = sodium.from_string(secretValue)
        const encBytes = sodium.crypto_box_seal(binsec, binkey)
        const encryptedValue = sodium.to_base64(encBytes, sodium.base64_variants.ORIGINAL)

        // Create or update the secret
        await github.rest.actions.createOrUpdateEnvironmentSecret({
            repository_id: (await github.rest.repos.get({ owner, repo })).data.id,
            environment_name: environmentName,
            secret_name: 'COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN',
            encrypted_value: encryptedValue,
            key_id: publicKey.key_id,
        })

        core.info(
            `✅ Secret 'COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN' created in ${owner}/${repo} (env: ${environmentName})`
        )
    } catch (error) {
        core.warning(
            `Failed to create secret in ${owner}/${repo}: ${error.message}`
        )
    }
}

module.exports = async ({ github, core, process, config }) => {
    try {
        // Parse config if it's a string
        const parsedConfig = typeof config === 'string' ? JSON.parse(config) : config

        const organizations = parsedConfig.organizations

        if (!organizations || organizations.length === 0) {
            core.warning('No organizations found in config.yaml')
            return { repositoriesProcessed: 0 }
        }

        // Get the secret value from environment
        const secretValue = process.env.SECRET_VALUE
        if (!secretValue) {
            throw new Error('SECRET_VALUE environment variable is required')
        }

        let totalRepositories = 0
        let successfulRepositories = 0

        // Process each organization
        for (const org of organizations) {
            core.info(`Processing organization: ${org}`)

            // Get all repositories in the organization
            const repositories = await getAllRepositories(github, core, org)

            core.info(`Found ${repositories.length} repositories in ${org}`)

            // Create environment and secret for each repository
            for (const repo of repositories) {
                totalRepositories++

                // Create the environment
                const environmentName = await createEnvironment(
                    github,
                    core,
                    repo.owner,
                    repo.name
                )

                if (environmentName) {
                    // Create the secret
                    await createEnvironmentSecret(
                        github,
                        core,
                        repo.owner,
                        repo.name,
                        environmentName,
                        secretValue
                    )
                    successfulRepositories++
                }
            }
        }

        core.info(
            `🎉 Processed ${successfulRepositories}/${totalRepositories} repositories successfully`
        )

        return {
            repositoriesProcessed: totalRepositories,
            successfulRepositories: successfulRepositories,
        }
    } catch (error) {
        core.setFailed(`Failed to create environment secrets: ${error.message}`)
        throw error
    }
}
