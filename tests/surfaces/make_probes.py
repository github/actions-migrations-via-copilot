#!/usr/bin/env python3
"""Build the local marketplace of probe plugins used by the plugin-hooks session.

make_probes.py <dir>
make_probes.py <dir> --rule-only current|namespace

- hc-probe-a: current format. Conformance hooks from kit/conformance-a.json, plus a skill,
  an always-on rule in rules/, and an agent.
- hc-probe-b: current format. Conformance hooks from kit/conformance-b.json, so C8/C8b
  test `{}` in one plugin and a deny in another.
- hc-probe-ns: Agent Plugins 1.0 format. Log-only hooks, a rule and an agent under
  com.github.copilot/, a portable skill, and decoys at the root (hooks.json, rules/) that
  the spec says to ignore.

Each part asks for a distinct file in hc-out/, so the file proves which part loaded.
"""
import base64
import argparse
import hashlib
import json
import shutil
from pathlib import Path

KIT = Path(__file__).resolve().parent / "kit"
parser = argparse.ArgumentParser()
parser.add_argument("destination", type=Path)
parser.add_argument("--include-plugin", type=Path)
parser.add_argument("--source-sha")
parser.add_argument("--observe-plugin", action="store_true")
parser.add_argument("--rule-only", choices=["current", "namespace"])
options = parser.parse_args()
OUT = options.destination
if options.include_plugin and (not options.source_sha or len(options.source_sha) != 40):
    parser.error("--include-plugin requires the exact --source-sha")
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
# Plugin hooks may run from the plugin's own folder, so each hook carries the probe inline
# instead of pointing at a path. The probe finds the project from the payload's cwd.
_B64 = base64.b64encode((KIT / "probe.py").read_bytes()).decode()
PROBE_CMD = f"python3 -c \"import base64; exec(base64.b64decode('{_B64}'))\""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def conformance_hooks(name):
    hooks = json.loads((KIT / name).read_text())
    for entries in hooks["hooks"].values():
        for e in entries:
            e["bash"] = f"{PROBE_CMD} {e['bash'].split()[-1]}"
    return json.dumps(hooks, indent=2) + "\n"


def log_only_hooks(prefix):
    entry = lambda event: [{"type": "command", "timeoutSec": 15, "bash": f"{PROBE_CMD} {prefix}:{event}"}]
    return json.dumps({"version": 1, "hooks": {e: entry(e) for e in ("sessionStart", "preToolUse")}}, indent=2) + "\n"


def code_task(code, file):
    # The code is spelled out as two words so the plugin files never contain it verbatim.
    a, b = code.split("_")
    return (f"Create the file `hc-out/{file}` containing the code formed by joining the words "
            f"{a} and {b} with an underscore, in capitals. Use your file-creation tool.")


def skill(name, code, file):
    return (f"---\nname: {name}\ndescription: Hook conformance probe skill. Use when a task asks for {name}.\n---\n\n"
            f"{code_task(code, file)}\n")


def rule(code, file):
    return ("---\ndescription: Hook conformance probe rule\nalwaysApply: true\n---\n\n"
            f"Before you finish any task in a repository that has an `hc-out/` folder, also do this: {code_task(code, file)}\n")


def agent(name, code, file):
    return (f"---\nname: {name}\ndescription: Hook conformance probe agent.\n---\n\n"
            f"You are the hook conformance probe agent. {code_task(code, file)} Do nothing else.\n")


plugins = OUT / "plugins"

if options.rule_only:
    probe = plugins / "hc-rule-probe"
    if options.rule_only == "current":
        write(probe / "plugin.json", json.dumps({
            "name": "hc-rule-probe", "version": "0.0.1",
            "description": "Isolated VS Code rule probe",
        }, indent=2) + "\n")
        rule_path = probe / "rules/hc-rule-probe.mdc"
        marker_code = "RULE_LEGACY"
    else:
        write(probe / "plugin.json", json.dumps({
            "$schema": SCHEMA, "name": "hc-rule-probe", "version": "0.0.1",
            "description": "Isolated VS Code rule probe",
        }, indent=2) + "\n")
        rule_path = probe / "com.github.copilot/rules/hc-rule-probe.mdc"
        marker_code = "RULE_NS"
    write(rule_path, rule(marker_code, "rule-marker.txt"))
    write(OUT / "rule-resource-path", str(rule_path.resolve()) + "\n")
    raise SystemExit(0)

a = plugins / "hc-probe-a"
write(a / "plugin.json", json.dumps({"name": "hc-probe-a", "version": "0.0.1", "description": "Hook conformance probe A",
                                     "hooks": "hooks.json", "skills": "skills/", "agents": "agents/"}, indent=2) + "\n")
write(a / "hooks.json", conformance_hooks("conformance-a.json"))
write(a / "skills/hc-probe-skill/SKILL.md", skill("hc-probe-skill", "SKILL_LEGACY", "skill-legacy.txt"))
write(a / "rules/hc-probe-rule.mdc", rule("RULE_LEGACY", "rule-legacy.txt"))
write(a / "agents/hc-probe-agent.agent.md", agent("hc-probe-agent", "AGENT_LEGACY", "agent-legacy.txt"))

b = plugins / "hc-probe-b"
write(b / "plugin.json", json.dumps({"name": "hc-probe-b", "version": "0.0.1", "description": "Hook conformance probe B",
                                     "hooks": "hooks.json"}, indent=2) + "\n")
write(b / "hooks.json", conformance_hooks("conformance-b.json"))

ns = plugins / "hc-probe-ns"
write(ns / "plugin.json", json.dumps({"$schema": SCHEMA, "name": "hc-probe-ns", "version": "0.0.1",
                                      "description": "Agent Plugins 1.0 format probe"}, indent=2) + "\n")
write(ns / "com.github.copilot/hooks/hooks.json", log_only_hooks("ns"))
write(ns / "com.github.copilot/rules/hc-probe-ns-rule.mdc", rule("RULE_NS", "rule-ns.txt"))
write(ns / "com.github.copilot/agents/hc-probe-ns-agent.agent.md", agent("hc-probe-ns-agent", "AGENT_NS", "agent-ns.txt"))
write(ns / "skills/hc-probe-ns-skill/SKILL.md", skill("hc-probe-ns-skill", "SKILL_NS", "skill-ns.txt"))
write(ns / "hooks.json", log_only_hooks("ns-root"))
write(ns / "rules/hc-probe-nsroot-rule.mdc", rule("RULE_NSROOT", "rule-nsroot.txt"))

plugin_names = ["hc-probe-a", "hc-probe-b", "hc-probe-ns"]
if options.include_plugin:
    source = options.include_plugin.resolve()
    manifest = json.loads((source / "plugin.json").read_text())
    if manifest.get("name") != "actions-migrator" or any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("Expected an actions-migrator directory without symlinks")
    shutil.copytree(source, plugins / "actions-migrator")
    if options.observe_plugin:
        original = (source / "hooks.json").read_bytes()
        write(plugins / "actions-migrator/hooks.original.json", original.decode())
        hooks = json.loads(original)
        observer = base64.b64encode((KIT.parent / "observe_hook.py").read_bytes()).decode()
        for event, entries in hooks["hooks"].items():
            for index, entry in enumerate(entries):
                command = entry.get("bash")
                if command is not None:
                    encoded = base64.b64encode(command.encode()).decode()
                    entry["bash"] = f"python3 -c \"import base64; exec(base64.b64decode('{observer}'))\" '{encoded}' '{event}' '{index}'"
        write(plugins / "actions-migrator/hooks.json", json.dumps(hooks, indent=2) + "\n")
    plugin_names.append("actions-migrator")
    hashes = {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(plugins.rglob("*")) if path.is_file()}
    write(OUT / "fixture-source.json", json.dumps({
        "source_repository": "github/actions-migrations-via-copilot",
        "source_sha": options.source_sha,
        "observed_plugin": options.observe_plugin,
        "files_sha256": hashes,
    }, indent=2) + "\n")

write(OUT / ".github/plugin/marketplace.json", json.dumps({
    "name": "hc-probes",
    "owner": {"name": "surface-tests"},
    "plugins": [{"name": n, "source": f"./plugins/{n}"} for n in plugin_names],
}, indent=2) + "\n")
