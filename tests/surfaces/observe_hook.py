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
    directory = payload.get("cwd") or payload.get("workingDirectory") or str(Path.cwd())
    root = Path(directory)
    root = next((path for path in [root, *root.parents] if (path / ".git").exists()), root)
    output = root / ".hook-conformance/plugin-guards.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    record = {"event": sys.argv[2], "index": int(sys.argv[3]), "raw": payload,
              "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
              "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
    with output.open("a") as stream:
        stream.write(json.dumps(record) + "\n")
except (OSError, ValueError, TypeError, AttributeError) as error:
    print(f"Hook evidence unavailable: {type(error).__name__}", file=sys.stderr)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)