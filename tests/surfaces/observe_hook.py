"""Record an unchanged hook command's result while forwarding its output and status."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys


raw = sys.stdin.read()
command = base64.b64decode(sys.argv[1]).decode()
result = subprocess.run(["bash", "-c", command], input=raw, text=True, capture_output=True)
try:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        payload = {}
    tool = payload.get("toolName") or payload.get("tool_name") or ""
    arguments = payload.get("toolArgs", payload.get("tool_input", {}))
    targets = set()
    if isinstance(arguments, dict):
        for key in ("path", "file", "filePath", "file_path", "uri"):
            value = arguments.get(key)
            if isinstance(value, str) and value.replace("\\", "/").endswith("hc-out/p1.md"):
                targets.add("hc-out/p1.md")
        for key in ("command", "cmd"):
            value = arguments.get(key)
            if isinstance(value, str) and "hc-does-not-exist" in value:
                targets.add("hc-does-not-exist")
    elif tool in {"bash", "run_in_terminal"} and isinstance(arguments, str):
        if "hc-does-not-exist" in arguments:
            targets.add("hc-does-not-exist")
    directory = payload.get("cwd") or payload.get("workingDirectory") or str(Path.cwd())
    root = Path(directory)
    root = next((path for path in [root, *root.parents] if (path / ".git").exists()), root)
    output = root / ".hook-conformance/plugin-guards.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    decision = None
    try:
        response = json.loads(result.stdout)
        if response.get("permissionDecision") in {"allow", "deny"}:
            decision = {"permissionDecision": response["permissionDecision"]}
            reason = response.get("permissionDecisionReason", "")
            if reason.startswith("Blocked: likely credential value in proposed output."):
                decision["permissionDecisionReason"] = "likely credential value in proposed output"
            elif (reason.startswith("Blocked: deletion outside .github/ci-archive/ is not allowed (")
                  and reason.endswith(").") and "hc-does-not-exist" in targets):
                decision["permissionDecisionReason"] = "deletion outside .github/ci-archive/ is not allowed"
    except (ValueError, AttributeError):
        pass
    record = {
        "event": sys.argv[2],
        "index": int(sys.argv[3]),
        "tool": tool,
        "targets": sorted(targets),
        "call": hashlib.sha256(json.dumps([
            payload.get("sessionId", payload.get("session_id", "")), tool, arguments
        ], sort_keys=True).encode()).hexdigest(),
        "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
        "decision": decision,
        "exit_code": result.returncode,
    }
    with output.open("a") as stream:
        stream.write(json.dumps(record) + "\n")
except (OSError, ValueError, TypeError, AttributeError) as error:
    print(f"Hook evidence unavailable: {type(error).__name__}", file=sys.stderr)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)