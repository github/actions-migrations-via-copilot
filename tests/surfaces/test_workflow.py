import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/surface-tests.yml"
REPOSITORY = "github/actions-migrations-via-copilot"
SHA = "a" * 40


def job(name):
    text = WORKFLOW.read_text()
    return re.search(rf"^  {name}:\n(.*?)(?=^  [\w-]+:|\Z)", text, re.M | re.S)[1]


def run_step(job_name, step_name):
    text = job(job_name).split(f"- name: {step_name}\n", 1)[1]
    block = text.split("        run: |\n", 1)[1]
    block = re.match(r"((?: {10}[^\n]*\n|\n)+)", block)[1]
    return "\n".join(line[10:] for line in block.splitlines()) + "\n"


class WorkflowTests(unittest.TestCase):
    def test_rule_warnings_are_visible_without_bypassing_other_gates(self):
        results = job("results")
        self.assertIn("::warning::", run_step("results", "Report non-blocking rule warnings"))
        for output in ("blocking_unexpected", "missing", "blocking_not_run", "execution_failed", "upstream_failed"):
            self.assertIn(f"steps.sum.outputs.{output} != '0'", results)
        failure = results.split("- name: Fail on unexpected results or missing surfaces", 1)[1]
        self.assertNotIn("steps.sum.outputs.warnings", failure)
        self.assertNotIn("steps.sum.outputs.unexpected", failure)
        self.assertNotIn("steps.sum.outputs.not_run", failure)
        self.assertIn("exit 1", failure)

    def test_offline_failure_blocks_live_jobs_and_combined_status(self):
        for name in ("cli", "vscode"):
            self.assertIn("needs: [offline, target]", job(name))
        self.assertIn("needs: [offline, target, cli, vscode]", job("results"))
        self.assertIn("OFFLINE_RESULT: ${{ needs.offline.result }}", job("results"))
        self.assertIn('--job-result "offline=$OFFLINE_RESULT"', run_step("results", "Summarize"))

    def decide(self, event="workflow_dispatch", head_repo=REPOSITORY,
               pr="", reviewed="", api_repo=REPOSITORY, api_sha=SHA,
               event_sha=SHA, api_status=0):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            summary = Path(directory) / "summary"
            env = {
                "PATH": os.environ["PATH"],
                "GITHUB_REPOSITORY": REPOSITORY,
                "GITHUB_SHA": event_sha,
                "GITHUB_OUTPUT": str(output),
                "GITHUB_STEP_SUMMARY": str(summary),
                "EVENT": event,
                "HEAD_REPO": head_repo,
                "PR_SHA": SHA if event == "pull_request" else "",
                "IN_PR": pr,
                "IN_SHA": reviewed,
                "API_HEAD": f"{api_repo}\t{api_sha}",
                "API_STATUS": str(api_status),
            }
            # The target's only external call is metadata lookup, never checkout or execution.
            stub = 'gh() { printf "%s\\n" "$API_HEAD"; return "$API_STATUS"; }\n'
            result = subprocess.run(
                ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c",
                 stub + run_step("target", "Decide what to test")],
                env=env, text=True, capture_output=True,
            )
            outputs = dict(line.split("=", 1) for line in output.read_text().splitlines()) if output.exists() else {}
            return result, outputs

    def test_fork_pull_request_is_offline_only(self):
        result, outputs = self.decide(event="pull_request", head_repo="contributor/fork")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(outputs, {"run": "false"})

    def test_fork_dispatch_rejected_for_stale_and_exact_review(self):
        for current in (SHA, "b" * 40):
            with self.subTest(current=current):
                result, outputs = self.decide(pr="42", reviewed=SHA,
                                              api_repo="contributor/fork", api_sha=current)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(outputs, {"run": "false"})
                self.assertIn("Credentialed fork execution is disabled", result.stdout)

    def test_repository_dispatch_requires_exact_head_and_event_revision(self):
        result, outputs = self.decide(pr="42", reviewed=SHA)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(outputs, {"run": "true", "sha": SHA})
        for values in ({"api_sha": "b" * 40}, {"event_sha": "b" * 40}):
            with self.subTest(values=values):
                result, outputs = self.decide(pr="42", reviewed=SHA, **values)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("sha", outputs)
                self.assertNotEqual(outputs.get("run"), "true")

    def test_bad_inputs_and_metadata_fail_closed(self):
        for values in (
            {"reviewed": SHA},
            {"pr": "42"},
            {"pr": "42; echo injected", "reviewed": SHA},
            {"pr": "42", "reviewed": "$(echo injected)"},
            {"pr": "42", "reviewed": SHA, "api_status": 1},
            {"event": "pull_request_target"},
        ):
            with self.subTest(values=values):
                result, outputs = self.decide(**values)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotEqual(outputs.get("run"), "true")

    def test_trusted_events_use_event_commit_not_pr_input(self):
        for event in ("push", "pull_request", "workflow_dispatch"):
            with self.subTest(event=event):
                result, outputs = self.decide(event=event, event_sha="c" * 40)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(outputs, {"run": "true", "sha": "c" * 40})

    def test_privileged_jobs_and_checkouts_exclude_fork_code(self):
        for name in ("cli", "vscode"):
            text = job(name)
            condition = text.split("    if: >-\n", 1)[1].split("    runs-on:", 1)[0]
            self.assertEqual(" ".join(condition.split()),
                             "needs.target.outputs.run == 'true' && "
                             f"github.repository == '{REPOSITORY}' && "
                             "(github.event_name == 'push' || github.event_name == 'workflow_dispatch' || "
                             "(github.event_name == 'pull_request' && "
                             "github.event.pull_request.head.repo.full_name == github.repository))")
        for name in ("cli", "vscode", "results"):
            text = job(name)
            self.assertIn("ref: ${{ github.sha }}", text)
            self.assertIn("persist-credentials: false", text)
            self.assertNotIn("ref: ${{ needs.target.outputs.sha }}", text)
            self.assertNotIn("refs/pull/", text)
        self.assertNotIn("actions/checkout@", job("target"))
        self.assertNotIn("actions/checkout@", job("pr-status"))

    def test_offline_has_no_copilot_credentials_or_shared_cache(self):
        text = WORKFLOW.read_text()
        self.assertIn("python3 -m unittest discover", job("offline"))
        self.assertIn("persist-credentials: false", job("offline"))
        self.assertNotIn("secrets.", job("offline"))
        self.assertNotIn("copilot-requests:", job("offline"))
        self.assertNotIn("actions/cache", text)
        self.assertNotRegex(text, r"(?m)^\s+cache:")
        self.assertRegex(text, r"permissions:\n  contents: read\n")

    def test_missing_credentials_never_start_runners(self):
        for name, step in (("cli", "Run the Copilot CLI tests"),
                           ("vscode", "Run the VS Code Agent Host tests")):
            for credential in ("", "offline-placeholder"):
                with self.subTest(job=name, supplied=bool(credential)), tempfile.TemporaryDirectory() as directory:
                    marker = Path(directory) / "runner-started"
                    output = Path(directory) / "output"
                    env = {"PATH": os.environ["PATH"], "COPILOT_GITHUB_TOKEN": credential,
                           "GITHUB_OUTPUT": str(output), "MARKER": str(marker)}
                    stub = 'bash() { printf "%s\\n" "$*" > "$MARKER"; }\n'
                    result = subprocess.run(
                        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c",
                         stub + run_step(name, step)], env=env, text=True, capture_output=True,
                    )
                    self.assertEqual(marker.exists(), bool(credential))
                    if credential:
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(marker.read_text().strip(), f"tests/surfaces/run-{name}.sh")
                    elif name == "cli":
                        self.assertNotEqual(result.returncode, 0)
                    else:
                        self.assertEqual(output.read_text().strip(), "ran=false")


if __name__ == "__main__":
    unittest.main()
