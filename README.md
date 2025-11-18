# CI/CD Migration Custom Agents

A collection of specialized GitHub Custom Agents for migrating CI/CD pipelines from various systems (Jenkins, Azure DevOps, CircleCI, etc.) to GitHub Actions. These agents use a structured knowledgebase of migration patterns, standards, and best practices to provide consistent, high-quality migrations.

## Overview

This project provides enterprise-grade GitHub Custom Agents that convert CI/CD pipeline configurations to GitHub Actions workflows. Each agent references a comprehensive knowledgebase of migration standards, action mappings, common patterns, and system-specific guidance to ensure consistent and reliable migrations.

## Key Features

- **Knowledgebase-Driven**: Agents reference migration standards, action mappings, and proven patterns
- **Specialized Agents**: Purpose-built agents for each major CI/CD system
- **Consistent Migrations**: Standardized approach using documented best practices
- **Comprehensive Reports**: Detailed migration documentation with validation results
- **Security Best Practices**: Proper credential migration and security enhancements
- **Validation & Testing**: Built-in linting and dry-run testing capabilities
- **Complete Archival**: Organized preservation of original configurations

## 📚 Knowledgebase

The migration knowledgebase contains:

- **Migration Standards**: Standardized workflows, guardrails, and reporting templates
- **Action Mappings**: Plugin/task to GitHub Actions mappings for each CI/CD system
- **Common Patterns**: Security scanning, secrets management, and system-specific patterns
- **Migration Workflow**: Step-by-step guidance for consistent migrations

This knowledgebase is stored in the `docs/` directory and used by agents during migrations to ensure consistent, high-quality conversions.

## Setup Requirements

### Prerequisites

- GitHub Enterprise Cloud with GitHub Copilot Business or Enterprise
- Enterprise Owner permissions
- Two repositories in your enterprise organization:
  - `.github-private` repository (for agents and knowledgebase)
  - This repository must have **Internal** visibility

### Deployment Steps

1. **Create the `.github-private` repository** in your enterprise organization:
   - Repository name: `.github-private` (exactly)
   - Visibility: **Internal** (required for agents to access knowledgebase)

2. **Deploy agents and knowledgebase**:
   ```bash
   # Clone this repository
   git clone https://github.com/github/actions-migrations-via-copilot.git
   cd actions-migrations-via-copilot

   # Copy to your .github-private repository
   cp -r agents/* /path/to/your/.github-private/agents/
   cp -r docs/* /path/to/your/.github-private/docs/
   ```

   **Important**: After copying the agent files, you must update the `{MY_ORGANIZATION}` placeholder in each agent file (`agents/*.md`) to match your organization slug (the organization hosting the `.github-private` repository). Search for `{MY_ORGANIZATION}` and replace it with your actual organization name.

3. **Verify the structure** in your `.github-private` repository:
   ```
   .github-private/
   ├── agents/
   │   ├── azure-devops-migrator.md
   │   ├── jenkins-migrator.md
   │   └── ... (other agent files)
   └── docs/
       ├── migration-standards.md
       ├── migration-workflow.md
       ├── actions-mapping/
       ├── patterns/
       └── report-template/
   ```

4. **Configure enterprise settings**:
   - Navigate to: Your profile → Enterprise → AI controls
   - In "Custom agents" section, select your organization
   - Verify agents appear at [https://github.com/copilot/agents](https://github.com/copilot/agents)

**Important**: The `.github-private` repository must have **Internal** visibility to allow agents to access the knowledgebase via the GitHub MCP server during migrations.

## Available Migration Agents

| Agent                         | Description                                                                     | Source Systems                                |
| ----------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------- |
| **Jenkins Migrator**          | Converts Jenkins declarative and scripted pipelines, including shared libraries | Jenkinsfile, scripted pipelines, YAML configs |
| **Azure DevOps Migrator**     | Migrates Azure Pipelines YAML with template expansion                           | azure-pipelines.yml, template files           |
| **CircleCI Migrator**         | Converts CircleCI workflows and jobs                                            | .circleci/config.yml                          |
| **GitLab Migrator**           | Transforms GitLab CI/CD pipelines                                               | .gitlab-ci.yml, pipeline configs              |
| **Travis CI Migrator**        | Migrates Travis CI build configurations                                         | .travis.yml                                   |
| **Bamboo Migrator**           | Converts Bamboo build plans and deployments                                     | Bamboo YAML specs, build configs              |
| **Bitbucket Migrator**        | Transforms Bitbucket Pipelines                                                  | bitbucket-pipelines.yml                       |
| **Drone CI Migrator**         | Converts Drone CI pipeline configurations                                       | .drone.yml                                    |
| **Reusable Workflow Builder** | Scans GitHub organizations for CI/CD patterns and generates reusable workflows  | GitHub Actions workflows across organizations |

### Special Setup: Reusable Workflow Builder Agent

The **Reusable Workflow Builder** agent has unique setup requirements as it analyzes CI/CD patterns across GitHub organizations and generates standardized reusable workflows.

#### Prerequisites

1. **Dedicated Repository for Reusable Workflows**:
   - Create a repository to host the generated reusable workflows
   - This repository will receive the agent's output (reusable workflows in `.github/workflows/` and usage examples in `docs/`)
   - Tasks for the Reusable Workflow Builder agent must be assigned from this repository

2. **GitHub Personal Access Token (PAT)**:
   - Create a GitHub PAT with `repo` scope (read access to all repositories in the target organizations)
   - The PAT must have access to all repositories you want to analyze
   - For organization analysis, ensure the PAT has appropriate organization permissions

3. **Copilot Environment Secret**:
   - Create a secret in the GitHub Copilot environment named `COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN`
   - Set the value to your GitHub PAT from step 2
   - This allows the agent to access repositories across the specified organizations

#### Usage Requirements

When invoking the Reusable Workflow Builder agent, you **must** provide:

- **Organization Names**: Specify which GitHub organization(s) to scan for CI/CD patterns
- **Repository Context**: Assign the task from your dedicated reusable workflows repository

**Example Invocation**:
```
Please analyze the following GitHub organizations for CI/CD patterns: my-org, my-other-org

Generate reusable workflows based on common patterns found across these organizations.
```

The agent will:
1. Scan the specified organizations for GitHub Actions workflows
2. Analyze common CI/CD patterns across repositories
3. Generate reusable workflows in `.github/workflows/` directory
4. Create usage examples in `docs/` directory for each reusable workflow

## How to Use

### 1. Access GitHub Copilot Agents

Navigate to the GitHub Copilot agents interface to invoke migration agents:

1. **Go to the agents tab** at [https://github.com/copilot/agents](https://github.com/copilot/agents)
2. **Select your repository and branch** using the dropdown menus (choose the repository containing your CI/CD files)
3. **Select the appropriate migration agent** from the agent dropdown (e.g., "jenkins-migrator", "azure-devops-migrator")
4. **Enter your migration request** in the text box:

```
Please migrate our Jenkins pipelines to GitHub Actions.

We have the following Jenkins files:
- Jenkinsfile (declarative pipeline)
- vars/buildApp.groovy (shared library)
- jenkins/deploy.jenkinsfile (deployment pipeline)
```

5. **Click "Start task"** or press Enter to begin the migration

### 2. Agent Analysis

The assigned agent will:
- Analyze your existing CI/CD configuration files
- Expand any shared libraries or templates inline
- Map system-specific features to GitHub Actions equivalents
- Generate complete, runnable workflows

### 3. Migration Output

Each agent provides:
- **GitHub Actions workflows** in `.github/workflows/`
- **Archived originals** in `.github/ci-archive/`
- **Complete migration report** with validation results and knowledge base references
- **Security and performance improvements** based on KB best practices
- **Pattern documentation** showing which KB patterns were applied

### 4. Validation & Testing

All migrations include:
- YAML syntax validation with actionlint
- Dry-run testing with act
- Security best practices review
- Performance optimization recommendations

## Agent Capabilities

### Universal Features (All Agents)

- **Knowledgebase Integration**: References migration standards and action mappings during conversion
- **Source File Analysis**: Deep understanding of CI/CD configuration syntax
- **Intelligent Conversion**: Context-aware mapping to GitHub Actions using documented patterns
- **Security Enhancement**: Proper secrets and credential management following best practices
- **Performance Optimization**: Caching, parallelization, and efficiency improvements
- **Complete Documentation**: Comprehensive migration reports with validation results
- **File Archival**: Organized preservation of original configurations

### Specialized Features by Agent

#### Jenkins Migrator
- Declarative and scripted pipeline support
- Shared library expansion and inline conversion
- Complex Groovy script handling
- Multi-branch pipeline conversion
- Jenkins plugin to GitHub Actions mapping

#### Azure DevOps Migrator
- Template system expansion
- Variable group migration
- Deployment job conversion
- Task library to Actions mapping
- Azure-specific service integration

#### CircleCI Migrator
- Orb expansion and inline conversion
- Workflow and job dependency mapping
- Executor to runner conversion
- Cache and artifact handling

#### GitLab Migrator
- Include template expansion
- Service dependency conversion
- GitLab-specific variable handling
- Pages and deployment job migration

## Migration Best Practices

### Before Migration

1. **Backup Existing Configurations**: Ensure you have backups of all CI/CD files
2. **Document Dependencies**: List external tools, services, and integrations
3. **Review Secrets**: Catalog credentials and environment variables
4. **Plan Testing**: Prepare test scenarios for validation

### During Migration

1. **Review Agent Output**: Carefully examine generated workflows
2. **Test Incrementally**: Validate workflows in feature branches
3. **Verify Security**: Ensure proper secret and credential handling
4. **Check Dependencies**: Confirm all external dependencies are addressed

### After Migration

1. **Monitor Performance**: Compare build times and resource usage
2. **Update Documentation**: Reflect new GitHub Actions workflows
3. **Train Team**: Educate developers on GitHub Actions workflows
4. **Archive Legacy**: Safely retire old CI/CD infrastructure

## Security Considerations

### Credential Migration

All agents automatically:
- Convert CI/CD system credentials to GitHub Secrets
- Implement least-privilege access patterns
- Use secure credential reference patterns
- Separate sensitive and non-sensitive configuration

### Security Enhancements

Migrations include:
- Updated action versions with latest security patches
- Proper permissions and scoping
- Security scanning integration recommendations
- Environment protection rule suggestions

## Support & Troubleshooting

### Common Issues

| Issue                | Solution                                                               |
| -------------------- | ---------------------------------------------------------------------- |
| Agent not available  | Verify `.github-private` repository setup and enterprise configuration |
| Migration fails      | Ensure all source CI/CD files are provided and accessible              |
| Validation errors    | Review generated workflows for syntax issues                           |
| Missing dependencies | Check that all required tools and services are available               |

### Getting Help

1. **Review Migration Reports**: Check the generated `MIGRATION-README.md` for details
2. **Validate Workflows**: Use actionlint and act for local testing
3. **Consult Documentation**: Reference system-specific migration guides
4. **Enterprise Support**: Contact your GitHub Enterprise support team

## Knowledgebase Structure

The knowledgebase in `docs/` contains:

```
docs/
├── migration-standards.md        # Standardized migration approach
├── migration-workflow.md         # Step-by-step migration process
├── migration-guardrails.md       # Migration safety checks
├── actions-mapping/              # CI/CD tool to Actions mappings
├── patterns/                     # Common patterns (security, secrets)
└── report-template/              # Migration report templates
```

## Contributing

Contributions to improve agents and knowledgebase are welcome:

1. **Improve Agents**: Enhance agent capabilities and coverage
2. **Update Mappings**: Add new action mappings as tools evolve
3. **Add Patterns**: Document new migration patterns
4. **Update Standards**: Refine migration standards and workflows
5. **Report Issues**: Submit bug reports or feature requests

