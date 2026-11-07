#!/usr/bin/env python3
"""Combine per-surface, per-session scores into one results table.

summarize.py --scores DIR --expect SURFACES [--expected expected.json] [--baseline results.json]
             [--meta key=value]... --out DIR

DIR holds <surface>/<session>/score.json. SURFACES is a comma list of surfaces that should have
run (e.g. "cli,vscode"); a missing one counts as a failure. expected.json lists the results that
aren't PASS today (known surface gaps); every other case is expected to PASS.

Writes results.json and results.md to --out, and prints unexpected=<n>, missing=<n>, not_run=<n>
and changed=<n> (also to $GITHUB_OUTPUT when set).
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
ap.add_argument("--out", type=Path, required=True)
a = ap.parse_args()
meta = dict(m.split("=", 1) for m in a.meta if "=" in m)
expect = [s for s in a.expect.split(",") if s]
known = json.loads(a.expected.read_text()) if a.expected.is_file() else {}
baseline = json.loads(a.baseline.read_text()).get("grid", {}) if a.baseline and a.baseline.is_file() else {}

grid, surface_meta, order = {}, {}, {s: [] for s in SESSIONS}
expected_text = {}
for s in SURFACES:
    for session in SESSIONS:
        f = a.scores / s / session / "score.json"
        if not f.is_file():
            continue
        data = json.loads(f.read_text())
        surface_meta.setdefault(s, {}).update(data.get("meta", {}))
        for c in data["cases"]:
            key = f"{session}:{c['case']}"
            grid.setdefault(s, {})[key] = {"result": c["result"], "observed": c["observed"]}
            if key not in expected_text:
                expected_text[key] = c["expected"]
                order[session].append(key)

unexpected, missing, not_run, changes = [], [], [], []
for s in expect:
    for session in SESSIONS:
        if not any(k.startswith(f"{session}:") for k in grid.get(s, {})):
            missing.append(f"{NAMES[s]}: {SESSIONS[session]} session produced no results")
for s, cells in grid.items():
    for key, c in cells.items():
        want = known.get(s, {}).get(key, {}).get("result", "PASS")
        label = f"{NAMES[s]} {key}"
        if c["result"] == "NOT RUN" and want != "NOT RUN":
            not_run.append(f"{label}: {c['observed']}")
        elif c["result"] != want:
            unexpected.append(f"{label}: expected {want}, got {c['result']} ({c['observed']})")
        before = baseline.get(s, {}).get(key, {}).get("result")
        if before and before != c["result"]:
            changes.append(f"{label}: {before} -> {c['result']}")

a.out.mkdir(parents=True, exist_ok=True)
(a.out / "results.json").write_text(json.dumps({
    "meta": meta, "surface_meta": surface_meta, "grid": grid,
    "unexpected": unexpected, "missing": missing, "not_run": not_run, "changes": changes,
}, indent=2) + "\n")


def cell(s, key):
    c = grid.get(s, {}).get(key)
    if not c:
        return ""
    want = known.get(s, {}).get(key, {})
    note = " (known)" if want and c["result"] == want.get("result") and c["result"] != "PASS" else ""
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
                     ("Not run (no evidence either way)", not_run), ("Changed since the last main run", changes)):
    lines += ["", f"**{title} ({len(items)}):**"] + [f"- {x}" for x in items or ["none"]]
(a.out / "results.md").write_text("\n".join(lines) + "\n")

summary = f"unexpected={len(unexpected)}\nmissing={len(missing)}\nnot_run={len(not_run)}\nchanged={len(changes)}\n"
print(summary, end="")
if os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(summary)
