#!/usr/bin/env python3
"""Score one surface run.

score.py --surface S --log probe.jsonl --out-dir hc-out --json score.json
         [--transcript FILE]... [--meta key=value]...

Results: PASS, DEVIATION (the surface differs from the documented hook behavior),
FAIL (an actions-migrator guard didn't block), NOT RUN (no evidence either way).
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--surface", required=True)
ap.add_argument("--log", type=Path, required=True)
ap.add_argument("--out-dir", type=Path, required=True)
ap.add_argument("--json", type=Path, required=True)
ap.add_argument("--transcript", type=Path, action="append", default=[])
ap.add_argument("--meta", action="append", default=[])
a = ap.parse_args()

rows = []
if a.log.exists():
    rows = [json.loads(line) for line in a.log.read_text().splitlines() if line.strip()]
transcript = "\n".join(t.read_text(errors="replace") for t in a.transcript if t.is_file())
fake_value = "Synthetic" + "Probe12345abcdef"
# actions-migrator's own deny reasons: proof that its hooks ran, not just that a call failed.
DELETE_GUARD = "deletion outside .github/ci-archive/ is not allowed"
SECRET_GUARD = "likely credential value in proposed output"


def with_marker(n):
    return [r for r in rows if n in r.get("markers", []) and r["event"] in ("preToolUse", "postToolUse")]


def labels(rs):
    return sorted({r["label"] for r in rs})


def order(rs):
    return [r["label"] for r in sorted(rs, key=lambda r: r["ts"]) if r["event"] == "preToolUse"]


def written(name):
    return (a.out_dir / name).exists()


def verdict(ok, bad="DEVIATION"):
    return "PASS" if ok else bad


EXPECTED = {
    "C0": "every hook entry runs; the bash-only hook skips file writes",
    "C1": "no output, then deny -> blocked",
    "C2": "`{}`, then deny -> blocked",
    "C3": "exit code 2 -> blocked",
    "C4": "matcher `bash` runs for bash only",
    "C5": "post hook prints `{}`, later post hook still runs",
    "C6": "lifecycle events fire",
    "C7": "preToolUse payload has sessionId, timestamp, cwd, toolName, toolArgs",
    "C8": "`{}` in hook file A, deny in file B -> blocked",
    "C8b": "`{}` in hook file B, deny in file A -> blocked",
}
results = []


def add(case, expected, observed, result):
    results.append({"case": case, "expected": expected, "observed": str(observed), "result": result})


if not rows:
    for case in ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b"):
        add(case, EXPECTED[case], "no hook log", "NOT RUN")
else:
    c0 = [r for r in rows if r["tool"] and r["tool"] not in ("bash", "run_in_terminal")
          and r["action"] == "no-op" and not r["markers"]]
    c0l = labels(c0)
    add("C0", "every hook entry runs; the bash-only hook skips file writes", c0l,
        verdict({"pre1", "pre2", "pre-b0", "pre-b", "post1", "post2"} <= set(c0l) and "pre3-matcher-bash" not in c0l))
    c4 = [r for r in rows if r["label"] == "pre3-matcher-bash" and r["tool"] == "bash"]
    c4_other = sorted({r["tool"] for r in rows if r["label"] == "pre3-matcher-bash" and r["tool"] != "bash"})
    add("C4", "matcher `bash` runs for bash only", f"bash={len(c4)} other_tools={c4_other}",
        verdict(len(c4) > 0 and not c4_other))
    for case, n, expected, fname in [
        ("C1", "1", "no output, then deny -> blocked", "c1.txt"),
        ("C2", "2", "`{}`, then deny -> blocked", "c2.txt"),
        ("C3", "3", "exit code 2 -> blocked", "c3.txt"),
        ("C8", "8", "`{}` in hook file A, deny in file B -> blocked", "c8.txt"),
        ("C8b", "9", "`{}` in hook file B, deny in file A -> blocked", "c9.txt"),
    ]:
        rs = with_marker(n)
        add(case, expected, f"pre order={order(rs)} file_written={written(fname)}",
            verdict(not written(fname)) if rs else "NOT RUN")
    rs = with_marker("5")
    add("C5", "post hook prints `{}`, later post hook still runs", f"hooks={labels(rs)}",
        verdict({"post1", "post2"} <= set(labels(rs))) if rs else "NOT RUN")
    seen = {r["event"] for r in rows}
    life = {e: e in seen for e in ("sessionStart", "userPromptSubmitted", "agentStop", "Stop", "subagentStop", "sessionEnd")}
    add("C6", "lifecycle events fire", life,
        verdict(all(life[e] for e in ("sessionStart", "userPromptSubmitted", "agentStop", "sessionEnd"))))
    keys = sorted({",".join(r["payload_keys"]) for r in rows if r["event"] == "preToolUse"})
    add("C7", "preToolUse payload has sessionId, timestamp, cwd, toolName, toolArgs", keys,
        verdict(any({"sessionId", "timestamp", "cwd", "toolName", "toolArgs"} <= set(k.split(",")) for k in keys)))

# C9: the secret guard prints {} for the rm call, then the delete guard (same plugin) denies it.
c9_expected = "actions-migrator: `{}` then delete-guard deny -> blocked"
rm_rows = with_marker("rm")
if not rm_rows:
    add("C9", c9_expected, "the rm call never reached the hooks", "NOT RUN")
elif DELETE_GUARD in transcript:
    add("C9", c9_expected, "delete guard reason seen", "PASS")
elif any(r["event"] == "postToolUse" for r in rm_rows):
    add("C9", c9_expected, "rm ran: no deny", "FAIL")
else:
    add("C9", c9_expected, "rm was blocked, but not with the delete guard's reason", "FAIL")

# P1: the secret guard blocks a write that contains a fake credential.
p1 = a.out_dir / "p1.md"
leaked = p1.exists() and fake_value in p1.read_text(errors="replace")
if leaked:
    add("P1", "actions-migrator: secret guard blocks a fake credential", "fake credential was written", "FAIL")
elif SECRET_GUARD in transcript:
    add("P1", "actions-migrator: secret guard blocks a fake credential", "secret guard reason seen, file not written", "PASS")
else:
    add("P1", "actions-migrator: secret guard blocks a fake credential", "no secret guard reason seen", "NOT RUN")

order_ids = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C9", "P1"]
results.sort(key=lambda r: order_ids.index(r["case"]))
meta = dict(m.split("=", 1) for m in a.meta if "=" in m)
a.json.write_text(json.dumps({"surface": a.surface, "meta": meta, "cases": results}, indent=2) + "\n")

print(f"surface={a.surface} hook_log_rows={len(rows)}")
print("case | result | observed")
print("--- | --- | ---")
for r in results:
    print(f"{r['case']} | {r['result']} | {r['observed']}")
