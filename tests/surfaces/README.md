# Plugin surface tests

Automated tests for the Copilot CLI and VS Code Agent Host. They cover `actions-migrator`'s own hooks and the plugin features it relies on: hooks, skills, rules and agents, in both plugin formats. Cloud-agent coverage is still being completed; VS Code Local is a separate, currently uncovered surface.

They follow the method in the [plugin surface testing skill](https://github.com/github/services-toolbox/tree/main/products/copilot/skills/plugin-surface-testing): prove a hook ran from its own log and deny message, not from whether a call failed.

## How it runs

[`surface-tests.yml`](../../.github/workflows/surface-tests.yml) runs on every change to `plugin/` or `tests/surfaces/`, on `main` and on pull requests:

| Who opens the PR | What happens |
|---|---|
| Someone with write access (a branch in this repo) | The tests run on the PR automatically |
| An outside contributor (a fork) | The PR shows a note. A maintainer reviews the changes, then runs **Surface Tests** from the Actions tab with the PR number and the commit they reviewed. The result appears on the PR. |

Fork PRs can't run on their own because GitHub doesn't give them this repo's secrets or Copilot access, which keeps untrusted code from using them.

The cloud agent isn't tested on PRs. The planned weekly run belongs in a private testing repo and uses reviewed `main` code. That runner is not operational yet: its cloud-agent plugin session, credentials, result retention and analysis handoff remain work in this draft. No hourly polling or GitHub App is required for the per-PR tests.

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

[`expected.json`](expected.json) records historical cloud-agent gaps, not proof that the cloud suite ran. Missing surfaces, missing cases and NOT RUN results fail the check. Current CLI and VS Code Agent Host have no expected exceptions. A maintainer's manual fork run authorizes execution of that exact reviewed commit with Copilot access; it does not make arbitrary fork code safe.

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
