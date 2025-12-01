/**
 * Parses and validates migration type prompts from environment variable
 * @param {object} core - GitHub Actions core utilities
 * @param {object} process - Node.js process object
 * @returns {object} Parsed migration type prompts mapping
 */
const parseMigrationTypePrompts = (core, process) => {
  core.info('Fetching available migration types from environment variable...')

  const migrationTypePromptsEnv = process.env.MIGRATION_TYPE_PROMPTS

  if (!migrationTypePromptsEnv) {
    const error = new Error(
      'MIGRATION_TYPE_PROMPTS environment variable is missing'
    )
    core.setFailed(
      'Environment variable MIGRATION_TYPE_PROMPTS is required but not found'
    )
    throw error
  }

  try {
    const migrationTypePrompts = JSON.parse(migrationTypePromptsEnv)
    const migrationTypes = Object.keys(migrationTypePrompts)

    if (migrationTypes.length === 0) {
      const error = new Error(
        'No migration types found in MIGRATION_TYPE_PROMPTS'
      )
      core.setFailed(
        'MIGRATION_TYPE_PROMPTS environment variable is empty or contains no migration types'
      )
      throw error
    }

    core.info(`Found migration types: ${migrationTypes.join(', ')}`)
    core.info(
      `Migration type mappings: ${JSON.stringify(
        migrationTypePrompts,
        null,
        2
      )}`
    )

    return { migrationTypePrompts, migrationTypes }
  } catch (parseError) {
    core.setFailed(
      `Failed to parse MIGRATION_TYPE_PROMPTS JSON: ${parseError.message}`
    )
    throw parseError
  }
}

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
 * @param {object} migrationTypePrompts - Migration type prompts mapping
 * @param {object} core - GitHub Actions core utilities
 * @param {string} org - Organization name
 * @returns {object[]} Array of valid repositories
 */
const validateRepositories = (
  repositories,
  migrationTypePrompts,
  core,
  org
) => {
  const validRepos = []

  for (const repo of repositories) {
    if (repo.migrationType && migrationTypePrompts[repo.migrationType]) {
      validRepos.push(repo)
      core.info(
        `Repository ${org}/${repo.name} needs migration from ${repo.migrationType}`
      )
    } else {
      core.info(
        `Repository ${org}/${repo.name} has migration type "${repo.migrationType}" but no corresponding prompt file found`
      )
    }
  }

  return validRepos
}

/**
 * Reads prompt file content for a specific migration type
 * @param {string} promptFileName - Name of the prompt file
 * @param {string} migrationType - Migration type for fallback message
 * @param {object} core - GitHub Actions core utilities
 * @param {object} process - Node.js process object
 * @returns {string} Prompt file content or fallback message
 */
const readPromptFile = (promptFileName, migrationType, core, process) => {
  try {
    const fs = require('fs')
    const path = require('path')

    const promptFilePath = path.join(
      process.cwd(),
      'agents',
      promptFileName
    )

    core.info(`Reading prompt file: ${promptFilePath}`)
    return fs.readFileSync(promptFilePath, 'utf8')
  } catch (fileError) {
    core.warning(
      `Failed to read prompt file ${promptFileName}: ${fileError.message}`
    )
    return `This repository has been identified for migration from ${migrationType} to GitHub Actions.`
  }
}

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
 * Assigns an issue to copilot-swe-agent
 * @param {object} issueGithub - GitHub client for issue operations
 * @param {object} core - GitHub Actions core utilities
 * @param {string} org - Organization name
 * @param {string} repoName - Repository name
 * @param {number} issueNumber - Issue number
 */
const assignIssueToCopilot = async (
  issueGithub,
  core,
  org,
  repoName,
  issueNumber
) => {
  try {
    const copilotQuery = `
      query {
        repository(owner: "${org}", name: "${repoName}") {
          suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {
            nodes {
              login
              __typename
              ... on Bot {
                id
              }
              ... on User {
                id
              }
            }
          }
          issue(number: ${issueNumber}) {
            id
            title
          }
        }
      }
    `

    const queryResult = await issueGithub.graphql(copilotQuery)
    const copilotBot = queryResult.repository.suggestedActors.nodes.find(
      (node) => node.login === 'copilot-swe-agent'
    )

    if (copilotBot && queryResult.repository.issue) {
      const assignMutation = `
        mutation {
          replaceActorsForAssignable(input: {
            assignableId: "${queryResult.repository.issue.id}",
            actorIds: ["${copilotBot.id}"]
          }) {
            assignable {
              ... on Issue {
                id
                title
                assignees(first: 10) {
                  nodes {
                    login
                  }
                }
              }
            }
          }
        }
      `

      await issueGithub.graphql(assignMutation)
      core.info(
        `Assigned copilot-swe-agent to issue #${issueNumber} in ${org}/${repoName}`
      )
    } else {
      core.warning(
        `Copilot-swe-agent not available for assignment in ${org}/${repoName} or issue not found`
      )
    }
  } catch (assignError) {
    core.warning(
      `Failed to assign copilot-swe-agent to issue #${issueNumber} in ${org}/${repoName}: ${assignError.message}`
    )
  }
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
    // Debug: Log available methods in github.rest.repos
    core.info(
      `Available repo methods: ${Object.keys(github.rest.repos)
        .filter((key) => key.includes('Custom'))
        .join(', ')}`
    )

    // Try the direct API call approach since the method might not exist
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
 * @param {object} migrationTypePrompts - Migration type prompts mapping
 * @param {object} github - GitHub API client
 * @param {object} core - GitHub Actions core utilities
 * @param {object} process - Node.js process object
 */
const processRepository = async (
  repo,
  org,
  migrationTypePrompts,
  github,
  core,
  process
) => {
  core.info(
    `Processing repository: ${org}/${repo.name} (Migration Type: ${repo.migrationType})`
  )

  try {
    const { migrationType } = repo
    const promptFileName = migrationTypePrompts[migrationType]

    if (!promptFileName) {
      core.warning(`No prompt file found for migration type: ${migrationType}`)
      return
    }

    // Read prompt file and create issue
    const issueBody = readPromptFile(
      promptFileName,
      migrationType,
      core,
      process
    )
    const issueTitle = `[Actions Migration] ${migrationType}`

    // Create GitHub client for issue operations
    const issueGithub = createIssueSubmitClient(github, core, process)

    // Create the migration issue
    const createdIssue = await issueGithub.rest.issues.create({
      owner: org,
      repo: repo.name,
      title: issueTitle,
      body: issueBody,
    })

    core.info(
      `Created migration issue for ${org}/${repo.name}: "${issueTitle}"`
    )

    // Assign issue to Copilot
    await assignIssueToCopilot(
      issueGithub,
      core,
      org,
      repo.name,
      createdIssue.data.number
    )

    // Update repository custom property
    await updateRepositoryMigrationProperty(github, core, org, repo.name)

    core.info(`Repository ${org}/${repo.name} processed successfully`)
  } catch (error) {
    core.warning(
      `Failed to process repository ${org}/${repo.name}: ${error.message}`
    )
  }
}

module.exports = async ({ github, context, core, process, org, batchSize }) => {
  try {
    core.info(`Starting migration process for organization: ${org}`)

    // Parse migration types from environment variable
    const { migrationTypePrompts, migrationTypes } = parseMigrationTypePrompts(
      core,
      process
    )

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
      migrationTypePrompts,
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

    // Process each repository
    for (const repo of batchedRepos) {
      await processRepository(
        repo,
        org,
        migrationTypePrompts,
        github,
        core,
        process
      )
    }

    core.info(`Completed processing repositories for organization: ${org}`)

    return {
      organization: org,
      totalRepositoriesSearched: foundRepos.length,
      repositoriesRequiringMigration: validRepos.length,
      processedRepositories: batchedRepos.length,
      repositoryNames: batchedRepos.map((repo) => repo.name),
    }
  } catch (error) {
    core.setFailed(
      `Failed to process repositories for ${org}: ${error.message}`
    )
    throw error
  }
}
