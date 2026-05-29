/**
 * Repo Scan — Stage 1, step 1: enumerate target repositories for this matrix shard.
 *
 * For matrix entries of kind 'org': lists every non-archived, non-disabled, non-fork
 * repository in the org via `GET /orgs/{org}/repos` (paginated).
 *
 * For matrix entries of kind 'explicit': iterates the `repositories` workflow input
 * and fetches each `owner/repo` directly via `GET /repos/{owner}/{repo}`.
 *
 * In both cases the global `excludes` workflow input is applied last.
 *
 * Output: writes the resolved list to `shard/<key>/repos.json` (one object per repo
 * with `owner`, `name`, `default_branch`, `description`, `topics`). Sets the
 * step output `count` (caller reads it to skip downstream steps when zero).
 *
 * @param {{ github: any, core: any, process: NodeJS.Process }} ctx
 * @returns {Promise<Array<{owner:string,name:string,default_branch:string,description:string|null,topics:string[]}>>}
 */
module.exports = async ({ github, core, process }) => {
    const fs = require('fs')
    const path = require('path')

    const kind = process.env.MATRIX_KIND
    const org = process.env.MATRIX_ORG
    const reposInput = process.env.REPOSITORIES_INPUT || '[]'
    const excludesInput = process.env.EXCLUDES_INPUT || '[]'

    if (!kind) throw new Error('MATRIX_KIND env var is required')
    if (!org) throw new Error('MATRIX_ORG env var is required')

    const parseArray = (raw, name) => {
        try {
            const parsed = JSON.parse(raw)
            if (!Array.isArray(parsed)) throw new Error(`${name} is not an array`)
            return parsed.map(String).map((s) => s.trim()).filter(Boolean)
        } catch (err) {
            throw new Error(`Failed to parse ${name}: ${err.message}`)
        }
    }

    const explicitRepos = parseArray(reposInput, 'repositories')
    const excludeSet = new Set(
        parseArray(excludesInput, 'excludes').map((s) => s.toLowerCase())
    )

    const normalize = (owner, name) => ({
        owner,
        name,
        key: `${owner}/${name}`.toLowerCase(),
    })

    let candidates = []

    if (kind === 'org') {
        core.info(`Enumerating repositories in org ${org}...`)
        const repos = await github.paginate(github.rest.repos.listForOrg, {
            org,
            type: 'all',
            per_page: 100,
        })
        core.info(`Org ${org}: ${repos.length} total repositories returned`)

        for (const r of repos) {
            if (r.archived) continue
            if (r.disabled) continue
            if (r.fork) continue
            candidates.push({
                owner: r.owner.login,
                name: r.name,
                default_branch: r.default_branch,
                description: r.description,
                topics: r.topics || [],
            })
        }
    } else if (kind === 'explicit') {
        core.info(`Resolving ${explicitRepos.length} explicit repositories...`)
        for (const entry of explicitRepos) {
            const [owner, name] = entry.split('/')
            if (!owner || !name) {
                core.warning(`Skipping malformed repositories entry: ${entry}`)
                continue
            }
            try {
                const { data } = await github.rest.repos.get({ owner, repo: name })
                if (data.archived || data.disabled) {
                    core.info(`Skipping ${entry}: archived or disabled`)
                    continue
                }
                candidates.push({
                    owner: data.owner.login,
                    name: data.name,
                    default_branch: data.default_branch,
                    description: data.description,
                    topics: data.topics || [],
                })
            } catch (err) {
                core.warning(`Failed to resolve ${entry}: ${err.status || ''} ${err.message}`)
            }
        }
    } else {
        throw new Error(`Unknown matrix kind: ${kind}`)
    }

    const filtered = candidates.filter((c) => {
        const key = normalize(c.owner, c.name).key
        if (excludeSet.has(key)) {
            core.info(`Excluding ${c.owner}/${c.name} (matched excludes)`)
            return false
        }
        return true
    })

    // Deduplicate by owner/name (case-insensitive) — explicit shard may overlap nothing,
    // but org-scan may legitimately list the same repo twice if pagination edge cases occur.
    const seen = new Set()
    const result = []
    for (const c of filtered) {
        const key = normalize(c.owner, c.name).key
        if (seen.has(key)) continue
        seen.add(key)
        result.push(c)
    }

    const shardDir = path.join('shard', sanitizeKey(org))
    fs.mkdirSync(shardDir, { recursive: true })
    fs.writeFileSync(
        path.join(shardDir, 'repos.json'),
        JSON.stringify(result, null, 2),
        'utf8'
    )

    core.setOutput('count', String(result.length))
    core.info(`Shard ${org}: ${result.length} repositories after filtering`)

    return result
}

function sanitizeKey(s) {
    return String(s).replace(/[^A-Za-z0-9._-]+/g, '_')
}
