import * as hcPolicyFs from "node:fs";
import * as hcPolicyPath from "node:path";

// Approves only the tool calls the smoke-test prompts ask for. Everything else stays denied.
// The plugin's own hooks still run on approved calls; this only replaces the human approval.
export function hcApproveTool(toolCall, workspace) {
  if (!workspace) return false;
  const tool = toolCall.toolName;
  let input;
  try {
    input = typeof toolCall.toolInput === "string" ? JSON.parse(toolCall.toolInput) : toolCall.toolInput;
  } catch {
    // Older Agent Hosts send a shell call's input as the bare command line.
    if (tool !== "bash") return false;
    input = { command: toolCall.toolInput };
  }
  if (!input || typeof input !== "object" || Array.isArray(input)) return false;
  if (tool === "skill") return ["actionlint", "actions-migrator:actionlint"].includes(input.skill ?? input.name);

  let root;
  try {
    root = hcPolicyFs.realpathSync(workspace);
  } catch {
    return false;
  }
  const requested = input.path ?? input.cwd ?? ".";
  if (typeof requested !== "string") return false;
  // Agent Host sessions run in a git worktree next to the workspace: <workspace>.worktrees/<name>.
  let target = hcPolicyPath.resolve(root, requested);
  const suppliedRoot = hcPolicyPath.resolve(workspace);
  if (target === suppliedRoot || target.startsWith(suppliedRoot + hcPolicyPath.sep) ||
      target.startsWith(suppliedRoot + ".worktrees" + hcPolicyPath.sep)) {
    target = root + target.slice(suppliedRoot.length);
  }
  let relative = hcPolicyPath.relative(root, target);
  if (relative === ".." || relative.startsWith(`..${hcPolicyPath.sep}`)) {
    const nested = hcPolicyPath.relative(root + ".worktrees", target).split(hcPolicyPath.sep);
    if (nested[0] === ".." || !nested[0]) return false;
    root = hcPolicyPath.join(root + ".worktrees", nested.shift());
    relative = nested.join(hcPolicyPath.sep);
  }
  let current = hcPolicyPath.parse(target).root;
  for (const component of target.split(hcPolicyPath.sep).filter(Boolean)) {
    current = hcPolicyPath.join(current, component);
    try {
      if (hcPolicyFs.lstatSync(current).isSymbolicLink()) return false;
    } catch (error) {
      if (error.code !== "ENOENT") return false;
    }
  }
  const parts = relative.split(hcPolicyPath.sep);
  if (tool === "bash") return !input.env && !relative && input.command === "rm hc-out/keep.txt";
  if (tool === "create") return ["hc-out/safe.txt", "hc-out/p1.md", "hc-out/agent.txt"].includes(parts.join("/"));
  if (tool === "view") return relative === "README.md";
  return false;
}
