/**
 * Repo Scan — Stage 1, step 3: extract CI-side dependencies from the pipeline
 * files captured by extract.js.
 *
 * "CI dependencies" means references that a pipeline file makes to artifacts
 * *outside the source repository* — reusable workflows, marketplace actions,
 * shared libraries, included pipeline files, templates, orbs, pipes, plugin
 * images, etc. We do NOT capture application-code package dependencies (npm,
 * Maven, pip, etc.) — that is a separate concern handled by GitHub's
 * Dependency Graph.
 *
 * Pure: no network calls. Reads only from shard/<key>/pipelines/.
 *
 * Output: shard/<key>/dependencies.csv with columns:
 *   org, repo, ci_platform, source_path, dependency_kind, dependency_ref, version
 *
 * Where:
 *   ci_platform     — canonical CI platform label (GitHubActions, GitLabCI,
 *                     AzureDevOps, Jenkins, CircleCI, BitbucketPipelines,
 *                     DroneCI, TravisCI)
 *   source_path     — path of the pipeline file declaring the dependency,
 *                     relative to the captured tree (e.g.
 *                     .github/workflows/ci.yml)
 *   dependency_kind — one of: Action, ReusableWorkflow, GitLabIncludeProject,
 *                     GitLabIncludeRemote, GitLabIncludeTemplate,
 *                     AzureTemplate, AzureRepoResource, JenkinsSharedLibrary,
 *                     CircleCIOrb, BitbucketPipe, BitbucketImport,
 *                     DronePlugin, TravisImport
 *   dependency_ref  — the referenced identifier (action name, workflow path,
 *                     library name, orb, pipe, plugin image, etc.)
 *   version         — the ref/version pin if specified, otherwise empty
 *
 * @param {{ core: any, process: NodeJS.Process }} ctx
 */
module.exports = async ({ core, process }) => {
    const fs = require('fs')
    const path = require('path')

    const matrixKey = process.env.MATRIX_KEY
    if (!matrixKey) throw new Error('MATRIX_KEY env var is required')
    const shardKey = sanitizeKey(matrixKey)
    const shardDir = path.join('shard', shardKey)
    const pipelinesRoot = path.join(shardDir, 'pipelines')

    const rows = [
        [
            'org',
            'repo',
            'ci_platform',
            'source_path',
            'dependency_kind',
            'dependency_ref',
            'version',
        ],
    ]

    if (!fs.existsSync(pipelinesRoot)) {
        core.info(`No pipelines/ directory at ${pipelinesRoot}; nothing to scan.`)
        fs.writeFileSync(
            path.join(shardDir, 'dependencies.csv'),
            rows.map(toCsvRow).join('\n') + '\n',
            'utf8'
        )
        return
    }

    let depCount = 0
    for (const owner of fs.readdirSync(pipelinesRoot)) {
        const ownerDir = path.join(pipelinesRoot, owner)
        if (!fs.statSync(ownerDir).isDirectory()) continue
        for (const repo of fs.readdirSync(ownerDir)) {
            const repoDir = path.join(ownerDir, repo)
            if (!fs.statSync(repoDir).isDirectory()) continue
            for (const file of walk(repoDir)) {
                const relPath = path.relative(repoDir, file).split(path.sep).join('/')
                const platform = detectPlatform(relPath)
                if (!platform) continue
                let content
                try {
                    content = fs.readFileSync(file, 'utf8')
                } catch (err) {
                    core.warning(`Failed to read ${file}: ${err.message}`)
                    continue
                }
                const deps = extractDependencies(platform, content)
                for (const dep of deps) {
                    rows.push([
                        owner,
                        repo,
                        platform,
                        relPath,
                        dep.kind,
                        dep.ref,
                        dep.version || '',
                    ])
                    depCount += 1
                }
            }
        }
    }

    fs.writeFileSync(
        path.join(shardDir, 'dependencies.csv'),
        rows.map(toCsvRow).join('\n') + '\n',
        'utf8'
    )
    core.info(`Wrote ${depCount} CI dependency rows for shard ${matrixKey}`)
}

function walk(dir) {
    const out = []
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, entry.name)
        if (entry.isDirectory()) {
            out.push(...walk(p))
        } else if (entry.isFile()) {
            out.push(p)
        }
    }
    return out
}

function detectPlatform(relPath) {
    const lower = relPath.toLowerCase()
    if (lower.startsWith('.github/workflows/') && /\.ya?ml$/.test(lower))
        return 'GitHubActions'
    if (/(^|\/)jenkinsfile(\.|$)/i.test(relPath) || /\.jenkinsfile$/i.test(relPath))
        return 'Jenkins'
    if (lower === '.gitlab-ci.yml' || lower.startsWith('.gitlab/'))
        return 'GitLabCI'
    if (
        lower === 'azure-pipelines.yml' ||
        lower === 'azure-pipelines.yaml' ||
        lower.startsWith('.azure-pipelines/') ||
        lower.startsWith('.pipelines/') ||
        /(^|\/)azure-pipelines[^/]*\.ya?ml$/.test(lower)
    )
        return 'AzureDevOps'
    if (lower === '.circleci/config.yml' || lower === '.circleci/config.yaml')
        return 'CircleCI'
    if (lower === 'bitbucket-pipelines.yml' || lower === 'bitbucket-pipelines.yaml')
        return 'BitbucketPipelines'
    if (lower === '.drone.yml' || lower === '.drone.yaml' || lower.startsWith('.drone/'))
        return 'DroneCI'
    if (lower === '.travis.yml' || lower === '.travis.yaml') return 'TravisCI'
    return null
}

function extractDependencies(platform, content) {
    switch (platform) {
        case 'GitHubActions':
            return extractGitHubActions(content)
        case 'GitLabCI':
            return extractGitLabCI(content)
        case 'AzureDevOps':
            return extractAzureDevOps(content)
        case 'Jenkins':
            return extractJenkins(content)
        case 'CircleCI':
            return extractCircleCI(content)
        case 'BitbucketPipelines':
            return extractBitbucket(content)
        case 'DroneCI':
            return extractDroneCI(content)
        case 'TravisCI':
            return extractTravisCI(content)
        default:
            return []
    }
}

// ── GitHub Actions ──────────────────────────────────────────────────────────
// `uses: owner/repo[/path]@ref` — split into action vs reusable workflow by
// whether the path includes `.github/workflows/`. Skip `uses: ./...` (local).
function extractGitHubActions(content) {
    const out = []
    const re = /^\s*-?\s*uses:\s*['"]?([^'"#\s]+)['"]?/gm
    let m
    while ((m = re.exec(content)) !== null) {
        const raw = m[1]
        if (raw.startsWith('./') || raw.startsWith('.\\')) continue
        if (raw.startsWith('docker://')) {
            out.push({ kind: 'Action', ref: raw, version: '' })
            continue
        }
        const atIdx = raw.lastIndexOf('@')
        const ref = atIdx === -1 ? raw : raw.slice(0, atIdx)
        const version = atIdx === -1 ? '' : raw.slice(atIdx + 1)
        const kind = /\.github\/workflows\//.test(ref) ? 'ReusableWorkflow' : 'Action'
        out.push({ kind, ref, version })
    }
    return out
}

// ── GitLab CI ───────────────────────────────────────────────────────────────
// Includes come in several shapes; capture project/remote/template, skip local.
function extractGitLabCI(content) {
    const out = []
    const projectRe = /^\s*-?\s*project:\s*['"]?([^'"#\s]+)['"]?/gm
    const remoteRe = /^\s*-?\s*remote:\s*['"]?(https?:\/\/[^'"#\s]+)['"]?/gm
    const templateRe = /^\s*-?\s*template:\s*['"]?([^'"#\s]+)['"]?/gm
    const shortRemoteRe = /^\s*include:\s*['"]?(https?:\/\/[^'"#\s]+)['"]?/gm
    let m
    while ((m = projectRe.exec(content)) !== null) {
        // try to find ref: on a nearby following line
        const tail = content.slice(m.index, m.index + 400)
        const refMatch = /\bref:\s*['"]?([^'"#\s]+)['"]?/.exec(tail)
        out.push({
            kind: 'GitLabIncludeProject',
            ref: m[1],
            version: refMatch ? refMatch[1] : '',
        })
    }
    while ((m = remoteRe.exec(content)) !== null) {
        out.push({ kind: 'GitLabIncludeRemote', ref: m[1], version: '' })
    }
    while ((m = shortRemoteRe.exec(content)) !== null) {
        out.push({ kind: 'GitLabIncludeRemote', ref: m[1], version: '' })
    }
    while ((m = templateRe.exec(content)) !== null) {
        out.push({ kind: 'GitLabIncludeTemplate', ref: m[1], version: '' })
    }
    return out
}

// ── Azure DevOps ────────────────────────────────────────────────────────────
// `template: file.yml@alias` and resources.repositories entries.
function extractAzureDevOps(content) {
    const out = []
    const tmplRe = /^\s*-?\s*template:\s*['"]?([^@'"#\s]+)(?:@([^'"#\s]+))?['"]?/gm
    let m
    while ((m = tmplRe.exec(content)) !== null) {
        const file = m[1]
        const alias = m[2] || ''
        if (file.startsWith('./') || (!alias && !file.includes('/') && !file.includes('@')))
            // Local template (no alias and looks like a sibling file) — skip.
            continue
        out.push({
            kind: 'AzureTemplate',
            ref: alias ? `${file}@${alias}` : file,
            version: '',
        })
    }
    // Repo resources: parse the `resources: repositories:` block by lines.
    const repoRes = parseAzureRepoResources(content)
    for (const r of repoRes) {
        out.push({
            kind: 'AzureRepoResource',
            ref: r.name,
            version: r.ref || '',
        })
    }
    return out
}

function parseAzureRepoResources(content) {
    const lines = content.split(/\r?\n/)
    const out = []
    let inRepos = false
    let current = null
    let reposIndent = -1
    for (const line of lines) {
        const trimmed = line.replace(/\s+$/, '')
        if (/^\s*repositories\s*:\s*$/.test(trimmed)) {
            inRepos = true
            reposIndent = trimmed.search(/\S/)
            continue
        }
        if (!inRepos) continue
        const indent = trimmed.search(/\S/)
        if (indent <= reposIndent && trimmed.trim() !== '') {
            // Left the repositories block.
            if (current && current.name) out.push(current)
            inRepos = false
            current = null
            continue
        }
        const repoStart = /^\s*-\s*repository:\s*(\S+)/.exec(trimmed)
        if (repoStart) {
            if (current && current.name) out.push(current)
            current = { alias: repoStart[1], name: '', ref: '' }
            continue
        }
        if (!current) continue
        const nameM = /^\s*name:\s*['"]?([^'"#\s]+)['"]?/.exec(trimmed)
        if (nameM) current.name = nameM[1]
        const refM = /^\s*ref:\s*['"]?([^'"#\s]+)['"]?/.exec(trimmed)
        if (refM) current.ref = refM[1]
    }
    if (current && current.name) out.push(current)
    return out
}

// ── Jenkins ─────────────────────────────────────────────────────────────────
// @Library('name@version') and library 'name@version'.
function extractJenkins(content) {
    const out = []
    const re1 = /@Library\(\s*['"]([^'"]+)['"]\s*\)/g
    const re2 = /\blibrary\s+(?:identifier:\s*)?['"]([^'"]+)['"]/g
    const seen = new Set()
    const push = (raw) => {
        const atIdx = raw.lastIndexOf('@')
        const ref = atIdx === -1 ? raw : raw.slice(0, atIdx)
        const version = atIdx === -1 ? '' : raw.slice(atIdx + 1)
        const key = `${ref}|${version}`
        if (seen.has(key)) return
        seen.add(key)
        out.push({ kind: 'JenkinsSharedLibrary', ref, version })
    }
    let m
    while ((m = re1.exec(content)) !== null) push(m[1])
    while ((m = re2.exec(content)) !== null) push(m[1])
    return out
}

// ── CircleCI ────────────────────────────────────────────────────────────────
// `orbs:` block — entries are `<alias>: <namespace>/<orb>@<version>`.
function extractCircleCI(content) {
    const out = []
    const lines = content.split(/\r?\n/)
    let inOrbs = false
    let orbsIndent = -1
    for (const line of lines) {
        if (/^\s*orbs\s*:\s*$/.test(line)) {
            inOrbs = true
            orbsIndent = line.search(/\S/)
            continue
        }
        if (!inOrbs) continue
        const stripped = line.replace(/\s+$/, '')
        if (stripped.trim() === '') continue
        const indent = stripped.search(/\S/)
        if (indent <= orbsIndent) {
            inOrbs = false
            continue
        }
        const m = /^\s*[\w-]+:\s*['"]?([a-z][\w-]+\/[\w-]+)@([^\s#'"]+)['"]?/.exec(stripped)
        if (m) out.push({ kind: 'CircleCIOrb', ref: m[1], version: m[2] })
    }
    return out
}

// ── Bitbucket Pipelines ─────────────────────────────────────────────────────
// `pipe: namespace/name:version` (or docker://...) and `import: repo:branch:pipeline`.
function extractBitbucket(content) {
    const out = []
    const pipeRe = /^\s*-?\s*pipe:\s*['"]?([^'"#\s]+)['"]?/gm
    const importRe = /^\s*-?\s*import:\s*['"]?([^'"#\s]+)['"]?/gm
    let m
    while ((m = pipeRe.exec(content)) !== null) {
        const raw = m[1]
        if (raw.startsWith('docker://')) {
            out.push({ kind: 'BitbucketPipe', ref: raw, version: '' })
            continue
        }
        const colonIdx = raw.lastIndexOf(':')
        const ref = colonIdx === -1 ? raw : raw.slice(0, colonIdx)
        const version = colonIdx === -1 ? '' : raw.slice(colonIdx + 1)
        out.push({ kind: 'BitbucketPipe', ref, version })
    }
    while ((m = importRe.exec(content)) !== null) {
        out.push({ kind: 'BitbucketImport', ref: m[1], version: '' })
    }
    return out
}

// ── Drone CI ────────────────────────────────────────────────────────────────
// Plugin steps are conventionally `image: plugins/<name>:<tag>`.
function extractDroneCI(content) {
    const out = []
    const re = /^\s*image:\s*['"]?(plugins\/[^\s#'"]+)['"]?/gm
    let m
    while ((m = re.exec(content)) !== null) {
        const raw = m[1]
        const colonIdx = raw.lastIndexOf(':')
        const ref = colonIdx === -1 ? raw : raw.slice(0, colonIdx)
        const version = colonIdx === -1 ? '' : raw.slice(colonIdx + 1)
        out.push({ kind: 'DronePlugin', ref, version })
    }
    return out
}

// ── Travis CI ───────────────────────────────────────────────────────────────
// `import: - source: <ref>` or `import: source: <ref>`.
function extractTravisCI(content) {
    const out = []
    const re = /^\s*-?\s*source:\s*['"]?([^'"#\s]+)['"]?/gm
    // Only consider sources that look like cross-repo imports (owner/repo:path).
    let m
    while ((m = re.exec(content)) !== null) {
        const raw = m[1]
        if (!/^[\w.-]+\/[\w.-]+:/.test(raw)) continue
        out.push({ kind: 'TravisImport', ref: raw, version: '' })
    }
    return out
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

// Hoist `fs`/`path` to module scope for the `walk` helper.
const fs = require('fs')
const path = require('path')
