You are tasked with converting Bitbucket Pipelines configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with Bitbucket Pipelines that need to be migrated to GitHub Actions. The repository contains bitbucket-pipelines.yml configuration files with various pipeline definitions, custom steps, and deployment configurations. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all Bitbucket Pipelines to GitHub Actions workflows
- Maintain the same logical flow and dependencies between steps and parallel jobs
- Preserve all build steps, deployment stages, and conditional logic
- Convert Bitbucket pipeline dependencies and parallel execution to GitHub Actions job dependencies using `needs:`
- Handle Bitbucket parallel steps as separate GitHub Actions jobs

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original Bitbucket files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `ci-pipeline.yml`, `deploy-production.yml`)

### 3. Template Handling

- For custom steps and reusable configurations, expand them inline in the resulting GitHub Actions workflow
- Apply the step parameters to generate the complete workflow without custom step references
- Convert Bitbucket variables to GitHub Actions workflow variables and secrets

### 4. Environment and Service Mapping

- Convert Bitbucket repository variables to GitHub Actions environment variables and secrets
- Map Bitbucket deployment environments to GitHub Actions environments
- Convert Bitbucket triggers to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements based on Bitbucket conditions
- Convert Bitbucket services (databases, caches) to GitHub Actions services

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from Bitbucket Pipelines to GitHub Actions
- Mapping of original Bitbucket files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues
- Variable and secret mapping requirements

### 6. Specific Considerations

- Preserve all artifact handling and caching configurations
- Convert Bitbucket repository access and clone configurations
- Maintain database setup and service configurations
- Keep all notification integrations and deployment notifications
- Preserve manual triggers and approval processes
- Handle multi-environment deployments (dev, staging, production)
- Maintain rollback capabilities
- Convert Bitbucket pipeline caches to GitHub Actions cache
- Handle Bitbucket pipeline size and memory limits appropriately

### 7. Bitbucket Specific Mappings

- Convert Bitbucket `image:` specifications to appropriate GitHub Actions `runs-on:` and container configurations
- Map Bitbucket steps to equivalent GitHub Actions steps
- Convert `parallel:` sections to separate jobs with appropriate dependencies
- Handle Bitbucket `condition:` statements as `if:` conditions
- Convert Bitbucket deployment environments to GitHub Actions environments with protection rules
- Map Bitbucket variables (repository, deployment, and secured) to appropriate GitHub Actions secrets and variables
- Convert Bitbucket triggers (push, pull request, manual, scheduled) to GitHub Actions equivalents

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── ci-pipeline.yml
│   ├── deploy-production.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── bitbucket-pipelines.yml
    ├── custom-steps/
    │   └── [custom step definitions]
    └── [other original files]
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all job dependencies and parallel execution are properly defined
- Confirm that all variables and secrets are properly referenced
- Test that triggers and conditions are properly converted
- Validate that deployment environments and protection rules are maintained
- Ensure caching and artifact handling work correctly
- Verify that service configurations (databases, etc.) are properly converted

Please provide the complete converted workflows and documentation as specified above.
