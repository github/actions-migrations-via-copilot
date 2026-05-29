/**
 * Repo Scan — Stage 1, step 3 (optional): query the GitHub Dependency Graph
 * for each repo and emit per-(repo, package) rows.
 *
 * Requires the GitHub App used by repo-scan.yml to have the
 * `Dependency graph: read` repository permission. If a repo returns an
 * authorization error, the failure is recorded in the per-shard error list
 * and the script moves on (does not fail the workflow).
 *
 * Output: shard/<key>/dependencies.csv with columns:
 *   org, repo, ecosystem, package, version, requirement, manifest_path
 *
 * @param {{ github: any, core: any, process: NodeJS.Process }} ctx
 */
module.exports = async ({ github, core, process }) => {
    const fs = require('fs')
    const path = require('path')

    const matrixKey = process.env.MATRIX_KEY
    if (!matrixKey) throw new Error('MATRIX_KEY env var is required')
    const shardKey = sanitizeKey(matrixKey)
    const shardDir = path.join('shard', shardKey)
    const reposJsonPath = path.join(shardDir, 'repos.json')
    if (!fs.existsSync(reposJsonPath)) {
        core.info('No repos.json found; nothing to query.')
        return
    }
    const repos = JSON.parse(fs.readFileSync(reposJsonPath, 'utf8'))

    const rows = [
        ['org', 'repo', 'ecosystem', 'package', 'version', 'requirement', 'manifest_path'],
    ]

    for (const repo of repos) {
        try {
            let cursor = null
            let pages = 0
            // Cap at 10 pages of manifests per repo to bound runtime on monorepos.
            while (pages < 10) {
                const query = `
          query($owner:String!,$name:String!,$cursor:String) {
            repository(owner:$owner, name:$name) {
              dependencyGraphManifests(first: 25, after: $cursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  filename
                  dependencies(first: 100) {
                    nodes {
                      packageName
                      packageManager
                      requirements
                      repository { name }
                    }
                  }
                }
              }
            }
          }
        `
                const resp = await github.graphql(query, {
                    owner: repo.owner,
                    name: repo.name,
                    cursor,
                })
                const manifests = resp.repository?.dependencyGraphManifests
                if (!manifests) break
                for (const m of manifests.nodes || []) {
                    for (const d of m.dependencies?.nodes || []) {
                        rows.push([
                            repo.owner,
                            repo.name,
                            d.packageManager || '',
                            d.packageName || '',
                            '',
                            d.requirements || '',
                            m.filename || '',
                        ])
                    }
                }
                if (!manifests.pageInfo?.hasNextPage) break
                cursor = manifests.pageInfo.endCursor
                pages += 1
            }
        } catch (err) {
            core.warning(
                `dependency graph for ${repo.owner}/${repo.name}: ${err.message}`
            )
        }
    }

    const csv = rows.map(toCsvRow).join('\n') + '\n'
    fs.writeFileSync(path.join(shardDir, 'dependencies.csv'), csv, 'utf8')
    core.info(`Wrote ${rows.length - 1} dependency rows for shard ${matrixKey}`)
}

function sanitizeKey(s) {
    return String(s).replace(/[^A-Za-z0-9._-]+/g, '_')
}

function toCsvRow(cells) {
    return cells
        .map((c) => {
            const s = c === null || c === undefined ? '' : String(c)
            if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"'
            return s
        })
        .join(',')
}
