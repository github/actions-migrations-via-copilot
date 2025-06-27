# GitHub Actions Migrations via Copilot

An automated solution for migrating CI/CD pipelines from various systems (Jenkins, Azure DevOps, CircleCI, etc.) to GitHub Actions at scale using GitHub Coding Agent.

## Key Features

- **Scalable**: Process multiple repositories simultaneously across organizations
- **Automated**: Reduce manual effort with AI-powered workflow generation
- **Consistent**: Standardized migration approach across all repositories
- **Reviewable**: Human oversight through Pull Request review process
- **Trackable**: Migration progress documented via issues and PRs

## Requirements & Important Notes

### Prerequisites

- **GitHub Enterprise Cloud** with:
  - GitHub Hosted Runners (required for Coding Agent)
  - GitHub Copilot Business or Enterprise
  - Repository custom properties
- **Administrative access** to target organizations

### Cost Considerations

- **GitHub Actions minutes**: Consumes entitlement minutes, then standard charges apply ([billing info](https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions))
- **Copilot requests**: Uses premium requests with included allowances ([plan details](https://docs.github.com/en/enterprise-cloud@latest/copilot/about-github-copilot/plans-for-github-copilot#comparing-copilot-plans))

### Behavior Notes

- **Non-deterministic**: Generated workflows may vary between runs due to LLM nature
- **Variable timing**: Processing time depends on repository complexity and CI/CD system
- **Testing recommended**: Run pilot migrations to estimate costs and timing

## Architecture

### System Components

This solution consists of several interconnected components that work together to automate CI/CD pipeline migrations:

```mermaid
graph TB
    subgraph "Configuration Layer"
        Config[config.yaml]
        Prompts[Migration Prompts]
        Instructions[Copilot Instructions]
    end

    subgraph "Execution Layer"
        SettingsWF[Settings Workflow]
        SubmitWF[Submit Repositories Workflow]
        SettingsScript[settings.js]
        SubmitScript[submit-repositories.js]
    end

    subgraph "GitHub Platform"
        App[GitHub App]
        CustomProps[Custom Properties]
        Variables[Repository Variables]
        Secrets[Repository Secrets]
    end

    subgraph "Target Repositories"
        Repos[Organization Repositories]
        Issues[Migration Issues]
        Agent[GitHub Coding Agent]
        PRs[Generated Pull Requests]
    end

    Config --> SettingsWF
    Prompts --> SubmitWF
    Instructions --> Agent

    SettingsWF --> SettingsScript
    SubmitWF --> SubmitScript

    SettingsScript --> App
    SettingsScript --> CustomProps
    SettingsScript --> Variables

    SubmitScript --> App
    SubmitScript --> Repos
    SubmitScript --> Issues

    Issues --> Agent
    Agent --> PRs

    Variables --> SubmitWF
    Secrets --> SubmitWF
    CustomProps --> SubmitScript
```

### Key Components

#### Configuration Files

- **`.github/settings/config.yaml`**: Central configuration for GitHub App, organizations, and migration settings
- **`.github/prompts/*.prompt.md`**: System-specific migration instructions for the Coding Agent
- **`.github/copilot-instructions.md`**: Development guidelines and coding standards

#### Workflow Components

- **Settings Workflow**: Bootstrap configuration, creates variables and custom properties
- **Submit Repositories Workflow**: Main orchestration, processes organizations in parallel
- **JavaScript Modules**: `settings.js` and `submit-repositories.js` for API operations

#### Authentication & Security

- **GitHub App**: Provides scoped API access with minimal permissions
- **Custom Properties**: Track migration status across repositories
- **Secrets Management**: Secure storage of credentials and tokens

### Migration Flow

1. **Configuration**: Admin updates `config.yaml` with target organizations
2. **Bootstrap**: Settings workflow creates variables and custom properties
3. **Tagging**: Repositories tagged with migration types via custom properties
4. **Execution**: Submit workflow creates issues in repositories needing migration
5. **Auto-Reset**: System sets migration type to 'None' after issue creation to prevent reprocessing
6. **Processing**: GitHub Coding Agent generates workflows and creates PRs
7. **Review**: Repository teams review, test, and merge generated changes

## How It Works

The migration process follows these automated steps:

```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant Org as Organization
    participant Repo as Repository
    participant Issue as Migration Issue
    participant Agent as GitHub Coding Agent
    participant PR as Pull Request
    participant Dev as Developers

    GHA->>Org: Query repositories with custom properties
    Org-->>GHA: Return repository list with migration types

    loop For each repository needing migration
        GHA->>Issue: Create migration issue with CI/CD context
        Issue->>Agent: Auto-assign GitHub Coding Agent
        Agent->>Repo: Analyze existing CI/CD configuration
        Agent->>PR: Generate GitHub Actions workflows
        PR->>Dev: Notify for review
        Dev->>PR: Review, test, and merge
        Dev->>Issue: Close migration issue
    end
```

### Migration Process

1. **Discovery**: Query organizations for repositories with migration custom properties
2. **Issue Creation**: Create migration issues in target repositories with system-specific prompts
3. **Auto-Reset**: System automatically sets repository migration type to 'None' after issue creation to prevent duplicate processing
4. **Agent Processing**: GitHub Coding Agent analyzes existing CI/CD and generates workflows
5. **Review**: Repository maintainers review and refine generated Pull Requests
6. **Completion**: Original CI/CD files archived, new workflows activated

## Quick Start

### 1. Setup Repository

```bash
# Clone the template repository
git clone https://github.com/github/actions-migrations-via-copilot.git
cd actions-migrations-via-copilot

# Push to your target GitHub Enterprise
git remote set-url origin https://github.com/YOUR-ENTERPRISE-ORG/actions-migrations-via-copilot.git
git push -u origin main
```

**Note**: All configuration and execution should be done in your target GitHub Enterprise environment where the migrations will occur.

### 2. Create GitHub App

In your target GitHub Enterprise, create a GitHub App with these permissions:

- **Repository**: Actions, Contents, Issues, Pull requests, Custom properties (Read/Write)
- **Organization**: Custom properties, Members (Read/Write + Read)

### 3. Configure Settings

1. In your target Enterprise repository, update `.github/settings/config.yaml`:

```yaml
gh_app_id: 'YOUR_APP_ID'
organizations:
  - 'your-org-1'
  - 'your-org-2'
batch_size: 50
```

2. Add repository secrets in your target Enterprise repository:

   - `GH_APP_PEM`: GitHub App private key
   - `ISSUE_SUBMIT_TOKEN`: Personal Access Token

3. Run the Configuration Settings workflow in your target Enterprise repository with bootstrap PAT

### 4. Tag Repositories

Set `GH_MIGRATION_TYPE` custom property on target repositories in your Enterprise:

- **Manual**: Repository Settings → Custom properties
- **Bulk**: Create a script to set repository properties via API
- **Auto-assign**: Set `default_value` in config.yaml to a specific migration type (e.g., 'Jenkins') to automatically migrate all repositories with the same approach

**Note**: After a migration issue is created, the system automatically resets the repository's migration type to 'None' to prevent duplicate processing on subsequent workflow runs.

### 5. Execute Migration

Run the "Submit Repositories" workflow in your target Enterprise repository manually or enable scheduling

## Architecture Overview

```mermaid
graph TB
    subgraph "Configuration"
        Config[config.yaml]
        Prompts[System-specific Prompts]
    end

    subgraph "Execution"
        Settings[Settings Workflow]
        Submit[Submit Workflow]
    end

    subgraph "GitHub Platform"
        App[GitHub App]
        Props[Custom Properties]
        Vars[Variables/Secrets]
    end

    subgraph "Target Repositories"
        Repos[Tagged Repositories]
        Issues[Migration Issues]
        Agent[Coding Agent]
        PRs[Generated PRs]
    end

    Config --> Settings
    Settings --> Props & Vars
    Submit --> App
    App --> Repos
    Repos --> Issues
    Issues --> Agent
    Agent --> PRs
```

## Configuration Reference

### Configuration File Structure (`.github/settings/config.yaml`)

```yaml
# GitHub App Configuration
gh_app_id: 'YOUR_APP_ID'

# Custom Property Configuration
gh_migration_type:
  default_value: 'None' # Can be set to specific type (e.g., 'Jenkins') for single-system migrations
  description: 'Migration tracking property'
  other_values:
    - 'Azure DevOps'
    - 'Jenkins'
    - 'CircleCI'
    - 'GitLab'
    # Add other CI/CD systems as needed

# Migration Prompt Mapping
migration_type_prompts:
  'Azure DevOps': 'azure-devops.prompt.md'
  'Jenkins': 'jenkins.prompt.md'
  'CircleCI': 'circleci.prompt.md'
  'GitLab': 'gitlab.prompt.md'

# Target Organizations
organizations:
  - 'organization-1'
  - 'organization-2'

# Processing Configuration
batch_size: 50 # Recommended starting value
```

### Required Secrets & Variables

| Type     | Name                 | Description            | Example                              |
| -------- | -------------------- | ---------------------- | ------------------------------------ |
| Secret   | `GH_APP_PEM`         | GitHub App private key | `-----BEGIN RSA PRIVATE KEY-----...` |
| Secret   | `ISSUE_SUBMIT_TOKEN` | PAT for issue creation | `ghp_xxxxxxxxxxxxxxxxxxxx`           |
| Variable | `GH_APP_ID`          | GitHub App identifier  | `1561891`                            |
| Variable | `ORGANIZATIONS`      | JSON array of orgs     | `["org1", "org2"]`                   |

### Prompt File Template

Create system-specific prompts in `.github/prompts/`:

```markdown
# [CI/CD System] Migration Prompt

## Context

Migration from [System] to GitHub Actions for this repository.

## Requirements

### 1. Conversion Standards

- Convert [system-specific] syntax to GitHub Actions
- Preserve logical flow and dependencies
- Map environment variables and secrets

### 2. File Organization

- Place workflows in `.github/workflows/`
- Archive original files to `.archive/`
- Create migration documentation

### 3. System-Specific Mappings

- [System-specific conversion rules]
- [Build tool mappings]
- [Environment configurations]
```

### Single-System Migration Configuration

For organizations migrating from a single CI/CD system (e.g., all repositories use Jenkins), you can simplify the process by setting the `default_value` to your migration type:

```yaml
gh_migration_type:
  default_value: 'Jenkins' # Instead of 'None'
  description: 'Migration tracking property'
  other_values:
    - 'Jenkins'
    - 'None' # Keep for repositories that shouldn't be migrated
```

**Benefits**:

- Eliminates need for manual repository tagging
- All repositories automatically get the specified migration type
- Reduces setup time for single-system environments
- Repositories can still be set to 'None' to exclude them from migration
- System automatically resets migration type to 'None' after processing to prevent duplicate migrations

**Use Cases**:

- Company-wide Jenkins to GitHub Actions migration
- Single CI/CD system consolidation projects
- Pilot migrations with homogeneous environments

## Troubleshooting & FAQ

### Common Issues

| Issue                          | Solution                                                |
| ------------------------------ | ------------------------------------------------------- |
| Custom properties not created  | Verify org has Enterprise Cloud and admin permissions   |
| Copilot not assigned to issues | Check `ISSUE_SUBMIT_TOKEN` scope and Copilot enablement |
| Workflow timeouts              | Reduce `batch_size` and add timeout configurations      |
| Permission errors              | Verify GitHub App permissions and installation          |

### Performance Tips

- **Start small**: Begin with `batch_size: 25-50`
- **Monitor usage**: Track GitHub Actions minutes and Copilot requests
- **Parallel processing**: Workflow uses matrix strategy for organizations
- **Rate limiting**: Built-in API rate limit handling
- **Single-system migrations**: Set `default_value` to your CI/CD system type to skip manual repository tagging
- **Automatic reset**: System prevents duplicate processing by resetting migration type to 'None' after issue creation

### Migration Timing

| Repository Type               | Typical Duration |
| ----------------------------- | ---------------- |
| Simple (basic CI/CD)          | 5-15 minutes     |
| Complex (multiple pipelines)  | 15-45 minutes    |
| Enterprise (extensive config) | 30-90 minutes    |

_Note: Timing varies due to non-deterministic LLM behavior_

## Deployment Scenarios

### For GitHub Customers

```bash
# Clone the template and push to your GitHub Enterprise
git clone https://github.com/github/actions-migrations-via-copilot.git
cd actions-migrations-via-copilot
git remote set-url origin https://github.com/YOUR-ENTERPRISE-ORG/actions-migrations-via-copilot.git
git push -u origin main
# Configure and execute in your target Enterprise environment
```

### For GitHub Service Engineers

```bash
# Fork to your development organization for feature work
# Submit PRs back to main repository
```

## Contributing

Contributions welcome! Please:

1. Open an issue for feature requests or bugs
2. Submit PRs with clear descriptions
3. Follow the coding guidelines in `.github/copilot-instructions.md`
4. Test changes with sample repositories
