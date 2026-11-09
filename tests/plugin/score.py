#!/usr/bin/env python3
"""Scores one surface's evidence into result.json, or summarizes several results.

  score.py cli|vscode OUT_DIR --runtime V --model M --setup-exit N --main-exit N --agent-exit N --interrupted N
  score.py summary RESULTS_DIR --expect cli,vscode --sha SHA

Each check is PASS, FAIL or NOT RUN, and anything but PASS fails the run. Evidence strings are
written by this script, never copied from logs, so result.json is safe to publish.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA = 1
CHECKS = [
    ("plugin-installed", "The plugin, its agents and its skills are discovered"),
    ("secret-guard-blocks-credential", "A fake credential is refused by the secret guard and not written"),
    ("delete-guard-blocks-delete", "rm of a workspace file is refused by the delete guard; the file survives"),
    ("safe-write-allowed", "A harmless write still succeeds"),
    ("scorecard-written", "The session's MIGRATION-SCORECARD.md entry is written exactly once"),
    ("skill-loads", "The actionlint skill loads"),
    ("agent-starts", "The jenkins-migrator agent starts and does its task"),
]
SECRET_DENIAL = "Denied by preToolUse hook: Blocked: likely credential value in proposed output."
DELETE_DENIAL = "Denied by preToolUse hook: Blocked: deletion outside .github/ci-archive/ is not allowed (hc-out/keep.txt)."
SKILL_NAMES = {"actionlint", "actions-migrator:actionlint"}


def read(path):
    try:
        return Path(path).read_text(errors="replace")
    except OSError:
        return None


def events(path):
    out = []
    for line in (read(path) or "").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def tool_results(items):
    """Pairs each CLI tool call with its completion: [(tool, arguments, success, error message)]."""
    starts, out = {}, []
    for item in items:
        data = item.get("data") or {}
        if item.get("type") == "tool.execution_start":
            starts[data.get("toolCallId")] = data
        elif item.get("type") == "tool.execution_complete" and data.get("toolCallId") in starts:
            start = starts[data["toolCallId"]]
            error = data.get("error") or {}
            out.append((start.get("toolName"), start.get("arguments") or {}, data.get("success") is True,
                        error.get("message", "") if isinstance(error, dict) else str(error)))
    return out


def file_is(path, expected):
    text = read(path)
    return text is not None and text.strip() == expected


def scorecard_entries(path):
    text = read(path) or ""
    return len(re.findall(r"^## .+\n- session: .+\n- reason: .+\n- workflows: total=", text, re.M))


def check(ok, evidence_pass, evidence_fail):
    return ("PASS", evidence_pass) if ok else ("FAIL", evidence_fail)


def score_cli(out):
    main, agent = tool_results(events(out / "main-events.jsonl")), events(out / "agent-events.jsonl")
    loaded = events(out / "main-events.jsonl")
    agents = {a.get("name") for e in loaded if e.get("type") == "session.custom_agents_updated"
              for a in (e.get("data") or {}).get("agents", [])}
    skills = {s.get("commandName") for e in loaded if e.get("type") == "session.skills_loaded"
              for s in (e.get("data") or {}).get("skills", [])}
    listed = re.search(r"actions-migrator@actions-migrations-via-copilot .*\(enabled\)", read(out / "plugin-list.txt") or "")

    def denied(tool, message, target):
        return any(t == tool and not ok and err.startswith(message) and target(args) for t, args, ok, err in main)

    secret = denied("create", SECRET_DENIAL, lambda a: str(a.get("path", "")).endswith("/hc-out/p1.md"))
    delete = denied("bash", DELETE_DENIAL, lambda a: a.get("command") == "rm hc-out/keep.txt")
    skill = any(t == "skill" and ok and (a.get("skill") or a.get("name")) in SKILL_NAMES for t, a, ok, _ in main)
    agent_ok = any(e.get("type") == "result" for e in agent) and file_is(out / "agent/hc-out/agent.txt", "AGENT_OK")
    return {
        "plugin-installed": check(
            bool(listed) and "actions-migrator:jenkins-migrator" in agents and "actions-migrator:actionlint" in skills,
            "plugin list shows it enabled; session loaded actions-migrator:jenkins-migrator and actions-migrator:actionlint",
            "plugin not listed as enabled, or its agent/skill missing from the session"),
        "secret-guard-blocks-credential": check(
            secret and read(out / "main/hc-out/p1.md") is None,
            "create hc-out/p1.md denied by the secret guard; file absent",
            "no secret-guard denial for hc-out/p1.md, or the file was written"),
        "delete-guard-blocks-delete": check(
            delete and file_is(out / "main/hc-out/keep.txt", "KEEP"),
            "rm hc-out/keep.txt denied by the delete guard; file intact",
            "no delete-guard denial for rm hc-out/keep.txt, or the file changed"),
        "safe-write-allowed": check(
            file_is(out / "main/hc-out/safe.txt", "SAFE_OK"),
            "hc-out/safe.txt contains SAFE_OK", "hc-out/safe.txt missing or wrong"),
        "scorecard-written": check(
            scorecard_entries(out / "main/MIGRATION-SCORECARD.md") == 1,
            "one scorecard entry", f"{scorecard_entries(out / 'main/MIGRATION-SCORECARD.md')} scorecard entries (expected 1)"),
        "skill-loads": check(
            skill, "skill tool loaded actionlint", "no successful skill call for actionlint"),
        "agent-starts": check(
            agent_ok, "--agent actions-migrator:jenkins-migrator wrote hc-out/agent.txt = AGENT_OK",
            "agent session did not finish or hc-out/agent.txt is missing or wrong"),
    }


def score_vscode(out):
    log = read(out / "main.log") or ""
    try:
        ready = json.loads(read(out / "main/plugin-ready.json") or "null")
        children = {(c.get("type"), c.get("name")) for p in ready for c in p.get("children", [])}
    except (TypeError, ValueError, AttributeError):
        children = set()
    try:
        selected = json.loads(read(out / "agent/agent-selected.json") or "{}").get("name")
    except (ValueError, AttributeError):
        selected = None
    skill = re.search(r"^\[tool\] Read skill \[actionlint\]\([^)\s]*/skills/actionlint/SKILL\.md\)", log, re.M)
    # Tool names and outcomes only, so a failure is diagnosable without publishing the log.
    seen = re.findall(r'^\[tool\] ("[^"]{1,40}" failed|Read skill \[[\w:-]{1,60}\])|^\[(denied \w{1,40})\]', log, re.M)
    skill_seen = "; ".join(a or b for a, b in seen if "kill" in (a or b) or b) or "no skill call or denial seen"
    return {
        "plugin-installed": check(
            {("agent", "jenkins-migrator"), ("skill", "actionlint"), ("hook", "hooks.json")} <= children,
            "Agent Host loaded the plugin with jenkins-migrator, actionlint and hooks.json",
            "plugin not ready, or jenkins-migrator, actionlint or hooks.json missing"),
        "secret-guard-blocks-credential": check(
            SECRET_DENIAL in log and read(out / "main/hc-out/p1.md") is None,
            "secret-guard denial in the session; hc-out/p1.md absent",
            "no secret-guard denial, or hc-out/p1.md was written"),
        "delete-guard-blocks-delete": check(
            DELETE_DENIAL in log and file_is(out / "main/hc-out/keep.txt", "KEEP"),
            "delete-guard denial for hc-out/keep.txt; file intact",
            "no delete-guard denial for hc-out/keep.txt, or the file changed"),
        "safe-write-allowed": check(
            file_is(out / "main/hc-out/safe.txt", "SAFE_OK"),
            "hc-out/safe.txt contains SAFE_OK", "hc-out/safe.txt missing or wrong"),
        "scorecard-written": check(
            scorecard_entries(out / "main/MIGRATION-SCORECARD.md") == 1,
            "one scorecard entry (Stop hook)",
            f"{scorecard_entries(out / 'main/MIGRATION-SCORECARD.md')} scorecard entries (expected 1)"),
        "skill-loads": check(
            bool(skill), "read the plugin's skills/actionlint/SKILL.md",
            "actionlint skill not read from the plugin (" + skill_seen + ")"),
        "agent-starts": check(
            selected == "jenkins-migrator" and file_is(out / "agent/hc-out/agent.txt", "AGENT_OK"),
            "selected discovered agent jenkins-migrator; it wrote hc-out/agent.txt = AGENT_OK",
            "jenkins-migrator not selected, or hc-out/agent.txt missing or wrong"),
    }


def score(surface, out, args):
    exits = {"setup": args.setup_exit, "main_session": args.main_exit, "agent_session": args.agent_exit,
             "interrupted": args.interrupted}
    if args.setup_exit or args.interrupted:
        results = {cid: ("NOT RUN", "setup failed or run interrupted") for cid, _ in CHECKS}
    else:
        results = (score_cli if surface == "cli" else score_vscode)(out)
    checks = [{"id": cid, "description": desc, "result": results[cid][0], "evidence": results[cid][1]}
              for cid, desc in CHECKS]
    passed = all(c["result"] == "PASS" for c in checks) and not any(exits.values())
    return {"schema": SCHEMA, "surface": surface, "runtime": args.runtime, "model": args.model,
            "exits": exits, "passed": passed, "checks": checks}


def summarize(results_dir, expect, sha):
    rows, ok = [], True
    for surface in expect:
        path = results_dir / surface / "result.json"
        try:
            result = json.loads(path.read_text())
            if result.get("schema") != SCHEMA or result.get("surface") != surface:
                raise ValueError
        except (OSError, ValueError):
            rows.append(f"| {surface} | — | NOT RUN | no result |")
            ok = False
            continue
        ok = ok and result.get("passed") is True
        for c in result["checks"]:
            rows.append(f"| {surface} | `{c['id']}` | {c['result']} | {c['evidence']} |")
        failed_exits = {k: v for k, v in result.get("exits", {}).items() if v}
        if failed_exits:
            rows.append(f"| {surface} | process exits | FAIL | {failed_exits} |")
        rows.append(f"| {surface} | runtime | | {result.get('runtime')} ({result.get('model')}) |")
    head = [f"### Plugin tests: {'PASS' if ok else 'FAIL'}", "", f"Commit `{sha}`", "",
            "| Surface | Check | Result | Evidence |", "|---|---|---|---|"]
    return ok, "\n".join(head + rows) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["cli", "vscode", "summary"])
    p.add_argument("dir", type=Path)
    p.add_argument("--runtime", default="unknown")
    p.add_argument("--model", default="unknown")
    for name in ("setup-exit", "main-exit", "agent-exit", "interrupted"):
        p.add_argument("--" + name, type=int, default=0)
    p.add_argument("--expect", default="cli,vscode")
    p.add_argument("--sha", default="unknown")
    args = p.parse_args(argv)
    if args.mode == "summary":
        ok, text = summarize(args.dir, [s for s in args.expect.split(",") if s], args.sha)
        print(text)
        return 0 if ok else 1
    result = score(args.mode, args.dir, args)
    (args.dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    for c in result["checks"]:
        print(f"{c['result']:8} {c['id']}: {c['evidence']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
