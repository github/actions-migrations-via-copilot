# Surface-test failure, cleanup, and evidence-safety audit

## Scope and evidence

The requested public-suite revision is `7a3e37b29bd17f91f3cd0f854a3508a11d9776fb`.
The investigation checkout is at `f2af619` (`Initial plan`); the surface runner,
scorer, sanitizer, and workflow files inspected here have no diff from the pinned
revision. Findings below therefore describe the pinned suite, not a later change.

The failed [Surface Tests run 42386108736](https://github.com/github/actions-migrations-via-copilot/actions/runs/42386108736)
used the pinned SHA. `target`, `offline`, `cli`, and `vscode` succeeded; `results`
failed with `unexpected=2`, `missing=0`, and `not_run=0`. The logs establish that
the summary gate caught two unexpected results; they do not include the two case
names. The existing offline tests also pass locally:
`python3 -m unittest discover -s tests/surfaces -p 'test_*.py' -v` (12 tests).
No live Copilot/model call, cloud task, cancellation, or secret inspection was
used.

## Ranked findings

### 1. A failed surface job is not itself a failing result — confirmed workflow gap

`.github/workflows/surface-tests.yml:187-217` runs `results` with `always()`,
downloads whatever artifacts exist, and gates only on score totals. It never
checks `needs.cli.result` or `needs.vscode.result`. The surface upload steps at
`:118-129` and `:174-185` run after a failed test step (`always()` for prepare;
`!cancelled()` for upload), so an upstream job can fail yet leave a complete,
passing `score.json` for `results` to accept. Missing artifacts and `NOT RUN`
scores are caught by `summarize.py:58-74`; a failed job with apparently complete
scores is not.

**Smallest fault injection:** in a disposable workflow copy, make a surface job
fail immediately after producing a complete passing score, while allowing its
prepare/upload steps to run. Confirm whether `results` succeeds. The result job
should fail whenever a required surface job did not succeed, even if its artifacts
look complete.

### 2. Runner exit statuses are recorded but discarded — confirmed; green impact not reproduced

Both runners use `set -uo pipefail`, not `set -e`. In `run-cli.sh:29-32` and
`:37-40`, the CLI and agent-command statuses are immediately overwritten by
`echo`; the loop at `:47-48` returns the last scoring call's status. In
`run-vscode.sh:76-89`, AHPX execution statuses are likewise only appended to
logs, after which scoring continues at `:108-110`. Thus an API error, CLI error,
or timeout (including GNU `timeout` status 124) is not independently considered
by the workflow. Missing evidence often turns into `NOT RUN` and fails the
summary, but a nonzero process status with enough artifacts to satisfy the score
is not rejected.

**Smallest fault injection:** substitute a local fake CLI/AHPX executable that
emits test evidence and then exits nonzero; assert that the runner returns
nonzero while still collecting/sanitizing its partial evidence. No live model is
needed.

### 3. Two negative plugin checks can pass without their own probe evidence — confirmed scorer gap

In `score.py:226-245`, `ns_loaded` can be inferred from unrelated namespace
evidence such as `skill-ns.txt` or `rule-ns.txt`. Once it is true, N2 passes
whenever there are no `ns-root:` hook rows, and R3 passes whenever
`rule-nsroot.txt` is absent. Neither verdict requires evidence that the
corresponding decoy was actually exercised.

**Offline reproduction performed:** scoring a plugin session with only
`skill-ns.txt` and `rule-ns.txt`, and no probe log, produced `N2=PASS` and
`R3=PASS` (while other cases remained deviations/not-run). This does not by
itself make the whole suite green, but it means these two cells can report success
without case-specific evidence.

**Smallest next test:** add a synthetic scorer test where normal namespace
evidence exists but the root-hook/root-rule challenge is omitted; require N2/R3
to be `NOT RUN` rather than `PASS`. Preserve a positive execution marker for each
challenge so “ignored as specified” is distinguished from “never tested.”

### 4. Artifact scrubbing misses generic bearer-style credentials — confirmed gap; exposure is conditional

`sanitize_artifacts.py:11-27` copies selected logs/transcripts and replaces
configured token values, a few GitHub token prefixes, `tkn=` query values, and
the fake probe credential. It does not redact generic bearer-style
`Authorization` headers. An offline check with a synthetic bearer-shaped string
confirmed that the published `session.log` retained it. No actual credential
was used or found; whether real credentials can reach these allowlisted outputs
is untested. The allowlist and omission of `connect.json`
reduce exposure, and the explicit symlink checks at `:17-21` reject symlinked
files/parents; no symlink bypass was reproduced.

**Smallest next test:** add a synthetic bearer-shaped value to an allowed log and
assert it is redacted. Also add a symlink-to-outside-file case and assert publish
fails without copying the target.

### 5. Remote cloud task cancellation and signal cleanup need verification — untested risk

`run-cloud-agent.sh:75-108` polls for at most `WAIT_MINUTES`, then its EXIT
cleanup at `:54-61` closes its PR/issue and deletes its owned branch. It does not
explicitly cancel a still-running Copilot task/run. Whether closing the issue
stops that task is not established by this static review. This script is not
invoked by the public `surface-tests.yml` workflow. Locally, `run-vscode.sh:23`
has an EXIT cleanup for `code agent kill` and normal-path `kill`/`wait` at
`:96-98`, but no signal-specific fault injection was performed.

**Smallest next test:** in an authorized private fixture only, let the cloud
wait expire while the owned task is still running and check that no task remains
after cleanup. Separately, use a fake local host to send TERM during a VS Code
session and verify its process exits. Do not use another user's task.

## Paths reviewed with no defect established

- **Reviewed SHA:** `.github/workflows/surface-tests.yml:80-92` requires a
  numeric PR and full 40-character SHA, compares it with the PR's current head,
  and exports that exact SHA. Surface jobs and `results` check out the exported
  SHA (`:104-107`, `:139-142`, `:192-195`). No mismatch path was found.
- **Missing and malformed evidence:** `summarize.py:58-74` fails for absent
  required sessions/cases, `NOT RUN`, and results differing from expectations.
  Malformed score JSON raises during summarization rather than becoming a pass.
  The observed failed run demonstrates the unexpected-result gate working.
- **Failed installs, unavailable credentials, and API/setup errors:** CLI
  installation has explicit retries/failure in `common.sh:59-73`; missing
  required credentials fail early in the runners. VS Code's missing secret is
  reported as skipped (`surface-tests.yml:166-173`), after which the required
  VS Code session is missing and should fail `results`. Installation and API
  errors are not all independently propagated (finding 2), but no offline test
  showed them producing a complete green suite.

## Maintainer decisions

1. Should any required runner/job nonzero status fail the check even when every
   score appears complete? The safe default is yes, while preserving artifacts
   for diagnosis.
2. What credential classes should the public-artifact sanitizer redact beyond
   the currently enumerated token formats? The allowed logs include model output
   and hook/tool evidence, so the intended boundary should be explicit.
3. Does closing the owned issue cancel its in-flight Copilot task? If not, what
   supported cancellation action should the runner use?

No implementation changes are made in this investigation. The smallest first
follow-up is the workflow fault injection in finding 1, followed by the two
offline scorer/sanitizer tests; cloud cleanup testing requires explicit
maintainer authorization and a dedicated private fixture.
