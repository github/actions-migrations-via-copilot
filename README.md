# GitHub Actions Migration Agents

Enterprise-grade GitHub Copilot Agents that automatically migrate CI/CD pipelines from virtually any platform to GitHub Actions—powered by a comprehensive knowledgebase of migration patterns and best practices.

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

## How It Works

Migration agents are GitHub Copilot Custom Agents deployed to your enterprise's `.github-private` repository. Each agent:

1. **Reads** source CI/CD configuration files
2. **References** the knowledgebase for conversion patterns
3. **Generates** GitHub Actions workflows
4. **Validates** with actionlint
5. **Documents** all changes in a migration report

**Knowledgebase-driven:** Agents fetch patterns, security guidelines, and action mappings from `knowledge/` during each migration, ensuring consistent, up-to-date conversions.

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

### Reusable Workflow Builder

This unique agent scans multiple GitHub organizations, detects common CI/CD patterns (Node.js builds, AWS deployments, Docker workflows), and generates standardized reusable workflows—reducing duplication and capturing organizational best practices.

## What You Get

Every migration produces:

1. **`.github/workflows/*.yml`** - Production-ready, validated workflows
2. **`.github/ci-archive/`** - Original files and **`MIGRATION-README.md`** preserved for reference
3. **Pull Request** - Migration report included in the PR body (mirroring `MIGRATION-README.md`) with:
   - Validation results
   - Required secrets
   - Next steps
   - Knowledgebase references

## Getting Started

### Quick Start

1. **Deploy** - Follow the [Deployment Guide](docs/deployment.md) to set up agents in your enterprise
2. **Migrate** - Use the [Operations Guide](docs/operations.md) to run migrations
3. **Extend** - Add new platforms using the [Extending Guide](docs/extending.md)

### Two Ways to Migrate

| Method     | Best For                  | Guide                                                   |
| ---------- | ------------------------- | ------------------------------------------------------- |
| **Manual** | Individual repos, testing | [Operations Guide](docs/operations.md#manual-migration) |
| **Batch**  | Multiple repos, scale     | [Operations Guide](docs/operations.md#batch-migration)  |

## Documentation

| Guide                                      | Purpose                            |
| ------------------------------------------ | ---------------------------------- |
| **[Deployment Guide](docs/deployment.md)** | Set up agents in your enterprise   |
| **[Operations Guide](docs/operations.md)** | Use agents to migrate repositories |
| **[Extending Guide](docs/extending.md)**   | Add new CI/CD platforms            |
| **[Contributing Guide](CONTRIBUTING.md)**  | Contribute improvements            |

## Project Structure

```
.
├── agents/                    # Agent definitions (9 migration agents)
├── docs/                      # Deployment, operations, and extending guides
├── knowledge/                 # Migration knowledgebase
│   ├── actions-mapping/       # CI/CD → Actions mappings
│   ├── patterns/              # Platform-specific conversion patterns
│   └── report-template/       # Migration report templates
└── .github/                   # Automation workflows
```

**Detailed structure:** See [Extending Guide](docs/extending.md#quick-reference) for complete file organization.

## Contributing

We welcome contributions! See our guides:

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - General contribution guidelines
- **[Extending Guide](docs/extending.md)** - Add new CI/CD platforms or improve agents

**Ways to contribute:**

- Add support for new CI/CD platforms
- Improve action mappings and patterns
- Enhance agent accuracy
- Report issues or suggest improvements

## Support

- **Documentation** - [Deployment](docs/deployment.md) | [Operations](docs/operations.md) | [Extending](docs/extending.md)
- **Discussions** - [Ask questions and share experiences](https://github.com/github/actions-migrations-via-copilot/discussions)
- **Issues** - [Report bugs or request features](https://github.com/github/actions-migrations-via-copilot/issues)
- **GitHub Actions Docs** - [Official documentation](https://docs.github.com/actions)

## Acknowledgments

Built by GitHub Professional Services for enterprise CI/CD migration programs. Contributions from GitHub's field engineering, solutions architecture, and customer success teams.
