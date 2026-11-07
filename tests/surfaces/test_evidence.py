import json
import base64
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from sanitize_artifacts import publish
from cloud_settings import configure


SUITE = Path(__file__).resolve().parent


class EvidenceTests(unittest.TestCase):
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
        modules = directory / "node_modules"
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
""")
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
                                    input=json.dumps({"cwd": str(root)}), text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '{"permissionDecision":"deny"}')
            self.assertEqual(result.stderr, "diagnostic")
            record = json.loads((root / ".hook-conformance/plugin-guards.jsonl").read_text())
            self.assertEqual(record["stdout"], result.stdout)
            self.assertEqual(record["exit_code"], result.returncode)

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
            root = Path(directory)
            source = root / "input"
            source.mkdir()
            (source / "connect.json").write_text('{"models": ["private-model"]}')
            (source / "session.log").write_text("ws://localhost?tkn=local-test-value\n" + "Synthetic" + "Probe12345abcdef")
            publish(source, root / "published")
            self.assertFalse((root / "published/connect.json").exists())
            self.assertEqual((root / "published/session.log").read_text(), "ws://localhost?tkn=REDACTED\n[fake-credential]")

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
            self.assertEqual(record["raw"], payload)

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
            self.assertEqual(mirror.read_text(), (root / ".hook-conformance/probe.jsonl").read_text())

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
                "--job-result", "target=success", "--job-result", "cli=failure", "--job-result", "vscode=success",
                "--out", str(root / "summary"),
            ], capture_output=True, text=True, check=True)
            summary = json.loads((root / "summary/results.json").read_text())
            self.assertIn("execution_failed=1", result.stdout)
            self.assertIn("upstream_failed=1", result.stdout)
            self.assertEqual(summary["unexpected"], [])
            self.assertEqual(summary["missing"], [])
            self.assertEqual(summary["not_run"], [])
            self.assertEqual(summary["execution_failures"], ["Copilot CLI repo cli_exit=37"])
            self.assertEqual(summary["upstream_failed"], ["cli: failure"])

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

    def test_terminal_colors_do_not_hide_guard_denials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "session.log"
            transcript.write_text("  \x1b[2mDenied by preToolUse hook: Blocked: likely credential value in proposed output\x1b[22m\n")
            subprocess.run([sys.executable, str(SUITE / "score.py"), "--surface", "vscode",
                            "--session", "repo", "--log", str(root / "absent.jsonl"),
                            "--out-dir", str(root), "--json", str(root / "score.json"),
                            "--transcript", str(transcript)], check=True, capture_output=True)
            result = json.loads((root / "score.json").read_text())
            self.assertEqual(next(case["result"] for case in result["cases"] if case["case"] == "P1"), "PASS")


if __name__ == "__main__":
    unittest.main()