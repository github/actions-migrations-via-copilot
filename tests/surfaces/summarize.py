#!/usr/bin/env python3
"""Combine per-surface, per-session scores into one results table.

summarize.py --scores DIR --expect SURFACES [--expected expected.json] [--baseline results.json]
             [--meta key=value]... --out DIR

DIR holds <surface>/<session>/score.json. SURFACES is a comma list of surfaces that should have
run (e.g. "cli,vscode"); a missing one counts as a failure. expected.json lists the results that
aren't PASS today (known surface gaps); every other case is expected to PASS.

Writes results.json and results.md to --out. Total unexpected/not_run counts retain every
outcome; blocking_unexpected/blocking_not_run apply the approved VS Code rule-warning policy.
Warnings, missing cases, process failures and job failures are reported separately.
Counts are also written to $GITHUB_OUTPUT when set.
"""
import argparse
import json
import os
from pathlib import Path

SURFACES = ["cli", "vscode", "cloud-agent"]
SESSIONS = {"repo": "Repository hooks + actions-migrator", "plugin": "Plugin hooks and plugin parts"}
NAMES = {"cli": "Copilot CLI", "vscode": "VS Code Agent Host", "cloud-agent": "Cloud agent"}
ICONS = {"PASS": "✅", "DEVIATION": "⚠️", "FAIL": "❌", "NOT RUN": "➖", "MISSING": "❓"}

ap = argparse.ArgumentParser()
ap.add_argument("--scores", type=Path, required=True)
ap.add_argument("--expect", default="")
ap.add_argument("--expected", type=Path, default=Path(__file__).resolve().parent / "expected.json")
ap.add_argument("--baseline", type=Path)
ap.add_argument("--meta", action="append", default=[])
ap.add_argument("--job-result", action="append", default=[], metavar="JOB=CONCLUSION")
ap.add_argument("--out", type=Path, required=True)
a = ap.parse_args()
meta = dict(m.split("=", 1) for m in a.meta if "=" in m)
job_results = dict(m.split("=", 1) for m in a.job_result if "=" in m)
upstream_failed = [f"{job}: {result}" for job, result in job_results.items() if result != "success"]
expect = [s for s in a.expect.split(",") if s]
required_cases = {
    "repo": {"C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10", "C9", "P1"},
    "plugin": {"C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10",
               "N1", "N2", "S1", "S2", "R1", "R2", "R3", "A1", "A2"},
}
known = json.loads(a.expected.read_text()) if a.expected.is_file() else {}
baseline = json.loads(a.baseline.read_text()).get("grid", {}) if a.baseline and a.baseline.is_file() else {}

grid, surface_meta, order = {}, {}, {s: [] for s in SESSIONS}
expected_text = {}
execution_failures = []
for s in SURFACES:
    for session in SESSIONS:
        f = a.scores / s / session / "score.json"
        if not f.is_file():
            continue
        data = json.loads(f.read_text())
        surface_meta.setdefault(s, {}).update(data.get("meta", {}))
        for key, value in data.get("meta", {}).items():
            if not key.endswith("_exit") and key != "selected_agent_failures":
                continue
            try:
                status = int(value)
            except (TypeError, ValueError):
                continue
            if status != 0:
                execution_failures.append(f"{NAMES[s]} {session} {key}={status}")
        for c in data["cases"]:
            key = f"{session}:{c['case']}"
            grid.setdefault(s, {})[key] = {"result": c["result"], "observed": c["observed"]}
            if "reason_code" in c:
                grid[s][key]["reason_code"] = c["reason_code"]
            if key not in expected_text:
                expected_text[key] = c["expected"]
                order[session].append(key)

unexpected, missing, not_run, changes = [], [], [], []
warnings, blocking_unexpected, blocking_not_run = [], [], []
warning_cells = set()
for s in expect:
    for session in SESSIONS:
        if not any(k.startswith(f"{session}:") for k in grid.get(s, {})):
            missing.append(f"{NAMES[s]}: {SESSIONS[session]} session produced no results")
        else:
            absent = sorted(case for case in required_cases[session] if f"{session}:{case}" not in grid[s])
            if absent:
                missing.append(f"{NAMES[s]} {session}: missing cases {', '.join(absent)}")
for s, cells in grid.items():
    for key, c in cells.items():
        want = known.get(s, {}).get(key, {}).get("result", "PASS")
        label = f"{NAMES[s]} {key}"
        warning_reason = None
        if s == "vscode" and key in {"plugin:R1", "plugin:R2"} and c["result"] == "DEVIATION":
            warning_reason = "Rule-following is an unresolved, non-blocking compatibility check."
        elif (s == "vscode" and key == "plugin:R3" and c["result"] == "NOT RUN"
              and c.get("reason_code") == "rule_positive_control_missing"
              and cells.get("plugin:R2", {}).get("result") == "DEVIATION"):
            warning_reason = "The challenge ran, but the non-blocking R2 rule control did not apply."
        if warning_reason:
            warnings.append({"surface": s, "case": key, "result": c["result"], "reason": warning_reason})
            warning_cells.add((s, key))
        if c["result"] == "NOT RUN":
            message = f"{label}: {c['observed']}"
            not_run.append(message)
            if not warning_reason:
                blocking_not_run.append(message)
        elif c["result"] != want:
            message = f"{label}: expected {want}, got {c['result']} ({c['observed']})"
            unexpected.append(message)
            if not warning_reason:
                blocking_unexpected.append(message)
        before = baseline.get(s, {}).get(key, {}).get("result")
        if before and before != c["result"]:
            changes.append(f"{label}: {before} -> {c['result']}")

a.out.mkdir(parents=True, exist_ok=True)
(a.out / "results.json").write_text(json.dumps({
    "meta": meta, "surface_meta": surface_meta, "grid": grid,
    "job_results": job_results, "upstream_failed": upstream_failed, "execution_failures": execution_failures,
    "unexpected": unexpected, "missing": missing, "not_run": not_run, "changes": changes,
    "warnings": warnings, "blocking_unexpected": blocking_unexpected, "blocking_not_run": blocking_not_run,
}, indent=2) + "\n")


def cell(s, key):
    c = grid.get(s, {}).get(key)
    if not c:
        return ""
    want = known.get(s, {}).get(key, {})
    note = " (known)" if want and c["result"] == want.get("result") and c["result"] != "PASS" else ""
    if (s, key) in warning_cells:
        note += " (non-blocking warning)"
    return f"{ICONS.get(c['result'], '')} {c['result']}{note}"


ran = [s for s in SURFACES if s in grid]
lines = [f"**Tool repo commit:** `{meta.get('sha', '?')}` ({meta.get('kind', '?')})", ""]
for session, title in SESSIONS.items():
    if not order[session]:
        continue
    lines += [f"### {title}", "", "| Case | Expected behavior | " + " | ".join(NAMES[s] for s in ran) + " |",
              "|---|---|" + "---|" * len(ran)]
    for key in order[session]:
        lines.append(f"| {key.split(':', 1)[1]} | {expected_text[key]} | " + " | ".join(cell(s, key) for s in ran) + " |")
    lines.append("")
lines.append("Versions: " + "; ".join(f"{NAMES[s]}: " + ", ".join(f"{k}={v}" for k, v in surface_meta.get(s, {}).items()) for s in ran))
known_notes = sorted({f"- {NAMES[s]} {k}: {v.get('why', '')}" for s, ks in known.items() if s in ran for k, v in ks.items()})
if known_notes:
    lines += ["", "**Known surface gaps** (expected results that aren't PASS):"] + known_notes
for title, items in (("Unexpected results", unexpected), ("Surfaces that didn't run", missing),
                     ("Not run (no evidence either way)", not_run), ("Changed since the last main run", changes),
                     ("Non-blocking rule warnings", [f"{NAMES[item['surface']]} {item['case']}: {item['result']}. {item['reason']}" for item in warnings]),
                     ("Blocking unexpected results", blocking_unexpected),
                     ("Blocking checks without evidence", blocking_not_run),
                     ("Recorded nonzero process exits", execution_failures),
                     ("Required jobs that did not succeed", upstream_failed)):
    lines += ["", f"**{title} ({len(items)}):**"] + [f"- {x}" for x in items or ["none"]]
(a.out / "results.md").write_text("\n".join(lines) + "\n")

summary = (f"unexpected={len(unexpected)}\nmissing={len(missing)}\nnot_run={len(not_run)}\n"
           f"changed={len(changes)}\nexecution_failed={len(execution_failures)}\n"
           f"upstream_failed={len(upstream_failed)}\n")
summary += (f"warnings={len(warnings)}\nblocking_unexpected={len(blocking_unexpected)}\n"
            f"blocking_not_run={len(blocking_not_run)}\n")
print(summary, end="")
if os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(summary)
