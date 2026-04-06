/**
 * Deploys hooks from .github/hooks/ in the control repository (.github-private)
 * to every target repository in the configured organizations.
 *
 * Hooks are per-repo only — they do NOT propagate from .github-private to target
 * repos when the coding agent runs. This script copies them via the Contents API.
 *
 * Run as part of settings.yml (one-time bootstrap) alongside create-environment-secrets.js.
 * Re-run whenever hooks are updated or new repos are added to the org.
 */

const path = require('path')
const fs = require('fs')

/**
 * Gets all repositories in an organization
 */
const getAllRepositories = async (github, core, org) => {
  core.info(`Fetching all repositories in organization: ${org}`)
  try {
    const repositories = await github.paginate(github.rest.repos.listForOrg, {
      org: org,
      per_page: 100,
    })
    core.info(`Found ${repositories.length} repositories in ${org}`)
    return repositories
      .filter((repo) => !repo.archived && !repo.fork)
      .filter((repo) => repo.name !== '.github-private')
      .map((repo) => ({ name: repo.name, owner: org }))
  } catch (error) {
    core.warning(`Failed to fetch repositories for ${org}: ${error.message}`)
    return []
  }
}

/**
 * Gets the SHA of an existing file (needed for updates via Contents API)
 */
const getFileSha = async (github, owner, repo, filePath) => {
  try {
    const { data } = await github.rest.repos.getContent({
      owner,
      repo,
      path: filePath,
    })
    return data.sha
  } catch {
    return null // File doesn't exist yet
  }
}

/**
 * Deploys a single hook file to a target repository
 */
const deployHookFile = async (github, core, owner, repo, hookName, content) => {
  const targetPath = `.github/hooks/${hookName}`
  const sha = await getFileSha(github, owner, repo, targetPath)

  const params = {
    owner,
    repo,
    path: targetPath,
    message: `Deploy migration hook: ${hookName}`,
    content: Buffer.from(content).toString('base64'),
    committer: {
      name: 'github-actions[bot]',
      email: '41898282+github-actions[bot]@users.noreply.github.com',
    },
  }

  if (sha) {
    params.sha = sha // Update existing file
  }

  await github.rest.repos.createOrUpdateFileContents(params)
}

/**
 * Main entry point
 */
module.exports = async ({ github, core, process, config, workspace }) => {
  const parsedConfig = JSON.parse(config)
  const organizations = parsedConfig.organizations || []

  // Read hook files from the local .github/hooks/ directory
  const hooksDir = path.join(workspace, '.github', 'hooks')

  if (!fs.existsSync(hooksDir)) {
    core.warning('No .github/hooks/ directory found — skipping hook deployment')
    return { deployed: 0, skipped: 0, failed: 0 }
  }

  const hookFiles = fs.readdirSync(hooksDir).filter((f) => {
    const ext = path.extname(f)
    return ext === '.sh' || ext === '.json'
  })

  if (hookFiles.length === 0) {
    core.info('No hook files found in .github/hooks/')
    return { deployed: 0, skipped: 0, failed: 0 }
  }

  core.info(`Found ${hookFiles.length} hook files: ${hookFiles.join(', ')}`)

  // Read all hook file contents
  const hooks = {}
  for (const hookFile of hookFiles) {
    hooks[hookFile] = fs.readFileSync(path.join(hooksDir, hookFile), 'utf8')
  }

  let deployed = 0
  let skipped = 0
  let failed = 0

  for (const org of organizations) {
    const repos = await getAllRepositories(github, core, org)

    for (const repo of repos) {
      core.info(`Deploying hooks to ${repo.owner}/${repo.name}`)

      try {
        for (const [hookName, content] of Object.entries(hooks)) {
          await deployHookFile(github, core, repo.owner, repo.name, hookName, content)
        }
        core.info(`✓ Deployed ${hookFiles.length} hooks to ${repo.owner}/${repo.name}`)
        deployed++
      } catch (error) {
        core.warning(`✗ Failed to deploy hooks to ${repo.owner}/${repo.name}: ${error.message}`)
        failed++
      }
    }
  }

  core.info(`Hook deployment complete: ${deployed} repos updated, ${skipped} skipped, ${failed} failed`)
  return { deployed, skipped, failed }
}
