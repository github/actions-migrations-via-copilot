# Migration correctness test design

## Confirmed evidence

- The requested public reference is commit `7a3e37b29bd17f91f3cd0f854a3508a11d9776fb`. This checkout is at `3d1c9bf14c6cf924afd51a638a200b40290e54c1`; the commits differ, but both have tree `23a31fc53eee54b7ebf405c9ecee53a6c432c335`, so the checked-in content is identical at those revisions. The findings below are pinned evidence, not claims about later code.
- The migration core calls for preserving source behavior, translating triggers, conditions, dependencies, secrets and deployment gates, linting with `actionlint`, pinning actions, using least-privilege permissions, and moving source files into `.github/ci-archive/` (`plugin/skills/migration-core/SKILL.md`). Platform mappings cover distinct constructs such as GitLab `rules`/manual jobs, Azure stages and `dependsOn`, and Jenkins parallel stages and `input` (`plugin/skills/{gitlab-migration,azure-devops-migration,jenkins-migration}/`).
- Existing offline tests exercise hooks, plugin loading, configuration and artifact handling (`tests/surfaces/test_evidence.py`, `scripts/refresh-pinned-actions.test.sh`). They do not compare a source pipeline with its migrated workflow. The surface workflow also has separate Copilot-backed CLI/VS Code jobs (`.github/workflows/surface-tests.yml`); those test the plugin surface, not migration correctness.

## Recommendation (design only)

Start with three tiny, redistributable fixture pairs; use fake secret *names* only, never credential values or customer configurations:

| Fixture | Source constructs to preserve |
|---|---|
| GitLab `.gitlab-ci.yml` | Branch/MR triggers and `rules`; build → test → manually gated production deploy; `needs`; environment and a secret reference. |
| Azure `azure-pipelines.yml` | Branch/PR filters; ordered stages with `dependsOn` and a success condition; deployment environment. Note source-side approval configuration separately if it is external to the YAML. |
| Jenkins `Jenkinsfile` | Conditional and parallel stages; an `input` gate; a credentials binding by name; archived build artifact. |

Keep each pipeline to a few jobs and one or two conditions. Pair each with a reviewed target workflow and a small explicit contract (expected events/branches, job dependency edges, condition outcomes, gate/environment, secret names, and archive paths); avoid whole-file snapshots so harmless formatting changes do not break tests.

An offline checker can deterministically assert, within this bounded feature set:

- mapped events and branch filters match the fixture contract, and simple conditions behave as expected for a small branch/event truth table;
- target job dependencies preserve required stage order and parallelism;
- secret references preserve names and contain no literal values; gated deploy jobs name the intended GitHub Environment;
- declared permissions are no broader than the fixture's reviewed expectation; every `uses:` reference is a full commit SHA with its version comment;
- source files are absent from their original paths and byte-identical copies are in the archive; and `actionlint` accepts each target workflow.

These are structural checks, not proof of runtime equivalence. Human review remains necessary for source/target semantic differences, complex expressions, implicit defaults, whether environment protection rules actually require approval, secret scope and least-privilege judgments, and any deployment behavior. Do not execute deployments.

## Cost and placement

- **PR:** Run the fixture checker and `actionlint` offline on every change to migration skills, fixtures, or checker. No model calls, network dependency, real credentials, deployment, or paid external systems; this should have no model cost.
- **Scheduled:** The initial layer needs no scheduled run; the same offline check can run on the default branch. If maintainers later want to measure actual model-generated output, keep that as a separate, explicitly approved experiment: at most one generation per fixture per run (three total), no retries or deployment, synthetic inputs only, and a hard spend cap set by the budget owner. This task does not authorize or require that experiment.

## Smallest next test and decision

The smallest useful increment is one GitLab fixture pair with build/test/manual-deploy jobs and one fake secret name. Check its trigger/rule contract, dependency, environment gate, secret reference, least-privilege permission expectation, action pins, source archival, and `actionlint` result offline. This validates the fixture/checker contract; without a model call it does **not** establish that the agent will generate that output.

Maintainers need to decide whether to accept this bounded GitLab case as the initial contract and later add the Jenkins/Azure cases, and whether any future scheduled model evaluation has an owner-approved budget. Approval configuration and deployment outcomes should remain explicitly outside deterministic PR checks.
