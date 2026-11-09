---
name: plugin-surface-testing
description: 'Test and investigate Copilot plugins, hooks, skills, rules, and agents across the CLI, VS Code Agent Host, VS Code Local, and the cloud agent. Use when running this repository testing suite, reproducing regressions, checking coverage, or analyzing saved results. Prove behavior from recorded hook and tool evidence, not the model summary.'
---

# Plugin Surface Testing

This repository owns both the testing method and the executable suite under
`tests/surfaces/`. Update them together in the same pull request. The private
runner may use a versioned copy of this skill, but it is not a second source.

Read [compatibility, payloads, and test recipes](./references/compatibility.md)
when investigating a specific surface or historical failure. Its dated results
are evidence from those runs, not promises about every later version.

## First identify what is being tested

- Record the plugin source commit, actual runtime version, model, and session.
- Separate repository hooks from hooks packaged inside plugins. A passing
  repository-hook test does not prove that plugin loading works.
- Separate VS Code Agent Host from the older Local mode. State an untested
  surface explicitly; do not silently count it as supported or passed.
- Separate plugin behavior from migration correctness. The current suite does
  not prove that a converted pipeline preserves every source behavior.

## Prove the result

1. Confirm the intended plugin and configuration loaded. In cloud tests, check
   the default-branch settings and fixture revision before starting the task.
2. Capture raw hook input, command identity, output and exit status. Preserve
   evidence before the runtime deletes its temporary workspace.
3. Match each case to its actual tool call. A report that repeats a marker or a
   missing file by itself is not proof of enforcement.
4. Require the expected hook decision and the resulting file state together.
   Distinguish the plugin's denial from built-in tool safety or an API error.
5. For rules, distinguish discovery, delivery to the model, and following the
   instruction. A registered rule and an absent marker do not identify a cause.
6. For agent selection, attempt the actual agent. Use a repository-agent positive
   control before interpreting plugin-agent startup rejection as a limitation.

Missing logs mean execution is not proven. Investigate loading, log destinations,
and workspace disposal before claiming a hook never ran. Missing cases, surfaces,
and unexecuted tests must remain visible and must not become passes.

## Run and interpret the suite

Start with the suite README and case definitions in `tests/surfaces/` at the
same source revision. The CLI and Agent Host runners use separate repository
and plugin sessions. Cloud sessions additionally require a versioned marketplace
and matching default-branch configuration; serialize sessions that change it.

For a historical VS Code comparison, pin the actual Agent Host server commit.
An old CLI can start a newer server. Use the editor customization interface for
editor-loader bugs; CLI-installed plugins alone did not reproduce those bugs.
Retain the server's ready message and plugin-discovery evidence.

Report these outcomes separately:

- **PASS:** the expected behavior has evidence.
- **DEVIATION:** observed behavior differs from the documented expectation.
- **FAIL:** an actual plugin safety check failed.
- **NOT RUN:** execution or the result is not established.

An expected deviation is still a limitation. Do not remove it without a fresh
successful retest. Different outcomes across different revisions do not establish
nondeterminism; repeat an otherwise identical case when that question matters.

## Analyze a failure

Classify it as a plugin defect, a runtime behavior change, a test defect, or
unresolved. Quote the relevant hook/tool evidence, separate facts from assumptions,
and propose the smallest test that distinguishes the remaining explanations.

Do not treat the agent's own explanation as proof. Do not weaken assertions or
add expected failures merely to make CI green. Keep human decisions about scope,
access, deployment and merging separate from automated analysis.

## Rules and model-dependent checks

- Separate rule-file discovery, the host reading its exact text, inclusion in
   a model request, the model attempting the action, tool completion, and the
   resulting file. Evidence for one stage does not prove the next stage.
- Rules guide model behavior; hooks execute code and can enforce a denial.
   A missed synthetic rule marker alone does not prove a broken migration or a
   bypassed security hook. Test those outcomes separately.
- Start with one rule, no selected agent, and a neutral task. Pin the suite,
   runtime, model selector, and prompt hash. Choose a fixed number of trials and
   retain every outcome; do not retry until green. A passing combined suite does
   not erase a failing isolated check that the combined workflow never ran.
- Verify the evidence source on the actual surface. Agent Host may not create
   the CLI session logs a runner expects. Use structured client events and match
   the exact write target and call ID; a read, report mention, or failed session
   cannot prove successful instruction-following.
- An observer loading is not proof that its callback attached or measured a
   request. Validate instrumentation separately, record when it observes nothing,
   and never interpret missing measurements as missing rule delivery. Prefer
   hashes and presence checks for the test rule over publishing model requests,
   unrelated instructions, or credentials.
- Stop repeating marker-only tests once the missing evidence is model-request
   delivery. Record the unresolved boundary and the runtime trace needed to cross
   it. Keep the limitation visible while improving the rest of the suite; neither
   a finite set of passes nor a clean PR guarantees future model compliance.

## Safety and maintenance

Use disposable test inputs and fake credentials, never customer secrets. Give
test execution only the access it needs. Keep unreviewed code away from repository
writers and trusted caches. Review the exact fork commit before privileged tests,
and do not mistake that review for technical isolation.

Filter evidence before publication. Keep private repository identities, credentials,
internal-only findings and runtime model catalogs out of public artifacts.

When deploying a copy of this skill, copy the reference file too. Record the
source repository, commit, file paths and content hashes. Refresh from this repo
through a reviewed change; never edit the deployed copy independently. Use that
recorded revision when locating suite code from an evidence-only checkout.