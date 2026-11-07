import json
import base64
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
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
                        "cases": [{"case": name, "expected": name, "result": "PASS", "observed": "evidence"}
                                  for name in names]
                    }))
            result = subprocess.run([
                sys.executable, str(SUITE / "summarize.py"), "--scores", str(root), "--expect", "cli,vscode",
                "--job-result", "target=success", "--job-result", "cli=failure", "--job-result", "vscode=success",
                "--out", str(root / "summary"),
            ], capture_output=True, text=True, check=True)
            summary = json.loads((root / "summary/results.json").read_text())
            self.assertIn("upstream_failed=1", result.stdout)
            self.assertEqual(summary["unexpected"], [])
            self.assertEqual(summary["missing"], [])
            self.assertEqual(summary["not_run"], [])
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