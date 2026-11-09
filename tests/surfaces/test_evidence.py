import json
import base64
import hashlib
import io
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from sanitize_artifacts import publish
from cloud_settings import authorize, configure, settings_for, verify_marketplace
import rule_evidence


SUITE = Path(__file__).resolve().parent


class EvidenceTests(unittest.TestCase):
    def test_warning_policy_preserves_results_and_required_failures(self):
        names = {
            "repo": ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10", "C9", "P1"),
            "plugin": ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10", "N1", "N2", "S1", "S2", "R1", "R2", "R3", "A1", "A2"),
        }
        scenarios = ("warnings", "guard", "hook", "cli_rule", "missing_case", "missing_session", "rule_not_run", "rule_fail", "unknown_dependency", "missing_challenge", "r2_not_run", "r2_pass", "r3_deviation", "process", "job")
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for surface in ("cli", "vscode"):
                    for session, cases in names.items():
                        if scenario == "missing_session" and surface == "vscode" and session == "repo":
                            continue
                        records = [{"case": case, "expected": case, "result": "PASS", "observed": "fixture evidence"} for case in cases]
                        for record in records:
                            case = record["case"]
                            if surface == "vscode" and session == "plugin":
                                if case in {"R1", "R2"}:
                                    record["result"] = "DEVIATION"
                                if case == "R3":
                                    record.update(result="NOT RUN", reason_code="rule_positive_control_missing")
                                if scenario == "rule_not_run" and case == "R1":
                                    record["result"] = "NOT RUN"
                                if scenario == "rule_fail" and case == "R1":
                                    record["result"] = "FAIL"
                                if scenario == "r2_not_run" and case == "R2":
                                    record["result"] = "NOT RUN"
                                if scenario == "r2_pass" and case == "R2":
                                    record["result"] = "PASS"
                                if scenario == "hook" and case == "C2":
                                    record["result"] = "DEVIATION"
                                if scenario == "unknown_dependency" and case == "R3":
                                    record.pop("reason_code")
                                if scenario == "missing_challenge" and case == "R3":
                                    record["reason_code"] = "challenge_evidence_incomplete"
                                if scenario == "r3_deviation" and case == "R3":
                                    record["result"] = "DEVIATION"
                            if scenario == "guard" and session == "repo" and case == "P1":
                                record["result"] = "FAIL"
                            if scenario == "cli_rule" and surface == "cli" and session == "plugin" and case == "R1":
                                record["result"] = "DEVIATION"
                        if scenario == "missing_case" and surface == "vscode" and session == "plugin":
                            records = [record for record in records if record["case"] != "R1"]
                        destination = root / surface / session
                        destination.mkdir(parents=True)
                        metadata = {"ahpx_exit": "124"} if scenario == "process" and surface == "vscode" else {}
                        (destination / "score.json").write_text(json.dumps({"meta": metadata, "cases": records}))
                result = subprocess.run([sys.executable, str(SUITE / "summarize.py"), "--scores", str(root), "--expect", "cli,vscode",
                                         "--job-result", "offline=" + ("failure" if scenario == "job" else "success"),
                                         "--out", str(root / "summary")], check=True, capture_output=True, text=True)
                summary = json.loads((root / "summary/results.json").read_text())
                blocking = any(summary[key] for key in ("blocking_unexpected", "blocking_not_run", "missing", "execution_failures", "upstream_failed"))
                self.assertEqual(blocking, scenario != "warnings")
                if scenario == "warnings":
                    self.assertEqual(len(summary["warnings"]), 3)
                    self.assertEqual(len(summary["unexpected"]), 2)
                    self.assertEqual(len(summary["not_run"]), 1)
                    self.assertEqual(summary["grid"]["vscode"]["plugin:R1"]["result"], "DEVIATION")
                    self.assertEqual(summary["grid"]["vscode"]["plugin:R3"]["result"], "NOT RUN")
                    self.assertIn("warnings=3", result.stdout)
                    self.assertIn("non-blocking warning", (root / "summary/results.md").read_text())

    def test_cloud_marketplace_requires_verified_bytes_and_immutable_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            expected = root / "expected"
            published = root / "published"
            subprocess.run([sys.executable, str(SUITE / "make_probes.py"), str(expected),
                            "--include-plugin", str(SUITE.parents[1] / "plugin"), "--source-sha", "a" * 40,
                            "--observe-plugin"], check=True, capture_output=True)
            shutil.copytree(expected, published)
            verify_marketplace(expected, published)
            settings = settings_for("plugin", "example/fixtures", "b" * 40)
            self.assertEqual(settings["extraKnownMarketplaces"]["hc-probes"]["source"]["ref"], "b" * 40)
            with self.assertRaises(ValueError):
                settings_for("plugin", "example/fixtures", "main")
            hook = published / "plugins/actions-migrator/hooks.json"
            original = hook.read_bytes()
            hook.write_text("{}")
            with self.assertRaises(ValueError):
                verify_marketplace(expected, published)
            hook.write_bytes(original)
            manifest = published / ".github/plugin/marketplace.json"
            original_manifest = manifest.read_bytes()
            manifest.write_text('{"plugins":[]}')
            with self.assertRaises(ValueError):
                verify_marketplace(expected, published)
            manifest.write_bytes(original_manifest)
            injected = published / "plugins/actions-migrator/injected.txt"
            injected.write_text("unexpected")
            with self.assertRaises(ValueError):
                verify_marketplace(expected, published)
            injected.unlink()
            hook.unlink()
            hook.symlink_to(expected / "plugins/actions-migrator/hooks.json")
            with self.assertRaises(ValueError):
                verify_marketplace(expected, published)

    def test_patch_targets_are_correlated_without_retaining_patch_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            patch_text = "*** Begin Patch\n*** Add File: hc-out/p1.md\n+private-patch-content\n*** Update File: hc-out/n2-root-hook.txt\n@@\n+private-patch-content\n*** Move to: hc-out/r3-rule-challenge.txt\n*** End Patch\n"
            command = base64.b64encode(b"printf '%s' '{\"permissionDecision\":\"deny\"}'").decode()
            for arguments in (patch_text, {"patch": patch_text}, {"input": patch_text}):
                payload = json.dumps({"cwd": str(root), "toolName": "apply_patch", "toolArgs": arguments})
                subprocess.run([sys.executable, str(SUITE / "kit/probe.py"), "ns:preToolUse"], input=payload, text=True, capture_output=True, check=True)
                subprocess.run([sys.executable, str(SUITE / "observe_hook.py"), command, "preToolUse", "0"], input=payload, text=True, capture_output=True, check=True)
                probe = json.loads((root / ".hook-conformance/probe.jsonl").read_text().splitlines()[-1])
                observer = json.loads((root / ".hook-conformance/plugin-guards.jsonl").read_text().splitlines()[-1])
                self.assertEqual(probe["targets"], ["hc-out/n2-root-hook.txt", "hc-out/p1.md", "hc-out/r3-rule-challenge.txt"])
                self.assertEqual(observer["targets"], probe["targets"])
                self.assertEqual(observer["call"], probe["call"])
                self.assertNotIn("private-patch-content", json.dumps([probe, observer]))
            payload = json.dumps({"cwd": str(root), "toolName": "apply_patch", "toolArgs": "*** Begin Patch\n*** Add File: report.md\n+*** Add File: hc-out/p1.md\n*** End Patch\n"})
            subprocess.run([sys.executable, str(SUITE / "kit/probe.py"), "ns:preToolUse"], input=payload, text=True, capture_output=True, check=True)
            self.assertEqual(json.loads((root / ".hook-conformance/probe.jsonl").read_text().splitlines()[-1])["targets"], [])

    def test_collection_removes_stale_scoring_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            (workspace / "hc-out").mkdir(parents=True)
            (workspace / "hc-out/rule-legacy.txt").write_text("RULE_LEGACY")
            output = root / "output"
            command = ["bash", "-c", 'source "$1/common.sh"; collect_and_score vscode plugin "$2" "$3" --meta agents=tested',
                       "test", str(SUITE), str(workspace), str(output)]
            subprocess.run(command, check=True, capture_output=True)
            first = json.loads((output / "score.json").read_text())
            self.assertEqual(next(case["result"] for case in first["cases"] if case["case"] == "R1"), "PASS")
            for name in ("probe.jsonl", "plugin-guards.jsonl", "hook-results.md"):
                (output / name).write_text("stale evidence")
            empty = root / "empty"
            (empty / "hc-out").mkdir(parents=True)
            command[-2] = str(empty)
            subprocess.run(command, check=True, capture_output=True)
            second = json.loads((output / "score.json").read_text())
            self.assertTrue(all(case["result"] != "PASS" for case in second["cases"]))
            self.assertEqual(next(case["result"] for case in second["cases"] if case["case"] == "R1"), "NOT RUN")
            self.assertFalse((output / "hc-out/rule-legacy.txt").exists())
            for name in ("probe.jsonl", "plugin-guards.jsonl", "hook-results.md"):
                self.assertFalse((output / name).exists())

    def test_delete_guard_execution_overrides_a_deny_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            probe = {"label": "pre1", "event": "preToolUse", "markers": ["rm"], "tool": "bash",
                     "payload_keys": [], "targets": ["hc-does-not-exist"], "call": "delete-call", "ts": "1", "action": "no-op"}
            guard = {"event": "preToolUse", "exit_code": 0, "call": "delete-call", "targets": ["hc-does-not-exist"],
                     "decision": {"permissionDecision": "deny", "permissionDecisionReason": "deletion outside .github/ci-archive/ is not allowed"}}
            (root / "plugin-guards.jsonl").write_text(json.dumps(guard) + "\n")
            command = [sys.executable, str(SUITE / "score.py"), "--surface", "cli", "--session", "repo",
                       "--log", str(root / "probe.jsonl"), "--out-dir", str(root), "--json", str(root / "score.json")]
            for executed, expected in ((False, "PASS"), (True, "FAIL")):
                records = [probe]
                if executed:
                    records.append({**probe, "event": "postToolUse", "label": "post1", "ts": "2"})
                (root / "probe.jsonl").write_text("".join(json.dumps(record) + "\n" for record in records))
                subprocess.run(command, check=True, capture_output=True)
                cases = json.loads((root / "score.json").read_text())["cases"]
                self.assertEqual(next(case["result"] for case in cases if case["case"] == "C9"), expected)

    def test_cloud_authorization_requires_target_policy_and_exact_source(self):
        repository = {"full_name": "example/test-runner", "private": True, "archived": False, "permissions": {"push": True}}
        policy = {"enabled": True, "repository": repository["full_name"], "source_repository": "github/actions-migrations-via-copilot", "source_commits": ["a" * 40]}
        fixture = {"source_repository": policy["source_repository"], "source_sha": "a" * 40}
        authorize(policy, repository, "a" * 40, fixture)
        for changed in ({"enabled": False}, {"repository": "example/production"}, {"source_commits": []}, {"source_commits": "a" * 40}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                authorize({**policy, **changed}, repository, "a" * 40, fixture)
        for changed in ({"private": False}, {"archived": True}, {"permissions": {"push": False}}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                authorize(policy, {**repository, **changed}, "a" * 40, fixture)
        with self.assertRaises(ValueError):
            authorize(policy, repository, "b" * 40, fixture)
        with self.assertRaises(ValueError):
            authorize(policy, repository, "a" * 40, {**fixture, "source_sha": "b" * 40})

    def test_minimized_probe_keeps_negative_case_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            for target in ("hc-out/n2-root-hook.txt", "hc-out/r3-rule-challenge.txt"):
                payload = {"cwd": str(root), "toolName": "create", "toolArgs": {"path": target, "content": "private-test-content"}}
                subprocess.run([sys.executable, str(SUITE / "kit/probe.py"), "ns:preToolUse"], input=json.dumps(payload), text=True, capture_output=True, check=True)
            records = [json.loads(line) for line in (root / ".hook-conformance/probe.jsonl").read_text().splitlines()]
            self.assertEqual([record["targets"] for record in records], [["hc-out/n2-root-hook.txt"], ["hc-out/r3-rule-challenge.txt"]])
            self.assertNotIn("private-test-content", json.dumps(records))

    def test_agent_host_approvals_are_scoped_to_disposable_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace = root / "ws"
            workspace.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (workspace / "hc-out").symlink_to(outside, target_is_directory=True)
            script = "const assert=require('node:assert/strict'); (async()=>{const {hcApproveFixtureTool:approve}=await import(process.argv[1]);const ws=process.argv[2];const call=(toolName,input)=>({toolName,toolInput:JSON.stringify(input)});assert.equal(approve(call('bash',{command:'echo hook-conformance-bash'}),ws),true);assert.equal(approve(call('bash',{command:'echo hook-conformance-bash; env'}),ws),false);assert.equal(approve(call('bash',{command:'rm hc-does-not-exist.txt',cwd:'/'}),ws),false);assert.equal(approve(call('create',{path:'.github/hooks/evil.json'}),ws),false);assert.equal(approve(call('create',{path:'hc-out/c0.txt'}),ws),false);assert.equal(approve(call('view',{path:'../outside'}),ws),false);assert.equal(approve(call('skill',{skill:'unreviewed'}),ws),false);require('node:fs').unlinkSync(ws+'/hc-out');require('node:fs').mkdirSync(ws+'/hc-out');assert.equal(approve(call('create',{path:'hc-out/c0.txt'}),ws),true);assert.equal(approve(call('skill',{skill:'hc-probe-skill'}),ws),true);assert.equal(approve(call('bash',{command:'env'}),''),false);})();"
            subprocess.run(["node", "-e", script, (SUITE / "fixture_permissions.mjs").as_uri(), str(workspace)], check=True, capture_output=True)
            worktree = root / "ws.worktrees/session"
            (worktree / "hc-out").mkdir(parents=True)
            script = "const assert=require('node:assert/strict'); (async()=>{const {hcApproveFixtureTool:approve}=await import(process.argv[1]);const ws=process.argv[2];const worktree=process.argv[3];assert.equal(approve({toolName:'view',toolInput:JSON.stringify({path:worktree})},ws),true);assert.equal(approve({toolName:'create',toolInput:JSON.stringify({path:worktree+'/hc-out/c0.txt'})},ws),true);})();"
            subprocess.run(["node", "-e", script, (SUITE / "fixture_permissions.mjs").as_uri(), str(workspace), str(worktree)], check=True, capture_output=True)
            script = "const assert=require('node:assert/strict'); (async()=>{const {hcApproveFixtureTool:approve}=await import(process.argv[1]);const ws=process.argv[2];for(const input of [{paths:['/etc/passwd']},{rootDir:'/etc'},{path:'README.md',cwd:'/etc'},{paths:[42]},{paths:'/etc'},{pattern:42},{glob:'../*'}])assert.equal(approve({toolName:'grep',toolInput:JSON.stringify(input)},ws),false);assert.equal(approve({toolName:'grep',toolInput:JSON.stringify({paths:['README.md','hc-out'],rootDir:ws,pattern:'test'})},ws),true);})();"
            subprocess.run(["node", "-e", script, (SUITE / "fixture_permissions.mjs").as_uri(), str(workspace)], check=True, capture_output=True)

    def fake_copilot(self, directory):
        executable = directory / "copilot"
        executable.write_text("""#!/usr/bin/env python3
import os
from pathlib import Path
import sys
import time
args = sys.argv[1:]
if args == ["--version"]:
    if os.environ.get("CLI_MODE") == "setup-error":
        sys.exit(17)
    print("Copilot CLI 1.0")
    sys.exit(0)
if args and args[0] == "plugin":
    sys.exit(0)
share = args[args.index("--share") + 1]
Path(share).write_text("partial transcript")
flag = os.environ.get("CLI_START_FLAG")
if flag:
    Path(flag).write_text("started")
if os.environ.get("CLI_MODE") in {"timeout", "signal"}:
    time.sleep(20)
sys.exit(int(os.environ.get("CLI_EXIT", "0")))
""")
        executable.chmod(0o755)
        return executable

    def run_fake_cli(self, root, executable, **extra):
        (root / "runner-temp").mkdir(exist_ok=True)
        env = {
            **os.environ,
            "COPILOT_GITHUB_TOKEN": "synthetic-token-for-tests",
            "COPILOT_BIN": str(executable),
            "OUT_DIR": str(root / "out"),
            "RUNNER_TEMP": str(root / "runner-temp"),
            "SESSIONS": "repo",
            **extra,
        }
        return subprocess.run(["bash", str(SUITE / "run-cli.sh")], env=env, capture_output=True, text=True)

    def fake_vscode_tools(self, directory):
        fake_bin = directory / "bin"
        fake_bin.mkdir()
        code = fake_bin / "code"
        code.write_text("""#!/usr/bin/env python3
import os
import sys
import time
args = sys.argv[1:]
if args == ["--version"]:
    print("1.2.3 (commit " + "a" * 40 + ")")
elif args[:2] == ["agent", "host"]:
    print("[abcdef0]: Server ready", flush=True)
    with open(os.environ["HOST_PID_FILE"], "w") as stream:
        stream.write(str(os.getpid()))
    time.sleep(30)
elif args[:2] == ["agent", "kill"]:
    open(os.environ["KILL_MARKER"], "w").write("called")
""")
        code.chmod(0o755)
        node = fake_bin / "node"
        node.write_text("""#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys
import time
args = sys.argv[1:]
if "connect" in args:
    deadline = time.monotonic() + 3
    while not Path(os.environ["HOST_PID_FILE"]).exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    status = int(os.environ.get("NODE_CONNECT_EXIT", "0"))
    if status:
        sys.exit(status)
    print(json.dumps({"agents": [{"provider": "copilotcli", "models": [{}]}]}))
elif "exec" in args:
    agent = os.environ.get("HC_AGENT_NAME")
    print("partial AHPX evidence", flush=True)
    if not agent and os.environ.get("AHPX_SLEEP"):
        time.sleep(int(os.environ["AHPX_SLEEP"]))
    agent_exit = os.environ.get("AGENT_NS_EXIT", "0") if agent == "hc-probe-ns-agent" else os.environ.get("AGENT_LEGACY_EXIT", "0")
    sys.exit(int(agent_exit if agent else os.environ.get("AHPX_EXEC_EXIT", "0")))
""")
        node.chmod(0o755)
        npm = fake_bin / "npm"
        npm.write_text("\n".join([
            "#!/usr/bin/env python3",
            "from pathlib import Path",
            "import shutil, sys",
            "root = Path(__file__).resolve().parents[1]",
            "prefix = Path(sys.argv[sys.argv.index('--prefix') + 1])",
            "shutil.copytree(root / 'node_modules', prefix / 'node_modules')",
        ]) + "\n")
        npm.chmod(0o755)
        modules = directory / "node_modules"
        (modules / ".bin").mkdir(parents=True)
        (modules / ".bin/ahpx").write_text("#!/bin/sh\nexit 0\n")
        (modules / ".bin/ahpx").chmod(0o755)
        ahpx = modules / "@tylerl0706/ahpx/dist/bin.js"
        ahpx.parent.mkdir(parents=True)
        ahpx.write_text("""import { createHash } from "node:crypto";
const path4 = { delimiter: ":" };
        path4.delimiter;
        async function discoverCustomizations(cwd) {
  const refs = [];
}
        this.allowedPaths.add(filePath);
    switch (method) {
      case "resourceRead": {
      }
            await client.disposeSession(sessionUri);
      const chatUri = await resolveChatChannel(client, sessionUri);
          ...this.model ? { model: { id: this.model } } : {},
""" + '      const content = await fs2.readFile(filePath);\n      return {\n        data: content.toString("base64"),\n  async handleToolConfirmation(toolCall) {\n')
        return code, node, modules

    def run_fake_vscode(self, root, code, modules, **extra):
        runner_temp = root / "runner-temp"
        runner_temp.mkdir(exist_ok=True)
        env = {
            **os.environ,
            "PATH": f"{code.parent}:{os.environ['PATH']}",
            "CODE_BIN": str(code),
            "COPILOT_GITHUB_TOKEN": "synthetic-token-for-tests",
            "AHPX_NODE_MODULES": str(modules),
            "OUT_DIR": str(root / "out"),
            "RUNNER_TEMP": str(runner_temp),
            "SESSIONS": "plugin",
            "HOST_PID_FILE": str(root / "host.pid"),
            "KILL_MARKER": str(root / "global-kill-called"),
            "HOST_READY_ATTEMPTS": "1",
            "HOST_RETRY_DELAY": "0",
            **extra,
        }
        return subprocess.run(["bash", str(SUITE / "run-vscode.sh")], env=env, capture_output=True, text=True)

    def test_testing_method_lives_with_the_suite(self):
        root = SUITE.parents[1]
        skill = root / ".github/skills/plugin-surface-testing/SKILL.md"
        reference = skill.parent / "references/compatibility.md"
        self.assertIn("name: plugin-surface-testing", skill.read_text())
        self.assertIn("./references/compatibility.md", skill.read_text())
        self.assertTrue(reference.is_file())
        readme = (SUITE / "README.md").read_text()
        self.assertIn("../../.github/skills/plugin-surface-testing/SKILL.md", readme)
        for text in (skill.read_text(), reference.read_text(), readme):
            self.assertNotIn("github/services-toolbox", text)
            self.assertNotIn("github/amer-es-nes", text)

    def test_cloud_agent_rejection_requires_a_working_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "hc-out"
            output.mkdir()
            control = root / "agents/control"
            (control / "hc-out").mkdir(parents=True)
            (control / "agent-selection.json").write_text(json.dumps({"completed": True}))
            (control / "hc-out/agent-legacy.txt").write_text("AGENT_LEGACY")
            for case in ("A1", "A2"):
                (root / "agents" / case).mkdir()
                (root / "agents" / case / "agent-selection.json").write_text(json.dumps({"completed": False, "rejected": True, "issue": "123"}))
            command = [sys.executable, str(SUITE / "score.py"), "--surface", "cloud-agent", "--session", "plugin",
                       "--log", str(root / "probe.jsonl"), "--out-dir", str(output), "--json", str(root / "score.json")]
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case["result"] for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["A1"], "DEVIATION")
            (control / "agent-selection.json").write_text(json.dumps({"completed": False}))
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case["result"] for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["A1"], "NOT RUN")

    def test_observer_preserves_output_and_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            command = "printf '%s' '{\"permissionDecision\":\"deny\"}'; printf 'diagnostic' >&2; exit 2"
            encoded = base64.b64encode(command.encode()).decode()
            result = subprocess.run([sys.executable, str(SUITE / "observe_hook.py"), encoded, "preToolUse", "0"],
                                    input=json.dumps({"cwd": str(root), "sessionId": "fake-session",
                                                      "toolName": "create", "toolArgs": {
                                                          "path": "hc-out/p1.md", "content": "fake-sensitive-content"}}),
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '{"permissionDecision":"deny"}')
            self.assertEqual(result.stderr, "diagnostic")
            record = json.loads((root / ".hook-conformance/plugin-guards.jsonl").read_text())
            self.assertEqual(record["exit_code"], result.returncode)
            self.assertEqual(record["decision"], {"permissionDecision": "deny"})
            self.assertEqual(record["targets"], ["hc-out/p1.md"])
            self.assertNotIn("raw", record)
            self.assertNotIn("fake-sensitive-content", json.dumps(record))

    def test_cloud_marketplace_keeps_plugin_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "plugin.json").write_text('{"name":"actions-migrator","version":"1.0.0"}')
            (source / "hooks.json").write_text('{"version":1,"hooks":{}}')
            subprocess.run([sys.executable, str(SUITE / "make_probes.py"), str(root / "marketplace"),
                            "--include-plugin", str(source), "--source-sha", "a" * 40], check=True)
            published = root / "marketplace/plugins/actions-migrator/hooks.json"
            self.assertEqual(published.read_bytes(), (source / "hooks.json").read_bytes())
            provenance = json.loads((root / "marketplace/fixture-source.json").read_text())
            self.assertIn("plugins/actions-migrator/hooks.json", provenance["files_sha256"])

    def test_cloud_sessions_enable_only_their_own_plugins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for session, expected in (("repo", {"actions-migrator@hc-probes"}),
                                      ("plugin", {"hc-probe-a@hc-probes", "hc-probe-b@hc-probes", "hc-probe-ns@hc-probes"}),
                                      ("none", set())):
                configure(root, session, "example/test-marketplace")
                settings = json.loads((root / ".github/copilot/settings.json").read_text())
                actual = {name for name, enabled in settings["enabledPlugins"].items() if enabled}
                self.assertEqual(actual, expected)
                self.assertEqual(settings["extraKnownMarketplaces"]["hc-probes"]["source"]["repo"], "example/test-marketplace")

    def test_cloud_preflight_rejects_wrong_default_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configure(root, "plugin", "example/test-marketplace")
            command = [sys.executable, str(SUITE / "cloud_settings.py"), "--check",
                       str(root / ".github/copilot/settings.json"), "repo", "example/test-marketplace"]
            result = subprocess.run(command, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            command[-2] = "plugin"
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_artifacts_exclude_catalog_and_redact_tokens(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "input"
            source.mkdir()
            (source / "connect.json").write_text('{"models": ["private-model"]}')
            gh_tokens = [prefix + letter * 36 for prefix, letter in (
                ("ghp_", "a"), ("gho_", "b"), ("ghu_", "c"), ("ghs_", "d"),
                ("ghr_", "e"), ("github_pat_", "f"),
            )]
            runtime_values = {
                "ACTIONS_RUNTIME_TOKEN": "runtime-test-token-123456",
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "oidc-test-token-123456",
                "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.test/oidc?token=runtime-query-secret",
                "ACTIONS_CACHE_URL": "https://example.test/cache?token=cache-query-secret",
            }
            log = "ws://localhost?tkn=local-test-value\n" + "Synthetic" + "Probe12345abcdef"
            log += "\n" + "\n".join(gh_tokens)
            log += "\nAuthorization: " + "header-test-value"
            log += "\nAuthorization: " + "Bearer " + "bearer-test-token"
            log += '\n{"Authorization": "Basic ' + "basic-test-token" + '"}'
            log += "\n" + "\n".join(f"{key}={value}" for key, value in runtime_values.items())
            log += "\nCOPILOT_GITHUB_TOKEN=environment-test-token"
            (source / "session.log").write_text(log)
            (source / "score.json").write_text(json.dumps({"message": log}))
            with patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "environment-test-token"}):
                publish(source, root / "published")
            self.assertFalse((root / "published/connect.json").exists())
            self.assertFalse((root / "published/session.log").exists())
            published = json.loads((root / "published/score.json").read_text())["message"]
            self.assertIn("ws://localhost?tkn=REDACTED", published)
            self.assertIn("[fake-credential]", published)
            for value in gh_tokens + list(runtime_values.values()) + [
                "bearer-test-token", "basic-test-token", "environment-test-token",
            ]:
                self.assertNotIn(value, published)
            self.assertIn("Authorization: [redacted]", published)
            self.assertIn('"Authorization": "[redacted]"', published)
            self.assertIn("ACTIONS_RUNTIME_TOKEN=[redacted]", published)
            self.assertIn("ACTIONS_ID_TOKEN_REQUEST_URL=[redacted]", published)

    def test_reports_do_not_count_as_test_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            log = root / "mirror.jsonl"
            payload = {"cwd": str(root), "toolName": "create", "toolArgs": {
                "path": "hook-results.md", "content": "hc-out/c2.txt HC_M2"}}
            result = subprocess.run([sys.executable, str(SUITE / "kit/probe.py"), "pre1"],
                                    input=json.dumps(payload), text=True, capture_output=True,
                                    env={**os.environ, "HC_FALLBACK_LOG": str(log)}, check=True)
            record = json.loads(log.read_text())
            self.assertEqual(record["markers"], [])
            self.assertEqual(result.stdout, "")
            self.assertNotIn("raw", record)
            self.assertNotIn("HC_M2", log.read_text())

    def test_actual_case_records_hook_decision_and_mirror(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            mirror = root / "mirror.jsonl"
            payload = {"workingDirectory": str(root), "toolName": "create", "toolArgs": {
                "path": "hc-out/c2.txt", "content": "HC_M2"}}
            result = subprocess.run([sys.executable, str(SUITE / "kit/probe.py"), "pre2"],
                                    input=json.dumps(payload), text=True, capture_output=True,
                                    env={**os.environ, "HC_FALLBACK_LOG": str(mirror)}, check=True)
            self.assertEqual(json.loads(result.stdout)["permissionDecision"], "deny")
            record = json.loads(mirror.read_text())
            self.assertEqual(record["action"], "deny-C2")
            self.assertEqual(record["markers"], ["2"])
            self.assertNotIn("raw", record)
            self.assertNotIn("HC_M2", mirror.read_text())
            self.assertEqual(mirror.read_text(), (root / ".hook-conformance/probe.jsonl").read_text())

    def test_artifact_symlinks_and_outside_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "input"
            source.mkdir()
            outside = root / "outside.log"
            outside.write_text("fake")
            (source / "score.json").symlink_to(outside)
            with self.assertRaises(ValueError):
                publish(source, root / "published")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "input"
            source.mkdir()
            outside = root / "outside.log"
            outside.write_text("fake")
            os.link(outside, source / "score.json")
            with self.assertRaises(ValueError):
                publish(source, root / "published")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "input"
            (source / "nested").mkdir(parents=True)
            (source / "nested/score.json").write_text("{}")
            outside = root / "outside"
            outside.mkdir()
            destination = root / "published"
            destination.mkdir()
            (destination / "nested").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                publish(source, destination)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "input"
            source.mkdir()
            (source / "score.json").write_text("{}")
            alias = root / "input-link"
            alias.symlink_to(source, target_is_directory=True)
            result = subprocess.run([sys.executable, str(SUITE / "sanitize_artifacts.py"), str(alias), str(root / "published")], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_artifacts_reject_raw_payloads_and_invalid_structured_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "input"
            source.mkdir()
            for content in ('{"raw":{"secret":"private"}}', "not-json"):
                (source / "score.json").write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    publish(source, root / "published")

    def test_cli_runner_has_narrow_unattended_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copilot = root / "copilot"
            copilot.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "if sys.argv[1:] == ['--version']:\n"
                "    print('Copilot CLI test stub')\n"
                "else:\n"
                "    with open(os.environ['COPILOT_ARGS_LOG'], 'a') as log:\n"
                "        log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            )
            copilot.chmod(0o755)
            args_log = root / "copilot-args.jsonl"
            result = subprocess.run(["bash", str(SUITE / "run-cli.sh")], env={
                **os.environ,
                "COPILOT_GITHUB_TOKEN": "fake-copilot-token",
                "COPILOT_BIN": str(copilot),
                "COPILOT_ARGS_LOG": str(args_log),
                "OUT_DIR": str(root / "out"),
                "RUNNER_TEMP": str(root),
                "SESSIONS": "repo",
            }, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in args_log.read_text().splitlines()]
            session = next(call for call in calls if "--output-format" in call)
            self.assertIn("--available-tools", session)
            self.assertIn("bash,create,edit,view,grep,glob,skill", session)
            self.assertIn("shell(echo hook-conformance-bash)", session)
            self.assertIn("shell(rm hc-does-not-exist.txt)", session)
            self.assertNotIn("--allow-all-tools", session)
            self.assertNotIn("--add-dir", session)
            self.assertNotIn("/tmp", session)
            self.assertIn("rm hc-does-not-exist.txt", session[session.index("-p") + 1])

    def test_missing_files_alone_do_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "score.json"
            subprocess.run([sys.executable, str(SUITE / "score.py"), "--surface", "cli",
                            "--session", "repo", "--log", str(root / "absent.jsonl"),
                            "--out-dir", str(root), "--json", str(report)],
                           check=True, capture_output=True)
            self.assertTrue(all(case["result"] == "NOT RUN" for case in json.loads(report.read_text())["cases"]))

    def test_missing_surface_is_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run([sys.executable, str(SUITE / "summarize.py"), "--scores", str(root),
                            "--expect", "cli,vscode", "--out", str(root / "summary")],
                           check=True, capture_output=True)
            summary = json.loads((root / "summary/results.json").read_text())
            self.assertEqual(len(summary["missing"]), 4)

    def test_valid_scores_do_not_hide_a_failed_upstream_job(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = {
                "repo": ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10", "C9", "P1"),
                "plugin": ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8b", "C10",
                           "N1", "N2", "S1", "S2", "R1", "R2", "R3", "A1", "A2"),
            }
            for surface in ("cli", "vscode"):
                for session, names in cases.items():
                    score_dir = root / surface / session
                    score_dir.mkdir(parents=True)
                    (score_dir / "score.json").write_text(json.dumps({
                        "meta": {"cli_exit": "37"} if surface == "cli" and session == "repo" else {},
                        "cases": [{"case": name, "expected": name, "result": "PASS", "observed": "evidence"}
                                  for name in names]
                    }))
            result = subprocess.run([
                sys.executable, str(SUITE / "summarize.py"), "--scores", str(root), "--expect", "cli,vscode",
                "--job-result", "target=success", "--job-result", "offline=failure", "--job-result", "cli=success", "--job-result", "vscode=success",
                "--out", str(root / "summary"),
            ], capture_output=True, text=True, check=True)
            summary = json.loads((root / "summary/results.json").read_text())
            self.assertIn("execution_failed=1", result.stdout)
            self.assertIn("upstream_failed=1", result.stdout)
            self.assertEqual(summary["unexpected"], [])
            self.assertEqual(summary["missing"], [])
            self.assertEqual(summary["not_run"], [])
            self.assertEqual(summary["execution_failures"], ["Copilot CLI repo cli_exit=37"])
            self.assertEqual(summary["upstream_failed"], ["offline: failure"])

    def test_malformed_score_artifact_fails_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            score = root / "cli/repo/score.json"
            score.parent.mkdir(parents=True)
            score.write_text("{not-json")
            result = subprocess.run([
                sys.executable, str(SUITE / "summarize.py"), "--scores", str(root), "--expect", "cli",
                "--out", str(root / "summary"),
            ], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_nonzero_cli_exit_keeps_partial_score_and_fails_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self.fake_copilot(root)
            result = self.run_fake_cli(root, executable, CLI_EXIT="37")
            score = json.loads((root / "out/cli/repo/score.json").read_text())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(score["meta"]["cli_exit"], "37")
            self.assertTrue((root / "out/cli/repo/transcript.md").is_file())
            self.assertTrue(all(case["result"] == "NOT RUN" for case in score["cases"]))

    def test_cli_timeout_keeps_partial_evidence_and_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self.fake_copilot(root)
            result = self.run_fake_cli(root, executable, CLI_MODE="timeout", CLI_TIMEOUT="1")
            score = json.loads((root / "out/cli/repo/score.json").read_text())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(score["meta"]["cli_exit"], "124")
            self.assertTrue((root / "out/cli/repo/transcript.md").is_file())

    def test_term_cancellation_scores_partial_evidence_and_fails_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self.fake_copilot(root)
            flag = root / "started"
            (root / "runner-temp").mkdir()
            env = {
                **os.environ,
                "COPILOT_GITHUB_TOKEN": "synthetic-token-for-tests",
                "COPILOT_BIN": str(executable),
                "OUT_DIR": str(root / "out"),
                "RUNNER_TEMP": str(root / "runner-temp"),
                "SESSIONS": "repo",
                "CLI_MODE": "signal",
                "CLI_START_FLAG": str(flag),
            }
            process = subprocess.Popen(
                ["bash", str(SUITE / "run-cli.sh")], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            deadline = time.monotonic() + 10
            while not flag.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(flag.exists(), "fake CLI did not start")
            process.send_signal(signal.SIGTERM)
            _, stderr = process.communicate(timeout=10)
            self.assertNotEqual(process.returncode, 0)
            self.assertNotIn("Traceback", stderr)
            score = json.loads((root / "out/cli/repo/score.json").read_text())
            self.assertEqual(score["meta"]["interrupt_exit"], "143")
            self.assertTrue((root / "out/cli/repo/transcript.md").is_file())

    def test_ahpx_and_selected_agent_failures_preserve_status_and_owned_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, node, modules = self.fake_vscode_tools(root)
            result = self.run_fake_vscode(root, code, modules, AHPX_EXEC_EXIT="31",
                                          AGENT_LEGACY_EXIT="41", AGENT_NS_EXIT="42")
            score = json.loads((root / "out/vscode/plugin/score.json").read_text())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(score["meta"]["ahpx_exit"], "31")
            self.assertEqual(score["meta"]["agent_legacy_exit"], "41")
            self.assertEqual(score["meta"]["agent_ns_exit"], "42")
            self.assertTrue((root / "out/vscode/plugin/session.log").is_file())
            self.assertFalse((root / "global-kill-called").exists())
            host_pid = int((root / "host.pid").read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(host_pid, 0)

    def test_ahpx_connection_error_is_scored_and_fails_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, node, modules = self.fake_vscode_tools(root)
            result = self.run_fake_vscode(root, code, modules, NODE_CONNECT_EXIT="23")
            score = json.loads((root / "out/vscode/plugin/score.json").read_text())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(score["meta"]["setup_exit"], "23")
            self.assertEqual(score["meta"]["signed_in"], "0")
            self.assertTrue((root / "out/vscode/plugin/connect.json").is_file())

    def test_ahpx_timeout_keeps_partial_session_log_and_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, node, modules = self.fake_vscode_tools(root)
            result = self.run_fake_vscode(root, code, modules, AHPX_SLEEP="20", AHPX_TIMEOUT="1")
            score = json.loads((root / "out/vscode/plugin/score.json").read_text())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(score["meta"]["ahpx_exit"], "124")
            self.assertIn("partial AHPX evidence", (root / "out/vscode/plugin/session.log").read_text())

    def test_cli_setup_error_is_not_reported_as_a_test_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self.fake_copilot(root)
            result = self.run_fake_cli(root, executable, CLI_MODE="setup-error")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("version check failed (exit=17)", (root / "out/cli/setup.log").read_text())

    def test_cloud_cleanup_is_owned_scoped_and_reports_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            gh = fake_bin / "gh"
            gh.write_text("""#!/usr/bin/env python3
import os
import sys
args = sys.argv[1:]
with open(os.environ["GH_CALL_LOG"], "a") as log:
    log.write(" ".join(args) + "\\n")
if args[:2] == ["pr", "view"]:
    print(os.environ["GH_PR_DETAILS"])
if os.environ.get("GH_FAIL") and os.environ["GH_FAIL"] in args:
    sys.exit(9)
""")
            gh.chmod(0o755)
            call_log = root / "gh-calls.log"
            cleanup_log = root / "cleanup.log"
            env = {
                **os.environ,
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "GH_CALL_LOG": str(call_log),
                "GH_PR_DETAILS": "copilot/owned\tsurface-run/123",
            }
            command = [
                "bash", "-c",
                'source "$1"; shift; cleanup_cloud_resources "$@"',
                "bash", str(SUITE / "common.sh"), "example/repo", "surface-run/123", "101", "42",
                "copilot/owned", "1", "1", "1", "1", str(cleanup_log),
            ]
            self.assertEqual(subprocess.run(command, env=env).returncode, 0)
            calls = call_log.read_text()
            self.assertIn("pr close 42 --repo example/repo", calls)
            self.assertIn("issue close 101 --repo example/repo", calls)
            self.assertIn("git/refs/heads/surface-run/123", calls)
            self.assertNotIn("--delete-branch", calls)
            self.assertNotIn("git/refs/heads/copilot/owned", calls)

            call_log.unlink()
            env["GH_PR_DETAILS"] = "other-user/branch\tsurface-run/123"
            result = subprocess.run(command, env=env)
            self.assertNotEqual(result.returncode, 0)
            calls = call_log.read_text()
            self.assertNotIn("pr close", calls)
            self.assertNotIn("git/refs/heads/surface-run/123", calls)
            self.assertIn("ownership could not be confirmed", cleanup_log.read_text())

            call_log.unlink()
            cleanup_log.unlink()
            command[13] = "0"
            result = subprocess.run(command, env=env)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(call_log.exists())
            self.assertIn("remote task may still be active", cleanup_log.read_text())

            call_log.unlink(missing_ok=True)
            cleanup_log.unlink()
            command[13] = "1"
            env["GH_PR_DETAILS"] = "copilot/owned\tsurface-run/123"
            env["GH_FAIL"] = "close"
            result = subprocess.run(command, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Cleanup failed to close owned pull request", cleanup_log.read_text())

    def test_n2_and_r3_need_their_own_negative_challenge_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "hc-out"
            output.mkdir()
            (output / "skill-ns.txt").write_text("SKILL_NS")
            (output / "rule-ns.txt").write_text("RULE_NS")
            log = root / "probe.jsonl"
            log.write_text(json.dumps({"label": "ns:sessionStart", "event": "sessionStart", "raw": {}}) + "\n")
            command = [
                sys.executable, str(SUITE / "score.py"), "--surface", "cli", "--session", "plugin",
                "--log", str(log), "--out-dir", str(output), "--json", str(root / "score.json"),
            ]
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case["result"] for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["N2"], "NOT RUN")
            self.assertEqual(cases["R3"], "NOT RUN")

            challenge_rows = [
                {"label": "ns:preToolUse", "event": "preToolUse",
                 "raw": {"toolArgs": {"path": "hc-out/n2-root-hook.txt"}}},
                {"label": "ns:preToolUse", "event": "preToolUse",
                 "raw": {"toolArgs": {"path": "hc-out/r3-rule-challenge.txt"}}},
            ]
            log.write_text("".join(json.dumps(row) + "\n" for row in challenge_rows))
            (output / "n2-root-hook.txt").write_text("N2_CHALLENGE")
            (output / "r3-rule-challenge.txt").write_text("R3_CHALLENGE")
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case["result"] for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["N2"], "PASS")
            self.assertEqual(cases["R3"], "PASS")
            challenge_rows.append({
                "label": "ns-root:preToolUse", "event": "preToolUse",
                "raw": {"toolArgs": {"path": "hc-out/n2-root-hook.txt"}},
            })
            log.write_text("".join(json.dumps(row) + "\n" for row in challenge_rows))
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case["result"] for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["N2"], "DEVIATION")
            self.assertEqual(cases["R3"], "PASS")

            (output / "rule-ns.txt").unlink()
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["R3"]["result"], "NOT RUN")
            self.assertEqual(cases["R3"]["reason_code"], "rule_positive_control_missing")
            (output / "r3-rule-challenge.txt").unlink()
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["R3"]["reason_code"], "challenge_evidence_incomplete")
            (output / "r3-rule-challenge.txt").write_text("R3_CHALLENGE")
            (output / "rule-nsroot.txt").write_text("RULE_NSROOT")
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["R3"]["reason_code"], "challenge_evidence_incomplete")

    def test_agent_report_cannot_prove_secret_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "hook-results.md"
            report.write_text("Denied by preToolUse hook: likely credential value in proposed output")
            subprocess.run([sys.executable, str(SUITE / "score.py"), "--surface", "cli",
                            "--session", "repo", "--log", str(root / "absent.jsonl"),
                            "--out-dir", str(root), "--json", str(root / "score.json"),
                            "--transcript", str(report)], check=True, capture_output=True)
            result = json.loads((root / "score.json").read_text())
            self.assertEqual(next(case["result"] for case in result["cases"] if case["case"] == "P1"), "NOT RUN")

    def test_forged_transcript_denial_is_not_guard_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "session.log"
            events = root / "events.jsonl"
            transcript.write_text("Denied by preToolUse hook: likely credential value in proposed output\n")
            events.write_text(json.dumps({
                "type": "assistant.message",
                "data": {"content": "Denied by preToolUse hook: likely credential value in proposed output"},
            }) + "\n")
            subprocess.run([sys.executable, str(SUITE / "score.py"), "--surface", "vscode",
                            "--session", "repo", "--log", str(root / "absent.jsonl"),
                            "--out-dir", str(root), "--json", str(root / "score.json"),
                            "--transcript", str(transcript), "--transcript", str(events)],
                           check=True, capture_output=True)
            result = json.loads((root / "score.json").read_text())
            self.assertEqual(next(case["result"] for case in result["cases"] if case["case"] == "P1"), "NOT RUN")

    def test_structured_tool_denial_is_correlated_to_the_requested_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "events.jsonl"
            events = [
                {"type": "tool.execution_start", "data": {
                    "toolCallId": "p1-call", "arguments": {"path": "hc-out/p1.md"}}},
                {"type": "tool.execution_complete", "data": {
                    "toolCallId": "p1-call", "success": False,
                    "error": {"message": "Denied by preToolUse hook: likely credential value in proposed output"}}},
            ]
            transcript.write_text("\n".join(json.dumps(event) for event in events))
            subprocess.run([sys.executable, str(SUITE / "score.py"), "--surface", "vscode",
                            "--session", "repo", "--log", str(root / "absent.jsonl"),
                            "--out-dir", str(root), "--json", str(root / "score.json"),
                            "--transcript", str(transcript)], check=True, capture_output=True)
            result = json.loads((root / "score.json").read_text())
            self.assertEqual(next(case["result"] for case in result["cases"] if case["case"] == "P1"), "PASS")

    def test_isolated_rule_fixtures_contain_one_rule_and_neutral_prompt(self):
        prompt = (SUITE / "prompt-rule.md").read_text()
        self.assertNotIn("RULE_LEGACY", prompt)
        self.assertNotIn("RULE_NS", prompt)
        self.assertNotIn("rule-marker.txt", prompt)
        for rule_format, relative_rule in (
                ("current", Path("rules/hc-rule-probe.mdc")),
                ("namespace", Path("com.github.copilot/rules/hc-rule-probe.mdc"))):
            with self.subTest(rule_format=rule_format), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run([sys.executable, str(SUITE / "make_probes.py"), str(root),
                                "--rule-only", rule_format], check=True, capture_output=True)
                plugin_root = root / "plugins"
                self.assertEqual([path.name for path in plugin_root.iterdir()], ["hc-rule-probe"])
                plugin = plugin_root / "hc-rule-probe"
                self.assertEqual(
                    {path.relative_to(plugin) for path in plugin.rglob("*") if path.is_file()},
                    {Path("plugin.json"), relative_rule},
                )
                rule_text = (plugin / relative_rule).read_text()
                self.assertIn("alwaysApply: true", rule_text)
                self.assertIn("rule-marker.txt", rule_text)
                self.assertEqual((root / "rule-resource-path").read_text().strip(),
                                 str((plugin / relative_rule).resolve()))

    def test_rule_client_capture_keeps_only_marker_events(self):
        events = [
            {"type": "delta", "data": {"content": "unrelated-private-text"}},
            {"type": "tool_call_ready", "data": {"toolCallId": "read", "toolName": "view",
             "toolInput": json.dumps({"path": rule_evidence.TARGET})}},
            {"type": "tool_call_ready", "data": {"toolCallId": "write", "toolName": "create",
             "toolInput": json.dumps({"path": rule_evidence.TARGET, "content": "RULE_LEGACY"})}},
            {"type": "tool_call_complete", "data": {"toolCallId": "read", "result": {"success": True}}},
            {"type": "tool_call_complete", "data": {"toolCallId": "write", "result": {
                "success": True, "content": "unrelated-private-text"}}},
            {"type": "turn_complete", "data": {"responseText": "unrelated-private-text"}},
        ]
        stream = io.StringIO('Ready plugin components: [{"name":"hc-rule-probe"}]\n' +
                            "\n".join(json.dumps(event) for event in events))
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "events.jsonl"
            rule_evidence.capture_client_output(stream, destination)
            captured = list(rule_evidence.jsonl(destination))
            self.assertEqual([event["type"] for event in captured],
                             ["tool.execution_start", "tool.execution_complete", "session.complete"])
            self.assertEqual(captured[0]["data"]["arguments"], {"path": rule_evidence.TARGET})
            self.assertTrue(captured[1]["data"]["success"])
            self.assertNotIn("unrelated-private-text", destination.read_text())
            self.assertNotIn("RULE_LEGACY", destination.read_text())

    def test_rule_readiness_requires_the_client_side_channel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readiness = root / "plugin-ready.json"
            spoofed = 'Ready plugin components: [{"name":"hc-rule-probe"}]\n' + json.dumps({"type": "plugin_ready", "data": {"name": "hc-rule-probe"}})
            rule_evidence.capture_client_output(io.StringIO(spoofed), root / "events.jsonl")
            self.assertFalse(rule_evidence.plugin_ready(readiness))
            readiness.write_text(json.dumps({"ready": True, "names": ["hc-rule-probe"]}))
            self.assertTrue(rule_evidence.plugin_ready(readiness))
            readiness.write_text(json.dumps({"ready": True, "names": ["different-plugin"]}))
            self.assertFalse(rule_evidence.plugin_ready(readiness))

    def test_rule_evidence_separates_delivery_tool_and_marker_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            marker = workspace / "hc-out/rule-marker.txt"
            marker.parent.mkdir(parents=True)
            marker.write_text("RULE_LEGACY")
            rule_file = root / "rule.mdc"
            rule_file.write_text("the isolated rule")
            fixture_sha = hashlib.sha256(rule_file.read_bytes()).hexdigest()
            delivery = root / "delivery.jsonl"
            delivery.write_text(json.dumps({
                "resource_read": True, "sha256": fixture_sha, "matches_expected": True,
            }) + "\n")
            events = root / "events.jsonl"
            events.write_text("\n".join(json.dumps(event) for event in (
                {"type": "user.message", "data": {"content": "unrelated prompt text"}},
                {"type": "tool.execution_start", "data": {
                    "toolCallId": "call-1", "toolName": "create",
                    "arguments": {"path": "hc-out/rule-marker.txt", "content": "RULE_LEGACY"},
                }},
                {"type": "tool.execution_complete", "data": {
                    "toolCallId": "call-1", "success": True,
                }},
            )) + "\n")
            evidence = rule_evidence.assess(
                "current", delivery, events, workspace, fixture_sha,
                {"plugin_discovered": "true", "server_commit_matches_pin": "true",
                 "model_selector": "claude-haiku-4.5", "session_exit": "0"},
            )
            self.assertEqual(evidence["result"], "PASS")
            self.assertTrue(evidence["rule_resource"]["exact_fixture_text_returned"])
            self.assertEqual(evidence["model_delivery"]["status"], "not_observable")
            self.assertTrue(evidence["marker_tool"]["attempted"])
            self.assertEqual(evidence["marker_tool"]["calls"][0]["execution"], "succeeded")
            self.assertTrue(evidence["model_compliance"]["marker_instruction_followed"])
            self.assertTrue(evidence["marker_file"]["matches_expected"])
            self.assertTrue(evidence["evidence_collection"]["event_record_seen"])
            self.assertNotIn("unrelated prompt text", json.dumps(evidence))

            for session_exit in (None, "1", "124"):
                with self.subTest(session_exit=session_exit):
                    failed = rule_evidence.assess(
                        "current", delivery, events, workspace, fixture_sha,
                        {"plugin_discovered": "true", "server_commit_matches_pin": "true",
                         "session_exit": session_exit},
                    )
                    self.assertEqual(failed["result"], "NOT RUN")
                    self.assertEqual(failed["diagnosis"], "session did not complete")

            for tool, target, call_id, success, content in (
                    ("view", rule_evidence.TARGET, "read", True, "RULE_LEGACY"),
                    ("create", "report.md", "report", True, "RULE_LEGACY"),
                    ("create", rule_evidence.TARGET, None, True, "RULE_LEGACY"),
                    ("create", rule_evidence.TARGET, "failed", False, "RULE_LEGACY"),
                    ("create", rule_evidence.TARGET, "wrong-content", True, "NOT_RULE_LEGACY")):
                with self.subTest(tool=tool, target=target, call_id=call_id):
                    marker.write_text(content)
                    events.write_text("\n".join(json.dumps(event) for event in (
                        {"type": "tool.execution_start", "data": {
                            "toolCallId": call_id, "toolName": tool,
                            "arguments": {"path": target, "content": rule_evidence.TARGET},
                        }},
                        {"type": "tool.execution_complete", "data": {
                            "toolCallId": call_id, "success": success,
                        }},
                    )) + "\n")
                    rejected = rule_evidence.assess(
                        "current", delivery, events, workspace, fixture_sha,
                        {"plugin_discovered": "true", "server_commit_matches_pin": "true",
                         "session_exit": "0"},
                    )
                    self.assertEqual(rejected["result"], "DEVIATION")

            result = subprocess.run([
                sys.executable, str(SUITE / "rule_evidence.py"), "--format", "current",
                "--delivery-log", str(delivery), "--events", str(events),
                "--workspace", str(workspace), "--rule-file", str(rule_file),
                "--out", str(root / "result.json"),
                "--meta", "plugin_discovered=true", "--meta", "server_commit_matches_pin=true",
                "--meta", "session_exit=0",
            ], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads((root / "result.json").read_text())["result"], "DEVIATION")

    def test_rule_evidence_keeps_unobserved_delivery_and_noncompliance_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            marker = workspace / "hc-out/rule-marker.txt"
            marker.parent.mkdir(parents=True)
            marker.write_text("RULE_NS")
            rule_file = root / "rule.mdc"
            rule_file.write_text("the isolated rule")
            fixture_sha = hashlib.sha256(rule_file.read_bytes()).hexdigest()
            events = root / "events.jsonl"
            events.write_text(json.dumps({"type": "user.message", "data": {"content": "neutral"}}) + "\n")

            no_delivery = rule_evidence.assess(
                "namespace", root / "missing.jsonl", events, workspace, fixture_sha,
                {"plugin_discovered": "true"},
            )
            self.assertEqual(no_delivery["result"], "NOT RUN")
            self.assertFalse(no_delivery["rule_resource"]["exact_fixture_text_returned"])

            delivery = root / "delivery.jsonl"
            delivery.write_text(json.dumps({
                "resource_read": True, "sha256": fixture_sha, "matches_expected": True,
            }) + "\n")
            deviation = rule_evidence.assess(
                "namespace", delivery, events, workspace, fixture_sha,
                {"plugin_discovered": "true", "server_commit_matches_pin": "true",
                 "session_exit": "0"},
            )
            self.assertEqual(deviation["result"], "DEVIATION")
            self.assertEqual(deviation["diagnosis"], "unresolved")
            self.assertFalse(deviation["marker_tool"]["attempted"])
            self.assertFalse(deviation["model_compliance"]["marker_instruction_followed"])
            self.assertTrue(deviation["marker_file"]["matches_expected"])

            events.write_text(json.dumps({"type": "tool.execution_start", "data": {
                "toolCallId": "call-2", "toolName": "create",
                "arguments": {"path": "hc-out/rule-marker.txt"},
            }}) + "\n")
            incomplete = rule_evidence.assess(
                "namespace", delivery, events, workspace, fixture_sha,
                {"plugin_discovered": "true", "server_commit_matches_pin": "true",
                 "session_exit": "1"},
            )
            self.assertEqual(incomplete["result"], "NOT RUN")
            self.assertEqual(incomplete["diagnosis"], "session did not complete")

            delivery.write_text(json.dumps({
                "resource_read": True, "sha256": "0" * 64, "matches_expected": False,
            }) + "\n")
            wrong_rule = rule_evidence.assess(
                "namespace", delivery, events, workspace, fixture_sha,
                {"plugin_discovered": "true", "server_commit_matches_pin": "true",
                 "session_exit": "0"},
            )
            self.assertEqual(wrong_rule["result"], "DEVIATION")
            self.assertEqual(wrong_rule["diagnosis"], "rule content differed from fixture")

            wrong_server = rule_evidence.assess(
                "namespace", delivery, events, workspace, fixture_sha,
                {"plugin_discovered": "true", "server_commit_matches_pin": "false"},
            )
            self.assertEqual(wrong_server["result"], "NOT RUN")
            self.assertEqual(wrong_server["diagnosis"], "Agent Host server did not match the requested commit")
    def test_structured_hook_decision_requires_a_call_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            probe_log = root / "probe.jsonl"
            probe_record = {
                "label": "pre1",
                "event": "preToolUse",
                "markers": [],
                "tool": "create",
                "payload_keys": [],
                "targets": ["hc-out/p1.md"],
                "call": "a" * 64,
            }
            probe_log.write_text(json.dumps(probe_record) + "\n")
            guard_log = root / "plugin-guards.jsonl"
            record = {
                "event": "preToolUse",
                "exit_code": 0,
                "decision": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "likely credential value in proposed output",
                },
                "targets": ["hc-out/p1.md"],
                "call": "a" * 64,
            }
            guard_log.write_text(json.dumps(record) + "\n")
            command = [sys.executable, str(SUITE / "score.py"), "--surface", "cli", "--session", "repo",
                       "--log", str(probe_log), "--out-dir", str(root),
                       "--json", str(root / "score.json")]
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case["result"] for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["P1"], "PASS")

            record["call"] = "not-a-call-id"
            guard_log.write_text(json.dumps(record) + "\n")
            subprocess.run(command, check=True, capture_output=True)
            cases = {case["case"]: case["result"] for case in json.loads((root / "score.json").read_text())["cases"]}
            self.assertEqual(cases["P1"], "NOT RUN")

    def test_ahpx_install_uses_a_locked_scriptless_dependency_tree(self):
        package = json.loads((SUITE / "ahpx/package.json").read_text())
        lock = json.loads((SUITE / "ahpx/package-lock.json").read_text())
        ahpx = lock["packages"]["node_modules/@tylerl0706/ahpx"]
        uuid = lock["packages"]["node_modules/uuid"]
        runner = (SUITE / "common.sh").read_text()
        self.assertEqual(package["dependencies"]["@tylerl0706/ahpx"], "0.6.0")
        self.assertEqual(ahpx["version"], "0.6.0")
        self.assertTrue(ahpx["integrity"].startswith("sha512-"))
        self.assertGreaterEqual(tuple(map(int, uuid["version"].split("."))), (11, 1, 1))
        self.assertIn('local -a npm_env=("PATH=$PATH" "HOME=$installation_root/npm-home")', runner)
        self.assertIn('env -i "${npm_env[@]}" npm ci --ignore-scripts', runner)
        self.assertIn("npm ci --ignore-scripts", runner)
        self.assertNotIn("AHPX_NODE_MODULES", runner)
        for name in ("run-vscode.sh", "run-vscode-rule.sh"):
            source = (SUITE / name).read_text()
            self.assertIn('prepare_ahpx "$ROOT"', source)
            self.assertNotIn("--approve-all", source)
            self.assertIn("--deny-all", source)


if __name__ == "__main__":
    unittest.main()