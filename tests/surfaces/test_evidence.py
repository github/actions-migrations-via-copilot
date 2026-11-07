import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from sanitize_artifacts import publish


SUITE = Path(__file__).resolve().parent


class EvidenceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()