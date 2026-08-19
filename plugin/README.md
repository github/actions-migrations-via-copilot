# `actions-migrator` — Copilot CLI Plugin

A GitHub Copilot CLI plugin that bundles nine specialized agents for migrating CI/CD pipelines to GitHub Actions, plus a catalog of composable skills covering the standard migration workflow, security guardrails, completion standards, and platform-specific syntax/secrets/report knowledge.

> Looking for the project overview or the cloud-agent variant? See the [top-level README](../README.md).

## Quick Start

### Install from the marketplace (use as-is)

```bash
copilot plugin marketplace add github/actions-migrations-via-copilot
copilot plugin install actions-migrator
```

### Install locally (to customize skills)

```bash
git clone https://github.com/github/actions-migrations-via-copilot.git
cd actions-migrations-via-copilot
copilot plugin install ./plugin
```

### Verify

```bash
copilot plugin list
```

In an interactive Copilot CLI session:

```
/agent          # list available agents (should include the migrators)
/skills list    # list available skills (should include all 11)
```

### Use

Ask Copilot to use the appropriate agent. Examples:

- `Use the jenkins-migrator agent to convert the Jenkinsfile in this repo.`
- `Use the azure-devops-migrator on azure-pipelines.yml.`
- `Use the reusable-workflow-builder agent. Analyze organizations: my-org-a, my-org-b for CI/CD patterns.`

Each migrator agent requires you to point it at real source files — it will refuse to invent pipelines from descriptions.

### Uninstall

```bash
copilot plugin uninstall actions-migrator
```

---

## What's Inside

```
plugin/
├── plugin.json                 # Plugin manifest
├── agents/                     # 9 agents (one per source CI system + reusable-workflow-builder)
│   ├── jenkins-migrator.agent.md
│   ├── azure-devops-migrator.agent.md
│   ├── circleci-migrator.agent.md
│   ├── gitlab-migrator.agent.md
│   ├── travisci-migrator.agent.md
│   ├── bamboo-migrator.agent.md
│   ├── bitbucket-migrator.agent.md
│   ├── droneci-migrator.agent.md
│   └── reusable-workflow-builder.agent.md
└── skills/                     # 11 skills
    ├── migration-core/             # 5-phase workflow + guardrails + deliverables/checklist
    ├── actionlint/                 # Install, run, interpret, and fix actionlint output
    ├── reusable-workflow-patterns/ # Reusable Workflow Builder catalog
    └── <platform>-migration/       # 8 platform skills
        ├── SKILL.md
        ├── mapping.md
        ├── report-template.md
        └── (jenkins only) pipeline.md, groovy.md
```

## Composition Model

Every migration agent loads:

1. **`migration-core`** — 5-phase process, guardrails, deliverables, archival, completion checklist
2. **`actionlint`** — install, run, interpret output, and fix errors
3. **1 platform skill** — mapping and report-template for the source CI platform

The Reusable Workflow Builder loads `reusable-workflow-patterns` + `migration-core` + `actionlint`.

This replaces the previous pattern of agents fetching `knowledge/*.md` files at runtime from a private `.github-private` repo via the GitHub MCP server — everything now ships locally with the plugin.

---

## Hooks — Deterministic Enforcement

The plugin includes hooks that run deterministic checks during migrations. Unlike skills and agent instructions (which the model can choose to ignore), hooks execute as shell commands at specific lifecycle points and can **block** operations or **inject warnings** into the agent's context.

### `hooks.json`

| Hook | Event | Matcher | What it does |
|------|-------|---------|-------------|
| Secret detection | `preToolUse` | `create\|edit` | Hard-denies file writes containing hardcoded secrets (passwords, tokens, API keys). Forces use of `${{ secrets.NAME }}`. Uses `permissionDecision: "deny"`. |
| File deletion guard | `preToolUse` | `bash` | Hard-denies `rm` operations outside `.github/ci-archive/`. Prevents accidental deletion of application source code. |
| Quality check + actionlint | `postToolUse` | `create\|edit` | After any workflow file write, injects `additionalContext` with: unpinned actions (tag vs SHA), placeholder text (TODO/FIXME), over-broad permissions (`write-all`), missing permissions block, and actionlint errors. The agent sees these on the same turn. |
| **Quality gate** | `agentStop` | — | Scans ALL workflow files when the agent finishes a turn. If any have issues, returns `decision: "block"` forcing the agent to take another turn to fix them. Safety valve releases after 3 attempts to prevent infinite loops. |
| **Migration scorecard** | `sessionEnd` (CLI) / `Stop` (VS Code) | — | Appends an entry to `.github/MIGRATION-SCORECARD.md` with session ID, timestamp, completion reason, and per-file workflow table (total / clean / with-issues). Multiple passes show quality progression. Audit artifact for migration quality tracking. |

The hooks run on all three Copilot surfaces — **CLI**, **Cloud agent**, and **VS Code Agent Plugins** — from this single `hooks.json`. The surfaces send different payload schemas (e.g. CLI `toolName`/`toolArgs`-string vs VS Code `tool_name`/`tool_input`-object, and CLI `sessionEnd` vs VS Code `Stop`); each hook normalizes its input and emits both output shapes so the same file works everywhere.

### Why hooks matter

The `migration-core` skill already contains guardrails as agent instructions. Hooks add a **deterministic layer** on supported tool/event paths. This is the difference between "please don't delete files outside ci-archive" (instruction) and "the system can reject the tool call" (hook).

**actionlint** is used opportunistically when available in the environment: `postToolUse` gives per-file feedback, `agentStop`/`Stop` enforce the quality gate, and `sessionEnd`/`Stop` append scorecard entries. If actionlint is unavailable, hooks still run static workflow checks and surface those findings.

**The quality gate** (`agentStop` on CLI/Cloud and `Stop` on VS Code) is the key enforcement mechanism. Instead of only warning after each file write, it scans all workflow files at turn-end and can return a block decision when issues remain. A built-in attempt cap prevents infinite loops.

### Enabling hooks

Hooks are installed automatically with the plugin. To verify:

```bash
copilot
/hooks list
```

To disable hooks temporarily (e.g., for debugging):

```bash
copilot --disable-hooks
```

### Testing the hooks

The hooks are covered by a contract test suite that pins their behavior on **both** the CLI and VS Code payload schemas, so a change that silently breaks one surface fails loudly instead of shipping unnoticed.

```bash
# from the repo root
bash plugin/hooks.test.sh
```

What it checks (22 cases): secret-detection deny/allow, destructive-op guard (rm/mv/git mv/find -delete, path traversal, CI-source archival, shell redirects), workflow quality flags, and scorecard generation including the VS Code `Stop` loop-guard — each exercised against both the CLI (`toolName`/`toolArgs`-string) and VS Code (`tool_name`/`tool_input`-object) shapes.

**Requirements:** `bash` and `jq` only. The suite is self-contained — it does **not** require `actionlint`, network access, `curl`, or `brew` (workflow-quality checks fall back to static `grep` analysis when `actionlint` is unavailable), it writes nothing to the working tree, and it cleans up its own temp files. If `jq` is missing it exits with a clear `FATAL: jq is required` message.

**CI:** [`.github/workflows/hooks-test.yml`](../.github/workflows/hooks-test.yml) runs this suite on every pull request that touches `plugin/hooks.json` or `plugin/hooks.test.sh`, and validates that `hooks.json` parses. A regression blocks the PR.

---

## Customizing Skills

Customizing skills is the CLI plugin's equivalent of editing the `knowledge/` knowledge base in the [cloud-agent deployment](../docs/deployment.md). Because the plugin ships content **locally**, your edits take effect on the next `copilot plugin install ./plugin`—no `.github-private` push, no MCP round-trip.

### What maps to what

If you've worked with the cloud-agent version, this table shows where the same content lives in the plugin:

| Cloud agent (knowledge base)                      | CLI plugin (skill)                                              | Purpose                                                      |
| ------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------ |
| `knowledge/migration-workflow.md`                 | `plugin/skills/migration-core/SKILL.md` (+ workflow files)      | 5-phase migration process                                    |
| `knowledge/migration-guardrails.md`               | `plugin/skills/migration-core/` (guardrails section)            | Security/quality guardrails                                  |
| `knowledge/migration-standards.md`                | `plugin/skills/migration-core/` (deliverables + checklist)      | Completion standards                                         |
| `knowledge/actions-mapping/<platform>.md`         | `plugin/skills/<platform>-migration/mapping.md`                 | Source-syntax → Actions mappings                             |
| `knowledge/report-template/<platform>.md`         | `plugin/skills/<platform>-migration/report-template.md`         | PR body / `MIGRATION-README.md` structure                    |
| `knowledge/patterns/<platform>/secrets.md`        | (consolidated) `plugin/skills/migration-core/` secrets guidance | Credential migration (shared across platforms in the plugin) |
| `knowledge/patterns/jenkins/{pipeline,groovy}.md` | `plugin/skills/jenkins-migration/{pipeline,groovy}.md`          | Platform-specific deep dives                                 |

### Common customization tasks

**Tighten guardrails for your org** (e.g., require approved actions only, mandate OIDC for cloud deploys):

1. Edit `plugin/skills/migration-core/SKILL.md` (and any companion files in that skill).
2. Re-install: `copilot plugin install ./plugin`.

**Add/override an action mapping** for a single source platform (e.g., your org uses a custom internal action instead of `actions/checkout`):

1. Edit `plugin/skills/<platform>-migration/mapping.md`.
2. Re-install.

**Customize the migration report** (e.g., add an "Approved by" section or a compliance checklist):

1. Edit `plugin/skills/<platform>-migration/report-template.md`.
2. Optionally update `plugin/skills/migration-core/` if you want the change to apply across all platforms (then prune per-platform templates accordingly).
3. Re-install.

**Adjust reusable-workflow detection rules** for the Reusable Workflow Builder:

1. Edit files under `plugin/skills/reusable-workflow-patterns/`.
2. Re-install.

**Add a new source platform** — see [Adding a new platform](#adding-a-new-platform) below and the [Extending Guide](../docs/extending.md).

### Edit-test loop

```bash
# 1. Edit a skill file
$EDITOR plugin/skills/jenkins-migration/mapping.md

# 2. Re-install to refresh the plugin cache
copilot plugin install ./plugin

# 3. Run a migration against a real Jenkinsfile and inspect the result
copilot
> Use the jenkins-migrator agent to convert ./Jenkinsfile
```

After each skill edit, re-run `copilot plugin install ./plugin` to refresh the cache.

### Distributing your customizations

After editing, you have two options:

- **Internal fork** — fork this repo, push your changes, and have your team install from your fork:
  ```bash
  copilot plugin marketplace add my-org/actions-migrations-via-copilot
  copilot plugin install actions-migrator
  ```
  This is the recommended pattern for org-wide customization. Update your fork's [`.github/plugin/marketplace.json`](../.github/plugin/marketplace.json) if you rename the plugin or its `source` path.
- **Local-only** — keep changes on your machine and `copilot plugin install ./plugin` from your clone. Best for personal experimentation.

### Adding a new platform

To add a new source CI system to the plugin:

1. Create `plugin/agents/<platform>-migrator.agent.md` — copy the slim composer template from an existing agent (e.g., `jenkins-migrator.agent.md`) and adjust the loaded skill + platform-specific instructions.
2. Create `plugin/skills/<platform>-migration/` with:
   - `SKILL.md` — YAML frontmatter (`name`, `description`) plus a short orientation. Copy from `plugin/skills/jenkins-migration/SKILL.md`.
   - `mapping.md` — source syntax → Actions mappings.
   - `report-template.md` — migration report structure for the PR body.
   - Optional extras (e.g., `pipeline.md`) for deeper subtopics.
3. Re-install: `copilot plugin install ./plugin`.
4. Mirror the entry in the top-level [`agents/`](../agents/) and [`knowledge/`](../knowledge/) trees if you also want cloud-agent support. See the [Extending Guide](../docs/extending.md) for full details.

---

## Relationship to `knowledge/` and Top-Level `agents/`

The repo root still contains the original `agents/` directory and `knowledge/` knowledge base. Those continue to work for the existing `.github-private` cloud-agent deployment pattern. The plugin in this directory is a **parallel** packaging that:

- Inlines the knowledge into composable skills.
- Removes the runtime MCP dependency on `.github-private`.
- Lets users install everything with a single `copilot plugin install` (or via the marketplace).

Source-of-truth for content currently lives in the root `knowledge/` tree; skill files were derived from it. When customizing for personal/team use, edit the skill files directly. When contributing back upstream, update the root `knowledge/` tree as well so both surfaces stay in sync.

## Reference

- [GitHub Copilot CLI — Creating plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)
- [GitHub Copilot CLI — Plugin marketplace](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace)
- [GitHub Copilot CLI plugin reference](https://docs.github.com/en/copilot/reference/cli-plugin-reference)
- [Extending Guide](../docs/extending.md) — add new CI/CD platforms (covers both surfaces)
