#!/usr/bin/env python3
"""Combine per-surface scores into one results table.

summarize.py --scores DIR [--baseline results.json] [--meta key=value]... --out DIR

DIR holds <surface>/score.json files. Writes results.json and results.md to --out, and
prints attention=<n> (anything not PASS), failed=<n> (FAIL only) and changed=<n>
(also to $GITHUB_OUTPUT when set).
"""
import argparse
import json
import os
from pathlib import Path

SURFACES = ["cli", "vscode", "cloud-agent"]
NAMES = {"cli": "Copilot CLI", "vscode": "VS Code Agent Host", "cloud-agent": "Cloud agent"}
ICONS = {"PASS": "✅", "DEVIATION": "⚠️", "FAIL": "❌", "NOT RUN": "➖"}

ap = argparse.ArgumentParser()
ap.add_argument("--scores", type=Path, required=True)
ap.add_argument("--baseline", type=Path)
ap.add_argument("--meta", action="append", default=[])
ap.add_argument("--out", type=Path, required=True)
a = ap.parse_args()

scores = {}
for s in SURFACES:
    f = a.scores / s / "score.json"
    if f.is_file():
        scores[s] = json.loads(f.read_text())
cases, expected = [], {}
for s in scores.values():
    for c in s["cases"]:
        if c["case"] not in expected:
            cases.append(c["case"])
            expected[c["case"]] = c["expected"]
grid = {s: {c["case"]: c for c in scores[s]["cases"]} for s in scores}

baseline = {}
if a.baseline and a.baseline.is_file():
    baseline = json.loads(a.baseline.read_text()).get("grid", {})

attention, failed, changes = [], [], []
for s in scores:
    for case, c in grid[s].items():
        if c["result"] != "PASS":
            attention.append(f"{NAMES[s]} {case}: {c['result']} ({c['observed']})")
        if c["result"] == "FAIL":
            failed.append(case)
        before = baseline.get(s, {}).get(case, {}).get("result")
        if before and before != c["result"]:
            changes.append(f"{NAMES[s]} {case}: {before} -> {c['result']}")

meta = dict(m.split("=", 1) for m in a.meta if "=" in m)
a.out.mkdir(parents=True, exist_ok=True)
(a.out / "results.json").write_text(json.dumps({
    "meta": meta,
    "surface_meta": {s: scores[s].get("meta", {}) for s in scores},
    "grid": {s: {k: {"result": v["result"], "observed": v["observed"]} for k, v in grid[s].items()} for s in scores},
    "attention": attention,
    "changes": changes,
}, indent=2) + "\n")

ran = [s for s in SURFACES if s in scores]
lines = [f"**Tool repo commit:** `{meta.get('sha', '?')}` ({meta.get('kind', '?')})", ""]
lines += ["| Case | Expected | " + " | ".join(NAMES[s] for s in ran) + " |",
          "|---|---|" + "---|" * len(ran)]
for case in cases:
    cells = [ICONS.get(grid[s].get(case, {}).get("result"), "") + " " + grid[s].get(case, {}).get("result", "") for s in ran]
    lines.append(f"| {case} | {expected[case]} | " + " | ".join(cells) + " |")
skipped = [NAMES[s] for s in SURFACES if s not in scores]
lines += ["", "Versions: " + "; ".join(f"{NAMES[s]}: " + ", ".join(f"{k}={v}" for k, v in scores[s].get("meta", {}).items()) for s in ran)]
if skipped:
    lines.append("Not run this time: " + ", ".join(skipped))
lines += ["", f"**Needs attention ({len(attention)}):**"] + [f"- {x}" for x in attention or ["none"]]
lines += ["", f"**Changed since the last main run ({len(changes)}):**"] + [f"- {x}" for x in changes or ["none"]]
(a.out / "results.md").write_text("\n".join(lines) + "\n")

summary = f"attention={len(attention)}\nfailed={len(failed)}\nchanged={len(changes)}\n"
print(summary, end="")
if os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(summary)
