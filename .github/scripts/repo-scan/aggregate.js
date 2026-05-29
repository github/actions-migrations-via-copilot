/**
 * Repo Scan — Stage 1, aggregator: combine all per-shard outputs into a single
 * `inventory/<run-id>/` snapshot, write manifest.json, update `inventory/latest`,
 * and apply snapshot retention.
 *
 * Reads:   shards/repo-scan-shard-XYZ/  (one directory per matrix entry, downloaded
 *          from the repo-scan-shard-KEY artifacts).
 *
 * Writes:
 *   inventory/<run-id>/repos.csv          (concatenated; header from first shard)
 *   inventory/<run-id>/dependencies.csv   (concatenated; header from first shard)
 *   inventory/<run-id>/pipelines/...      (merged from all shards)
 *   inventory/<run-id>/manifests/...
 *   inventory/<run-id>/raw/...
 *   inventory/<run-id>/manifest.json
 *   inventory/latest                       (text file containing <run-id>)
 *
 * Retention: keeps the RETENTION most recent inventory/<id>/ directories,
 * sorted numerically descending by directory name. Older ones are removed.
 *
 * @param {{ core: any, process: NodeJS.Process }} ctx
 */
module.exports = async ({ core, process }) => {
    const fs = require('fs')
    const path = require('path')

    const runId = process.env.RUN_ID
    if (!runId) throw new Error('RUN_ID env var is required')
    const retention = Math.max(
        1,
        parseInt(process.env.RETENTION || '12', 10) || 12
    )

    const snapshotDir = path.join('inventory', runId)
    fs.mkdirSync(snapshotDir, { recursive: true })

    const shardsRoot = 'shards'
    if (!fs.existsSync(shardsRoot)) {
        core.warning(`No shards directory found at ${shardsRoot}; aggregating an empty snapshot.`)
    }

    const shardDirs = fs.existsSync(shardsRoot)
        ? fs.readdirSync(shardsRoot).map((d) => path.join(shardsRoot, d))
        : []

    let repoCount = 0
    let pipelineCount = 0
    let reposWithPipelines = 0
    let truncatedCount = 0

    const reposCsvOut = path.join(snapshotDir, 'repos.csv')
    const depsCsvOut = path.join(snapshotDir, 'dependencies.csv')
    let reposHeaderWritten = false
    let depsHeaderWritten = false

    for (const shard of shardDirs) {
        // repos.csv
        const reposCsv = path.join(shard, 'repos.csv')
        if (fs.existsSync(reposCsv)) {
            const lines = fs.readFileSync(reposCsv, 'utf8').split('\n')
            if (lines.length > 0) {
                if (!reposHeaderWritten) {
                    fs.writeFileSync(reposCsvOut, lines[0] + '\n', 'utf8')
                    reposHeaderWritten = true
                }
                for (const line of lines.slice(1)) {
                    if (line.trim() === '') continue
                    fs.appendFileSync(reposCsvOut, line + '\n', 'utf8')
                    repoCount += 1
                }
            }
        }

        // dependencies.csv (optional)
        const depsCsv = path.join(shard, 'dependencies.csv')
        if (fs.existsSync(depsCsv)) {
            const lines = fs.readFileSync(depsCsv, 'utf8').split('\n')
            if (lines.length > 0) {
                if (!depsHeaderWritten) {
                    fs.writeFileSync(depsCsvOut, lines[0] + '\n', 'utf8')
                    depsHeaderWritten = true
                }
                for (const line of lines.slice(1)) {
                    if (line.trim() === '') continue
                    fs.appendFileSync(depsCsvOut, line + '\n', 'utf8')
                }
            }
        }

        // Tree copies (pipelines/, manifests/, raw/)
        for (const sub of ['pipelines', 'manifests', 'raw']) {
            const src = path.join(shard, sub)
            if (fs.existsSync(src)) {
                copyDir(src, path.join(snapshotDir, sub))
            }
        }

        // Count pipelines + truncation from raw/
        const rawDir = path.join(shard, 'raw')
        if (fs.existsSync(rawDir)) {
            for (const f of fs.readdirSync(rawDir)) {
                if (!f.endsWith('.json')) continue
                try {
                    const data = JSON.parse(fs.readFileSync(path.join(rawDir, f), 'utf8'))
                    const count = (data.pipeline_files || []).length
                    pipelineCount += count
                    if (count > 0) reposWithPipelines += 1
                    if (data.truncated) truncatedCount += 1
                } catch (err) {
                    core.warning(`Failed to parse ${f}: ${err.message}`)
                }
            }
        }
    }

    const manifest = {
        run_id: runId,
        started_at: null,
        finished_at: new Date().toISOString(),
        inputs: {
            organizations: safeJson(process.env.ORGS_INPUT, []),
            repositories: safeJson(process.env.REPOS_INPUT, []),
            excludes: safeJson(process.env.EXCLUDES_INPUT, []),
            scan_depth: process.env.SCAN_DEPTH || 'shallow',
            retention,
        },
        counts: {
            repositories_scanned: repoCount,
            pipelines_captured: pipelineCount,
            repositories_with_pipelines: reposWithPipelines,
            repositories_truncated: truncatedCount,
        },
    }
    fs.writeFileSync(
        path.join(snapshotDir, 'manifest.json'),
        JSON.stringify(manifest, null, 2),
        'utf8'
    )

    // Update inventory/latest pointer.
    fs.writeFileSync(path.join('inventory', 'latest'), runId + '\n', 'utf8')

    // Apply retention.
    const allSnapshots = fs
        .readdirSync('inventory', { withFileTypes: true })
        .filter((d) => d.isDirectory())
        .map((d) => d.name)
        .filter((n) => /^\d+$/.test(n))
        .sort((a, b) => Number(b) - Number(a))
    const toDelete = allSnapshots.slice(retention)
    for (const old of toDelete) {
        const oldPath = path.join('inventory', old)
        core.info(`Retention: removing ${oldPath}`)
        fs.rmSync(oldPath, { recursive: true, force: true })
    }

    core.info(
        `Snapshot ${runId} aggregated: ${repoCount} repos, ${pipelineCount} pipelines (${truncatedCount} truncated).`
    )
}

function copyDir(src, dst) {
    const fs = require('fs')
    const path = require('path')
    fs.mkdirSync(dst, { recursive: true })
    for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
        const s = path.join(src, entry.name)
        const d = path.join(dst, entry.name)
        if (entry.isDirectory()) copyDir(s, d)
        else fs.copyFileSync(s, d)
    }
}

function safeJson(raw, fallback) {
    if (!raw) return fallback
    try {
        return JSON.parse(raw)
    } catch {
        return fallback
    }
}
