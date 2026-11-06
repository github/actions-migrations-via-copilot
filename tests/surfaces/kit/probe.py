#!/usr/bin/env python3
"""Hook conformance probe. Every hook entry runs this with a label.

It logs every call before acting, never filters on cwd, and builds marker
strings at runtime so the hook files never contain them.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / ".hook-conformance" / "probe.jsonl"
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


def marker(n):
    return "HC_" + "M" + n


present = [n for n in ("1", "2", "3", "5", "8", "9") if marker(n) in raw]
if "hc-does-not-exist" in raw:
    present.append("rm")
tool = payload.get("toolName") or payload.get("tool_name") or ""
# Act on file-writing tools and shell commands that point at hc-out/. The results
# file and the agent's own commit/scan/validation tools are never touched.
SHELL_TOOLS = {"bash", "run_in_terminal"}
targets_out = (tool in WRITE_TOOLS or tool in SHELL_TOOLS) and OUT in raw and "hook-results.md" not in raw

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
    "event": payload.get("hook_event_name") or EVENTS.get(label, label),
    "session": payload.get("sessionId") or payload.get("session_id") or "",
    "tool": tool,
    "payload_keys": sorted(payload),
    "markers": present,
    "action": action,
}
LOG.parent.mkdir(parents=True, exist_ok=True)
with LOG.open("a") as f:
    f.write(json.dumps(record) + "\n")
print(f"HC_PROBE {label} tool={tool or '-'} action={action}", file=sys.stderr)
if output:
    print(output)
sys.exit(code)
