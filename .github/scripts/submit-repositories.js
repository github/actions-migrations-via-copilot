const { resolveMigrationSkills } = require('./migration-targets')

/**
 * Searches for repositories with specific migration types
 * @param {object} github - GitHub API client
 * @param {object} core - GitHub Actions core utilities
 * @param {string} org - Organization name
 * @param {string[]} migrationTypes - Array of migration types to search for
 * @returns {object[]} Array of repositories with migration types
 */
const searchRepositoriesForMigration = async (
  github,
  core,
  org,
  migrationTypes
) => {
  core.info(
    `Searching for repositories with migration types: ${migrationTypes.join(
      ', '
    )}`
  )

  const allRepos = []
  const seenRepos = new Set() // Track repos to avoid duplicates

  // Search for each migration type separately to avoid complex query issues
  for (const migrationType of migrationTypes) {
    const searchQuery = `org:${org} props.GH_MIGRATION_TYPE:"${migrationType}"`
    core.info(`Searching with query: ${searchQuery}`)

    try {
      const searchResults = await github.paginate(github.rest.search.repos, {
        q: searchQuery,
        per_page: 100,
      })

      core.info(
        `Found ${searchResults.length} repositories for migration type: ${migrationType}`
      )

      // Add repos to our collection, avoiding duplicates
      for (const repo of searchResults) {
        const repoKey = `${org}/${repo.name}`
        if (!seenRepos.has(repoKey)) {
          seenRepos.add(repoKey)
          allRepos.push({
            ...repo,
            migrationType: migrationType,
          })
        }
      }
    } catch (searchError) {
      core.warning(
        `Failed to search for migration type "${migrationType}": ${searchError.message}`
      )
      continue
    }
  }

  return allRepos
}

/**
 * Validates repositories and filters those with valid migration types
 * @param {object[]} repositories - Array of repositories to validate
 * @param {object} migrationSkills - Migration type skills mapping
 * @param {object} core - GitHub Actions core utilities
 * @param {string} org - Organization name
 * @returns {object[]} Array of valid repositories
 */
const validateRepositories = (
  repositories,
  migrationSkills,
  core,
  org
) => {
  const validRepos = []

  for (const repo of repositories) {
    if (repo.migrationType && migrationSkills[repo.migrationType]) {
      validRepos.push(repo)
      core.info(
        `Repository ${org}/${repo.name} needs migration from ${repo.migrationType}`
      )
    } else {
      core.info(
        `Repository ${org}/${repo.name} has migration type "${repo.migrationType}" but no corresponding skill configured`
      )
    }
  }

  return validRepos
}

const buildMigrationTask = (migrationType, skill) => [
  `Migrate this repository from ${migrationType} to GitHub Actions.`,
  '',
  `Use the installed actions-migrator plugin's migration-core, ${skill}, and actionlint skills.`,
  'Before changing files, locate and load those installed skills. If the plugin or any required skill is unavailable, stop without migration edits and report the missing prerequisite.',
  'Do not install a plugin, change plugin settings, fetch another copy of the migration guides, or substitute generic migration instructions.',
  'Follow the skills for conversion, validation, source archival, and the migration report. Keep secret scanning and push protection enabled. Never include credential values in files, reports, or PR text.',
].join('\n')

/**
 * Creates a GitHub client with issue submit token
 * @param {object} github - Original GitHub API client
 * @param {object} core - GitHub Actions core utilities
 * @param {object} process - Node.js process object
 * @returns {object} GitHub client with issue submit token
 */
const createIssueSubmitClient = (github, core, process) => {
  const issueSubmitToken = process.env.ISSUE_SUBMIT_TOKEN

  if (!issueSubmitToken) {
    const error = new Error(
      'ISSUE_SUBMIT_TOKEN environment variable is missing'
    )
    core.setFailed(
      'Environment variable ISSUE_SUBMIT_TOKEN is required but not found'
    )
    throw error
  }

  return new github.constructor({ auth: issueSubmitToken })
}

/**
 * Creates a migration issue and assigns it to the Copilot cloud agent in a
 * single REST call using the agent_assignment input.
 * See: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api
 * @param {object} issueGithub - GitHub client for issue operations
 * @param {object} core - GitHub Actions core utilities
 * @param {string} org - Organization name
 * @param {string} repoName - Repository name
 * @param {string} baseBranch - Base branch the agent should branch from
 * @param {string} issueTitle - Issue title
 * @param {string} issueBody - Short task referencing installed migration skills
 */
const createAndAssignMigrationIssue = async (
  issueGithub,
  core,
  org,
  repoName,
  baseBranch,
  issueTitle,
  issueBody
) => {
  const createdIssue = await issueGithub.request(
    'POST /repos/{owner}/{repo}/issues',
    {
      owner: org,
      repo: repoName,
      title: issueTitle,
      body: issueBody,
      assignees: ['copilot-swe-agent[bot]'],
      agent_assignment: {
        target_repo: `${org}/${repoName}`,
        base_branch: baseBranch,
      },
      headers: {
        'X-GitHub-Api-Version': '2022-11-28',
      },
    }
  )

  core.info(
    `Created and assigned migration issue #${createdIssue.data.number} ` +
    `to copilot-swe-agent using installed plugin skills in ${org}/${repoName}`
  )
}

/**
 * Updates repository custom property to mark migration as complete
 * @param {object} github - GitHub API client
 * @param {object} core - GitHub Actions core utilities
 * @param {string} org - Organization name
 * @param {string} repoName - Repository name
 */
const updateRepositoryMigrationProperty = async (
  github,
  core,
  org,
  repoName
) => {
  try {
    await github.request('PATCH /repos/{owner}/{repo}/properties/values', {
      owner: org,
      repo: repoName,
      properties: [
        {
          property_name: 'GH_MIGRATION_TYPE',
          value: 'None',
        },
      ],
      headers: {
        'X-GitHub-Api-Version': '2022-11-28',
      },
    })

    core.info(
      `Updated custom property GH_MIGRATION_TYPE to "None" for ${org}/${repoName}`
    )
  } catch (propertyError) {
    core.warning(
      `Failed to update custom property for ${org}/${repoName}: ${propertyError.message}`
    )
  }
}

/**
 * Processes a single repository for migration
 * @param {object} repo - Repository object
 * @param {string} org - Organization name
 * @param {object} migrationSkills - Migration type skills mapping
 * @param {object} github - GitHub API client
 * @param {object} issueGithub - GitHub client for issue operations
 * @param {object} core - GitHub Actions core utilities
 * @param {object} process - Node.js process object
 */
const processRepository = async (
  repo,
  org,
  migrationSkills,
  github,
  issueGithub,
  core,
  process
) => {
  core.info(
    `Processing repository: ${org}/${repo.name} (Migration Type: ${repo.migrationType})`
  )

  try {
    const { migrationType } = repo
    const skill = migrationSkills[migrationType]

    if (!skill) {
      throw new Error(`No skill configured for migration type: ${migrationType}`)
    }

    const issueBody = buildMigrationTask(migrationType, skill)
    const issueTitle = `[Actions Migration] ${migrationType}`

    // Base branch the cloud agent should branch from
    const baseBranch = repo.default_branch || 'main'

    // Create the migration issue and assign it to the Copilot cloud agent
    // in a single REST call using the agent_assignment input.
    await createAndAssignMigrationIssue(
      issueGithub,
      core,
      org,
      repo.name,
      baseBranch,
      issueTitle,
      issueBody
    )

    // Update repository custom property
    await updateRepositoryMigrationProperty(github, core, org, repo.name)

    core.info(`Repository ${org}/${repo.name} processed successfully`)
    return true
  } catch (error) {
    core.warning(
      `Failed to process repository ${org}/${repo.name}: ${error.message}`
    )
    return false
  }
}

module.exports = async ({ github, context, core, process, org, batchSize }) => {
  try {
    core.info(`Starting migration process for organization: ${org}`)

    const migrationSkills = resolveMigrationSkills({
      skills: process.env.MIGRATION_TYPE_SKILLS || undefined,
      prompts: process.env.MIGRATION_TYPE_PROMPTS || undefined,
      warn: (message) => core.warning(message),
    })
    const migrationTypes = Object.keys(migrationSkills)
    if (!Number.isInteger(batchSize) || batchSize < 1) {
      throw new Error('Batch size must be a positive integer')
    }

    // Search for repositories requiring migration
    const foundRepos = await searchRepositoriesForMigration(
      github,
      core,
      org,
      migrationTypes
    )
    core.info(
      `Found ${foundRepos.length} total repositories requiring migration`
    )

    // Validate repositories and filter by valid migration types
    const validRepos = validateRepositories(
      foundRepos,
      migrationSkills,
      core,
      org
    )
    core.info(
      `Found ${validRepos.length} unique repositories requiring migration`
    )

    // Apply batch size limit
    const batchedRepos = validRepos.slice(0, batchSize)
    core.info(
      `Processing ${batchedRepos.length} repositories (batch size: ${batchSize})`
    )

    // Create the GitHub client for issue operations once for all repositories
    const issueGithub = createIssueSubmitClient(github, core, process)

    const submittedRepositories = []
    for (const repo of batchedRepos) {
      const submitted = await processRepository(
        repo,
        org,
        migrationSkills,
        github,
        issueGithub,
        core,
        process
      )
      if (submitted) submittedRepositories.push(repo.name)
    }

    const failedRepositories = batchedRepos.length - submittedRepositories.length
    if (failedRepositories > 0) {
      core.setFailed(`${failedRepositories} migration issue assignment(s) failed`)
    }
    core.info(`Completed processing repositories for organization: ${org}`)

    return {
      organization: org,
      totalRepositoriesSearched: foundRepos.length,
      repositoriesRequiringMigration: validRepos.length,
      processedRepositories: submittedRepositories.length,
      failedRepositories,
      repositoryNames: submittedRepositories,
    }
  } catch (error) {
    core.setFailed(
      `Failed to process repositories for ${org}: ${error.message}`
    )
    throw error
  }
}
