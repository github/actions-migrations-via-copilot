You are tasked with converting CircleCI configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with CircleCI pipelines that need to be migrated to GitHub Actions. The repository contains .circleci/config.yml configuration files with various job definitions, workflows, and orb usage. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all CircleCI workflows and jobs to GitHub Actions workflows
- Maintain the same logical flow and dependencies between jobs
- Preserve all build steps, deployment stages, and conditional logic
- Convert CircleCI workflow dependencies to GitHub Actions job dependencies using `needs:`
- Handle CircleCI parallel jobs as separate GitHub Actions jobs

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original CircleCI files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `build-and-test.yml`, `deploy-workflow.yml`)

### 3. Template Handling

- For orb usage and reusable commands, expand them inline in the resulting GitHub Actions workflow
- Apply the orb parameters and command definitions to generate the complete workflow
- Convert CircleCI parameters and environment variables to GitHub Actions workflow inputs and variables

### 4. Environment and Service Mapping

- Convert CircleCI environment variables to GitHub Actions environment variables and secrets
- Map CircleCI executors to appropriate GitHub Actions runners (`runs-on:`)
- Convert CircleCI triggers and filters to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements based on CircleCI when conditions
- Convert CircleCI contexts to GitHub Actions environments and organization secrets

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from CircleCI to GitHub Actions
- Mapping of original CircleCI files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues
- Context and secret mapping requirements
- Orb replacement strategies

### 6. Specific Considerations

- Preserve all artifact handling and workspace persistence
- Convert CircleCI docker layer caching and dependency caching
- Maintain database setup and service configurations
- Keep all notification integrations (Slack, email, etc.)
- Preserve approval jobs and manual triggers
- Handle multi-environment deployments (dev, staging, production)
- Maintain rollback capabilities
- Convert CircleCI machine and docker executors appropriately
- Handle CircleCI resource classes and parallelism settings

### 7. CircleCI Specific Mappings

- Convert CircleCI `executor:` specifications to appropriate GitHub Actions `runs-on:` and container configurations
- Map CircleCI `steps:` to equivalent GitHub Actions steps
- Convert CircleCI `requires:` to `needs:` in GitHub Actions
- Handle CircleCI `when:` conditions as `if:` conditions
- Convert CircleCI contexts to GitHub Actions environments and secrets
- Map CircleCI orbs to equivalent GitHub Actions or custom actions
- Convert CircleCI workflows with filters to appropriate GitHub Actions triggers
- Handle CircleCI matrix jobs using GitHub Actions matrix strategy

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── build-and-test.yml
│   ├── deploy-workflow.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── .circleci/
    │   ├── config.yml
    │   └── [other circleci files]
    └── [other original files]
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all job dependencies and workflow triggers are properly defined
- Confirm that all contexts and secrets are properly referenced
- Test that filters and conditions are properly converted
- Validate that approval jobs and deployment environments are maintained
- Ensure caching strategies and artifact handling work correctly
- Verify that orb functionality is properly replaced with equivalent actions or scripts

Please provide the complete converted workflows and documentation as specified above.
