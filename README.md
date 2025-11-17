# CI/CD Migration Custom Agents with RAG Knowledge Base

A collection of specialized GitHub Custom Agents for migrating CI/CD pipelines from various systems (Jenkins, Azure DevOps, CircleCI, etc.) to GitHub Actions. These agents leverage GitHub Copilot's advanced capabilities enhanced with RAG (Retrieval-Augmented Generation) to provide automated, intelligent, and consistent migration assistance powered by a comprehensive knowledge base.

## Overview

This project provides enterprise-grade GitHub Custom Agents that specialize in converting existing CI/CD pipeline configurations to GitHub Actions workflows. Each agent is expertly trained to handle the nuances and complexities of specific CI/CD systems, and is enhanced with access to a comprehensive knowledge base of migration examples, patterns, and best practices.

## Key Features

- **RAG-Enhanced Agents**: Agents reference a comprehensive knowledge base of proven migration patterns
- **Knowledge Base**: Extensive library of migration examples, common patterns, and best practices
- **Specialized Agents**: Purpose-built agents for each major CI/CD system
- **Intelligent Migration**: AI-powered analysis and conversion referencing proven patterns
- **Pattern-Based Approach**: Leverage tested migration patterns from the knowledge base
- **Comprehensive Documentation**: Detailed migration reports with validation results and KB references
- **Security Best Practices**: Proper credential migration and security enhancements
- **Validation & Testing**: Built-in linting and dry-run testing capabilities
- **Complete Archival**: Organized preservation of original configurations

## 📚 Knowledge Base

The RAG knowledge base is deployed to GitHub Pages and provides:

### Migration Examples by System
- **Jenkins**: Maven builds, Docker builds, multi-stage deployments, shared libraries
- **CircleCI**: Orb conversions, executor mappings, workflow patterns
- **Azure DevOps**: Template expansions, task conversions, pipeline patterns
- And more for each supported CI/CD system

### Common Patterns
Reusable patterns for standard CI/CD tasks:
- **Matrix Builds** - Test across multiple configurations
- **Security Scanning** - Integrate security tools (SAST, DAST, container scanning)
- **Multi-Environment Deployments** - Deploy to dev, staging, production
- **Database Migrations** - Handle schema changes safely
- **Caching Strategies** - Optimize build performance
- **Monorepo Strategies** - Manage multiple projects
- **Docker Builds** - Container image management
- **Artifact Management** - Build output handling

### Reference Materials
Quick reference guides:
- **Action Mappings** - Comprehensive plugin/task to GitHub Actions mappings for all systems
- **Runner Specifications** - Choose the right runners for your workload
- **Security Best Practices** - Secure your workflows and secrets
- **Performance Optimization** - Make pipelines faster and more efficient

**Access the Knowledge Base**: https://github.github.io/actions-migrations-via-copilot/

## 🔄 How RAG Enhancement Works

### Traditional Migration
```
Source Pipeline → Agent Converts → GitHub Actions Workflow
```

### RAG-Enhanced Migration
```
Source Pipeline
    ↓
Agent Analyzes Components
    ↓
Agent Searches Knowledge Base for Matching Patterns
    ↓
Agent Applies Proven Patterns from KB
    ↓
Agent Customizes for Specific Requirements
    ↓
Enhanced Workflow + KB References + Documentation
```

### Benefits of RAG Enhancement

1. **Consistency** - All migrations follow proven, tested patterns
2. **Quality** - Best practices embedded in every migration
3. **Learning** - KB references help users understand decisions made
4. **Maintainability** - Centralized knowledge base easy to update
5. **Speed** - Agents leverage existing patterns instead of starting from scratch
6. **Continuous Improvement** - KB grows with new patterns and examples

## Setup Requirements

### Prerequisites

- **GitHub Enterprise Cloud** with GitHub Copilot Business or Enterprise
- **Enterprise Owner** permissions
- Access to create and manage custom agents
- A `.github-private` repository in your enterprise organization

### Deployment to .github-private Repository

The migration agents must be deployed to a `.github-private` repository in your enterprise organization. The agent files should be placed in an `agents/` folder at the root of the `.github-private` repository.

#### Deploy to .github-private Repository

1. **Create or locate your .github-private repository** in your enterprise organization:
   ```bash
   # If creating new, use the official template:
   # Navigate to: https://github.com/docs/custom-agents-template
   # Click "Use this template" → Create a new repository
   # Name: .github-private (exactly)
   # Visibility: Private
   ```

2. **Copy agent files** from this repository to your `.github-private` repository:
   ```bash
   # Clone this repository
   git clone https://github.com/github/actions-migrations-via-copilot.git
   cd actions-migrations-via-copilot

   # Copy agent files to the agents/ folder at the root of your .github-private repository
   # Note: agents/ folder should be at repository root, NOT in .github/agents/
   cp -r agents/* /path/to/your/.github-private/agents/
   ```

3. **Verify correct structure** in your `.github-private` repository:
   ```
   .github-private/
   ├── agents/
   │   ├── azure-devops-migrator.md
   │   ├── bamboo-migrator.md
   │   ├── bitbucket-migrator.md
   │   ├── circleci-migrator.md
   │   ├── droneci-migrator.md
   │   ├── gitlab-migrator.md
   │   ├── jenkins-migrator.md
   │   ├── reusable-workflow-builder.md
   │   └── travisci-migrator.md
   └── other files...
   ```

4. **Commit and push** the agent definitions to your `.github-private` repository

### Enterprise Configuration

1. **Navigate to Enterprise AI Controls**:
   - Click your profile picture → Enterprise → AI controls

2. **Configure Custom Agents**:
   - In "Custom agents" section, select your organization containing `.github-private`
   - Click "Create ruleset" to protect agent files (recommended)

3. **Verify Setup**:
   - Agents should appear at [https://github.com/copilot/agents](https://github.com/copilot/agents)
   - Test with a simple migration request using the agents interface

For detailed setup instructions, see the [official documentation](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-enterprise/manage-agents/prepare-for-custom-agents).

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

- **Knowledge Base Integration**: References proven migration patterns during conversion
- **Source File Analysis**: Deep understanding of CI/CD configuration syntax
- **Intelligent Conversion**: Context-aware mapping to GitHub Actions using KB patterns
- **Pattern Matching**: Identifies and applies relevant patterns from knowledge base
- **Security Enhancement**: Proper secrets and credential management following KB best practices
- **Performance Optimization**: Caching, parallelization, and efficiency improvements from KB
- **Complete Documentation**: Comprehensive migration reports with KB references and validation
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

## 📖 Knowledge Base Maintenance

### Adding Migration Examples

See the [Implementation Guide](docs/reference/implementation-guide.md) for detailed instructions on:
- Adding new migration examples
- Creating pattern documentation
- Updating action mappings
- Maintaining the knowledge base

### Knowledge Base Structure

```
docs/
├── index.md                      # Knowledge base home
├── jenkins/                      # Jenkins-specific examples
├── azure-devops/                 # Azure DevOps examples
├── circleci/                     # CircleCI examples
├── patterns/                     # Common CI/CD patterns
└── reference/                    # Quick reference guides
```

## Contributing

We welcome contributions to improve the migration agents and knowledge base:

1. **Report Issues**: Submit bug reports or feature requests
2. **Improve Agents**: Enhance agent capabilities and coverage
3. **Add Systems**: Create agents for additional CI/CD systems
4. **Add Examples**: Contribute migration examples to the knowledge base
5. **Add Patterns**: Document new CI/CD patterns
6. **Update Documentation**: Keep guides and examples current
7. **Update Action Mappings**: Add new tool mappings as they become available

