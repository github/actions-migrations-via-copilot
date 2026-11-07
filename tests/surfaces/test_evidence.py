import json
import base64
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from sanitize_artifacts import publish
from cloud_settings import configure


SUITE = Path(__file__).resolve().parent


class EvidenceTests(unittest.TestCase):
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
            root = Path(directory)
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
            with patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "environment-test-token"}):
                publish(source, root / "published")
            self.assertFalse((root / "published/connect.json").exists())
            published = (root / "published/session.log").read_text()
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
            root = Path(directory)
            source = root / "input"
            source.mkdir()
            outside = root / "outside.log"
            outside.write_text("fake")
            (source / "session.log").symlink_to(outside)
            with self.assertRaises(ValueError):
                publish(source, root / "published")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input"
            source.mkdir()
            outside = root / "outside.log"
            outside.write_text("fake")
            os.link(outside, source / "session.log")
            with self.assertRaises(ValueError):
                publish(source, root / "published")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input"
            (source / "nested").mkdir(parents=True)
            (source / "nested/session.log").write_text("fake")
            outside = root / "outside"
            outside.mkdir()
            destination = root / "published"
            destination.mkdir()
            (destination / "nested").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                publish(source, destination)

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
            self.assertIn("bash,create,edit,view,grep,glob", session)
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
        runner = (SUITE / "run-vscode.sh").read_text()
        self.assertEqual(package["dependencies"]["@tylerl0706/ahpx"], "0.6.0")
        self.assertEqual(ahpx["version"], "0.6.0")
        self.assertTrue(ahpx["integrity"].startswith("sha512-"))
        self.assertGreaterEqual(tuple(map(int, uuid["version"].split("."))), (11, 1, 1))
        self.assertIn('local -a npm_env=("PATH=$PATH" "HOME=$ROOT/npm-home")', runner)
        self.assertIn('env -i "${npm_env[@]}" npm ci --ignore-scripts', runner)
        self.assertIn("npm ci --ignore-scripts", runner)
        self.assertNotIn("AHPX_NODE_MODULES", runner)


if __name__ == "__main__":
    unittest.main()