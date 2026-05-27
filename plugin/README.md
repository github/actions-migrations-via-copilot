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
