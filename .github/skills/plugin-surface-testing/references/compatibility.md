# Compatibility and Test History

Detailed reference for the [plugin surface testing skill](../SKILL.md) maintained
with this repository's suite. Historical findings below retain their test dates;
check the latest run before describing current support.

## When to Use

- Testing hooks, skills, or agents on any Copilot surface
- Debugging "the hook didn't fire" or "my agent doesn't appear"
- Validating plugin distribution before a release
- Answering "does surface X support Y?" — check the surface matrix first

---

## Rule 1 — Never trust the outcome; prove the hook fired

**This is the single most important lesson from this work.** An agent that
appears to behave correctly proves nothing. Five real incidents, all of which
looked like success or failure and were neither:

| What we saw                                                | What we concluded                     | What was actually true                                                                                                                                                                                                      |
| ---------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| VS Code refused to delete `README.md`                      | "Our destructive guard works"         | **VS Code's own terminal safety** blocked it. Our hook never ran.                                                                                                                                                           |
| `audit-log.sh` produced entries in VS Code                 | "Hook is wired up"                    | It logged `tool:"null"` — fired, but read CLI field names against a VS Code payload. Useless data.                                                                                                                          |
| CCA agent deleted files despite a deny hook                | "Hooks don't work on CCA"             | Hook fired fine. The **matcher missed the MCP tool names** the agent routed through.                                                                                                                                        |
| No VS Code records in the capture log (2026-09-26)         | "Agent Host doesn't run plugin hooks" | The capture script only kept records whose `cwd` matched. Agent Host 1.139.1 sent plugin hooks `workingDirectory` instead, so every record was dropped.                                                                     |
| The delete guard didn't block `rm` in VS Code (2026-09-26) | "Our guard is broken"                 | A **second enabled plugin** printed `{}` first. Tested VS Code Agent Host 1.139.1 stops at the first JSON output, so our guard never ran. See [microsoft/vscode#338457](https://github.com/microsoft/vscode/issues/338457). |

Every one of these was resolved the same way: **capture the raw payload and
read it.** Not the agent's summary. Not the PR diff. The actual hook stdin.

### The capture harness

Put it where the hooks under test are loaded from. That's a plugin's own hooks
file: root `hooks.json` for a legacy plugin, or
`com.github.copilot/hooks/hooks.json` for an
[Agent Plugins 1.0](#agent-plugins-10-format-support-2026-10-16) plugin. Each
surface reads only one of those, so a copy in the wrong file says nothing about
the real hooks. A repo-level `.github/hooks/zz-debug-capture.json` proves only
that repository hooks load, not that the plugin's did. It records every event on
every surface without changing behavior:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "p=$(cat | tr '\\n' ' '); mkdir -p /tmp/hook-debug; printf '{\"ts\":\"%s\",\"event\":\"sessionStart\",\"payload\":%s}\\n' \"$(date -u +%FT%TZ)\" \"${p:-null}\" >> /tmp/hook-debug/capture.jsonl"
      }
    ],
    "userPromptSubmitted": [
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "p=$(cat | tr '\\n' ' '); mkdir -p /tmp/hook-debug; printf '{\"ts\":\"%s\",\"event\":\"userPromptSubmitted\",\"payload\":%s}\\n' \"$(date -u +%FT%TZ)\" \"${p:-null}\" >> /tmp/hook-debug/capture.jsonl"
      }
    ],
    "preToolUse": [
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "p=$(cat | tr '\\n' ' '); mkdir -p /tmp/hook-debug; printf '{\"ts\":\"%s\",\"event\":\"preToolUse\",\"payload\":%s}\\n' \"$(date -u +%FT%TZ)\" \"${p:-null}\" >> /tmp/hook-debug/capture.jsonl"
      }
    ],
    "postToolUse": [
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "p=$(cat | tr '\\n' ' '); mkdir -p /tmp/hook-debug; printf '{\"ts\":\"%s\",\"event\":\"postToolUse\",\"payload\":%s}\\n' \"$(date -u +%FT%TZ)\" \"${p:-null}\" >> /tmp/hook-debug/capture.jsonl"
      }
    ],
    "agentStop": [
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "p=$(cat | tr '\\n' ' '); mkdir -p /tmp/hook-debug; printf '{\"ts\":\"%s\",\"event\":\"agentStop\",\"payload\":%s}\\n' \"$(date -u +%FT%TZ)\" \"${p:-null}\" >> /tmp/hook-debug/capture.jsonl"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "p=$(cat | tr '\\n' ' '); mkdir -p /tmp/hook-debug; printf '{\"ts\":\"%s\",\"event\":\"Stop\",\"payload\":%s}\\n' \"$(date -u +%FT%TZ)\" \"${p:-null}\" >> /tmp/hook-debug/capture.jsonl"
      }
    ],
    "sessionEnd": [
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "p=$(cat | tr '\\n' ' '); mkdir -p /tmp/hook-debug; printf '{\"ts\":\"%s\",\"event\":\"sessionEnd\",\"payload\":%s}\\n' \"$(date -u +%FT%TZ)\" \"${p:-null}\" >> /tmp/hook-debug/capture.jsonl"
      }
    ]
  }
}
```

Three rules keep the harness from changing what it measures:

- **Print nothing.** The June 2026 version printed `{}`. In tested VS Code Agent Host 1.139.1, that made every later plugin hook for the event silently skip, including the plugin's own guards.
- **Log everything, and never filter on `cwd`.** Agent Host 1.139.1 sent plugin hooks `workingDirectory` instead of `cwd`.
- **Use flat entries, as in the [GitHub hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference).** `version: 1` with camelCase events also loads in VS Code Local, which maps them to its own names. Copilot CLI fires both `agentStop` and `Stop`, so expect two stop records there.
- **Write one JSON record per line.** The payload is wrapped as-is, so a multi-line payload or an event name inside a tool's content can't break parsing or counting. The hook itself needs no `jq`, so a missing `jq` can't look like "the hook never ran".

Then run **one** agent prompt and read it:

```bash
jq -c . /tmp/hook-debug/capture.jsonl
jq -s 'map(select(.event == "preToolUse")) | length' /tmp/hook-debug/capture.jsonl   # did it fire at all?
jq -r 'select(.event == "preToolUse") | .payload.toolName // .payload.tool_name' /tmp/hook-debug/capture.jsonl
```

**If the capture file is missing, hook execution is not proven.** Check loading
errors, log destination, and whether the runtime disposed of the test workspace.
Do not turn missing evidence into a PASS or assume it proves the hook was absent.

### Three questions to answer before declaring a hook result

1. **Did it fire?** → capture log exists and has an entry for that event
2. **Did it read the right fields?** → the logged payload has the field your
   script reads, not `null`
3. **Did the matcher catch the tool the agent actually used?** → the logged
   `toolName`/`tool_name` matches your matcher regex

---

## Surface matrix

Agent Host and Local are separate VS Code execution paths with different hook
implementations. Test both while claiming support for both; passing Agent Host
does not establish Local compatibility. If a product supports only Agent Host,
state that limit explicitly rather than counting Local as passed or silently
dropping it. Older results below remain dated observations; see the
[automated-suite recipe](#automated-regression-suite-2026-11-07) for newer results.

Verified behavior. Dates are when the fact was last confirmed. VS Code has two
separate hook implementations, so it has two columns. **Agent Host** is the
Copilot session target used for plugin testing since September. **Local** is
the built-in harness, and the June results came from it. Agent Host results
are from 1.139.1. The fix originally targeted 1.141
([microsoft/vscode#338512](https://github.com/microsoft/vscode/pull/338512))
and was backported to stable 1.140.0 in
[#338528](https://github.com/microsoft/vscode/pull/338528). Source/package
inclusion is verified, and the fixed editor **was re-tested live on 1.141.0 on
2026-10-07** — see [the retest table](#vs-code-agent-host-11410--live-retest-2026-10-07). The **github.com cloud agent (CCA)** results from 2026-09-30 come from the
[conformance test](#docs-based-conformance-test-cli-vs-code-cloud-agent) as
repository hooks, plus a real plugin loaded from the org's `.github-private`.

| Capability                                                      | CLI                                  | VS Code Agent Host (1.139.1)                                                                                            | VS Code Local                                              | github.com cloud agent (CCA)                                                                                                                                  | Verified   |
| --------------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Plugin install                                                  | `copilot plugin install`             | User-level `chat.pluginLocations`; CLI-installed plugins are also synced                                                | `chat.pluginLocations` or `enabledPlugins`                 | `enabledPlugins` + `extraKnownMarketplaces` in `.github/copilot/settings.json`, in the org's `.github-private` or the consumer repo. Marketplace plugins only | 2026-09-30 |
| Plugin skills load                                              | ✅                                   | ✅                                                                                                                      | ✅                                                         | ✅                                                                                                                                                            | 2026-09-28 |
| Plugin agents in picker                                         | ✅                                   | not tested                                                                                                              | ✅                                                         | ❌ — needs `.github/agents/*.agent.md` in consumer repo. Selecting a plugin agent via the API fails to start, any format                                      | 2026-10-16 |
| `sessionStart` / `userPromptSubmitted` / `sessionEnd`           | ✅                                   | ✅                                                                                                                      | not tested                                                 | ✅                                                                                                                                                            | 2026-09-30 |
| `preToolUse` / `postToolUse` fire                               | ✅                                   | ✅ but see next row                                                                                                     | ✅                                                         | ✅                                                                                                                                                            | 2026-09-30 |
| **All hooks for an event run**                                  | ✅                                   | ❌ on 1.139.1 **stops at the first command that prints JSON, even `{}`**; ✅ **verified fixed on 1.141.0 (2026-10-07)** | not tested                                                 | ✅ including a plugin's `{}` followed by the same plugin's deny                                                                                               | 2026-10-07 |
| Later `preToolUse` hooks after a deny or exit 2                 | Skipped; the call is already blocked | Skipped on 1.141.0; verified C1/C3                                                                                      | not tested                                                 | Skipped, same as CLI                                                                                                                                          | 2026-10-07 |
| `preToolUse` exit code 2 = deny                                 | ✅                                   | ❌ treated as no output on 1.139.1; ✅ verified on 1.141.0 in C3, raw exit 2 and file absent                            | not tested                                                 | ✅                                                                                                                                                            | 2026-10-07 |
| `agentStop` / `Stop`                                            | ✅ both fire                         | ❌ neither fires on 1.139.1; ✅ **both fire on 1.141.0 (2026-10-07)**, `Stop` with a snake_case payload                 | `Stop` only                                                | ✅ both fire                                                                                                                                                  | 2026-10-07 |
| Repo `.github/hooks/*.json`                                     | ✅ including `-p` on 1.0.89          | ✅                                                                                                                      | ✅                                                         | ✅                                                                                                                                                            | 2026-09-30 |
| Matchers honored                                                | ✅                                   | ❌ ignored for plugin hooks on 1.139.1; ✅ **honored on 1.141.0 (2026-10-07)**                                          | ❌ **parsed but ignored** — every hook runs on every event | ✅                                                                                                                                                            | 2026-10-07 |
| Agent Plugins 1.0 hooks (`com.github.copilot/hooks/hooks.json`) | ✅                                   | ✅ (1.141.0)                                                                                                            | not tested                                                 | ❌ **ignored**; reads root `hooks.json` instead. See [Agent Plugins 1.0](#agent-plugins-10-format-support-2026-10-16)                                         | 2026-10-16 |
| Plugin rules (`alwaysApply: true`)                              | ✅                                   | not tested                                                                                                              | not tested                                                 | ❌ **none applied, in any plugin format**                                                                                                                     | 2026-10-16 |

"Expected fixed" means the fix hands plugin hooks from plugin folders
to the Copilot runtime, the same engine as Copilot CLI. Those rows are now
**confirmed live on 1.141.0** — see the next section. The 1.139.1 column is kept
to distinguish the tested affected version from the verified fixed version.

### VS Code Agent Host 1.141.0 — live retest (2026-10-07)

First live retest on a fixed build, closing the pending item above. Editor
**1.141.0** (`2a59476c9bfcb90b3ddc372c36762471b7dfad1c`), plugin hooks from three
plugin folders. Both scored sessions used the test folder as the actual
workspace root. A separate misrouted session is excluded.

| Behavior                          | 1.139.1                | 1.141.0                         | Evidence                                                                                                                                            |
| --------------------------------- | ---------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| All hooks for an event run        | ❌ stops at first `{}` | ✅ **fixed**                    | `candidate` printed `{}`, then 4 later plugin hooks still ran on the same call                                                                      |
| Matchers honored                  | ❌ ignored             | ✅ **fixed**                    | `postToolUse` matcher `create\|edit` correctly did _not_ fire on `apply_patch`, while an unmatched hook did                                         |
| Plugin hooks get `cwd`            | ❌ `workingDirectory`  | ✅ `cwd`, no `workingDirectory` | payload keys `cwd, prompt, sessionId, timestamp`                                                                                                    |
| `agentStop`                       | ❌ never fires         | ✅ **fires**                    | 2 per session (two plugins)                                                                                                                         |
| `Stop`                            | ❌ never fires         | ✅ **fires**                    | 2 per session, not skipped. Payload is **snake_case** (`session_id`, `stop_reason`, `hook_event_name`) while `agentStop`/`sessionEnd` are camelCase |
| `sessionEnd`                      | ✅                     | ✅                              | one scorecard entry per session, no duplicate                                                                                                       |
| `preToolUse` deny via JSON object | ✅                     | ✅                              | synthetic credential blocked, file absent                                                                                                           |
| `preToolUse` exit code 2 = deny   | ❌                     | ✅ **fixed**                    | C3: `pre1` returned exit 2, later hooks skipped, `hc-out/c3.txt` absent                                                                             |

The conformance session passed all ten
scored cases, including same-plugin and cross-plugin `{}` followed by deny,
exit 2, post-hook ordering, matchers, lifecycle, and documented payload fields.
It captured 81 records, including both lifecycle session-ID spellings. The
candidate's secret guard returned `{}` before its deletion guard denied the
disposable deletion; the target remained present.

A full migration session captured 146 records.
It loaded all three required skills and moved references, denied exactly one
unchanged synthetic credential without echoing its value, archived the Jenkinsfile
byte-for-byte, wrote the report, passed actionlint, and produced one scorecard.
All captured candidate command hashes match PR #54 source at `25e2495`, including
`agentStop`, `Stop`, and `sessionEnd`. The first token-shaped fixture was masked
before reaching the hook and is not counted as a negative test.

Built-in Local, `subagentStop`, and
marketplace installation were not tested.

**All three of `agentStop`, `Stop` and `sessionEnd` now fire**, and `candidate` still
wrote exactly one scorecard entry per session, so its deduplication holds when all
three run. But the payload casing is **not uniform across events on the same
surface**:

| Event        | Casing                                                               | Session field    |
| ------------ | -------------------------------------------------------------------- | ---------------- |
| `agentStop`  | camelCase (`stopReason`, `transcriptPath`)                           | `sessionId`      |
| `Stop`       | **snake_case** (`stop_reason`, `transcript_path`, `hook_event_name`) | **`session_id`** |
| `sessionEnd` | camelCase (`reason`)                                                 | `sessionId`      |

A per-session filter that reads only `.sessionId` drops every `Stop` record and makes
`Stop` look dead. That mistake was made and corrected while writing this entry — read
`.sessionId // .session_id` for lifecycle events, exactly as you would for tool events.

**Consequence worth planning for: fixing matcher honoring un-masks matcher bugs.**
On 1.139.1 every hook ran on every event, so a too-narrow matcher was harmless. On
1.141.0 a narrow matcher now silently skips. The fixture's `postToolUse` matcher
`create|edit` missed `apply_patch` — the tool the agent actually used — so the
per-write quality hook never fired in either run, on a build where matchers work.
This describes PR #54 at `25e2495`; end-of-turn gates did run and pass.
**Fixed in source on 2026-10-07:** commit `87c4523` adds `apply_patch` and parses
its raw/object patch payloads, resolves workspace-relative paths, and checks all
affected workflows. A matcher-only change was insufficient because the old body
expected a single file path. The new regression failed before the fix; all 94
hook tests and all four CI checks pass at `426fc0f` (formatting-only follow-up).
This follow-up has automated regression coverage, not a fresh live editor run.
Audit matchers against the [tool names per surface](#tool-names-differ-per-surface)
before upgrading.

**CLI and CCA behaved identically in every case on 2026-09-30.** Both ran
`conformance-b.json` before `conformance-a.json`, so don't rely on the order of
hook files. Put hooks that must run in a set order in one file.

### CLI repository trust (verified 2026-10-05)

On CLI 1.0.90-5 and 1.0.100, `--allow-all-tools` alone did not load repository
hooks in a fresh isolated `COPILOT_HOME`. `--add-dir` alone did not establish
hook loading either.

**Use `--trust-folder` for a single non-interactive run** (verified on 1.0.100,
2026-10-23: the same repo hook didn't run with `--allow-all-tools` alone and did
with `--trust-folder` added). The
[CLI programmatic reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference)
says it trusts the folder's hooks, workspace MCP servers, and repository plugin
settings for that session only, without granting tool, path, or URL permissions.
Combine it with `--allow-all-tools` and keep path checks on. An interactive
session's normal workspace-trust approval also works.

Avoid `COPILOT_ALLOW_ALL` for this. The CLI reference says `true` grants full
permissions, while `copilot help environment` on 1.0.100 says it only approves
tools and, set to exactly `true`, also trusts the folder. Don't rely on either
reading. Don't use `--allow-all` or `--allow-all-paths` just to make a test pass.
Only trust a disposable fixture whose configuration and hook commands you have
reviewed.

Evidence from PR #54 testing: an untrusted APM-generated hook fixture allowed a
synthetic credential write with no hook capture. With explicit repository trust,
the same generated commands allowed the safe reference and denied the credential;
`agentStop` and `sessionEnd` ran and one scorecard was written. APM 0.26.0 printed
inline-hook discovery warnings and normalized `Stop` to `stop`, but preserved the
command bodies. This verifies the tested CLI path, not VS Code lifecycle behavior.

The existing conformance kit passed all ten scored CLI cases plus the candidate
plugin's chained deletion denial after trust was established. Create `hc-out/`
before running it: CLI 1.0.90-5's file-creation tool did not create its missing
parent directory. A filesystem failure is not a hook denial.

**The GitHub docs understate CCA plugin support.** The hooks reference says a
cloud agent sandbox "does not ship with … installed plugins" and only has
`.github/hooks/*.json` by default. In practice the org-level plugin from
`.github-private` loaded and its hooks ran (2026-09-30), as they did on
2026-09-25.

### Agent Plugins 1.0 format support (2026-10-16)

The [Agent Plugins 1.0](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)
format is chosen by `$schema` in `plugin.json`. Its manifest is closed: no
`agents`, `skills` or `hooks` fields. Skills stay in `skills/`; Copilot-specific
parts move to `com.github.copilot/agents/`, `com.github.copilot/hooks/hooks.json`
and `com.github.copilot/rules/*.mdc`. Only rules with `alwaysApply: true` are on
by default.

**The cloud agent does not support this layout yet. Copilot CLI does.** Tested
with CLI 1.0.100-0 and the github.com cloud agent on 2026-10-16, using three
probe plugins enabled together from one marketplace:

| Part                                     | CLI                                          | Cloud agent                     |
| ---------------------------------------- | -------------------------------------------- | ------------------------------- |
| Hooks in `com.github.copilot/hooks/`     | ✅ ran                                       | ❌ ignored (5 of 5 runs)        |
| Root `hooks.json` in a 1.0-format plugin | ignored, as the spec says                    | ✅ ran (wrong)                  |
| Hooks in a legacy-format plugin          | ✅                                           | ✅                              |
| Rules, any format                        | ✅ applied                                   | ❌ none (2 of 2 runs)           |
| Agents in `com.github.copilot/agents/`   | ✅ load                                      | ❌ can't be selected; see below |
| Root `agents/` in a 1.0-format plugin    | rejected (`No such agent`), as the spec says | ❌ can't be selected; see below |
| Skills                                   | ✅                                           | ✅                              |

**Plugin agents can't be selected as the cloud agent's custom agent, in any
format, including legacy.** Assigning an issue with `agent_assignment.custom_agent`
set to a plugin agent (with or without the `plugin:` prefix) fails with "The
agent encountered an error and was unable to start working on this issue." A
`.github/agents/*.agent.md` agent in the same repo started fine; its run log
showed `Additional custom agents available: repo-control-agent` and
`Selecting custom agent "repo-control-agent"`. This matches the older finding
that plugin agents need a repo stub, so it is not specific to the 1.0 layout.

**Consequence: a plugin's safety hooks silently stop running on the cloud agent
when it moves to the 1.0 layout.** In testing, a synthetic credential that the
legacy plugin's hook denied was committed by the 1.0-format version. Keep
security hooks in the legacy format until the cloud agent supports the new
layout. Do not ship a root `hooks.json` alongside the 1.0 layout as a
workaround: it only runs because of the gap and may stop when it is fixed.

The tested surfaces read different hook locations. The marker logs establish
that behavior; they do not by themselves identify the internal implementation.

#### How to test which layout a surface reads

- **Use a dual-layout probe.** One 1.0-format plugin with hooks, rules and
  agents in _both_ the namespace folder and the root, each with a distinct
  marker. Whichever markers appear tell you which finder ran, in one session.
  Add a namespace-only plugin and a legacy plugin as controls.
- **Make hooks log to the repo, silently.** One file per marker under a folder
  the agent commits, with no stdout. Count events per file.
- **Test rules by behavior, not by asking.** A rule like "before your final
  commit, create `rule-evidence/<CODE>.txt`" proves it was applied. Asking the
  model to list rule codes is weaker evidence.
- **Test agents by starting them.** CLI: `copilot --agent <plugin>:<agent> -p ...`
  either runs or fails with `No such agent: ..., available: ...`, which lists
  exactly what loaded. Cloud agent: create the issue with
  `agent_assignment: {target_repo, base_branch, custom_agent}`; the run log line
  `Additional custom agents available:` lists what it can select.
- **Use an isolated CLI profile and a local marketplace.** `COPILOT_HOME=<tmp>`,
  then `copilot plugin marketplace add <repo-path>` and
  `copilot plugin install <name>@<marketplace>`. Marketplace plugins from a local
  path load live; edits apply on the next session. Direct path installs are
  deprecated.
- **Cloud agent logs show plugin loading, not parts.** `gh run view <id> --log`
  shows `[plugins] Resolved plugin "<name>"` and `Successfully loaded N/N`,
  but nothing about which hooks, rules or agents were found. Use the probes.
- **The cloud agent declines to inspect its own runtime** (`/opt/copilot-runtime`).
  Don't design a test that needs its bundled CLI version.
- **Wait on the PR branch's run, not a time window.** Filtering
  `gh run list` by date matched older runs and ended the wait early.

### Agent discovery — two distinct mechanisms

Do not conflate these. Putting a file in the wrong place produces an agent that
**silently never appears**, with no error.

| Mechanism                    | Location                               | File extension           | Surface                                        |
| ---------------------------- | -------------------------------------- | ------------------------ | ---------------------------------------------- |
| Org/enterprise custom agents | `.github-private` repo root, `agents/` | `.md`                    | github.com cloud agent, Enterprise AI controls |
| CCA subagents                | consumer repo `.github/agents/`        | **`.agent.md` required** | "assign Copilot" subagent dropdown             |

Plain `.md` does not register for CCA. Plugin-declared agents do not populate
the CCA dropdown — a stub `.github/agents/<name>.agent.md` in the consumer repo
is the workaround.

---

## Payload schemas — ground truth

**2026-09-25 update:** the table below describes the June captures, not every
current payload. CLI 1.0.86 `create` sent an object in `toolArgs` with `file_text`.
The cloud agent sent `apply_patch` with raw patch text in `toolArgs`, not JSON.
Do not discard that text when JSON parsing fails: recognize the patch tool and
scan added lines, preserving credential-removal edits. This gap was reproduced
live and fixed in actions-migrations-via-copilot PR #52, commit `7caf2ae`.

Captured 2026-06-18 for CLI and VS Code Local; the Agent Host column was captured
2026-09-28 on VS Code 1.139.1. This mismatch is the root cause of most "hook fired
but did nothing" bugs.

| Field             | CLI                                                                                                                            | VS Code Agent Host 1.139.1 (plugin hooks)                           | VS Code Local                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- | ----------------------------- |
| tool name         | `.toolName`                                                                                                                    | `.toolName`                                                         | `.tool_name`                  |
| tool args         | `.toolArgs` — **a JSON string, needs double-parse** (June). CLI 1.0.86+: object for `create`, raw patch text for `apply_patch` | `.toolArgs` — object for `create`, raw patch text for `apply_patch` | `.tool_input` — **an object** |
| session           | `.sessionId`                                                                                                                   | `.sessionId`                                                        | `.session_id`                 |
| working directory | `.cwd`                                                                                                                         | **`.workingDirectory`, no `cwd`**                                   | `.cwd`                        |
| result            | `.toolResult.resultType`                                                                                                       | `.toolResult.resultType`                                            | `.tool_response`              |
| event name        | —                                                                                                                              | —                                                                   | `.hook_event_name`            |

In Agent Host 1.139.1, **repository** hooks still receive `cwd`, and only
**plugin** hooks get `workingDirectory`. Repository hooks go through the Copilot
runtime; plugin hooks went through VS Code's own code. The upstream fix and its
1.140.0 backport change that. Read `.cwd // .workingDirectory` for compatibility.

**The github.com cloud agent sends the same fields as CLI** (2026-09-30):
`preToolUse` gets `cwd, sessionId, timestamp, toolArgs, toolName`, and
`postToolUse` adds `toolResult`. A PascalCase `Stop` entry gets the snake_case
form (`hook_event_name`, `session_id`, `stop_reason`, `transcript_path`). Tool
results show the checkout at `/home/runner/work/<repo>/<repo>`, not `/workspace`
as the docs say, so find files from the git root, not a fixed path.

### Tool names differ per surface

| Action            | CLI and VS Code Agent Host                        | VS Code Local                                     | CCA extras                                                                                                       |
| ----------------- | ------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| shell             | `bash`                                            | `run_in_terminal`                                 |                                                                                                                  |
| create            | `create`, or `apply_patch` depending on the model | `create_file`                                     | `apply_patch` in practice; `github-mcp-server-create_or_update_file`                                             |
| edit              | `edit` or `apply_patch`                           | `replace_string_in_file`, `insert_edit_into_file` | `apply_patch`                                                                                                    |
| skill load        | `skill` (also triggers `preToolUse`)              | —                                                 |                                                                                                                  |
| delete            | —                                                 | —                                                 | `github-mcp-server-delete_file`                                                                                  |
| push              | —                                                 | —                                                 | `github-mcp-server-push_files`                                                                                   |
| agent's own tools | —                                                 | —                                                 | `engine-tools-report_progress` (commit and push), `runtime-tools-secret_scanning`, `parallel_validation`, `glob` |

On CCA, the agent's own commit, scan and validation tools also go through
`preToolUse`, and their input can contain file paths and contents. A hook with
no matcher that denies on content can block the agent's own commit. Filter on
write and shell tool names before deciding.

### Event name mapping — register both

| Behavior      | CLI key        | VS Code Agent Host 1.139.1              | VS Code Local key              |
| ------------- | -------------- | --------------------------------------- | ------------------------------ |
| pre-tool      | `preToolUse`   | `preToolUse` ✅                         | `PreToolUse` (auto-converted)  |
| post-tool     | `postToolUse`  | `postToolUse` ✅                        | `PostToolUse` (auto-converted) |
| quality gate  | `agentStop`    | ❌ neither `agentStop` nor `Stop` fires | `Stop`                         |
| session end   | `sessionEnd`   | `sessionEnd` ✅                         | `Stop` (same script)           |
| session begin | `sessionStart` | `sessionStart` ✅                       | `SessionStart`                 |

Copilot CLI and the github.com cloud agent both run a plugin's PascalCase `Stop`
entry as well as `agentStop`, then `sessionEnd`. A plugin that registers for more
than one of these must make sure its end-of-session work runs only once.

**Expected: one scorecard entry per session, on every surface.** Two entries
for the same session is a bug in actions-migrator on `main`, which writes the
scorecard from both `sessionEnd` and `Stop`
([tool issue #49](https://github.com/github/actions-migrations-via-copilot/issues/49)).
It is fixed in [PR #52](https://github.com/github/actions-migrations-via-copilot/pull/52),
which deduplicates. If a test run shows two entries, check that the plugin under
test includes that fix before treating it as a new problem.

### Normalization snippet

```bash
TOOL=$(printf '%s' "$INPUT" | jq -r '.toolName // .tool_name // empty')
ARGS=$(printf '%s' "$INPUT" | jq -c '(.toolArgs // .tool_input) as $a
  | if ($a|type) == "object" then $a
    elif ($a|type) == "string" then (try ($a|fromjson) catch {raw: $a})
    else {} end')
```

A raw `apply_patch` payload isn't JSON, so it lands in `.raw` instead of being
dropped. A content guard must scan the patch's added (`+`) lines in `.raw`, and
allow edits whose only change is removing a credential.

### Emit both output shapes

```json
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "...",
  "additionalContext": "...",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "...",
    "additionalContext": "..."
  }
}
```

CLI reads top-level. VS Code Local reads `hookSpecificOutput`.

**To allow, print nothing.** Don't print `{}`. The GitHub hooks reference only
says "Empty output uses default behavior" for `preToolUse`. VS Code Agent Host
1.139.1 treats `{}` as a final answer and skips every later plugin hook for
that event ([microsoft/vscode#338457](https://github.com/microsoft/vscode/issues/338457)).
Empty output is safe on every surface and version.

**To deny, print a deny object.** Don't rely on exit code 2: Copilot CLI treats
it as a deny, but VS Code Agent Host 1.139.1 ignored it.

**`additionalContext` vs `permissionDecisionReason`:** session-level policy
("do not try alternative tools") must go in `additionalContext`. Putting it in
`permissionDecisionReason` does not work — the agent silently retries through
another tool.

---

## Reading logs per surface

| Surface            | Where the evidence is                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CLI                | `/tmp/hook-debug/capture.jsonl` + terminal output                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| VS Code Agent Host | Your own hook log first. Then `~/Library/Application Support/Code/logs/<newest>/agenthost.log` for plugin sync (`Syncing plugin` / `Failed to sync plugin`) and session start. Then `~/.copilot/session-state/<session-id>/events.jsonl` for tool results. `hook.start` / `hook.end` there show the runtime invoked an event, not that **your** command ran                                                                                                                                          |
| VS Code Local      | `/tmp/hook-debug/capture.jsonl`. Do **not** trust the chat UI — VS Code's own safety prompts look like hook denials                                                                                                                                                                                                                                                                                                                                                                                  |
| CCA                | The sandbox is deleted when the job ends, so have your hooks write their log **inside the repo**, where the agent's commit picks it up. Then read it from the PR branch: `gh api "repos/<owner>/<repo>/contents/<path>?ref=<branch>" --jq .content \| base64 -d`. `agentStop`, `Stop` and `sessionEnd` entries still made it into the commit on 2026-09-30. Also: `gh run view <id> --log` on the `Running Copilot cloud agent` run, where the agent session log shows each tool call and its result |
| gh-aw              | `gh run view <id> --log-failed`; look for `GH_AW_*` env markers in the conclusion step                                                                                                                                                                                                                                                                                                                                                                                                               |

```bash
# CCA: find the agent run, then read it
gh run list --repo <owner>/<repo> --limit 10
gh run view <run-id> --repo <owner>/<repo> --log | grep -iE 'hook|deny|blocked|tool'
```

---

## Test recipes

### Automated regression suite (2026-11-07)

[actions-migrations-via-copilot#61](https://github.com/github/actions-migrations-via-copilot/pull/61)
contains this testing method and its executable suite together. The suite owns
fixtures, runners and scoring; this skill explains how to interpret the evidence.
Maintain both in this repository and update them in the same PR.

- Run repository-hook and plugin-hook sessions separately. The same test cases
  packaged as repository hooks cannot reproduce plugin-only loading defects.
- Test both plugin formats, skills, always-on rules, and actual agent selection.
  Positive behavior must be tied to the component that supplied it.
- Match case markers to actual tool inputs, not the agent's report repeating
  those markers. Record raw hook payloads, emitted decisions, exit codes and
  call identities. Ignore terminal color escapes when parsing runtime output.
- Count missing cases, missing surfaces and unexecuted tests as incomplete.
  A successful process or workflow is not proof of complete coverage.

[Hosted run 42380311478](https://github.com/github/actions-migrations-via-copilot/actions/runs/42380311478)
passed 33 CLI checks and 33 VS Code Agent Host checks, plus seven offline evidence
tests. Each live surface has 13 repository/real-plugin cases and 20 plugin cases.
This does not cover VS Code Local or establish that a weekly cloud-analysis
pipeline is operational.

A later [run on the same day](https://github.com/github/actions-migrations-via-copilot/actions/runs/42386108736)
failed the two VS Code rule checks. Discovery showed both rule components, but
the required marker actions were absent. This does not prove instruction delivery
to the model or identify a runtime defect; the cause remains under investigation.

The same plugin cases were run locally against the genuine VS Code 1.139.1
server (`04c0d99`): 10 PASS and 10 DEVIATION. They reproduced ignored matchers,
short-circuiting after `{}`, ignored exit-code-2 blocks, missing later post hooks,
missing stop events and `workingDirectory` instead of `cwd`. Current server
`c4453f8` passed the same checks.

For a valid headless comparison:

1. Pin and record the actual Agent Host server commit. An old `code` CLI can
   start a newer cached/downloaded server. The suite uses
   `VSCODE_CLI_INITIAL_AH_VERSION` and records the server's ready message; the
   CLI banner alone is insufficient evidence.
2. Send plugins through VS Code's customization interface. CLI-installed plugins
   alone did not reproduce the editor-specific failures. The pinned AHPX client
   needs an adapter for plugin file serving and discovered-agent selection.
3. Capture files before one-shot session disposal. Old builds delete the
   worktree. Mirror hook records outside it so late lifecycle events survive.
4. Keep credentials narrowly scoped, separate PR-controlled code from repository
   writers, and filter artifacts before publishing them.

When the suite changes, update its coverage and this recipe in the same PR.
Analysis deployments that copy this skill must record this repository's source
commit and hashes for the skill and reference files, then refresh through review.
The deployment copy must not become an independently maintained guide.

#### Cloud discovery checks (2026-11-07)

A fresh private test repo confirmed that task-branch configuration alone was
insufficient: repository hooks ran, but plugins did not load. Publishing the same
`.github/copilot/settings.json` on the default branch caused plugin discovery to
run. A repository custom-agent control also needed its `.github/agents/` file on
the default branch before it could be selected. Always verify the configuration
actually used at task startup; the existence of files on a task branch is not
loading evidence.

For isolated cloud sessions, publish a versioned test marketplace with source
commit and file hashes. Validate the default-branch configuration before starting
each session and serialize sessions that require different enabled-plugin sets.
Do not modify a shared organization-wide plugin configuration to run these tests.

Read the exact `Copilot cloud agent` workflow for the task branch, not simply
the newest Actions run: later security scans can otherwise be mistaken for agent
logs. A changed PR title is not proof that the agent run completed.

The real-plugin guard session passed 13 checks after adding a transparent hook
recorder. It preserves the original command, stdout, stderr and exit code and
records a command hash; it does not replace the hook's decision. Generic Actions
logs showed plugin loading but did not expose the individual guard responses.

The plugin session reproduced the new-format hook-location and rule gaps. Both
plugin custom-agent selections were rejected at startup; the same agent defined
in the repository started and wrote its expected marker. Keep startup rejection,
timeout, missing evidence and successful selection separate in results.

Combined cloud result: 13 repository checks PASS; 14 plugin checks PASS and six
confirmed DEVIATION results, with no NOT RUN cases. The six deviations cover the
two hook-location checks, two rule checks and two plugin-agent selections. This
is validation of the test cases, not a claim that the weekly scheduler and
automated analysis handoff have been deployed.

### Local surfaces (CLI / VS Code)

```bash
# Contract tests — bash + jq only, no network, no actionlint
bash plugin/hooks.test.sh

# Install local plugin (reinstall after EVERY hooks.json edit)
copilot plugin install ./plugin

# Confirm hooks registered
copilot
/hooks list
```

### VS Code Agent Host hook test

Use this recipe whenever a result has to hold for VS Code. It is how the
[microsoft/vscode#338457](https://github.com/microsoft/vscode/issues/338457) bug
was found and confirmed.

1. **Clean the plugin list first.** Run `copilot plugin list` and read user-level
   `chat.pluginLocations`. Turn off every other plugin whose tool hooks print
   output, because on tested 1.139.1 their `{}` can stop yours. `copilot plugin disable`
   was not enough to remove a plugin from VS Code; `copilot plugin uninstall` was.
2. **Point user-level `chat.pluginLocations` at a new folder path.** Back up
   `~/Library/Application Support/Code/User/settings.json` first. VS Code keeps
   its own copy of each plugin, and editing a folder it already copied isn't
   reliably picked up, so every changed version gets a new path.
3. **Confirm the sync** in `agenthost.log`: a `Syncing plugin: file:///…` line
   and no `Failed to sync plugin` after it.
4. **For a manual editor test, open the test repo with File → Open Folder.** Start a **new Agent Host chat
   from the VS Code UI** and paste the prompt. A chat started by an agent tool
   ran in a `*.worktrees/…` checkout and did not load the plugin in the earlier
   manual tests. Headless automation now has a separate validated recipe above;
   it must explicitly supply plugins and preserve worktree evidence.
5. **Read your hook log, not the chat.** Each command should append its own name
   first, before any decision, so you can see exactly which commands ran.
6. **After changing hooks mid-chat, send a user message before testing.** VS Code
   only reloads the hook setup when the user sends a message.
7. **Restore the settings** afterwards.

### Minimal two-plugin repro

This is the smallest test that separates "`{}` stops later hooks" from
everything else. Make two plugin folders that differ in one line, and prompt
the agent to create a file containing `BLOCK_ME`:

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {"type": "command", "timeoutSec": 10, "bash": "echo hook1 >> /tmp/hooks.log; echo '{}'"},
      {
        "type": "command",
        "timeoutSec": 10,
        "bash": "echo hook2 >> /tmp/hooks.log; if grep -q BLOCK_ME; then echo '{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"hook2 denied\"}'; fi"
      }
    ]
  }
}
```

Each folder also needs a `plugin.json` with `"hooks": "hooks.json"`. Plugin B
is the same except hook 1 ends with `true`, so it prints nothing. On
2026-09-28 with VS Code 1.139.1, CLI ran both hooks and blocked the file in
both cases. VS Code Agent Host ran only `hook1` and wrote the file for A, and
ran both and blocked the file for B.

### Docs-based conformance test (CLI, VS Code, cloud agent)

Two versions of the kit exist.

- **Plugin version (2026-09-28, CLI vs VS Code).** The original kit was deleted;
  its design is preserved below and implemented by this repository's current suite.
  The plugin (`plugin.json` without `$schema`, root `hooks.json`, one trivial
  skill) holds `pre1`, `pre2`, `pre3` with `"matcher": "bash"`, `post1`, `post2`
  and log-only lifecycle entries. A repo with a committed `.github/hooks/*.json`
  holds one hook that prints `{}` for M8.
- **Repository-hook version (2026-09-30, CLI vs cloud agent).** Put these in
  `.github/hooks/` on a non-default test branch, then start the cloud agent
  against that branch with `gh agent-task create --base <branch>`:
  - `probe.py`: every entry runs this
  - `conformance-a.json`: `pre1`, `pre2`, `pre3-matcher-bash`, `post1`, `post2`
    and lifecycle entries
  - `conformance-b.json`: `pre-b0` (prints `{}` for M9) and `pre-b` (denies M8)
  - `prompt.md` for the cloud agent and `prompt-cli.md` for the CLI baseline
  - `score.py` to score a run
  - `README.md`

Rules that apply to both:

- **One probe script** runs for every entry. It logs every call to a file before
  acting, never filters on `cwd`, and builds marker strings at runtime so the
  hook files don't contain them.
- **It acts only on file-write tools and shell commands that target the test
  folder.** It never acts on the agent's own commit, scan or validation tools,
  or on the results file.
- **One prompt** with a separate tool call per case, asking for the file-creation
  tool rather than shell commands.
- **A scoring script** reads the log for one session and marks each case PASS,
  DEVIATION or NOT RUN.

| Case     | Checks                                                                                                                           | Doc source                                    |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| C0       | Every hook entry for the event runs, and the `bash`-only hook doesn't run for file writes                                        | GitHub hooks reference, VS Code agent plugins |
| C1       | Hook 1 prints nothing, hook 2 denies → blocked                                                                                   | same                                          |
| C2       | Hook 1 prints `{}`, hook 2 denies → blocked                                                                                      | same                                          |
| C3       | Hook 1 exits with code 2 → blocked                                                                                               | GitHub hooks reference, exit codes            |
| C4       | `"matcher": "bash"` runs for `bash`                                                                                              | GitHub hooks reference, matcher filtering     |
| C5       | `postToolUse` prints `{}` → later post hooks still run                                                                           | GitHub hooks reference                        |
| C6       | Lifecycle events fire                                                                                                            | GitHub hooks reference, hook events           |
| C7       | Payload fields match the docs                                                                                                    | GitHub hooks reference, `preToolUse` input    |
| C8 / C8b | `{}` in one hook file, deny in the other → blocked. Two mirrored cases, so the test holds whichever file runs first              | GitHub hooks reference, hook locations        |
| C9       | A plugin prints `{}` (actions-migrator's secret guard), then the same plugin denies (its delete guard, on `rm /tmp/…`) → blocked | same                                          |

CLI baseline, run from the repo. Add `--plugin-dir <actions-migrator plugin>` to
cover C9, because the cloud agent loads that plugin from the org's `.github-private`.
Create `hc-out/` first, since the file-creation tool doesn't create missing
folders. Use `--trust-folder` so repository hooks load without loosening path
checks (see [CLI repository trust](#cli-repository-trust-verified-2026-10-05)). If a
case targets a disposable path outside the repo, such as C9's `rm /tmp/…`, add only
that folder with `--add-dir`:

```bash
mkdir -p hc-out
copilot --plugin-dir <plugin> --trust-folder --allow-all-tools --add-dir <disposable-dir> \
  -p "$(cat .github/hooks/prompt-cli.md)"
python3 .github/hooks/score.py .hook-conformance/probe.jsonl <session-id> --out hc-out
```

Results:

- **2026-09-28:** CLI 1.0.89 passed all 9 plugin-version cases. VS Code 1.139.1
  Agent Host deviated on C0 (matcher), C2, C3, C5 and C6, and passed C1, C4 and
  C8. C7 was partial: plugin hooks got `workingDirectory` instead of `cwd`.
- **2026-09-30:** CLI 1.0.89 and the github.com cloud agent both passed all 10
  repository-hook cases and C9, with identical results.

## Known traps

| Trap                                                         | Detail                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Inferring hook success**                                   | See Rule 1. Always read the capture log.                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| VS Code ignores matchers                                     | Every hook runs on every event, in VS Code Local and in Agent Host plugin hooks (1.139.1). Self-guard inside the script.                                                                                                                                                                                                                                                                                                                                                                              |
| CLI `-p` mode                                                | **Superseded 2026-09-28.** The June note said repo `.github/hooks/*.json` don't load in prompt mode. On CLI 1.0.89 they did load in `-p`, from a repo inside a trusted folder. Re-check on older CLIs.                                                                                                                                                                                                                                                                                                |
| `sessionStart` on reused session                             | Only fires on a brand-new session. Not a bug.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `agentStop`/`sessionEnd` in VS Code                          | **Local:** neither fires; Local sends `Stop`. **Agent Host 1.139.1:** `sessionEnd` fires, but neither `agentStop` nor `Stop` does, so a `Stop` quality gate never runs there. **Agent Host 1.141.0 (2026-10-07):** all three fire — superseded for fixed builds.                                                                                                                                                                                                                                      |
| Reinstall after edit                                         | `copilot plugin install ./plugin` after every `hooks.json` change or you test stale code.                                                                                                                                                                                                                                                                                                                                                                                                             |
| Fake SHAs                                                    | Agents invent plausible-looking commit SHAs. Scorecard checks SHA _format_, not existence. Verify against the real ref.                                                                                                                                                                                                                                                                                                                                                                               |
| CCA has no local filesystem                                  | `./local-path` plugin specs are rejected. Marketplace or repo spec only.                                                                                                                                                                                                                                                                                                                                                                                                                              |
| jq missing                                                   | Hooks fail closed by design. Check `command -v jq` before blaming the hook.                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Inherited plugin interferes with test hooks                  | The cloud agent loads the main-branch plugin through enterprise or org settings even when test-branch repository hooks contain newer code. Verify the resolved plugin commit in runner logs. Keep test lifecycle output separate; do not claim PR plugin distribution was tested.                                                                                                                                                                                                                     |
| VS Code chat target                                          | `code chat --mode agent` can select Copilot Agent Host rather than Local. A VS Code window alone does not prove Local hooks ran; inspect the session target and captures.                                                                                                                                                                                                                                                                                                                             |
| VS Code plugin-location scope                                | In VS Code 1.139.1, `chat.pluginLocations` is machine-scoped. Workspace-only entries did not load the PR plugin. A user-level entry produced an explicit plugin-sync log. Get approval before changing user settings and restore them afterward.                                                                                                                                                                                                                                                      |
| Fixture redaction invalidates a negative test                | A file-read result can replace a synthetic token with literal `******` before the agent writes it. Verify the exact proposed value in the hook input; a written masked placeholder is not a credential-blocking failure.                                                                                                                                                                                                                                                                              |
| Agent Host versus built-in Local                             | Keep these results separate. On 2026-09-25, built-in Local could not fetch models (`unauthorized: chat not enabled for IDE token`), while a fresh Agent Host chat successfully exercised PR hooks. After changing the plugin selection, an already-running turn had no PR captures; the fresh chat did.                                                                                                                                                                                               |
| Desktop plugin sync and repository fallback                  | On 2026-09-25, Desktop-folder Agent Host tests produced no PR captures even with correct user settings. After reload, the host logged `Failed to sync plugin ... No connection for authority`; a fresh registration still did not prove delivery. Installing the unchanged instrumented scripts in `.github/hooks/pr52-test.json` in an initialized scratch repository produced live captures. This is repository-hook evidence, not a successful plugin install.                                     |
| Guard can obstruct test preparation                          | The PR guard denied a synthetic Jenkins source write containing a credential-ID reference and also denied diagnostic shell calls containing synthetic literal examples. Treat this as a false-positive investigation item; do not bypass denials or claim credential-reference conversion was tested.                                                                                                                                                                                                 |
| `{}` stops later plugin hooks in VS Code                     | In tested Agent Host 1.139.1, the first plugin command that prints a JSON object, even `{}`, ends that event. Later commands, including denies from other plugins, never run. A repository hook's `{}` did not stop plugin hooks. Allow by printing nothing. Fix backported to stable 1.140.0 ([microsoft/vscode#338528](https://github.com/microsoft/vscode/pull/338528)); **verified fixed live on 1.141.0, 2026-10-07**.                                                                           |
| Filtering hook logs on `cwd`                                 | Agent Host 1.139.1 sent plugin hooks `workingDirectory`, not `cwd`. A `cwd` filter silently drops every VS Code record and looks exactly like "hook never ran". Log unconditionally.                                                                                                                                                                                                                                                                                                                  |
| `cwd` is the **workspace root**, not the test folder         | Verified 2026-10-07 on 1.141.0. Plugin hooks get the folder VS Code opened, not the directory named in the prompt. A misrouted chat correctly triggered the wrapper's scope guard and skipped commands; this is not a product failure. Open the test folder as the actual workspace root. Keep raw logging unconditional, record skipped execution explicitly, and exclude misrouted sessions. Do not remove lifecycle scope protection: it prevents scorecards being written into another workspace. |
| A fixed build un-masks narrow matchers                       | While matchers were ignored (1.139.1 and Local), a too-narrow matcher was harmless because every hook ran anyway. On 1.141.0 matchers are honored, so the same matcher now silently skips. Re-audit every matcher against [tool names per surface](#tool-names-differ-per-surface) when upgrading — especially `apply_patch`, which models use instead of `create`/`edit`.                                                                                                                            |
| Lifecycle payload casing is **not uniform within a surface** | On 1.141.0, `agentStop` and `sessionEnd` send `sessionId` (camelCase) but `Stop` sends `session_id`, `stop_reason`, `hook_event_name` (snake_case). Filtering a log by `.sessionId` alone drops 100% of `Stop` records and reads as "`Stop` never fires" — this produced a wrong conclusion here on 2026-10-07 before it was caught. Always read `.sessionId // .session_id`.                                                                                                                         |
| Other enabled plugins change the result                      | A leftover test plugin in `chat.pluginLocations` that printed `{}` disabled every other plugin's tool hooks. Check `chat.pluginLocations` and `copilot plugin list` before each VS Code test. `copilot plugin disable` didn't remove a plugin from VS Code; `uninstall` did.                                                                                                                                                                                                                          |
| VS Code reloads hooks only on a user message                 | Hook changes made while a reply is running are ignored until the user sends the next chat message. When an agent drives the test, a reply to one of its multiple-choice questions doesn't count; the user has to type a real message.                                                                                                                                                                                                                                                                 |
| VS Code's plugin copy goes stale                             | VS Code copies each plugin to `~/Library/Application Support/Code/agentPlugins/`. Editing the original folder, or that copy, isn't reliably picked up. Point `chat.pluginLocations` at a new folder path to force a fresh copy.                                                                                                                                                                                                                                                                       |
| Plugin sync can fail                                         | After VS Code restarts while the Agent Host keeps running, new plugin folders failed with `Unable to resolve nonexistent file 'vscode-agent-client://…'`, or with `No connection for authority`. It recovered on its own later. Check `agenthost.log` before every run.                                                                                                                                                                                                                               |
| Agent-created chats skip the plugin                          | A chat started by an agent tool ran in a `*.worktrees/…` checkout and reported `Skill not found`. Start test chats from the VS Code UI in the opened folder.                                                                                                                                                                                                                                                                                                                                          |
| The bundled SDK runtime is not Agent Host                    | Driving VS Code's bundled `copilot-runtime` directly ran no plugin or repository hooks, and reported `Standalone server does not support server effect 'hooks_explicit_plugins'`. Don't use it as a stand-in.                                                                                                                                                                                                                                                                                         |
| Approval mode                                                | Default vs Allow All didn't change hook results. With Allow All, the first send can fail with `Copilot SDK rejected permission mode 'allow-all'`; sending again works.                                                                                                                                                                                                                                                                                                                                |
| A loaded skill proves nothing about hooks                    | VS Code delivers skills and hooks through separate paths. The plugin skill loaded in every failing run. Only your own hook log proves a command ran.                                                                                                                                                                                                                                                                                                                                                  |
| The cloud agent may write files with shell commands          | In the first 2026-09-30 run, the agent created every test file with `printf … > file` through `bash`, although the prompt said "Create the file". A probe that only watched file-write tools logged the calls but blocked nothing. Ask for the file-creation tool explicitly, and make guards cover shell writes too (actions-migrator's secret guard does).                                                                                                                                          |
| Contradictory prompts make the cloud agent stop              | A prompt that said both "don't touch `.hook-conformance/`" and "commit `.hook-conformance/probe.jsonl`" made the agent decline the whole task (test PR #30). Say which files the hooks write by themselves.                                                                                                                                                                                                                                                                                           |
| The agent's own tools pass through `preToolUse`              | On the cloud agent, `engine-tools-report_progress` (its commit), `runtime-tools-secret_scanning` and `parallel_validation` all trigger `preToolUse`. Their input can include file paths and contents, so a content-based deny without a tool-name filter can block the agent's own commit.                                                                                                                                                                                                            |
| Hook file order isn't alphabetical                           | On CLI 1.0.89 and the cloud agent, `conformance-b.json` ran before `conformance-a.json`. Don't depend on the order of hook files. Keep hooks that must run in sequence in one file.                                                                                                                                                                                                                                                                                                                   |
| A denied call skips the remaining hooks                      | On CLI and the cloud agent, once a `preToolUse` hook denies or exits 2, the rest for that call don't run. That's expected, since the call is already blocked. Don't read a missing log line after a deny as "hook didn't fire".                                                                                                                                                                                                                                                                       |
| Cloud agent docs vs reality on plugins                       | The GitHub hooks reference says the cloud agent sandbox has no installed plugins. Plugins enabled in the org's `.github-private` did load and run their hooks (2026-09-25 and 2026-09-30). Test before trusting either.                                                                                                                                                                                                                                                                               |

---
