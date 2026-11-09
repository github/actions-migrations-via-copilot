#!/usr/bin/env python3
"""Hook conformance probe. Every hook entry runs this with a label.

It logs every call before acting, never filters on cwd, and builds marker
strings at runtime so the hook files never contain them.
"""
import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

OUT = "hc-out/"
WRITE_TOOLS = {
    "create", "edit", "apply_patch", "write", "str_replace_editor", "create_file",
    "replace_string_in_file", "insert_edit_into_file",
    "github-mcp-server-create_or_update_file", "github-mcp-server-push_files",
}

label = sys.argv[1] if len(sys.argv) > 1 else ""
raw = sys.stdin.read()
try:
    payload = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    payload = {}
if not isinstance(payload, dict):
    payload = {}


def git_root(path):
    return next((d for d in [path, *path.parents] if (d / ".git").exists()), None)


# Log in the project the agent works in. Plugin hooks run from the plugin's folder, so use the
# payload's working directory first; fall back to this file's repo, then $HC_FALLBACK_LOG.
root, root_from = None, "none"
for key in ("cwd", "workingDirectory"):
    if isinstance(payload.get(key), str) and payload[key]:
        root, root_from = git_root(Path(payload[key])), key
        break
if root is None and "__file__" in globals():
    root, root_from = git_root(Path(__file__).resolve().parent), "file"
LOG = root / ".hook-conformance" / "probe.jsonl" if root else None
if LOG is None and os.environ.get("HC_FALLBACK_LOG"):
    LOG, root_from = Path(os.environ["HC_FALLBACK_LOG"]), "fallback"


def marker(n):
    return "HC_" + "M" + n


def safe_targets(arguments, tool):
    targets = set()
    if isinstance(arguments, dict):
        for key in ("path", "file", "filePath", "file_path", "uri"):
            value = arguments.get(key)
            if isinstance(value, str):
                normalized = value.replace("\\", "/")
                for target in ("hc-out/p1.md", "hc-out/n2-root-hook.txt", "hc-out/r3-rule-challenge.txt"):
                    if normalized == target or normalized.endswith("/" + target):
                        targets.add(target)
        for key in ("command", "cmd"):
            value = arguments.get(key)
            if isinstance(value, str) and "hc-does-not-exist" in value:
                targets.add("hc-does-not-exist")
    elif tool in {"bash", "run_in_terminal"} and isinstance(arguments, str):
        if "hc-does-not-exist" in arguments:
            targets.add("hc-does-not-exist")
    return sorted(targets)


tool = payload.get("toolName") or payload.get("tool_name") or ""
arguments = payload.get("toolArgs", payload.get("tool_input", {}))
argument_text = json.dumps(arguments, sort_keys=True)
# Act on file-writing tools and shell commands that point at hc-out/. The results
# file and the agent's own commit/scan/validation tools are never touched.
SHELL_TOOLS = {"bash", "run_in_terminal"}
targets_out = (tool in WRITE_TOOLS or tool in SHELL_TOOLS) and OUT in argument_text and "hook-results.md" not in argument_text
present = [number for number in ("1", "2", "3", "5", "8", "9") if targets_out and marker(number) in argument_text]
if targets_out and "hc-out/c0.txt" in argument_text:
    present.append("0")
if tool in SHELL_TOOLS and "hc-does-not-exist" in argument_text and "hook-results.md" not in argument_text:
    present.append("rm")

action, output, code = "log-only", "", 0
if targets_out:
    action = "no-op"
    deny = lambda case: json.dumps({
        "permissionDecision": "deny",
        "permissionDecisionReason": f"hook-conformance deny {case}",
    })
    if label == "pre1":
        if "2" in present or "8" in present:
            action, output = "empty-json", "{}"
        elif "3" in present:
            action, code = "exit-2", 2
    elif label == "pre2" and ("1" in present or "2" in present or "9" in present):
        case = "C1" if "1" in present else "C2" if "2" in present else "C8b"
        action, output = f"deny-{case}", deny(case)
    elif label == "pre-b0" and "9" in present:
        action, output = "empty-json", "{}"
    elif label == "pre-b" and "8" in present:
        action, output = "deny-C8", deny("C8")
    elif label == "post1" and "5" in present:
        action, output = "empty-json", "{}"

EVENTS = {
    "pre1": "preToolUse", "pre2": "preToolUse", "pre3-matcher-bash": "preToolUse",
    "pre-b": "preToolUse", "pre-b0": "preToolUse", "post1": "postToolUse", "post2": "postToolUse",
}
record = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "label": label,
    "event": payload.get("hook_event_name") or EVENTS.get(label) or label.split(":")[-1],
    "session": hashlib.sha256(str(payload.get("sessionId", payload.get("session_id", ""))).encode()).hexdigest()[:16],
    "tool": tool,
    "payload_keys": sorted(payload),
    "markers": present,
    "targets": safe_targets(arguments, tool),
    "action": action,
    "log_from": root_from,
    "call": hashlib.sha256(json.dumps([payload.get("sessionId", payload.get("session_id", "")), tool, arguments], sort_keys=True).encode()).hexdigest(),
    "output": output,
    "exit_code": code,
}
logs = {LOG} if LOG is not None else set()
if os.environ.get("HC_FALLBACK_LOG"):
    logs.add(Path(os.environ["HC_FALLBACK_LOG"]))
for log in logs:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        f.write(json.dumps(record) + "\n")
print(f"HC_PROBE {label} tool={tool or '-'} action={action}", file=sys.stderr)
if output:
    print(output)
sys.exit(code)
