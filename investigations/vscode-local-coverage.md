# VS Code Local coverage investigation

**Date:** 2026-11-07
**Scope:** Evidence review only. No VS Code session, live Copilot/model call, settings change, or implementation change was made.

## Recommendation

Keep the broad VS Code support promise. Treat **Local** as a separate supported runtime and add a Local-specific validation before claiming that the existing Agent Host and hook-contract results cover it. The current evidence does not establish that Local works; it also does not establish that Local is impossible to automate.

The public [`plugin/README.md`](../plugin/README.md#L107) says the hooks work on VS Code Agent Plugins, describes VS Code’s snake_case payload and `Stop` handling, and says the suite covers the VS Code payload schema ([testing claims](../plugin/README.md#L141)). That language does not name Local explicitly. If “VS Code” is intended to include both Local and Agent Host, Local needs its own evidence. Do not silently narrow the promise; maintainers should confirm the intended scope and decide whether Local evidence is a required per-PR check or a separately reported authenticated run.

## Confirmed findings

- **Pinned-suite comparison:** the checkout is `0cb4a09`, a direct child of the requested [public-suite revision `7a3e37b`](https://github.com/github/actions-migrations-via-copilot/tree/7a3e37b29bd17f91f3cd0f854a3508a11d9776fb). Its tree is identical to that parent (the added “Initial plan” commit has no file changes), so the pinned evidence and working-tree files reviewed here are the same.
- **The current VS Code runner tests Agent Host, not Local.** [`run-vscode.sh`](../tests/surfaces/run-vscode.sh#L2) starts `code agent host`, connects through AHPX, and executes the same headless sessions as the CLI runner; it does not launch the VS Code workbench or select Local ([runner setup and execution](../tests/surfaces/run-vscode.sh#L57)). The [surface-test README](../tests/surfaces/README.md#L3) also explicitly calls Local uncovered.
- **Contract tests are not runtime tests.** [`plugin/hooks.test.sh`](../plugin/hooks.test.sh#L38) pipes fabricated CLI and VS Code-shaped JSON directly to hook shell commands and checks their output. This proves those scripts handle the supplied examples; it does not prove that Local loads the plugin, dispatches events, or consumes the outputs.
- **Local is a distinct harness with its own hook contract.** The [VS Code Local hooks reference](https://code.visualstudio.com/docs/agents/reference/hooks-reference) documents Local input such as `hook_event_name`, `tool_name`, `tool_input`, and `stop_hook_active`. The [VS Code hooks guide](https://code.visualstudio.com/docs/agent-customization/hooks) distinguishes Local from the Copilot harness and says that accepting a compatible hook-file format does not make the event payloads equivalent. In Local, `Stop` is about the current execution stopping; it is not evidence that the whole session ended.
- **Local is UI-selectable and has diagnostics.** The hooks guide directs users to choose the Local session target and use the agent debug logs / GitHub Copilot Chat Hooks output channel to inspect execution. This is a path to investigate—not a reason to rule out UI automation.
- **Authentication is a practical prerequisite, not proven identical across harnesses.** The current Agent Host workflow uses `COPILOT_GITHUB_TOKEN` and documents that the GitHub workflow token is not accepted there. This does not prove what Local accepts. A Local run needs an available VS Code Copilot sign-in/entitlement; whether a pre-authenticated test profile can be used headlessly must be verified with maintainers.

## Feasible automation and prerequisites

1. **Workbench UI test (automated):** run the desktop VS Code build in a GUI-capable runner (a virtual display such as Xvfb on Linux is one option), open a disposable workspace/profile, use a UI driver such as Playwright/Electron automation to explicitly select Local, and submit a fixed harmless probe. VS Code’s [extension testing documentation](https://code.visualstudio.com/api/working-with-extensions/testing-extension) describes launching VS Code for integration tests; an extension test harness alone is not proof that the Copilot chat UI and Local selector are driven, so first demonstrate that the chosen driver can reach those controls.
2. **Maintainer-operated UI smoke (semi-automated):** on a trusted desktop, select Local and run the same disposable fixture while capturing the sanitized hook/debug evidence below. This is feasible even if CI authentication or display setup is not ready.

Both options require a VS Code version with the Copilot Chat/agent UI and Local target, a trusted disposable workspace if required by the hook source, and an account with Copilot access. The hooks guide says `chat.useHooks` controls Local hook execution; do not change this or any user/editor setting for this investigation. First check whether hooks are enabled under the intended profile and establish the supported default. The profile should be disposable and pre-authenticated only through an approved method; do not put credentials in the repository or assume the Agent Host token path works for Local. OAuth, MFA, or policy prompts may require a maintainer to authenticate interactively.

## Smallest distinguishing smoke test

Use one disposable workspace and the real plugin (or a probe plugin installed through the same Local plugin-discovery path). Start an explicitly **Local** session, make one fixed request that attempts a destructive operation against a scratch-only sentinel, and let the turn finish so the `Stop` hook runs. The test should assert:

- a Local hook invocation is recorded with its event name and the observed `tool_name`/`tool_input` shape;
- the expected pre-tool denial is surfaced and the scratch sentinel remains unchanged; and
- one scorecard/Stop record is produced, with no repeated block when `stop_hook_active` is true.

Use synthetic test data only. Keep the fixture’s audit record to event/tool identifiers and pass/fail facts—do not capture prompts, tool arguments, results, or credentials wholesale. A passing contract test or Agent Host session must not substitute for this smoke.

### Proving Local actually ran

Do not use the test label, a passing score, or snake_case fields alone as proof: they can be supplied by a runner, and Agent Host also exercises a VS Code-shaped payload. Retain sanitized evidence that ties together (1) the workbench’s **Local** target selection for the tested session, (2) VS Code’s Local agent/hook diagnostics for that same session, and (3) the corresponding hook event and expected denial/Stop result. Record the VS Code version and session identifier (or a non-sensitive correlation value). If available diagnostics do not identify the Local harness for that session, the result is inconclusive until the evidence method is agreed; do not infer Local from an Agent Host log.

## Maintainer decision

Confirm that the public VS Code support promise includes both Local and Agent Host (recommendation: yes), and decide whether the first Local result should gate each PR or be a documented manual/periodic authenticated check. Also approve the runner/authentication approach and the evidence acceptable for identifying Local. This investigation changes neither the support wording nor user/editor settings.
