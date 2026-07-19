# GitHub Actions Migration Agents

Enterprise-grade GitHub Copilot agents that automatically migrate CI/CD pipelines from virtually any platform to GitHub Actions—powered by a comprehensive knowledgebase of migration patterns and best practices.

## Why This Project?

Organizations migrating to GitHub Actions face:

- Inconsistent migrations across teams
- Loss of domain knowledge during manual conversions
- Security oversights with credentials
- Time-consuming manual work
- Lack of validation leading to broken workflows

**This project delivers:**

- ⚡ **Faster** than manual migration
- 🎯 **Consistent quality** using documented best practices
- ✅ **Built-in validation** with actionlint
- 📊 **Complete documentation** of every decision
- 🔄 **Reusable patterns** for future migrations

## Available Migration Agents

| Agent                         | Migrates From              | Handles                                     |
| ----------------------------- | -------------------------- | ------------------------------------------- |
| **Jenkins Migrator**          | Jenkinsfile                | Pipelines, shared libraries, Groovy scripts |
| **Azure DevOps Migrator**     | azure-pipelines.yml        | YAML pipelines, templates, variable groups  |
| **CircleCI Migrator**         | .circleci/config.yml       | Workflows, jobs, Orbs                       |
| **GitLab Migrator**           | .gitlab-ci.yml             | Pipelines, includes, Pages                  |
| **Travis CI Migrator**        | .travis.yml                | Build matrix, deploy providers              |
| **Bamboo Migrator**           | bamboo-specs.yml           | Build plans, deployment projects            |
| **Bitbucket Migrator**        | bitbucket-pipelines.yml    | Pipelines, Pipes                            |
| **Drone CI Migrator**         | .drone.yml                 | Pipelines, plugins                          |
| **Reusable Workflow Builder** | GitHub Actions across orgs | Pattern analysis, reusable workflows        |

The **Reusable Workflow Builder** scans multiple GitHub organizations, detects common CI/CD patterns (Node.js builds, AWS deployments, Docker workflows), and generates standardized reusable workflows—reducing duplication and capturing organizational best practices.

## Choose Your Surface

This project ships the same agents for two GitHub Copilot surfaces. Pick the one that matches how your team works.

| Surface                   | Best For                                                                      | How agents are delivered                                                                                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **🌐 Copilot cloud agent** | Org-wide rollout, batch migrations across many repos, central governance      | Deployed to your enterprise's `.github-private` repository. Agents fetch the knowledgebase from `knowledge/` at runtime via the GitHub MCP server. → [Jump to setup](#using-the-copilot-cloud-agent) |
| **💻 Copilot CLI**         | Local/interactive use, individual developers, customizing skills for your org | Installed as a Copilot CLI plugin. The knowledgebase ships pre-split into composable skills under `plugin/`—no runtime fetch required. → [Jump to setup](#using-the-copilot-cli)                     |

Both surfaces produce the same deliverables:

1. **`.github/workflows/*.yml`** — production-ready, validated workflows
2. **`.github/ci-archive/`** — original files and `MIGRATION-README.md` preserved for reference
3. **Pull Request** — migration report in the PR body with validation results, required secrets, next steps, and knowledgebase references

---

## 🌐 Using the Copilot Cloud Agent

Agents live in [`agents/`](agents/) and reference the knowledgebase in [`knowledge/`](knowledge/) at runtime. They are deployed to your enterprise's `.github-private` repository so they're available to all internal repos.

### Getting started

1. **Deploy** — Follow the [Deployment Guide](docs/deployment.md) to set up the agents in your enterprise's `.github-private` repo.
2. **Migrate** — Run migrations using the [Operations Guide](docs/operations.md).

### Two ways to migrate

| Method     | Best For                  | Guide                                                   |
| ---------- | ------------------------- | ------------------------------------------------------- |
| **Manual** | Individual repos, testing | [Operations Guide](docs/operations.md#manual-migration) |
| **Batch**  | Multiple repos, scale     | [Operations Guide](docs/operations.md#batch-migration)  |

---

## 💻 Using the Copilot CLI

The same nine agents are packaged as a Copilot CLI plugin under [`plugin/`](plugin/README.md), with the knowledgebase pre-split into composable skills. See [`plugin/README.md`](plugin/README.md) for the composition model and full skill catalog.

### Option A — Install from the marketplace (use as-is)

Fastest path. Use this when you want the agents with the default knowledgebase.

```bash
copilot plugin marketplace add github/actions-migrations-via-copilot
copilot plugin install actions-migrator
```

The marketplace is defined in [`.github/plugin/marketplace.json`](.github/plugin/marketplace.json).

### Option B — Install locally (customize skills)

Use this when you want to tailor patterns, action mappings, security guardrails, or report templates to your organization.

```bash
git clone https://github.com/github/actions-migrations-via-copilot.git
cd actions-migrations-via-copilot
# edit files under plugin/skills/ to match your org's standards
copilot plugin install ./plugin
```

### Option C — Install via APM (pinned, hashed, auditable) *(experimental)*

Use this when you need reproducible installs with lockfile-pinned versions, content-integrity scanning, SBOM export, or air-gapped operation — typical for regulated industries.

Install the [APM CLI](https://microsoft.github.io/apm/) once:

```bash
curl -sSL https://aka.ms/apm-unix | sh      # macOS / Linux
# irm https://aka.ms/apm-windows | iex        # Windows
```

Add the dependency to your project's `apm.yml`:

```yaml
dependencies:
  apm:
    - github/actions-migrations-via-copilot#v1.2.0
```

Then run:

```bash
apm install
```

APM deploys the agents and skills into your repo, pins the resolved sources and content hashes in `apm.lock.yaml`, and content-scans every primitive before it reaches disk.

---

## How Migration Works

Whichever surface you choose, each agent follows the same five-phase process:

1. **Reads** source CI/CD configuration files
2. **References** the knowledgebase for conversion patterns
3. **Generates** GitHub Actions workflows
4. **Validates** with actionlint
5. **Documents** all changes in a migration report

## Documentation

| Guide                                      | Purpose                                        |
| ------------------------------------------ | ---------------------------------------------- |
| **[Deployment Guide](docs/deployment.md)** | Set up agents in your enterprise (cloud agent) |
| **[Operations Guide](docs/operations.md)** | Use agents to migrate repositories             |
| **[Extending Guide](docs/extending.md)**   | Add new CI/CD platforms                        |
| **[Plugin README](plugin/README.md)**      | Copilot CLI plugin details                     |
| **[Contributing Guide](CONTRIBUTING.md)**  | Contribute improvements                        |

## Project Structure

```
.
├── agents/                    # Agent definitions (9 migration agents) — cloud agent / .github-private deployment
├── docs/                      # Deployment, operations, and extending guides
├── knowledge/                 # Migration knowledgebase (source of truth for cloud agent)
│   ├── actions-mapping/       # CI/CD → Actions mappings
│   ├── patterns/              # Platform-specific conversion patterns
│   └── report-template/       # Migration report templates
├── plugin/                    # Copilot CLI plugin (agents + composable skills, derived from knowledge/)
│   ├── plugin.json
│   ├── agents/                # 9 thin agent composers
│   └── skills/                # 11 skills (3 core + 8 platform)
└── .github/
    └── plugin/
        └── marketplace.json   # Copilot CLI plugin marketplace manifest
```

**Detailed structure:** See [Extending Guide](docs/extending.md#quick-reference) for complete file organization.

## Contributing

We welcome contributions! See our guides:

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — General contribution guidelines
- **[Extending Guide](docs/extending.md)** — Add new CI/CD platforms or improve agents

**Ways to contribute:**

- Add support for new CI/CD platforms
- Improve action mappings and patterns
- Enhance agent accuracy
- Report issues or suggest improvements

## Support

- **Documentation** — [Deployment](docs/deployment.md) | [Operations](docs/operations.md) | [Extending](docs/extending.md) | [Plugin](plugin/README.md)
- **Discussions** — [Ask questions and share experiences](https://github.com/github/actions-migrations-via-copilot/discussions)
- **Issues** — [Report bugs or request features](https://github.com/github/actions-migrations-via-copilot/issues)
- **GitHub Actions Docs** — [Official documentation](https://docs.github.com/actions)

## Acknowledgments

Built by GitHub Professional Services for enterprise CI/CD migration programs. Contributions from GitHub's field engineering, solutions architecture, and customer success teams.
