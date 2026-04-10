module.exports = async ({ github, core, process }) => {
    const fs = require('fs')
    const crypto = require('crypto')
    const { getOctokit } = require('@actions/github')

    const orgs = JSON.parse(process.env.ORGANIZATIONS)
    const prompts = JSON.parse(process.env.MIGRATION_TYPE_PROMPTS)
    const batchSize = parseInt(process.env.BATCH_SIZE_VAR) || 100
    const appId = process.env.GH_APP_ID
    const appPem = process.env.GH_APP_PEM
    const apiBase = process.env.GITHUB_API_URL || 'https://api.github.com'

    function generateJWT() {
        const now = Math.floor(Date.now() / 1000)
        const header = Buffer.from(JSON.stringify({ alg: 'RS256', typ: 'JWT' })).toString('base64url')
        const payload = Buffer.from(JSON.stringify({
            iat: now - 60,
            exp: now + (10 * 60),
            iss: appId
        })).toString('base64url')
        const signature = crypto.createSign('RSA-SHA256')
            .update(`${header}.${payload}`)
            .sign(appPem, 'base64url')
        return `${header}.${payload}.${signature}`
    }

    async function getInstallationToken(org) {
        const jwt = generateJWT()

        const installRes = await fetch(
            `${apiBase}/orgs/${encodeURIComponent(org)}/installation`,
            {
                headers: {
                    'Authorization': `Bearer ${jwt}`,
                    'Accept': 'application/vnd.github+json',
                    'X-GitHub-Api-Version': '2022-11-28'
                }
            }
        )
        if (!installRes.ok) {
            throw new Error(`Failed to get app installation for ${org}: ${installRes.status} ${installRes.statusText}`)
        }
        const installation = await installRes.json()

        const tokenRes = await fetch(
            `${apiBase}/app/installations/${installation.id}/access_tokens`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${jwt}`,
                    'Accept': 'application/vnd.github+json',
                    'X-GitHub-Api-Version': '2022-11-28'
                }
            }
        )
        if (!tokenRes.ok) {
            throw new Error(`Failed to create installation token for ${org}: ${tokenRes.status} ${tokenRes.statusText}`)
        }
        const tokenData = await tokenRes.json()

        return tokenData.token
    }

    async function withRetry(fn, label, maxRetries = 3) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await fn()
            } catch (err) {
                const status = err.status || err.response?.status
                if ((status === 403 || status === 429) && attempt < maxRetries) {
                    const retryAfter = parseInt(err.response?.headers?.['retry-after'] || '60', 10)
                    core.warning(`Rate limited on ${label} (attempt ${attempt}/${maxRetries}), waiting ${retryAfter}s`)
                    await new Promise(r => setTimeout(r, retryAfter * 1000))
                    continue
                }
                throw err
            }
        }
    }

    const eligible = []
    const skipped = []
    const errors = []
    let totalScanned = 0

    for (const org of orgs) {
        let submitted = 0
        core.info(`Scanning organization: ${org}`)

        let orgGithub
        try {
            const token = await withRetry(
                () => getInstallationToken(org),
                `getInstallationToken(${org})`
            )
            orgGithub = getOctokit(token)
        } catch (err) {
            errors.push({ org, error: `Failed to authenticate: ${err.message}` })
            continue
        }

        let repos
        try {
            repos = await withRetry(
                () => orgGithub.paginate(orgGithub.rest.repos.listForOrg, { org, per_page: 100, type: 'all' }),
                `listForOrg(${org})`
            )
        } catch (err) {
            errors.push({ org, error: err.message })
            continue
        }

        for (const repo of repos) {
            if (repo.archived || repo.fork) continue
            if (repo.name === '.github-private') continue
            totalScanned++

            let migrationType = null
            try {
                const { data: props } = await withRetry(
                    () => orgGithub.request(
                        'GET /repos/{owner}/{repo}/properties/values',
                        { owner: org, repo: repo.name }
                    ),
                    `properties(${org}/${repo.name})`
                )
                const prop = props.find(p => p.property_name === 'GH_MIGRATION_TYPE')
                migrationType = prop?.value
            } catch (err) { }

            if (!migrationType || migrationType === 'None') {
                skipped.push({ repo: `${org}/${repo.name}`, reason: 'No migration type or set to None' })
                continue
            }

            if (!prompts[migrationType]) {
                skipped.push({ repo: `${org}/${repo.name}`, reason: `Unknown migration type: ${migrationType}` })
                continue
            }

            try {
                const { data: search } = await withRetry(
                    () => orgGithub.rest.search.issuesAndPullRequests({
                        q: `repo:${org}/${repo.name} is:open "[Actions Migration]" in:title`
                    }),
                    `search(${org}/${repo.name})`
                )
                if (search.total_count > 0) {
                    skipped.push({ repo: `${org}/${repo.name}`, reason: 'Open migration issue/PR already exists' })
                    continue
                }
            } catch (err) {
                core.warning(`Search failed for ${org}/${repo.name}: ${err.message}`)
            }

            eligible.push({ repo: `${org}/${repo.name}`, migrationType })
            submitted++
            if (submitted >= batchSize) {
                core.info(`Batch size ${batchSize} reached for ${org}`)
                break
            }
        }
    }

    const results = { eligible, skipped, errors, totalScanned, orgs: orgs.length }
    fs.mkdirSync('/tmp/gh-aw/agent', { recursive: true })
    fs.writeFileSync('/tmp/gh-aw/agent/scan-results.json', JSON.stringify(results, null, 2))
    core.info(`Scan complete: ${eligible.length} eligible, ${skipped.length} skipped, ${errors.length} errors out of ${totalScanned} repos`)
}
