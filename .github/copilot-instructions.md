# GitHub Actions Migrations via Copilot - Development Guidelines

This document provides coding standards and best practices for contributing to the GitHub Actions Migrations via Copilot project.

## Project Overview

This is a GitHub Actions-based automation tool designed to migrate CI/CD pipelines from various systems (Jenkins, Azure DevOps, CircleCI, etc.) to GitHub Actions at scale. The project uses GitHub Coding Agent integration and issue-ops workflows for automated, scalable migrations.

## Architecture & File Organization

### Directory Structure

```
.github/
├── copilot-instructions.md     # This file
├── prompts/                    # Migration prompt templates (organized by CI/CD system)
├── scripts/                    # JavaScript modules for GitHub Actions workflows
├── settings/                   # YAML configuration files
└── workflows/                  # GitHub Actions workflow definitions
```

### Key Components

- **Workflows**: Orchestrate the migration process using GitHub Actions
- **Scripts**: Reusable JavaScript modules called by workflows via `actions/github-script`
- **Settings**: YAML configuration files for organizations, migration types, and prompts
- **Prompts**: Markdown templates used by GitHub Coding Agent for specific CI/CD migrations

## Coding Standards

### JavaScript (GitHub Actions Scripts)

#### Module Structure

- All scripts must export an async function with destructured parameters:

```javascript
module.exports = async ({
  github,
  context,
  core,
  process,
  ...additionalParams
}) => {
  try {
    // Implementation
    return result
  } catch (error) {
    core.setFailed(`Operation failed: ${error.message}`)
    throw error
  }
}
```

#### Error Handling

- Always wrap main logic in try-catch blocks
- Use `core.setFailed()` for critical errors
- Use `core.warning()` for non-critical issues
- Use `core.info()` for status updates
- Re-throw errors after logging for proper workflow failure handling

#### GitHub API Usage

- Use `github.paginate()` for API calls that return large datasets
- Always specify `per_page: 100` for optimal API performance
- Handle rate limiting gracefully with appropriate error messages
- Use repository custom properties for tracking migration state

#### Logging Standards

- Start operations with `core.info('Starting operation: description')`
- Log progress for batch operations: `core.info('Processing ${current}/${total} items')`
- Use descriptive log messages with context (org/repo names, counts, etc.)
- End operations with success/completion messages

#### Variable Naming

- Use camelCase for variables and functions
- Use descriptive names: `migrationTypeProperty` not `prop`
- Use plural forms for arrays: `repos`, `repoNames`, `organizations`
- Use full words: `organization` not `org` (except for GitHub API parameters)

### YAML Configuration

#### GitHub Actions Workflows

- Use descriptive workflow names with proper capitalization
- Include helpful comments explaining workflow purpose
- Use `workflow_dispatch` for manual triggers in addition to other triggers
- Use matrix strategies for processing multiple organizations
- Set `fail-fast: false` for batch operations to process all items even if some fail

#### Workflow Structure

```yaml
name: Descriptive Workflow Name

# Brief comment explaining workflow purpose

on:
  workflow_dispatch:
  # Additional triggers as needed

jobs:
  job-name:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        organization: ${{ fromJson(vars.ORGANIZATIONS || '["DEFAULT_ORG"]') }}
      fail-fast: false

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      # Additional steps...
```

#### Configuration Files

- Use lowercase with underscores for configuration keys: `gh_app_id`, `migration_type`
- Include comprehensive comments explaining each section
- Provide example/placeholder values for required fields
- Group related configuration items with descriptive section headers

### Documentation Standards

#### README Files

- Include Mermaid diagrams for complex workflow visualizations
- Provide both high-level overview and detailed step-by-step explanations
- Include deployment instructions for different scenarios (customer vs. development)
- Use clear section headers and maintain consistent formatting

#### Code Comments

- Add inline comments for complex logic or GitHub API-specific requirements
- Include examples in comments for configuration or usage patterns
- Document any workarounds or platform-specific considerations

## GitHub Actions Best Practices

### Security

- Use GitHub App tokens instead of PATs where possible
- Scope tokens to minimum required permissions
- Store sensitive values in repository secrets, not variables
- Use `actions/create-github-app-token` for generating app tokens

### Performance

- Use batch processing with configurable batch sizes
- Implement pagination for large datasets
- Use matrix strategies for parallel processing when appropriate
- Cache dependencies when possible

### Reliability

- Implement proper error handling and recovery
- Use `continue-on-error` judiciously (prefer explicit error handling)
- Include timeout settings for long-running operations
- Provide clear failure messages with actionable information

Remember: This project operates at scale across multiple organizations and repositories. Always consider the impact of changes on performance, reliability, and user experience across diverse environments.
