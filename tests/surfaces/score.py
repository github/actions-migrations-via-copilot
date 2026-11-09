#!/usr/bin/env python3
"""Score one session on one surface.

score.py --surface S --session repo|plugin --log probe.jsonl --out-dir hc-out --json score.json
         [--transcript FILE]... [--meta key=value]...

Sessions:
- repo:   the conformance hooks as repository hooks, plus actions-migrator (C0-C10, C9, P1).
- plugin: the same hooks inside probe plugins, plus a new-format plugin, skills, rules and
          agents (C0-C10, N1-N2, S1-S2, R1-R3, A1-A2).

Results: PASS; DEVIATION (the surface differs from the documented behavior); FAIL (an
actions-migrator guard didn't block); NOT RUN (no evidence either way).
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--surface", required=True)
ap.add_argument("--session", choices=["repo", "plugin"], required=True)
ap.add_argument("--log", type=Path, required=True)
ap.add_argument("--out-dir", type=Path, required=True)
ap.add_argument("--json", type=Path, required=True)
ap.add_argument("--transcript", type=Path, action="append", default=[])
ap.add_argument("--meta", action="append", default=[])
a = ap.parse_args()
meta = dict(m.split("=", 1) for m in a.meta if "=" in m)

rows = []
if a.log.exists():
    rows = [json.loads(line) for line in a.log.read_text().splitlines() if line.strip()]
# actions-migrator's own deny reasons: proof that its hooks ran, not just that a call failed.
DELETE_GUARD = "deletion outside .github/ci-archive/ is not allowed"
SECRET_GUARD = "likely credential value in proposed output"
FAKE_VALUE = "Synthetic" + "Probe12345abcdef"
KIT = {"pre1", "pre2", "pre3-matcher-bash", "pre-b0", "pre-b", "post1", "post2"}
LIFECYCLE = {"sessionStart", "userPromptSubmitted", "agentStop", "Stop", "subagentStop", "sessionEnd"}

EXPECTED = {
    "C0": "every hook entry runs; the bash-only hook skips file writes",
    "C1": "hook 1 prints nothing, hook 2 denies -> blocked",
    "C2": "hook 1 prints `{}`, hook 2 denies -> blocked",
    "C3": "hook 1 exits with code 2 -> blocked",
    "C4": "matcher `bash` runs for bash only",
    "C5": "post hook prints `{}`, later post hook still runs",
    "C6": "lifecycle events fire (sessionStart, userPromptSubmitted, agentStop, sessionEnd)",
    "C7": "preToolUse payload has sessionId, timestamp, cwd, toolName, toolArgs",
    "C8": "`{}` in hook file A, deny in file B -> blocked",
    "C8b": "`{}` in hook file B, deny in file A -> blocked",
    "C10": "after a deny or exit 2, later hooks for that call don't run",
    "C9": "actions-migrator: secret guard prints `{}`, delete guard denies `rm` -> blocked",
    "P1": "actions-migrator: secret guard blocks a fake credential",
    "N1": "new-format plugin: hooks in com.github.copilot/hooks/ run",
    "N2": "new-format plugin: root hooks.json ignored, per the spec",
    "S1": "current-format plugin: skill loads",
    "S2": "new-format plugin: skill loads",
    "R1": "current-format plugin: always-on rule in rules/ applies",
    "R2": "new-format plugin: always-on rule in com.github.copilot/rules/ applies",
    "R3": "new-format plugin: root rules/ ignored, per the spec",
    "A1": "current-format plugin: agent can be started",
    "A2": "new-format plugin: agent in com.github.copilot/agents/ can be started",
}
ORDER = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10", "C9", "P1",
         "N1", "N2", "S1", "S2", "R1", "R2", "R3", "A1", "A2"]
results = []


def add(case, observed, result, reason_code=None):
    record = {"case": case, "expected": EXPECTED[case], "observed": str(observed), "result": result}
    if reason_code is not None:
        record["reason_code"] = reason_code
    results.append(record)


def verdict(ok):
    return "PASS" if ok else "DEVIATION"


def with_marker(n, events=("preToolUse", "postToolUse")):
    return [r for r in rows if r["label"] in KIT and n in r.get("markers", []) and r["event"] in events]


def labels(rs):
    return sorted({r["label"] for r in rs})


def actions(rs):
    return {(r["label"], r["action"]) for r in rs}


def file_has(name, code):
    f = a.out_dir / name
    return f.is_file() and code in f.read_text(errors="replace")


def guard_denied(reason, target):
    expected_calls = {record.get("call") for record in rows
                      if target in record.get("targets", []) and record.get("call")}
    guard_log = a.log.parent / "plugin-guards.jsonl"
    if guard_log.is_file():
        for line in guard_log.read_text().splitlines():
            try:
                record = json.loads(line)
                decision = record["decision"]
                if (record["event"] == "preToolUse" and record["exit_code"] == 0
                        and record["call"] in expected_calls
                        and decision.get("permissionDecision") == "deny"
                        and reason in decision.get("permissionDecisionReason", "")
                        and target in record.get("targets", [])):
                    return True
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
    calls = {}
    for source in a.transcript:
        if not source.is_file() or source.suffix != ".jsonl":
            continue
        for line in source.read_text(errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = event.get("data", {})
            if event.get("type") == "tool.execution_start":
                calls[data.get("toolCallId")] = json.dumps(data.get("arguments", {}))
            if event.get("type") == "tool.execution_complete" and data.get("success") is False:
                message = data.get("error", {}).get("message", "")
                if reason in message and target in calls.get(data.get("toolCallId"), ""):
                    return True
    return False


kit_rows = [r for r in rows if r["label"] in KIT | LIFECYCLE]

# C0-C10: the same conformance kit in both sessions (repository hooks, or hooks inside plugins).
if not any(r["label"] in KIT for r in rows):
    for case in ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10"):
        add(case, "no conformance hook calls logged", "NOT RUN")
else:
    c0 = labels(with_marker("0"))
    add("C0", c0, verdict({"pre1", "pre2", "pre-b0", "pre-b", "post1", "post2"} <= set(c0)
                          and "pre3-matcher-bash" not in c0))

    # Each blocked case needs the expected hook actions in the log *and* the file not written.
    blocked_cases = [
        ("C1", "1", {("pre2", "deny-C1")}, "c1.txt"),
        ("C2", "2", {("pre1", "empty-json"), ("pre2", "deny-C2")}, "c2.txt"),
        ("C3", "3", {("pre1", "exit-2")}, "c3.txt"),
    ]
    for case, n, needed, fname in blocked_cases:
        rs = with_marker(n)
        got = actions(rs)
        written = (a.out_dir / fname).exists()
        missing = sorted(f"{lab}:{act}" for lab, act in needed - got)
        observed = f"hook actions={sorted(f'{lab}:{act}' for lab, act in got if act != 'no-op')} missing={missing} file_written={written}"
        add(case, observed, "NOT RUN" if not rs else verdict(not missing and not written))

    # C8/C8b mirror each other because surfaces may run the two hook files in either order.
    # Each must be blocked by its own deny; at least one must show `{}` from one file before the other file's deny.
    pair, empty_first = [], []
    for case, n, empty, deny, fname in (("C8", "8", "pre1", ("pre-b", "deny-C8"), "c8.txt"),
                                        ("C8b", "9", "pre-b0", ("pre2", "deny-C8b"), "c9.txt")):
        rs = sorted(with_marker(n, ("preToolUse",)), key=lambda r: r["ts"])
        deny_at = next((i for i, r in enumerate(rs) if (r["label"], r["action"]) == deny), None)
        first = deny_at is not None and any(r["label"] == empty and r["action"] == "empty-json" for r in rs[:deny_at])
        empty_first.append(first)
        pair.append((case, rs, deny_at, first, (a.out_dir / fname).exists()))
    for case, rs, deny_at, first, written in pair:
        observed = f"denied={deny_at is not None} empty_json_first={first} file_written={written}"
        if not rs:
            add(case, observed, "NOT RUN")
        else:
            add(case, observed + ("" if any(empty_first) else " (neither order showed `{}` before the deny)"),
                verdict(deny_at is not None and not written and any(empty_first)))

    c4 = [r for r in kit_rows if r["label"] == "pre3-matcher-bash"]
    c4_tools = sorted({r["tool"] for r in c4})
    bash_called = any(r["tool"] == "bash" for r in kit_rows)
    add("C4", f"tools seen by the bash-only hook: {c4_tools}",
        "NOT RUN" if not bash_called and not c4 else verdict(c4_tools == ["bash"]))

    rs = with_marker("5", ("postToolUse",))
    got = actions(rs)
    add("C5", f"post hooks={labels(rs)}", "NOT RUN" if not rs else
        verdict(("post1", "empty-json") in got and "post2" in labels(rs)))

    seen = {r["event"] for r in kit_rows}
    life = {e: e in seen for e in ("sessionStart", "userPromptSubmitted", "agentStop", "Stop", "sessionEnd")}
    add("C6", life, verdict(all(life.values())))

    keys = sorted({",".join(r["payload_keys"]) for r in kit_rows if r["event"] == "preToolUse"})
    add("C7", keys, verdict(any({"sessionId", "timestamp", "cwd", "toolName", "toolArgs"} <= set(k.split(",")) for k in keys)))

    late = []
    stops = 0
    for n in ("1", "2", "3", "8", "9"):
        calls = {}
        for record in with_marker(n, ("preToolUse",)):
            calls.setdefault(record.get("call", record.get("session", "")), []).append(record)
        for pre in calls.values():
            pre.sort(key=lambda record: record["ts"])
            stop = next((index for index, record in enumerate(pre) if record["action"].startswith(("deny", "exit-2"))), None)
            if stop is not None:
                stops += 1
                late += [f"{n}:{record['label']}" for record in pre[stop + 1:]]
    add("C10", f"hooks that ran after the deny: {late}", verdict(not late) if stops else "NOT RUN")

if a.session == "repo":
    rm_rows = with_marker("rm")
    if not rm_rows:
        add("C9", "the rm call never reached the hooks", "NOT RUN")
    elif any(r["event"] == "postToolUse" for r in rm_rows):
        add("C9", "rm executed despite the required deletion guard", "FAIL")
    elif guard_denied(DELETE_GUARD, "hc-does-not-exist"):
        add("C9", "delete guard's deny reason seen", "PASS")
    else:
        add("C9", "rm was blocked, but not with the delete guard's reason", "FAIL")

    p1 = a.out_dir / "p1.md"
    if p1.is_file() and FAKE_VALUE in p1.read_text(errors="replace"):
        add("P1", "fake credential was written", "FAIL")
    elif guard_denied(SECRET_GUARD, "hc-out/p1.md"):
        add("P1", "secret guard's deny reason seen, file not written", "PASS")
    else:
        add("P1", "no secret guard deny reason seen", "NOT RUN")
else:
    ns_rows = [r for r in rows if r["label"].startswith("ns:")]
    ns_root_rows = [r for r in rows if r["label"].startswith("ns-root:")]
    ns_loaded = bool(ns_rows or ns_root_rows) or any(
        file_has(f, c) for f, c in (("skill-ns.txt", "SKILL_NS"), ("rule-ns.txt", "RULE_NS"), ("rule-nsroot.txt", "RULE_NSROOT")))
    ran = bool(rows) or any(p.name != ".gitkeep" for p in a.out_dir.glob("*"))

    if not ns_loaded:
        add("N1", "no sign the new-format plugin loaded", "NOT RUN" if not ran else "DEVIATION")
    else:
        add("N1", f"namespace hook calls={len(ns_rows)}", verdict(bool(ns_rows)))

    def challenge_calls(hook_rows, path):
        calls = []
        for record in hook_rows:
            if path in record.get("targets", []):
                calls.append(record)
                continue
            payload = record.get("raw", {})
            arguments = payload.get("toolArgs", payload.get("tool_input", {}))
            target = arguments.get("path") if isinstance(arguments, dict) else None
            if isinstance(target, str) and (target == path or target.endswith("/" + path)):
                calls.append(record)
        return calls

    n2_calls = challenge_calls(ns_rows, "hc-out/n2-root-hook.txt")
    n2_root_calls = challenge_calls(ns_root_rows, "hc-out/n2-root-hook.txt")
    n2_file = file_has("n2-root-hook.txt", "N2_CHALLENGE")
    if not n2_calls and not n2_root_calls:
        add("N2", "no hook evidence for the root-hook challenge", "NOT RUN")
    else:
        add("N2", f"challenge_calls={len(n2_calls)} root_hook_calls={len(n2_root_calls)} challenge_file={n2_file}",
            verdict(n2_file and not n2_root_calls))

    for case, fname, code in (("S1", "skill-legacy.txt", "SKILL_LEGACY"), ("S2", "skill-ns.txt", "SKILL_NS"),
                              ("R1", "rule-legacy.txt", "RULE_LEGACY"), ("R2", "rule-ns.txt", "RULE_NS")):
        ok = file_has(fname, code)
        add(case, f"{fname} has the code: {ok}", "NOT RUN" if not ran else verdict(ok))
    r3_calls = challenge_calls(ns_rows, "hc-out/r3-rule-challenge.txt")
    r3_file = file_has("r3-rule-challenge.txt", "R3_CHALLENGE")
    r2_control = file_has("rule-ns.txt", "RULE_NS")
    root_rule = file_has("rule-nsroot.txt", "RULE_NSROOT")
    if not r3_calls or not r2_control:
        reason = "rule_positive_control_missing" if r3_calls and r3_file and not root_rule else "challenge_evidence_incomplete"
        add("R3", f"challenge_calls={len(r3_calls)} new-format-rule-control={r2_control}", "NOT RUN", reason)
    else:
        add("R3", f"challenge_file={r3_file} root_rule_applied={root_rule}",
            verdict(r3_file and not root_rule))

    for case, fname, code in (("A1", "agent-legacy.txt", "AGENT_LEGACY"), ("A2", "agent-ns.txt", "AGENT_NS")):
        agent_results = a.log.parent / "agents"
        if a.surface == "cloud-agent" and agent_results.is_dir():
            try:
                selection = json.loads((agent_results / case / "agent-selection.json").read_text())
                control = json.loads((agent_results / "control/agent-selection.json").read_text())
                control_ok = control["completed"] and (agent_results / "control/hc-out/agent-legacy.txt").read_text().strip() == "AGENT_LEGACY"
                marker = agent_results / case / "hc-out" / fname
                if selection["completed"] and marker.is_file() and code in marker.read_text():
                    add(case, "selected plugin agent produced its marker", "PASS")
                elif selection["rejected"] and control_ok:
                    add(case, f"plugin-agent startup rejected (issue {selection['issue']}); repository-agent control passed", "DEVIATION")
                else:
                    add(case, "no conclusive selection result or positive control", "NOT RUN")
            except (OSError, ValueError, KeyError):
                add(case, "cloud agent-selection evidence missing or invalid", "NOT RUN")
        elif meta.get("agents") != "tested":
            add(case, f"not testable here ({meta.get('agents', 'not tested')})", "NOT RUN")
        else:
            ok = file_has(fname, code)
            add(case, f"{fname} has the code: {ok}", verdict(ok))

results.sort(key=lambda r: ORDER.index(r["case"]))
a.json.write_text(json.dumps({"surface": a.surface, "session": a.session, "meta": meta,
                              "hook_log_rows": len(rows), "cases": results}, indent=2) + "\n")

print(f"surface={a.surface} session={a.session} hook_log_rows={len(rows)}")
print("case | result | observed")
print("--- | --- | ---")
for r in results:
    print(f"{r['case']} | {r['result']} | {r['observed']}")
