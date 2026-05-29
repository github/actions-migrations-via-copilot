/**
 * Repo Scan — Stage 1, step 4: translate per-repo raw signals into canonical
 * labels and emit shard/<key>/repos.csv. The canonical label vocabulary is
 * documented in plugin/skills/inventory-analysis/SKILL.md (Canonical taxonomy).
 *
 * Reads:   shard/<key>/raw/<owner>__<repo>.json (produced by extract.js)
 *          shard/<key>/pipelines/<owner>/<repo>/...  (for deploy-target scanning)
 *
 * Writes:  shard/<key>/repos.csv with columns documented in
 *          docs/repo-scan.md (#reposcsv-columns).
 *
 * Pure: no network calls. Safe to re-run locally.
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
    const rawDir = path.join(shardDir, 'raw')
    if (!fs.existsSync(rawDir)) {
        core.info(`No raw/ directory at ${rawDir}; nothing to classify.`)
        return
    }

    const header = [
        'org',
        'repo',
        'default_branch',
        'primary_language',
        'secondary_languages',
        'build_tools',
        'package_managers',
        'ci_platforms',
        'deploy_targets',
        'container',
        'iac',
        'has_dockerfile',
        'has_helm',
        'pipeline_file_count',
        'total_loc_pipeline',
        'signals_json',
    ]
    const rows = [header]

    const files = fs.readdirSync(rawDir).filter((f) => f.endsWith('.json'))
    for (const f of files) {
        const raw = JSON.parse(fs.readFileSync(path.join(rawDir, f), 'utf8'))
        const row = classifyOne(raw, shardDir)
        rows.push(header.map((h) => row[h]))
    }

    const csv = rows.map(toCsvRow).join('\n') + '\n'
    fs.writeFileSync(path.join(shardDir, 'repos.csv'), csv, 'utf8')
    core.info(`Classified ${rows.length - 1} repos for shard ${matrixKey}`)
}

function classifyOne(raw, shardDir) {
    const langEntries = Object.entries(raw.languages || {}).sort(
        (a, b) => b[1] - a[1]
    )
    const primary = langEntries[0]?.[0] || ''
    const secondary = langEntries.slice(1).map((e) => e[0])

    // Build tools / package managers — start from manifests, then refine.
    const manifestLabels = new Set(
        (raw.manifest_files || []).map((m) => m.tool).filter(Boolean)
    )
    const buildTools = new Set()
    const pkgManagers = new Set()

    // npm/Yarn/pnpm disambiguation based on lockfile presence.
    if (manifestLabels.has('npm') || manifestLabels.has('Yarn') || manifestLabels.has('pnpm')) {
        if (manifestLabels.has('pnpm')) {
            pkgManagers.add('pnpm')
            buildTools.add('pnpm')
        } else if (manifestLabels.has('Yarn')) {
            pkgManagers.add('Yarn')
            buildTools.add('Yarn')
        } else {
            pkgManagers.add('npm')
            buildTools.add('npm')
        }
    }

    const buildOnly = ['Maven', 'Gradle', 'SBT', 'DotNet', 'Make', 'Bazel']
    const tools = [
        'Maven', 'Gradle', 'Pip', 'Poetry', 'Setuptools', 'GoModules',
        'CargoCrate', 'Bundler', 'DotNet', 'Make', 'Bazel', 'SBT', 'Mix', 'Composer',
    ]
    for (const t of tools) {
        if (manifestLabels.has(t)) {
            buildTools.add(t)
            // package manager equivalence
            if (buildOnly.includes(t)) pkgManagers.add(t)
            else pkgManagers.add(t)
        }
    }

    // Container & IaC
    const hasDockerfile = manifestLabels.has('Docker') || manifestLabels.has('DockerCompose')
    const pathOnlyLabels = new Set((raw.path_only_hits || []).map((h) => h.label))
    const hasHelm = pathOnlyLabels.has('Helm')

    const iacLabels = [
        'Terraform', 'OpenTofu', 'Pulumi', 'Helm', 'Kustomize',
        'CloudFormation', 'Bicep', 'ARM', 'Ansible', 'Chef', 'Puppet',
    ]
    const iac = iacLabels.filter((l) => pathOnlyLabels.has(l))

    // CI platforms from pipeline_files
    const ciPlatforms = Array.from(
        new Set((raw.pipeline_files || []).map((p) => p.platform).filter(Boolean))
    )

    // Deploy targets — scan pipeline file contents
    const deployTargets = scanDeployTargets(raw, shardDir)

    // Path-only deploy-target hints (e.g. serverless.yml → AWS-Lambda)
    const pathDeploy = ['AWS-Lambda', 'AWS-Beanstalk', 'AWS-ECS', 'GCP-AppEngine']
    for (const d of pathDeploy) {
        if (pathOnlyLabels.has(d)) deployTargets.add(d)
    }

    const totalLoc = (raw.pipeline_files || []).reduce(
        (acc, p) => acc + (p.loc || 0),
        0
    )

    return {
        org: raw.owner || '',
        repo: raw.repo || '',
        default_branch: raw.default_branch || '',
        primary_language: primary,
        secondary_languages: secondary.join(';'),
        build_tools: Array.from(buildTools).join(';'),
        package_managers: Array.from(pkgManagers).join(';'),
        ci_platforms: ciPlatforms.join(';'),
        deploy_targets: Array.from(deployTargets).join(';'),
        container: String(hasDockerfile),
        iac: iac.join(';'),
        has_dockerfile: String(hasDockerfile),
        has_helm: String(hasHelm),
        pipeline_file_count: String((raw.pipeline_files || []).length),
        total_loc_pipeline: String(totalLoc),
        signals_json: JSON.stringify({
            pipeline_files: raw.pipeline_files || [],
            manifest_files: raw.manifest_files || [],
            path_only_hits: raw.path_only_hits || [],
            languages: raw.languages || {},
            truncated: !!raw.truncated,
            errors: raw.errors || [],
        }),
    }
}

// Deploy-target content scanning cues. Labels match the canonical taxonomy in
// plugin/skills/inventory-analysis/SKILL.md.
const DEPLOY_TARGET_CUES = [
    { label: 'AWS-S3', re: /\baws\s+s3\b/i },
    { label: 'AWS-Lambda', re: /\baws\s+lambda\b|aws-actions\/aws-lambda/i },
    { label: 'AWS-ECS', re: /\baws\s+ecs\b|aws-actions\/amazon-ecs-deploy/i },
    { label: 'AWS-EKS', re: /\baws\s+eks\b/i },
    { label: 'AWS-CloudFront', re: /\baws\s+cloudfront\b/i },
    { label: 'AWS-Beanstalk', re: /\beb\s+deploy\b|elasticbeanstalk/i },
    { label: 'Azure-WebApp', re: /azure\/webapps-deploy|az\s+webapp\b/i },
    { label: 'Azure-Functions', re: /azure\/functions-action|func\s+azure\b/i },
    { label: 'Azure-AKS', re: /azure\/aks-set-context|az\s+aks\b/i },
    { label: 'Azure-StaticWebApps', re: /Azure\/static-web-apps-deploy/i },
    { label: 'Azure-ContainerApps', re: /az\s+containerapp\b/i },
    { label: 'GCP-CloudRun', re: /gcloud\s+run\s+deploy|google-github-actions\/deploy-cloudrun/i },
    { label: 'GCP-GKE', re: /gcloud\s+container\s+clusters\s+get-credentials/i },
    { label: 'GCP-AppEngine', re: /gcloud\s+app\s+deploy/i },
    { label: 'GCP-CloudFunctions', re: /gcloud\s+functions\s+deploy/i },
    { label: 'Kubernetes', re: /\bkubectl\s+apply\b|\bhelm\s+upgrade\b/i },
    { label: 'Heroku', re: /heroku\/deploy|git\s+push\s+heroku/i },
    { label: 'Netlify', re: /netlify\s+deploy|nwtgck\/actions-netlify/i },
    { label: 'Vercel', re: /vercel\s+deploy|amondnet\/vercel-action/i },
    { label: 'GitHubPages', re: /actions\/deploy-pages|peaceiris\/actions-gh-pages/i },
    { label: 'Cloudflare-Pages', re: /cloudflare\/pages-action/i },
    { label: 'Cloudflare-Workers', re: /wrangler\s+(deploy|publish)/i },
    { label: 'GHCR', re: /ghcr\.io\//i },
    { label: 'ECR', re: /\.dkr\.ecr\.[^/]+\.amazonaws\.com\//i },
    { label: 'GCR', re: /(^|[^a-z])gcr\.io\/|pkg\.dev\//i },
    { label: 'ACR', re: /\.azurecr\.io\//i },
    { label: 'DockerHub', re: /docker\.io\/|hub\.docker\.com/i },
    { label: 'NPMRegistry', re: /\bnpm\s+publish\b|JS-DevTools\/npm-publish/i },
    { label: 'MavenCentral', re: /\bmvn\s+deploy\b|sonatype/i },
    { label: 'PyPI', re: /\btwine\s+upload\b|pypa\/gh-action-pypi-publish/i },
    { label: 'NuGet', re: /\bnuget\s+push\b|dotnet\s+nuget\s+push/i },
    { label: 'RubyGems', re: /\bgem\s+push\b/i },
]

function scanDeployTargets(raw, shardDir) {
    const hits = new Set()
    const fs = require('fs')
    const path = require('path')
    for (const pf of raw.pipeline_files || []) {
        const filePath = path.join(shardDir, 'pipelines', raw.owner, raw.repo, pf.path)
        let content
        try {
            content = fs.readFileSync(filePath, 'utf8')
        } catch {
            continue
        }
        for (const cue of DEPLOY_TARGET_CUES) {
            if (cue.re.test(content)) hits.add(cue.label)
        }
    }
    return hits
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
