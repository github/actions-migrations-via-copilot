import * as hcPolicyFs from "node:fs";
import * as hcPolicyPath from "node:path";

export function hcApproveFixtureTool(toolCall, workspace) {
  if (!workspace) return false;
  let input;
  try {
    input = typeof toolCall.toolInput === "string" ? JSON.parse(toolCall.toolInput) : toolCall.toolInput;
  } catch {
    return false;
  }
  if (!input || typeof input !== "object" || Array.isArray(input)) return false;
  const tool = toolCall.toolName;
  if (tool === "skill") {
    return ["hc-probe-skill", "hc-probe-ns-skill", "hc-probe-a:hc-probe-skill", "hc-probe-ns:hc-probe-ns-skill"]
      .includes(input.skill ?? input.name);
  }
  let root;
  try {
    root = hcPolicyFs.realpathSync(workspace);
  } catch {
    return false;
  }
  const requested = input.path ?? input.cwd ?? ".";
  if (typeof requested !== "string") return false;
  let target = hcPolicyPath.resolve(root, requested);
  const suppliedRoot = hcPolicyPath.resolve(workspace);
  if (target === suppliedRoot || target.startsWith(suppliedRoot + hcPolicyPath.sep) ||
      target.startsWith(suppliedRoot + ".worktrees" + hcPolicyPath.sep)) {
    target = root + target.slice(suppliedRoot.length);
  }
  let relative = hcPolicyPath.relative(root, target);
  if (relative === ".." || relative.startsWith(`..${hcPolicyPath.sep}`)) {
    const worktrees = root + ".worktrees";
    const nested = hcPolicyPath.relative(worktrees, target).split(hcPolicyPath.sep);
    if (nested[0] === ".." || !nested[0]) return false;
    root = hcPolicyPath.join(worktrees, nested.shift());
    relative = nested.join(hcPolicyPath.sep);
  }
  const components = hcPolicyPath.resolve(target).split(hcPolicyPath.sep);
  let current = hcPolicyPath.parse(target).root;
  for (const component of components.filter(Boolean)) {
    current = hcPolicyPath.join(current, component);
    try {
      if (hcPolicyFs.lstatSync(current).isSymbolicLink()) return false;
    } catch (error) {
      if (error.code !== "ENOENT") return false;
    }
  }
  if (tool === "bash") {
    return !input.env && (!input.cwd || !relative) &&
      ["echo hook-conformance-bash", "rm hc-does-not-exist.txt"].includes(input.command);
  }
  if (["create", "edit"].includes(tool)) {
    return relative === "hook-results.md" || relative.startsWith(`hc-out${hcPolicyPath.sep}`);
  }
  if (["view", "grep", "glob"].includes(tool)) {
    if (input.pattern && (hcPolicyPath.isAbsolute(input.pattern) || input.pattern.split(/[\\/]/).includes(".."))) return false;
    return !relative || relative === "README.md" || relative === "hook-results.md" ||
      relative === "hc-out" || relative.startsWith(`hc-out${hcPolicyPath.sep}`);
  }
  return false;
}