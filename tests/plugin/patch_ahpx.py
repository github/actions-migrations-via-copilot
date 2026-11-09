#!/usr/bin/env python3
"""patch_ahpx.py <ahpx dist/bin.js>

Adapts the pinned AHPX 0.6.0 client so the VS Code Agent Host loads the real plugin the way the
VS Code editor does (as an offered plugin directory), not through a Copilot CLI install. It also:
waits until the plugin is loaded, selects one discovered plugin agent, approves only the smoke-test
tool calls (approve_tool.mjs), and copies the session worktree's evidence before it is deleted.
Exits non-zero if the pinned client changed, so an upgrade can't silently skip a patch.
"""
import sys
from pathlib import Path

MARKER = "hcApproveTool"

IMPORTS = """import { readdirSync as hcReaddirSync, realpathSync as hcRealpathSync, writeFileSync as hcWriteFileSync } from "node:fs";
import { cp as hcCopy, mkdir as hcMkdir } from "node:fs/promises";
import { pathToFileURL as hcPathToFileURL } from "node:url";
"""

PATCHES = [
    # Offer the plugin directory as a customization, the way the editor does.
    ("async function discoverCustomizations(cwd) {\n  const refs = [];\n", """
  for (const dir of (process.env.HC_PLUGIN_DIRS || "").split(path4.delimiter).filter(Boolean)) {
    const abs = hcRealpathSync(dir);
    refs.push({ uri: hcPathToFileURL(abs).href, displayName: "Plugin: " + path4.basename(abs),
      nonce: createHash("sha256").update(abs).digest("hex") });
  }
""", "after"),
    # Let the host read the offered plugin's files (and nothing else new). Symlinks are skipped.
    ("        this.allowedPaths.add(filePath);\n", """        const pluginRoots = (process.env.HC_PLUGIN_DIRS || "").split(nodePath.delimiter)
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
""", "after"),
    # The host asks for file metadata before reading; AHPX 0.6.0 doesn't implement it.
    ('    switch (method) {\n      case "resourceRead": {', '''    switch (method) {
      case "resourceResolve": {
        const filePath = resolveAndValidatePath(params.uri, this.allowedPaths);
        const stat = await fs2.lstat(filePath);
        if (stat.isSymbolicLink()) throw new Error("Symlinks are not offered");
        return { uri: params.uri, type: stat.isDirectory() ? "directory" : "file",
          size: stat.size, mtime: stat.mtime.toISOString(), ctime: stat.ctime.toISOString() };
      }
      case "resourceRead": {''', "replace"),
    # Copy test outputs out of the session worktree before the session (and worktree) is disposed.
    ("            await client.disposeSession(sessionUri);", """            if (process.env.HC_EVIDENCE_DIR) {
                            const worktrees = path4.resolve(cwd) + ".worktrees";
                            const candidates = hcReaddirSync(worktrees, { withFileTypes: true })
                                .filter((entry) => entry.isDirectory());
                            if (candidates.length !== 1) throw new Error("Expected exactly one test worktree");
                            const source = path4.join(worktrees, candidates[0].name);
                            await hcMkdir(process.env.HC_EVIDENCE_DIR, { recursive: true });
                            for (const name of ["hc-out", ".github"]) {
                                try {
                                    await hcCopy(path4.join(source, name), path4.join(process.env.HC_EVIDENCE_DIR, name),
                                        { recursive: true, dereference: false });
                                } catch (error) {
                                    if (error.code !== "ENOENT") throw error;
                                }
                            }
                        }
                        await client.disposeSession(sessionUri);""", "replace"),
    # Wait for the plugin to load, record what the host discovered, and select the requested agent.
    ("      const chatUri = await resolveChatChannel(client, sessionUri);", """      if (process.env.HC_PLUGIN_DIRS) {
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
                            finish(new Error("The plugin failed to load"));
                        } else if (plugins.length > 0 && plugins.every((item) => item && item.load?.kind !== "loading" && Array.isArray(item.children))) {
                            if (process.env.HC_EVIDENCE_DIR) {
                                hcWriteFileSync(path4.join(process.env.HC_EVIDENCE_DIR, "plugin-ready.json"), JSON.stringify(
                                    plugins.map((item) => ({ name: item.name,
                                        children: item.children.map((child) => ({ type: child.type, name: child.name })) }))),
                                    { mode: 0o600 });
                            }
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
                if (matches.length !== 1) throw new Error("Plugin agent was not uniquely discovered: " + process.env.HC_AGENT_NAME);
                process.env.HC_SELECTED_AGENT_URI = matches[0].uri;
                if (process.env.HC_EVIDENCE_DIR) {
                    hcWriteFileSync(path4.join(process.env.HC_EVIDENCE_DIR, "agent-selected.json"),
                        JSON.stringify({ name: matches[0].name }), { mode: 0o600 });
                }
            }
      const chatUri = await resolveChatChannel(client, sessionUri);""", "replace"),
    ("          ...this.model ? { model: { id: this.model } } : {},",
     "\n          ...process.env.HC_SELECTED_AGENT_URI ? { agent: { uri: process.env.HC_SELECTED_AGENT_URI } } : {},",
     "after"),
    # Replace the --deny-all answer with the narrow smoke-test approvals.
    ("  async handleToolConfirmation(toolCall) {\n", """    if (process.env.HC_WORKSPACE) {
      const approved = hcApproveTool(toolCall, process.env.HC_WORKSPACE);
      this.output.write((approved ? "[approved " : "[denied ") + toolCall.toolName + "]\\n");
      return approved;
    }
""", "after"),
]


def patch(text, approval_source):
    if MARKER in text:
        sys.exit("AHPX is already patched; reinstall it with npm ci")
    if "createHash" not in text or "path4." not in text:
        sys.exit("AHPX changed; update tests/plugin/patch_ahpx.py")
    for anchor, change, mode in PATCHES:
        if text.count(anchor) != 1:
            sys.exit(f"AHPX changed; anchor not found once: {anchor.strip()[:60]}")
        text = text.replace(anchor, anchor + change if mode == "after" else change)
    lines = text.splitlines(keepends=True)
    lines.insert(1 if text.startswith("#!") else 0, IMPORTS + approval_source + "\n")
    return "".join(lines)


if __name__ == "__main__":
    target = Path(sys.argv[1])
    approval = (Path(__file__).parent / "approve_tool.mjs").read_text()
    target.write_text(patch(target.read_text(), approval))
