# Plugin tests

Runs the real `plugin/` on the Copilot CLI and on VS Code (the headless Agent Host) and checks behavior this repository owns.
They don't test whether each Copilot surface follows its own rules in general.

| Check | What it proves |
|---|---|
| `plugin-installed` | The plugin loads with every agent and skill in `plugin/` (names read from the files) |
| `secret-guard-blocks-credential` | A fake credential is refused and never written |
| `delete-guard-blocks-delete` | `rm hc-out/keep.txt` is refused by the delete guard and the file survives (the secret guard runs on the same call first, so this also fails if it stops later hooks) |
| `safe-write-allowed` | The guards don't block a harmless write |
| `scorecard-written` | `.github/MIGRATION-SCORECARD.md` gets exactly one entry |
| `skill-loads` | The `actionlint` skill loads from the plugin |
| `agent-starts` | The `jenkins-migrator` agent is selected and does a small task (one sample: all agents load the same way) |

Each check is PASS, FAIL or NOT RUN. Anything but PASS fails the run. The result is `result.json`, written only by `score.py`, so it never contains raw logs.

Tool permissions are granted only for the exact calls the prompts ask for (`approve_tool.mjs` for VS Code, `--allow-tool` for the CLI), so a refusal comes from the plugin's hooks.

## When it runs

- **PRs and `main`:** pinned CLI and VS Code versions (`PINNED_*` in the workflow). A failure means the change broke something.
- **Weekly:** latest versions. A failure means an upstream release broke the plugin; it doesn't block PRs.
- **Manually:** any version, for example `vscode_version: 1.139.1` to reproduce an old bug.
- **Fork PRs:** offline tests only, never with Copilot credentials.

## Run locally

```bash
python3 -m unittest discover -s tests/plugin -p 'test_*.py'          # offline, no Copilot access

export COPILOT_GITHUB_TOKEN=...                                       # a Copilot user's token
COPILOT_BIN=$(command -v copilot) OUT_DIR=/tmp/out bash tests/plugin/run-cli.sh
CODE_BIN=/path/to/vscode-cli/code OUT_DIR=/tmp/out bash tests/plugin/run-vscode.sh
```

VS Code needs the standalone VS Code CLI (`code`). The VS Code runner installs the pinned test client from `ahpx/package-lock.json` and patches it with `patch_ahpx.py` so the Agent Host loads the plugin the way the editor does.

## Not here

Cloud agent smoke tests come in a follow-up once credential ownership is agreed. Broader conformance testing of the Copilot surfaces lives in the testing repository.
