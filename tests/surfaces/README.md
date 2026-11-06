# Plugin surface tests

Automated tests that check `actions-migrator`'s hooks behave the same on every Copilot surface: the Copilot CLI, VS Code (headless Agent Host), and the Copilot cloud agent. They follow the method in the [plugin surface testing skill](https://github.com/github/services-toolbox/tree/main/products/copilot/skills/plugin-surface-testing): prove a hook ran from its own log and deny message, not from the outcome.

## How it runs

1. A change to `plugin/` or `tests/surfaces/` on `main`, or on a PR branch in this repo, triggers [`surface-tests-dispatch.yml`](../../.github/workflows/surface-tests-dispatch.yml).
2. That workflow pings the private testing repo `alexdemichieli-migrations/actions-migrations-via-copilot-testing` in the volcano-coffee EMU, which runs these scripts against the commit.
3. The testing repo records the results, and assigns Copilot to analyze any failure or change from the last `main` run.

The cloud agent runs only for `main`, because it loads the plugin from this repo's `main` branch.

## Cases

Each run creates a scratch repo holding the conformance hooks from [`kit/`](kit/), installs `actions-migrator` from the tested commit, and gives the agent one [prompt](prompt.md) with a separate tool call per case.

| Case | Checks |
|---|---|
| C0 | Every hook entry for an event runs, and a `bash`-only hook skips file writes |
| C1 | Hook 1 prints nothing, hook 2 denies → blocked |
| C2 | Hook 1 prints `{}`, hook 2 denies → blocked |
| C3 | Hook 1 exits with code 2 → blocked |
| C4 | A `"matcher": "bash"` hook runs for `bash` only |
| C5 | A `postToolUse` hook prints `{}` → later post hooks still run |
| C6 | Lifecycle events fire (`sessionStart`, `userPromptSubmitted`, `agentStop`, `sessionEnd`) |
| C7 | The `preToolUse` payload has the documented fields |
| C8 / C8b | `{}` in one hook file and a deny in the other → blocked, whichever file runs first |
| C9 | actions-migrator's secret guard prints `{}`, then its delete guard denies an `rm` → blocked |
| P1 | actions-migrator's secret guard blocks writing a fake credential |

Results: **PASS**; **DEVIATION**, where the surface differs from the documented hook behavior; **FAIL**, where an actions-migrator guard didn't block; or **NOT RUN**, with no evidence either way.

## Run locally

```bash
# Copilot CLI
COPILOT_GITHUB_TOKEN=$(gh auth token) OUT_DIR=/tmp/surface-out tests/surfaces/run-cli.sh

# VS Code Agent Host (needs the VS Code CLI)
CODE_BIN=/path/to/code COPILOT_GITHUB_TOKEN=$(gh auth token) OUT_DIR=/tmp/surface-out tests/surfaces/run-vscode.sh

# Combine the results
tests/surfaces/summarize.py --scores /tmp/surface-out --out /tmp/surface-out/summary
```

The VS Code tests need a Copilot user's token. The workflow token isn't accepted there yet ([microsoft/vscode#346628](https://github.com/microsoft/vscode/issues/346628)).
