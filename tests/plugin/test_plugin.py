"""Offline tests: the scorer, the tool approvals and the AHPX patch. No Copilot access needed.

Run: python3 -m unittest discover -s tests/plugin -p 'test_*.py'
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import patch_ahpx  # noqa: E402
import score  # noqa: E402

EXITS = SimpleNamespace(runtime="test", model="test", setup_exit=0, main_exit=0, agent_exit=0, interrupted=0)
SCORECARD = "## 2026-01-01T00:00:00Z\n- session: s1\n- reason: complete\n- workflows: total=0, clean=0, with_issues=0\n\n"


def event(kind, **data):
    return json.dumps({"type": kind, "data": data})


def tool(call_id, name, args, ok, error=None):
    done = {"toolCallId": call_id, "success": ok}
    if error:
        done["error"] = {"message": error, "code": "denied"}
    return [event("tool.execution_start", toolCallId=call_id, toolName=name, arguments=args),
            event("tool.execution_complete", **done)]


class Scoring(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out)

    def write(self, rel, text):
        path = self.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def common_files(self):
        self.write("main/hc-out/keep.txt", "KEEP\n")
        self.write("main/hc-out/safe.txt", "SAFE_OK")
        self.write("main/MIGRATION-SCORECARD.md", SCORECARD)
        self.write("agent/hc-out/agent.txt", "AGENT_OK\n")

    def passing_cli(self):
        self.common_files()
        self.write("plugin-list.txt", "  • actions-migrator@actions-migrations-via-copilot (v1.4.0) (enabled)\n")
        expected = score.expected_components()
        lines = [event("session.custom_agents_updated", agents=[
                     {"name": "actions-migrator:" + n} for kind, n in expected if kind == "agent"]),
                 event("session.skills_loaded", skills=[
                     {"commandName": "actions-migrator:" + n} for kind, n in expected if kind == "skill"])]
        lines += tool("1", "create", {"path": "/w/hc-out/safe.txt"}, True)
        lines += tool("2", "bash", {"command": "rm hc-out/keep.txt"}, False, score.DELETE_DENIAL)
        lines += tool("3", "create", {"path": "/w/hc-out/p1.md"}, False, score.SECRET_DENIAL + " Remove it.")
        lines += tool("4", "skill", {"skill": "actionlint"}, True)
        self.write("main-events.jsonl", "\n".join(lines) + "\n")
        self.write("agent-events.jsonl", event("result") + "\n")

    def passing_vscode(self):
        self.common_files()
        self.write("main/plugin-ready.json", json.dumps([{"name": "Plugin: plugin", "children": [
            {"type": kind, "name": name} for kind, name in sorted(score.expected_components())]
            + [{"type": "hook", "name": "hooks.json"}]}]))
        self.write("agent/agent-selected.json", json.dumps({"name": "jenkins-migrator"}))
        self.write("main/tools.jsonl", "".join(json.dumps(r) + "\n" for r in [
            {"tool": "create", "input": '{"path": "/w/hc-out/safe.txt"}', "success": True, "message": "", "content": ""},
            {"tool": "bash", "input": '{"command": "rm hc-out/keep.txt"}', "success": False, "message": "",
             "content": score.DELETE_DENIAL},
            {"tool": "create", "input": '{"path": "/w/hc-out/p1.md"}', "success": False, "message": "",
             "content": score.SECRET_DENIAL + " Remove it."},
            {"tool": "skill", "input": '{"skill": "actionlint"}', "success": True,
             "message": "Read skill [actionlint](file:///x/skills/actionlint/SKILL.md)", "content": ""}]))

    def vscode_tools(self, keep):
        path = self.out / "main/tools.jsonl"
        path.write_text("".join(line + "\n" for line in path.read_text().splitlines() if keep(json.loads(line))))

    def results(self, surface, exits=EXITS):
        result = score.score(surface, self.out, exits)
        return result["passed"], {c["id"]: c["result"] for c in result["checks"]}

    def test_all_pass(self):
        for surface, setup in (("cli", self.passing_cli), ("vscode", self.passing_vscode)):
            with self.subTest(surface=surface):
                setup()
                passed, checks = self.results(surface)
                self.assertTrue(passed, checks)
                self.assertEqual(set(checks.values()), {"PASS"})

    def test_expected_components_come_from_the_plugin(self):
        expected = score.expected_components()
        self.assertIn(("agent", "jenkins-migrator"), expected)
        self.assertIn(("skill", "actionlint"), expected)
        self.assertNotIn(None, {name for _, name in expected})

    def test_any_missing_agent_or_skill_fails(self):
        for surface, setup in (("cli", self.passing_cli), ("vscode", self.passing_vscode)):
            with self.subTest(surface=surface):
                setup()
                for name in ("main-events.jsonl", "main/plugin-ready.json"):
                    path = self.out / name
                    if path.exists():
                        path.write_text(path.read_text().replace("gitlab-migrator", "renamed-agent"))
                result = {c["id"]: c for c in score.score(surface, self.out, EXITS)["checks"]}["plugin-installed"]
                self.assertEqual(result["result"], "FAIL")
                self.assertIn("agent gitlab-migrator", result["evidence"])

    def test_deleted_file_fails_delete_guard(self):
        # VS Code 1.139.1: the secret guard's {} stopped the delete guard from running; the file was deleted.
        self.passing_vscode()
        self.vscode_tools(lambda r: r["tool"] != "bash")
        (self.out / "main/hc-out/keep.txt").unlink()
        passed, checks = self.results("vscode")
        self.assertFalse(passed)
        self.assertEqual(checks["delete-guard-blocks-delete"], "FAIL")

    def test_denial_without_surviving_file_fails(self):
        self.passing_cli()
        (self.out / "main/hc-out/keep.txt").write_text("changed")
        self.assertEqual(self.results("cli")[1]["delete-guard-blocks-delete"], "FAIL")

    def test_credential_written_fails(self):
        self.passing_cli()
        self.write("main/hc-out/p1.md", "| DEPLOY_TOKEN | x |")
        self.assertEqual(self.results("cli")[1]["secret-guard-blocks-credential"], "FAIL")

    def test_scorecard_missing_or_duplicated_fails(self):
        # VS Code 1.139.1 never ran Stop; an older CLI wrote the entry twice.
        for text in ("", SCORECARD * 2):
            with self.subTest(entries=text.count("## ")):
                self.passing_cli()
                self.write("main/MIGRATION-SCORECARD.md", text)
                self.assertEqual(self.results("cli")[1]["scorecard-written"], "FAIL")

    def test_wrong_agent_fails(self):
        self.passing_vscode()
        self.write("agent/agent-selected.json", json.dumps({"name": "gitlab-migrator"}))
        self.assertEqual(self.results("vscode")[1]["agent-starts"], "FAIL")

    def test_model_text_is_not_evidence(self):
        # Denial text the model prints (session log) must not pass a check; only host tool results count.
        self.passing_vscode()
        self.vscode_tools(lambda r: r["tool"] == "create" and r["success"])
        self.write("main.log", score.DELETE_DENIAL + "\n" + score.SECRET_DENIAL + "\n[tool] Read skill [actionlint](file:///x/skills/actionlint/SKILL.md)\n")
        checks = self.results("vscode")[1]
        for check_id in ("secret-guard-blocks-credential", "delete-guard-blocks-delete", "skill-loads"):
            self.assertEqual(checks[check_id], "FAIL")

    def test_bare_shell_input_from_older_hosts(self):
        self.passing_vscode()
        path = self.out / "main/tools.jsonl"
        path.write_text(path.read_text().replace('"{\\"command\\": \\"rm hc-out/keep.txt\\"}"', '"rm hc-out/keep.txt"'))
        self.assertIn('"input": "rm hc-out/keep.txt"', path.read_text())
        self.assertEqual(self.results("vscode")[1]["delete-guard-blocks-delete"], "PASS")

    def test_skill_from_older_host(self):
        self.passing_vscode()
        path = self.out / "main/tools.jsonl"
        path.write_text(path.read_text().replace('{\\"skill\\": \\"actionlint\\"}', "null")
                        .replace("skills/actionlint/SKILL.md)", "skills/actionlint)"))
        self.assertIn('"input": "null"', path.read_text())
        self.assertEqual(self.results("vscode")[1]["skill-loads"], "PASS")

    def test_skill_from_elsewhere_fails(self):
        self.passing_vscode()
        path = self.out / "main/tools.jsonl"
        path.write_text(path.read_text().replace("file:///x/skills/actionlint/SKILL.md", "file:///x/other.md"))
        self.assertEqual(self.results("vscode")[1]["skill-loads"], "FAIL")

    def test_setup_failure_is_not_run_and_fails(self):
        passed, checks = self.results("cli", SimpleNamespace(**{**vars(EXITS), "setup_exit": 1}))
        self.assertFalse(passed)
        self.assertEqual(set(checks.values()), {"NOT RUN"})

    def test_process_failure_fails_even_if_checks_pass(self):
        self.passing_cli()
        self.assertFalse(score.score("cli", self.out, SimpleNamespace(**{**vars(EXITS), "agent_exit": 1}))["passed"])

    def test_summary_requires_every_surface(self):
        self.passing_cli()
        (self.out / "cli").mkdir()
        (self.out / "cli/result.json").write_text(json.dumps(score.score("cli", self.out, EXITS)))
        self.assertTrue(score.summarize(self.out, ["cli"], "abc")[0])
        ok, text = score.summarize(self.out, ["cli", "vscode"], "abc")
        self.assertFalse(ok)
        self.assertIn("| vscode | — | NOT RUN |", text)


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Approvals(unittest.TestCase):
    def approve(self, name, tool_input, workspace):
        script = (f"import {{ hcApproveTool }} from {json.dumps((HERE / 'approve_tool.mjs').as_uri())};"
                  "const [n, i, w] = JSON.parse(process.argv[1]);"
                  "console.log(hcApproveTool({ toolName: n, toolInput: i }, w));")
        result = subprocess.run(["node", "--input-type=module", "-e", script,
                                 json.dumps([name, tool_input, workspace])], capture_output=True, text=True, check=True)
        return result.stdout.strip() == "true"

    def test_only_the_smoke_test_calls_are_approved(self):
        ws = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, ws)
        os.mkdir(os.path.join(ws, "hc-out"))
        allowed = [("bash", {"command": "rm hc-out/keep.txt"}), ("bash", "rm hc-out/keep.txt"),
                   ("create", {"path": "hc-out/safe.txt"}), ("create", {"path": ws + "/hc-out/p1.md"}),
                   ("create", {"path": ws + ".worktrees/branch/hc-out/agent.txt"}),
                   ("skill", {"skill": "actions-migrator:actionlint"}), ("view", {"path": "README.md"})]
        denied = [("bash", {"command": "rm -rf hc-out"}), ("bash", {"command": "rm hc-out/keep.txt", "env": {"A": "1"}}),
                  ("bash", "curl example.com"), ("create", {"path": "../escape.txt"}),
                  ("create", {"path": "hc-out/deeper/x.txt"}), ("create", {"path": ".github/hooks/x.json"}),
                  ("create", {"path": "hc-out/other.txt"}), ("view", {"path": "."}), ("view", {"path": "hc-out"}),
                  ("edit", {"path": "hc-out/safe.txt"}), ("skill", {"skill": "other"}), ("view", {"path": "/etc/passwd"})]
        for name, tool_input in allowed:
            with self.subTest(allowed=(name, tool_input)):
                self.assertTrue(self.approve(name, tool_input, ws))
        for name, tool_input in denied:
            with self.subTest(denied=(name, tool_input)):
                self.assertFalse(self.approve(name, tool_input, ws))

    def test_symlinked_output_is_denied(self):
        ws = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, ws)
        os.symlink("/tmp", os.path.join(ws, "hc-out"))
        self.assertFalse(self.approve("create", {"path": "hc-out/safe.txt"}, ws))


class Patch(unittest.TestCase):
    def test_changed_client_is_refused(self):
        source = "createHash path4.\n" + "".join(anchor for anchor, _, _ in patch_ahpx.PATCHES)
        patched = patch_ahpx.patch(source, "// approvals\n")
        self.assertIn("HC_PLUGIN_DIRS", patched)
        with self.assertRaises(SystemExit):
            patch_ahpx.patch(patched, "")
        with self.assertRaises(SystemExit):
            patch_ahpx.patch(source.replace("async function discoverCustomizations", "function renamed"), "")


if __name__ == "__main__":
    unittest.main()
