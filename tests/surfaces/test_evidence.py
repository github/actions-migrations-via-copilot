import json
import base64
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from sanitize_artifacts import publish
from cloud_settings import configure
import rule_evidence


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
                 "model_selector": "claude-haiku-4.5"},
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
                {"plugin_discovered": "true", "server_commit_matches_pin": "true"},
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


if __name__ == "__main__":
    unittest.main()