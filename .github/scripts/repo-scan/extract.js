/**
 * Repo Scan — Stage 1, step 2: download pipeline + manifest files for each repo
 * resolved by enumerate.js, and emit a raw signals JSON per repo.
 *
 * Strategy (one round-trip per repo for the file tree):
 *   1. GET /repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1
 *      → flat list of blobs in the default branch.
 *   2. Match paths against the pipeline + manifest glob patterns defined
 *      below in PIPELINE_PATTERNS / MANIFEST_PATTERNS (source of truth for
 *      pipeline + manifest signal detection).
 *   3. Download matching blobs via GET /repos/{owner}/{repo}/contents/{path}
 *      (or via git/blobs if size exceeds 1MB).
 *   4. Record path-only signals (no download needed) using PATH_ONLY_PATTERNS.
 *   5. Fetch language stats via GET /repos/{owner}/{repo}/languages.
 *
 * Caps (env): MAX_PIPELINE_FILES_PER_REPO (default 25),
 *             MAX_PIPELINE_BYTES_PER_REPO (default 524288).
 * When a cap is hit, sets `truncated: true` in the raw signals file.
 *
 * Outputs under shard/<key>/:
 *   - pipelines/<owner>/<repo>/<original-path>   (raw content of pipeline files)
 *   - manifests/<owner>/<repo>/<original-path>   (raw content of manifest files)
 *   - raw/<owner>__<repo>.json                   (extracted signals, see schema below)
 *
 * Raw signals schema:
 * {
 *   "owner": "...",
 *   "repo": "...",
 *   "default_branch": "...",
 *   "languages": { "JavaScript": 12345, "HTML": 678 },
 *   "pipeline_files": [{ "path": "...", "platform": "GitHubActions", "size": 123, "loc": 45 }],
 *   "manifest_files": [{ "path": "...", "tool": "Maven", "size": 123 }],
 *   "path_only_hits": [{ "pattern": "*.tf", "label": "Terraform", "example_path": "..." }],
 *   "truncated": false,
 *   "errors": ["..."]
 * }
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
        core.info(`No repos.json at ${reposJsonPath}; nothing to extract.`)
        return
    }
    const repos = JSON.parse(fs.readFileSync(reposJsonPath, 'utf8'))

    const maxFiles = parseInt(process.env.MAX_PIPELINE_FILES_PER_REPO || '25', 10)
    const maxBytes = parseInt(process.env.MAX_PIPELINE_BYTES_PER_REPO || '524288', 10)

    fs.mkdirSync(path.join(shardDir, 'raw'), { recursive: true })

    for (const repo of repos) {
        const result = {
            owner: repo.owner,
            repo: repo.name,
            default_branch: repo.default_branch,
            languages: {},
            pipeline_files: [],
            manifest_files: [],
            path_only_hits: [],
            truncated: false,
            errors: [],
        }

        try {
            // Languages
            try {
                const { data } = await github.rest.repos.listLanguages({
                    owner: repo.owner,
                    repo: repo.name,
                })
                result.languages = data || {}
            } catch (err) {
                result.errors.push(`languages: ${err.status || ''} ${err.message}`)
            }

            // File tree
            let tree
            try {
                const { data } = await github.rest.git.getTree({
                    owner: repo.owner,
                    repo: repo.name,
                    tree_sha: repo.default_branch,
                    recursive: 'true',
                })
                tree = data.tree || []
                if (data.truncated) {
                    result.truncated = true
                    result.errors.push('git tree truncated by GitHub API')
                }
            } catch (err) {
                result.errors.push(`tree: ${err.status || ''} ${err.message}`)
                tree = []
            }

            let bytesFetched = 0

            for (const node of tree) {
                if (node.type !== 'blob') continue
                const p = node.path

                // Pipeline file?
                const pipelineHit = matchPipeline(p)
                if (pipelineHit) {
                    if (result.pipeline_files.length >= maxFiles) {
                        result.truncated = true
                        continue
                    }
                    if (bytesFetched + (node.size || 0) > maxBytes) {
                        result.truncated = true
                        continue
                    }
                    const content = await fetchFile(github, repo.owner, repo.name, p, node.sha, core)
                    if (content !== null) {
                        const target = path.join(
                            shardDir,
                            'pipelines',
                            repo.owner,
                            repo.name,
                            p
                        )
                        fs.mkdirSync(path.dirname(target), { recursive: true })
                        fs.writeFileSync(target, content)
                        const loc = content.toString('utf8').split('\n').length
                        result.pipeline_files.push({
                            path: p,
                            platform: pipelineHit,
                            size: node.size || content.length,
                            loc,
                        })
                        bytesFetched += node.size || content.length
                    }
                    continue
                }

                // Manifest file?
                const manifestHit = matchManifest(p)
                if (manifestHit) {
                    const content = await fetchFile(github, repo.owner, repo.name, p, node.sha, core)
                    if (content !== null) {
                        const target = path.join(
                            shardDir,
                            'manifests',
                            repo.owner,
                            repo.name,
                            p
                        )
                        fs.mkdirSync(path.dirname(target), { recursive: true })
                        fs.writeFileSync(target, content)
                        result.manifest_files.push({
                            path: p,
                            tool: manifestHit,
                            size: node.size || content.length,
                        })
                    }
                    continue
                }

                // Path-only signal?
                const pathOnly = matchPathOnly(p)
                if (pathOnly) {
                    const already = result.path_only_hits.find(
                        (h) => h.label === pathOnly.label
                    )
                    if (!already) {
                        result.path_only_hits.push({
                            pattern: pathOnly.pattern,
                            label: pathOnly.label,
                            example_path: p,
                        })
                    }
                }
            }
        } catch (err) {
            result.errors.push(`unhandled: ${err.message}`)
        }

        const rawPath = path.join(
            shardDir,
            'raw',
            `${repo.owner}__${repo.name}.json`
        )
        fs.writeFileSync(rawPath, JSON.stringify(result, null, 2), 'utf8')
        core.info(
            `Extracted ${repo.owner}/${repo.name}: ${result.pipeline_files.length} pipeline, ${result.manifest_files.length} manifest, ${result.path_only_hits.length} path-only${result.truncated ? ' (truncated)' : ''}`
        )
    }
}

// ---- helpers ----

function sanitizeKey(s) {
    return String(s).replace(/[^A-Za-z0-9._-]+/g, '_')
}

async function fetchFile(github, owner, repo, p, sha, core) {
    try {
        // Use git/blobs for any size; returns base64.
        const { data } = await github.rest.git.getBlob({
            owner,
            repo,
            file_sha: sha,
        })
        return Buffer.from(data.content, data.encoding || 'base64')
    } catch (err) {
        core.warning(`fetch ${owner}/${repo}:${p}: ${err.status || ''} ${err.message}`)
        return null
    }
}

// ---- pattern matchers ----
// Source of truth for pipeline/manifest/path-only signal detection. The canonical
// labels these patterns produce are documented in plugin/skills/inventory-analysis/SKILL.md.

const PIPELINE_PATTERNS = [
    { re: /^\.github\/workflows\/[^/]+\.ya?ml$/, label: 'GitHubActions' },
    { re: /^Jenkinsfile$/, label: 'Jenkins' },
    { re: /^Jenkinsfile\.[^/]+$/, label: 'Jenkins' },
    { re: /\.jenkinsfile$/, label: 'Jenkins' },
    { re: /^\.jenkins\/.*\.groovy$/, label: 'Jenkins' },
    { re: /^azure-pipelines\.yml$/, label: 'AzureDevOps' },
    { re: /^azure-pipelines-[^/]+\.yml$/, label: 'AzureDevOps' },
    { re: /^\.azure-pipelines\/.*\.ya?ml$/, label: 'AzureDevOps' },
    { re: /^\.gitlab-ci\.yml$/, label: 'GitLabCI' },
    { re: /^\.circleci\/config\.yml$/, label: 'CircleCI' },
    { re: /^\.travis\.yml$/, label: 'TravisCI' },
    { re: /^bamboo-specs\/.*\.ya?ml$/, label: 'Bamboo' },
    { re: /^bamboo\.ya?ml$/, label: 'Bamboo' },
    { re: /^bitbucket-pipelines\.yml$/, label: 'BitbucketPipelines' },
    { re: /^\.drone\.ya?ml$/, label: 'DroneCI' },
]

const MANIFEST_PATTERNS = [
    { re: /^package\.json$/, label: 'npm' },
    { re: /^package-lock\.json$/, label: 'npm' },
    { re: /^yarn\.lock$/, label: 'Yarn' },
    { re: /^pnpm-lock\.yaml$/, label: 'pnpm' },
    { re: /^pom\.xml$/, label: 'Maven' },
    { re: /^build\.gradle(\.kts)?$/, label: 'Gradle' },
    { re: /^settings\.gradle(\.kts)?$/, label: 'Gradle' },
    { re: /^requirements[^/]*\.txt$/, label: 'Pip' },
    { re: /^pyproject\.toml$/, label: 'Poetry' },
    { re: /^setup\.py$/, label: 'Setuptools' },
    { re: /^setup\.cfg$/, label: 'Setuptools' },
    { re: /^go\.mod$/, label: 'GoModules' },
    { re: /^Cargo\.toml$/, label: 'CargoCrate' },
    { re: /^Gemfile$/, label: 'Bundler' },
    { re: /^Gemfile\.lock$/, label: 'Bundler' },
    { re: /\.csproj$/, label: 'DotNet' },
    { re: /\.fsproj$/, label: 'DotNet' },
    { re: /\.vbproj$/, label: 'DotNet' },
    { re: /\.sln$/, label: 'DotNet' },
    { re: /^global\.json$/, label: 'DotNet' },
    { re: /^Makefile$/, label: 'Make' },
    { re: /^GNUmakefile$/, label: 'Make' },
    { re: /^BUILD(\.bazel)?$/, label: 'Bazel' },
    { re: /^WORKSPACE$/, label: 'Bazel' },
    { re: /^MODULE\.bazel$/, label: 'Bazel' },
    { re: /^build\.sbt$/, label: 'SBT' },
    { re: /^mix\.exs$/, label: 'Mix' },
    { re: /^composer\.json$/, label: 'Composer' },
    { re: /^Dockerfile$/, label: 'Docker' },
    { re: /\.dockerfile$/, label: 'Docker' },
    { re: /^containerfile$/i, label: 'Docker' },
    { re: /^docker-compose\.ya?ml$/, label: 'DockerCompose' },
    { re: /^compose\.yml$/, label: 'DockerCompose' },
    { re: /^Procfile$/, label: 'Buildpacks' },
]

const PATH_ONLY_PATTERNS = [
    { re: /\.tf$/, pattern: '*.tf', label: 'Terraform' },
    { re: /\.tf\.json$/, pattern: '*.tf.json', label: 'Terraform' },
    { re: /^terraform\//, pattern: 'terraform/**', label: 'Terraform' },
    { re: /\.tofu$/, pattern: '*.tofu', label: 'OpenTofu' },
    { re: /^Pulumi\.ya?ml$/, pattern: 'Pulumi.yaml', label: 'Pulumi' },
    { re: /^Pulumi\.[^/]+\.ya?ml$/, pattern: 'Pulumi.*.yaml', label: 'Pulumi' },
    { re: /(^|\/)Chart\.yaml$/, pattern: '**/Chart.yaml', label: 'Helm' },
    { re: /^charts\//, pattern: 'charts/**', label: 'Helm' },
    { re: /^kustomization\.ya?ml$/, pattern: 'kustomization.yaml', label: 'Kustomize' },
    { re: /\.template\.ya?ml$/, pattern: '*.template.yaml', label: 'CloudFormation' },
    { re: /^cloudformation\//, pattern: 'cloudformation/**', label: 'CloudFormation' },
    { re: /\.bicep$/, pattern: '*.bicep', label: 'Bicep' },
    { re: /^azuredeploy\.json$/, pattern: 'azuredeploy.json', label: 'ARM' },
    { re: /^playbook\.yml$/, pattern: 'playbook.yml', label: 'Ansible' },
    { re: /^playbooks\//, pattern: 'playbooks/**', label: 'Ansible' },
    { re: /^roles\/[^/]+\/tasks\/main\.yml$/, pattern: 'roles/**/tasks/main.yml', label: 'Ansible' },
    { re: /^metadata\.rb$/, pattern: 'metadata.rb', label: 'Chef' },
    { re: /^cookbooks\//, pattern: 'cookbooks/**', label: 'Chef' },
    { re: /^manifests\/.+\.pp$/, pattern: 'manifests/**/*.pp', label: 'Puppet' },
    { re: /^Puppetfile$/, pattern: 'Puppetfile', label: 'Puppet' },
    { re: /^serverless\.yml$/, pattern: 'serverless.yml', label: 'AWS-Lambda' },
    { re: /^sam\.yaml$/, pattern: 'sam.yaml', label: 'AWS-Lambda' },
    { re: /^app\.yaml$/, pattern: 'app.yaml', label: 'GCP-AppEngine' },
    { re: /^\.elasticbeanstalk\//, pattern: '.elasticbeanstalk/**', label: 'AWS-Beanstalk' },
    { re: /^task-definition\.json$/, pattern: 'task-definition.json', label: 'AWS-ECS' },
]

function matchPipeline(p) {
    for (const m of PIPELINE_PATTERNS) if (m.re.test(p)) return m.label
    return null
}
function matchManifest(p) {
    for (const m of MANIFEST_PATTERNS) if (m.re.test(p)) return m.label
    return null
}
function matchPathOnly(p) {
    for (const m of PATH_ONLY_PATTERNS) if (m.re.test(p)) return m
    return null
}
