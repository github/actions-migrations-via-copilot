#!/usr/bin/env python3
"""patch_ahpx.py <ahpx dist/bin.js>

Adapts AHPX 0.6.0 for editor-path plugin tests: serve explicitly offered plugin files,
wait for discovery, select discovered agents, and retain evidence before disposal.
The isolated-rule probe also records a hash-only result for its one resource read.
CLI-installed plugins alone miss editor-loader bugs. Fails if the pinned client changes.
"""
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
anchor = "async function discoverCustomizations(cwd) {\n  const refs = [];\n"
addition = """  for (const dir of (process.env.HC_PLUGIN_DIRS || "").split(path4.delimiter).filter(Boolean)) {
        const abs = hcRealpathSync(dir);
        refs.push({ uri: hcPathToFileURL(abs).href, displayName: "Plugin: " + path4.basename(abs),
      nonce: createHash("sha256").update(abs).digest("hex") });
  }
"""
imports = """import { readdirSync as hcReaddirSync, realpathSync as hcRealpathSync } from "node:fs";
import { appendFile as hcAppendFile, cp as hcCopy, mkdir as hcMkdir } from "node:fs/promises";
import { pathToFileURL as hcPathToFileURL } from "node:url";
"""
allow_anchor = """        this.allowedPaths.add(filePath);
"""
allow_addition = """        const pluginRoots = (process.env.HC_PLUGIN_DIRS || "").split(nodePath.delimiter)
                    .filter(Boolean).map((dir) => hcRealpathSync(dir));
                if (pluginRoots.includes(filePath)) {
                    const offerDirectory = (directory) => {
                        for (const entry of hcReaddirSync(directory, { withFileTypes: true })) {
                            if (entry.isSymbolicLink()) continue;
                            const child = nodePath.join(directory, entry.name);
                            this.allowedPaths.add(child);
                            if (entry.isDirectory()) offerDirectory(child);
                        }
                    };
                    offerDirectory(filePath);
                }
"""
resolve_anchor = '    switch (method) {\n      case "resourceRead": {'
resolve_replacement = '''    switch (method) {
      case "resourceResolve": {
        const filePath = resolveAndValidatePath(params.uri, this.allowedPaths);
        const stat = await fs2.lstat(filePath);
        if (stat.isSymbolicLink()) throw new Error("Symlinks are not offered");
        return { uri: params.uri, type: stat.isDirectory() ? "directory" : "file",
          size: stat.size, mtime: stat.mtime.toISOString(), ctime: stat.ctime.toISOString() };
      }
      case "resourceRead": {'''
dispose_anchor = '            await client.disposeSession(sessionUri);'
dispose_replacement = '''            if (process.env.HC_EVIDENCE_DIR) {
                            const worktrees = path4.resolve(cwd) + ".worktrees";
                            const candidates = hcReaddirSync(worktrees, { withFileTypes: true })
                                .filter((entry) => entry.isDirectory());
                            if (candidates.length !== 1) throw new Error("Expected exactly one test worktree");
                            const source = path4.join(worktrees, candidates[0].name);
                            await hcMkdir(process.env.HC_EVIDENCE_DIR, { recursive: true });
                            for (const name of ["hc-out", ".hook-conformance", "hook-results.md"]) {
                                try {
                                    await hcCopy(path4.join(source, name), path4.join(process.env.HC_EVIDENCE_DIR, name),
                                        { recursive: true, dereference: false });
                                } catch (error) {
                                    if (error.code !== "ENOENT") throw error;
                                }
                            }
                        }
                        await client.disposeSession(sessionUri);'''
selection_anchor = '      const chatUri = await resolveChatChannel(client, sessionUri);'
selection_addition = '''      if (process.env.HC_PLUGIN_DIRS) {
                const offered = activeClientParam?.customizations || [];
                await new Promise((resolve, reject) => {
                    let timer;
                    const finish = (error) => {
                        clearTimeout(timer);
                        client.removeListener("action", check);
                        if (error) reject(error); else resolve();
                    };
                    const check = () => {
                        const current = client.state.getSession(sessionUri)?.customizations || [];
                        const plugins = offered.map((item) => current.find((candidate) => candidate.uri === item.uri));
                        if (plugins.some((item) => item?.load?.kind === "error" || item?.load?.kind === "degraded")) {
                            finish(new Error("A test plugin failed to load"));
                        } else if (plugins.length > 0 && plugins.every((item) => item && item.load?.kind !== "loading" && Array.isArray(item.children))) {
                            console.error("Ready plugin components: " + JSON.stringify(plugins.map((item) => ({
                                name: item.name, load: item.load, children: item.children.map((child) => ({type: child.type, name: child.name}))
                            }))));
                            finish();
                        }
                    };
                    timer = setTimeout(() => finish(new Error("Plugin discovery did not become ready")), 30000);
                    client.on("action", check);
                    check();
                });
            }
            if (process.env.HC_AGENT_NAME) {
                const flatten = (items) => items.flatMap((item) => [item, ...flatten(item.children || [])]);
                const matches = flatten(client.state.getSession(sessionUri)?.customizations || [])
                    .filter((item) => item.type === "agent" && item.name === process.env.HC_AGENT_NAME);
                if (matches.length !== 1) throw new Error("Requested plugin agent was not uniquely discovered: " + process.env.HC_AGENT_NAME);
                process.env.HC_SELECTED_AGENT_URI = matches[0].uri;
                console.error("Selected discovered agent: " + matches[0].name);
            }
'''
message_anchor = '          ...this.model ? { model: { id: this.model } } : {},'
message_addition = '\n          ...process.env.HC_SELECTED_AGENT_URI ? { agent: { uri: process.env.HC_SELECTED_AGENT_URI } } : {},'
resource_anchor = '''      const content = await fs2.readFile(filePath);
      return {
        data: content.toString("base64"),
'''
resource_replacement = '''      const content = await fs2.readFile(filePath);
      if (process.env.HC_EVIDENCE_DIR && process.env.HC_RULE_RESOURCE_PATH &&
          filePath === process.env.HC_RULE_RESOURCE_PATH) {
        const digest = createHash("sha256").update(content).digest("hex");
        await hcMkdir(process.env.HC_EVIDENCE_DIR, { recursive: true });
        await hcAppendFile(path4.join(process.env.HC_EVIDENCE_DIR, "rule-resource.jsonl"),
          JSON.stringify({ resource_read: true, sha256: digest,
            matches_expected: digest === process.env.HC_RULE_RESOURCE_SHA256 }) + "\\n", { mode: 0o600 });
      }
      return {
        data: content.toString("base64"),
'''
if addition in text:
    if "process.env.HC_RULE_RESOURCE_PATH" in text:
        sys.exit(0)
    old_import = 'import { cp as hcCopy, mkdir as hcMkdir } from "node:fs/promises";'
    new_import = 'import { appendFile as hcAppendFile, cp as hcCopy, mkdir as hcMkdir } from "node:fs/promises";'
    if text.count(resource_anchor) != 1:
        sys.exit(f"AHPX at {path} changed; update tests/surfaces/patch_ahpx.py")
    if new_import not in text:
        if text.count(old_import) != 1:
            sys.exit(f"AHPX at {path} changed; update tests/surfaces/patch_ahpx.py")
        text = text.replace(old_import, new_import)
    path.write_text(text.replace(resource_anchor, resource_replacement))
    sys.exit(0)

if any(text.count(part) != 1 for part in (anchor, allow_anchor, resolve_anchor, dispose_anchor, selection_anchor,
                                           message_anchor, resource_anchor)) or "createHash" not in text or "path4." not in text:
    sys.exit(f"AHPX at {path} changed; update tests/surfaces/patch_ahpx.py")
text = text.replace(anchor, anchor + addition).replace(allow_anchor, allow_anchor + allow_addition)
text = text.replace(resolve_anchor, resolve_replacement)
text = text.replace(resource_anchor, resource_replacement)
text = text.replace(dispose_anchor, dispose_replacement)
text = text.replace(selection_anchor, selection_addition + selection_anchor)
text = text.replace(message_anchor, message_anchor + message_addition)
lines = text.splitlines(keepends=True)
lines.insert(1 if text.startswith("#!") else 0, imports)
path.write_text("".join(lines))
