# `actions-migrator` — Copilot CLI Plugin

A GitHub Copilot CLI plugin that bundles nine specialized agents for migrating CI/CD pipelines to GitHub Actions, plus a catalog of composable skills covering the standard migration workflow, security guardrails, completion standards, and platform-specific syntax/secrets/report knowledge.

## What's inside

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

## Composition model

Every migration agent loads:

1. **`migration-core`** — 5-phase process, guardrails, deliverables, archival, completion checklist
2. **`actionlint`** — install, run, interpret output, and fix errors
3. **1 platform skill** — mapping and report-template for the source CI platform

The Reusable Workflow Builder loads `reusable-workflow-patterns` + `migration-core` + `actionlint`.

This replaces the previous pattern of agents fetching `knowledge/*.md` files at runtime from a private `.github-private` repo via the GitHub MCP server — everything now ships locally with the plugin.

## Install (local, for development)

From the repository root:

```bash
copilot plugin install ./plugin
```

Verify:

```bash
copilot plugin list
```

In an interactive Copilot CLI session:

```
/agent          # list available agents (should include the migrators)
/skills list    # list available skills (should include all 12)
```

After editing plugin contents, re-install to refresh the cache:

```bash
copilot plugin install ./plugin
```

## Uninstall

```bash
copilot plugin uninstall actions-migrator
```

## Use

Once installed, ask Copilot to use the appropriate agent. Examples:

- `Use the jenkins-migrator agent to convert the Jenkinsfile in this repo.`
- `Use the azure-devops-migrator on azure-pipelines.yml.`
- `Use the reusable-workflow-builder agent. Analyze organizations: my-org-a, my-org-b for CI/CD patterns.`

Each migrator agent requires you to point it at real source files — it will refuse to invent pipelines from descriptions.

## Relationship to `knowledge/` and top-level `agents/` in this repo

The repo root still contains the original `agents/` directory and `knowledge/` knowledge base. Those continue to work for the existing `.github-private` deployment pattern. The plugin in this directory is a **parallel** packaging that:

- Inlines the knowledge into composable skills.
- Removes the runtime MCP dependency on `.github-private`.
- Lets users install everything with a single `copilot plugin install`.

Source-of-truth for content currently lives in the root `knowledge/` tree; skill files were derived from it.

## Reference

- [GitHub Copilot CLI — Creating plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)
- [GitHub Copilot CLI plugin reference](https://docs.github.com/en/copilot/reference/cli-plugin-reference)
