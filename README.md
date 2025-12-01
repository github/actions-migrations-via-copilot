# CI/CD Migration Custom Agents

Enterprise-grade GitHub Custom Agents that automatically migrate CI/CD pipelines from Jenkins, Azure DevOps, CircleCI, GitLab, and other platforms to GitHub Actions—powered by a comprehensive knowledgebase of migration patterns and best practices.

## Why This Project?

### The Challenge

Organizations migrating to GitHub Actions face common obstacles:

- **Inconsistent migrations** across teams and repositories
- **Loss of domain knowledge** during manual conversions
- **Security oversights** when migrating credentials and secrets
- **Time-consuming manual work** translating CI/CD syntax
- **Lack of validation** leading to broken workflows post-migration

### The Solution

**Agent-Powered Migration Benefits:**

- ⚡ **10-100x faster** than manual migration
- 🎯 **Consistent quality** using documented best practices
- 🔒 **Security-first** approach to credential migration
- ✅ **Built-in validation** with actionlint and dry-run testing
- 📊 **Complete documentation** of every migration decision
- 🔄 **Reusable patterns** captured for future migrations

## How It Works

### Architecture

```mermaid
graph TB
    subgraph GHE["GitHub Enterprise Cloud"]
        Private[".github-private Repository"]
        Agents["Migration Agents<br/>• Jenkins Migrator<br/>• Azure DevOps Migrator<br/>• CircleCI Migrator<br/>• GitLab Migrator<br/>• Travis CI Migrator<br/>• Bamboo Migrator<br/>• Bitbucket Migrator<br/>• Drone CI Migrator<br/>• Reusable Workflow Builder"]
        KB["Knowledgebase<br/>• Migration Standards<br/>• Action Mappings<br/>• Security Patterns<br/>• Best Practices<br/>• Validation Rules"]
        Automation["GitHub Actions Workflows<br/>(Automated bulk migrations)"]

        Private -.-> Agents
        Private -.-> KB
        Private -.-> Automation
        Agents -."references"..-> KB

        CopilotAgents["GitHub Copilot Agents<br/>(Available to Enterprise Users)"]
        Agents --> CopilotAgents

        Reusable["reusable-workflows Repository<br/>(Generated reusable workflows)"]
        CopilotAgents -.->|"generates workflows"| Reusable

        UserRepos["User Repositories<br/>(CI/CD files being migrated)"]
        CopilotAgents -."invoked from".-> UserRepos
        Automation -->|"invokes agents<br/>across repos"| CopilotAgents
    end

    User["👤 User"] -->|"invokes manually"| CopilotAgents
    User -->|"triggers automation"| Automation
```

### Migration Process

Each migration follows a standardized five-phase process:

1. **Analysis**
   - Read source files
   - Parse CI/CD syntax
   - Expand templates
   - Resolve dependencies

2. **Conversion**
   - Reference knowledgebase
   - Map to GitHub Actions
   - Apply patterns
   - Generate workflows

3. **Validation**
   - YAML syntax validation with actionlint
   - Security and best practices review

4. **Archival**
   - Preserve history
   - Archive original files

5. **Documentation**
   - Document changes and decisions
   - Create migration report
   - List next steps
   - Include validation results

### Knowledgebase-Driven Intelligence

The knowledgebase is the "brain" behind consistent migrations:

| Component               | Purpose                                                            | Example                                                         |
| ----------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------- |
| **Migration Standards** | Define quality requirements, deliverables, and validation criteria | "All workflows must pass actionlint validation"                 |
| **Action Mappings**     | Map CI/CD plugins/tasks to equivalent GitHub Actions               | `maven-plugin` → `actions/setup-java` + Maven commands          |
| **Security Patterns**   | Template secure credential handling                                | Jenkins `withCredentials` → GitHub Secrets with least privilege |
| **Common Patterns**     | Reusable conversion templates                                      | Multi-stage pipeline → Multiple workflow jobs                   |
| **Validation Rules**    | Automated quality checks                                           | Required fields, best practices, security checks                |

Agents dynamically fetch relevant knowledgebase content during migrations, ensuring every conversion benefits from accumulated organizational knowledge.

## What You Get

### Migration Deliverables

Every migration produces:

1. **GitHub Actions Workflows** (`.github/workflows/`)
   - Production-ready, validated YAML
   - Optimized for performance and security
   - Uses latest action versions

2. **Archived Originals** (`.github/ci-archive/`)
   - Complete preservation of source files
   - Organized by CI/CD system
   - Reference for future audits

3. **Migration Report** (`.github/ci-archive/MIGRATION-README.md`)
   - Detailed conversion documentation
   - Validation results (actionlint)
   - Next steps and recommendations
   - Knowledgebase references used

4. **Security Enhancements**
   - Proper GitHub Secrets usage
   - Least-privilege permissions
   - Updated action versions
   - Security scanning recommendations

## Available Migration Agents

| Agent                         | Migrates From                      | Handles                                        |
| ----------------------------- | ---------------------------------- | ---------------------------------------------- |
| **Jenkins Migrator**          | Jenkinsfile (declarative/scripted) | Pipelines, shared libraries, Groovy scripts    |
| **Azure DevOps Migrator**     | azure-pipelines.yml                | YAML pipelines, templates, variable groups     |
| **CircleCI Migrator**         | .circleci/config.yml               | Workflows, jobs, Orbs                          |
| **GitLab Migrator**           | .gitlab-ci.yml                     | Pipelines, includes, GitLab Pages              |
| **Travis CI Migrator**        | .travis.yml                        | Build matrix, deploy providers                 |
| **Bamboo Migrator**           | bamboo-specs.yml                   | Build plans, deployment projects               |
| **Bitbucket Migrator**        | bitbucket-pipelines.yml            | Pipelines, Pipes                               |
| **Drone CI Migrator**         | .drone.yml                         | Pipelines, plugins                             |
| **Reusable Workflow Builder** | GitHub Actions across orgs         | Pattern analysis, reusable workflow generation |

### Special Agent: Reusable Workflow Builder

The **Reusable Workflow Builder** is unique—it analyzes CI/CD patterns across your GitHub organization(s) and generates standardized reusable workflows.

**How it works:**

- **Input**: Scans multiple GitHub organizations (e.g., 3 orgs with 100+ repos total)
- **Analysis**: Detects common patterns across repositories
  - Build patterns (Node.js, Python, Go, Java)
  - Deployment patterns (AWS, Azure, Kubernetes)
  - Common tooling (Docker, security scanning)
- **Output**: Generates reusable workflows in `.github/workflows/` with usage documentation

This agent reduces duplication, standardizes CI/CD across your enterprise, and captures organizational best practices as reusable workflows.

## Getting Started

### Quick Start

1. **Deploy to your enterprise** following the [Deployment Guide →](docs/deployment.md)
2. **Invoke an agent** from [github.com/copilot/agents](https://github.com/copilot/agents)
3. **Review and test** the migrated workflows
4. **Merge and deploy** your new GitHub Actions workflows

### Documentation

- **[Deployment Guide](docs/deployment.md)** - Complete enterprise setup instructions
- **[Operations Guide](docs/operations.md)** - Day-to-day usage playbooks for each agent
- **[Migration Knowledgebase](knowledge/)** - Standards, patterns, and mappings used by agents

## Project Structure

```
.
├── agents/                    # Agent definition files
│   ├── jenkins-migrator.md
│   ├── azure-devops-migrator.md
│   ├── circleci-migrator.md
│   ├── gitlab-migrator.md
│   ├── travisci-migrator.md
│   ├── bamboo-migrator.md
│   ├── bitbucket-migrator.md
│   ├── droneci-migrator.md
│   └── reusable-workflow-builder.md
│
├── docs/                      # Documentation
│   ├── deployment.md          # Enterprise deployment guide
│   └── operations.md          # Day-to-day operations playbooks
│
├── knowledge/                 # Migration knowledgebase (deploy to .github-private)
│   ├── README.md              # Knowledgebase overview
│   ├── migration-standards.md # Quality and validation standards
│   ├── migration-workflow.md  # Standard 5-phase process
│   ├── migration-guardrails.md # Security and safety guidelines
│   │
│   ├── actions-mapping/       # CI/CD tool → Actions mappings
│   │   ├── jenkins.md
│   │   ├── azure-devops.md
│   │   ├── circleci.md
│   │   ├── gitlab.md
│   │   ├── travisci.md
│   │   ├── bamboo.md
│   │   ├── bitbucket.md
│   │   └── droneci.md
│   │
│   ├── patterns/              # System-specific patterns
│   │   ├── jenkins/
│   │   │   ├── pipeline.md   # Pipeline conversions
│   │   │   ├── groovy.md     # Groovy script handling
│   │   │   └── secrets.md    # Credential migration
│   │   ├── azure-devops/
│   │   │   └── secrets.md
│   │   ├── circleci/
│   │   │   └── secrets.md
│   │   └── ... (other systems)
│   │
│   └── report-template/       # Migration report templates
│       ├── jenkins.md
│       ├── azure-devops.md
│       └── ... (other systems)
│
└── README.md                  # This file (project overview)
```

## Support and Resources

- **[Deployment Guide](docs/deployment.md)** - Enterprise setup and configuration
- **[Operations Guide](docs/operations.md)** - Daily usage playbooks
- **[GitHub Actions Documentation](https://docs.github.com/actions)** - Official Actions docs
- **[GitHub Community](https://github.community)** - Community support

## Contributing

Contributions to improve agents and knowledgebase are welcome:

1. **Enhance agents** - Improve conversion accuracy and coverage
2. **Update mappings** - Add new CI/CD tool to Actions mappings
3. **Document patterns** - Share successful migration patterns
4. **Refine standards** - Improve quality and validation criteria
5. **Report issues** - Submit bug reports or feature requests

## Acknowledgments

Built by GitHub Professional Services for enterprise CI/CD migration programs. Contributions from teams across GitHub's field engineering, solutions architecture, and customer success organizations.

