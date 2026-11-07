# Plugin surface tests

Automated tests for the Copilot CLI, VS Code Agent Host and the cloud agent. They cover `actions-migrator`'s own hooks and the plugin features it relies on: hooks, skills, rules and agents, in both plugin formats. VS Code Local is a separate, currently uncovered surface.

The [plugin surface testing skill](../../.github/skills/plugin-surface-testing/SKILL.md) lives in this repo with the tests: prove a hook ran from its own log and deny message, not from whether a call failed. Update the method and test code together in the same PR. Private runners use a versioned copy of this guide, not a separately maintained one.

## How it runs

[`surface-tests.yml`](../../.github/workflows/surface-tests.yml) runs on every change to `plugin/` or `tests/surfaces/`, on `main` and on pull requests:

| Who opens the PR | What happens |
|---|---|
| Someone with write access (a branch in this repo) | Offline and credentialed tests run on the PR's event revision automatically |
| An outside contributor (a fork) | Only offline checks run. Credentialed fork tests are disabled, including manual dispatch of an exact reviewed SHA. |

Repository-owned branches are the credentialed execution trust boundary: their
writers can already change executable workflow code. Manual PR runs require that
the API reports a head in this repository, its SHA matches the reviewed SHA, and
the selected workflow branch is at that same revision. Select that branch in the
Actions tab; selecting `main` while supplying a different PR SHA fails closed.
All credentialed jobs and the summarizer check out `github.sha`, never a supplied
SHA or a fork PR ref. Automatic repository-owned PR runs test the event's merge
revision. The metadata selector and status writer do not check out or run PR code.

Reviewing fork code is not credential or cache isolation. Until separate execution
infrastructure enforces those boundaries, neither the runners nor the sanitizer
may execute fork code with Copilot credentials. The offline job uses a fresh
GitHub-hosted runner, read-only contents permission, no persisted checkout
credentials, no Copilot credentials, and no shared-cache restore/save steps.
Credentialed jobs also do not restore/save shared caches. Missing credentials
prevent runner startup (CLI fails; VS Code records `ran=false`). This fallback
sacrifices automatic/live fork coverage, not contributor offline validation:

```bash
python3 -m unittest discover -s tests/surfaces -p 'test_*.py' -v
```

### CodeQL follow-up

This change starts from reviewed suite revision
`67924a46ae3e195e0521a9e7b9f82a47143a186b`; no suite file changes preceded it.
[Alert 33's review comment](https://github.com/github/actions-migrations-via-copilot/pull/61#discussion_r4502054023)
reports cache poisoning through `workflow_dispatch` and privileged checkout of
`needs.target.outputs.sha`. That checkout path is removed, not suppressed.
Fetching the full alert through the integration returned HTTP 403
(`Resource not accessible by integration`), so its complete trace and final
disposition remain unverified. Absence of an explicit cache action is not evidence
that the alert is a false positive.

A maintainer with code-scanning access must inspect
[alert 33](https://github.com/github/actions-migrations-via-copilot/security/code-scanning/33)
and rerun the existing CodeQL analysis on this PR's exact head revision. Confirm
whether the dispatch-to-untrusted-checkout flow is eliminated. If it remains,
provide the rule ID, analyzed commit/ref, all source-to-sink locations and messages,
and any implicated cache scope/key/action from the trace (or its SARIF code flows).
Keep the alert open pending that evidence. Related investigations: #62 and #65;
result aggregation/failure propagation and other security-comment fixes are
separate follow-ups.

The cloud agent isn't tested automatically on public PRs. Its two sessions have been validated as one-off runs in a private testing repo using versioned fixtures. The planned weekly schedule and automatic analysis handoff still need deployment and credentials. No hourly polling or GitHub App is required for the per-PR CLI and Agent Host tests.

VS Code Local is the older built-in agent mode, not another name for Agent Host. It has different hook payloads and event handling. The plugin's broad VS Code compatibility claim includes those paths, so Local needs its own coverage unless that support claim is explicitly narrowed. Passing Agent Host does not prove Local works.

## Cases

Each implemented surface runs two sessions: 13 repository-hook checks and 20 plugin checks, for 33 checks. Each session creates a scratch repo, installs the plugins for that session from the tested commit, and gives the agent one prompt with a separate tool call per case. The probe plugins and marker files are small synthetic test fixtures, not customer migration data. The real `actions-migrator` plugin is also tested. The secret-guard check uses a deliberately fake credential.

**Session 1: repository hooks + actions-migrator** ([prompt](prompt.md)). The conformance hooks in [`kit/`](kit/) are installed as repository hooks.

**Session 2: plugin hooks and plugin parts** ([prompt](prompt-plugin.md)). The same hooks are installed inside two probe plugins, next to a third probe plugin in the newer Agent Plugins 1.0 format. Several VS Code bugs affected only hooks that come from plugins.

| Case | Session | Checks |
|---|---|---|
| C0 | both | Every hook entry for an event runs, and a `bash`-only hook skips file writes |
| C1 | both | Hook 1 prints nothing, hook 2 denies → blocked |
| C2 | both | Hook 1 prints `{}`, hook 2 denies → blocked |
| C3 | both | Hook 1 exits with code 2 → blocked |
| C4 | both | A `"matcher": "bash"` hook runs for `bash` only |
| C5 | both | A `postToolUse` hook prints `{}` → later post hooks still run |
| C6 | both | Lifecycle events fire (`sessionStart`, `userPromptSubmitted`, `agentStop`, `Stop`, `sessionEnd`) |
| C7 | both | The `preToolUse` payload has the documented fields, including `cwd` |
| C8 / C8b | both | `{}` in one hook file (or plugin) and a deny in the other → blocked, whichever runs first |
| C10 | both | After a deny or exit code 2, later hooks for that call don't run |
| C9 | 1 | actions-migrator's secret guard prints `{}`, then its delete guard denies an `rm` → blocked |
| P1 | 1 | actions-migrator's secret guard blocks writing a fake credential |
| N1 | 2 | New-format plugin: hooks in `com.github.copilot/hooks/` run |
| N2 | 2 | New-format plugin: a root `hooks.json` is ignored, as the spec says |
| S1 / S2 | 2 | A skill loads, in each format |
| R1 / R2 | 2 | An always-on rule applies, in each format |
| R3 | 2 | New-format plugin: a root `rules/` folder is ignored, as the spec says |
| A1 / A2 | 2 | A plugin agent can be started, in each format |

Each part of a probe plugin asks for its own file with its own code word, so a file with the right code proves that part loaded.

Results: **PASS**; **DEVIATION**, where the surface differs from the documented behavior; **FAIL**, where an actions-migrator guard didn't block; or **NOT RUN**, with no evidence either way.

[`expected.json`](expected.json) records the six cloud-agent deviations reconfirmed on 2026-11-07. It is not proof of execution: each run still needs its own evidence. Missing surfaces, missing cases and NOT RUN results fail the check. Current CLI and VS Code Agent Host have no expected exceptions. Fork commits cannot run with Copilot access in this workflow, even after review.

## Cloud runs

Use a dedicated private repository. Publish the generated `hc-probes` marketplace
on its default branch, retaining `fixture-source.json` with the source commit and
per-file hashes. `make_probes.py --include-plugin <plugin-dir> --source-sha <sha>
--observe-plugin <destination>` includes the real plugin with an observation wrapper
that preserves each original command, stdout, stderr and exit code. The original
hook file is retained alongside the observed copy.

Before each cloud session, generate and publish its settings with
`cloud_settings.py <testing-repo-checkout> repo|plugin <owner/testing-repo>`.
The cloud agent reads plugin settings from the default branch, not merely the
task branch. Run these sessions serially because they need different enabled-plugin
sets. The runner rejects mismatched default settings and source revisions.
After the batch, publish `cloud_settings.py <testing-repo-checkout> none
<owner/testing-repo>` so probe hooks do not affect unrelated analysis tasks.

```bash
REPO=owner/testing-repo CLOUD_SESSION=repo OUT_DIR=/tmp/cloud-out \
	tests/surfaces/run-cloud-agent.sh
REPO=owner/testing-repo CLOUD_SESSION=plugin OUT_DIR=/tmp/cloud-out \
	tests/surfaces/run-cloud-agent.sh
```

Provide `GH_TOKEN` through the environment, with permission to push test branches,
create issues and assign the cloud agent. Do not store it in source. The plugin
session additionally runs both plugin-agent selections and a positive control:
publish the generated legacy probe agent at `.github/agents/hc-probe-agent.agent.md`
on the private repo's default branch. Startup rejection counts as a tested
deviation only when the repository-agent control succeeds. Temporary issues,
PRs and branches are closed or removed by the runner after evidence collection.

The 2026-11-07 cloud result is **13 repository checks passed; 14 plugin checks
passed and 6 known deviations**. The deviations reproduce ignored new-format
hook locations, execution of the root decoy hook, missing plugin rules, and
rejected plugin custom-agent selection. No cloud case was left unexecuted in
that result. This does not claim that the weekly scheduler is deployed.

## Historical regression check

Verified locally on 2026-11-07 with `claude-haiku-4.5`:

| Runtime | Repository session | Plugin session |
|---|---|---|
| Copilot CLI 1.0.105 | 13 PASS | 20 PASS |
| VS Code Agent Host 1.145.2, server `c4453f8` | 13 PASS | 20 PASS |
| VS Code Agent Host 1.139.1, server `04c0d99` | Not included in the final historical comparison | 10 PASS, 10 DEVIATION |

The old build reproduces C0/C4 matcher failures, C2 stopping after `{}`, C3 ignoring exit code 2, C5 skipping later post hooks, C6 missing stop events, C7 receiving `workingDirectory` instead of `cwd`, C8/C8b cross-plugin ordering failures, and C10 continuing after exit code 2. These are expected failures in the historical comparison, not exceptions allowed in current CI.

The runner pins the actual server commit, not just the CLI version. The AHPX adapter serves plugin files through the host's customization interface, selects discovered agents, and captures evidence before the old host deletes its temporary worktree. Installing plugins only through the Copilot CLI did not reproduce the editor's old failures.

## Run locally

```bash
# Copilot CLI
COPILOT_GITHUB_TOKEN=$(gh auth token) OUT_DIR=/tmp/surface-out tests/surfaces/run-cli.sh

# VS Code Agent Host (needs the VS Code CLI; any version, e.g. an older one to check a past bug)
CODE_BIN=/path/to/code COPILOT_GITHUB_TOKEN=$(gh auth token) OUT_DIR=/tmp/surface-out tests/surfaces/run-vscode.sh

# Combine the results
tests/surfaces/summarize.py --scores /tmp/surface-out --expect cli,vscode --out /tmp/surface-out/summary
```

The VS Code tests need a Copilot user's token. The workflow token isn't accepted there yet ([microsoft/vscode#346628](https://github.com/microsoft/vscode/issues/346628)).
