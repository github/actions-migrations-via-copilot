You are tasked with converting Drone CI configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with Drone CI pipelines that need to be migrated to GitHub Actions. The repository contains various Drone configuration files, including pipeline definitions and templates. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all Drone CI pipelines to GitHub Actions workflows
- Maintain the same logical flow and dependencies between jobs
- Preserve all build steps, deployment stages, and conditional logic
- Convert Drone pipeline dependencies to GitHub Actions job dependencies using `needs:`

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original Drone files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `scoop-ci.yml`, `spg-order-service.yml`)

### 3. Template Handling

- For template-based configurations (like `spg-order-service-drone.yml` using `spg-awsma-java21.yaml`), expand the template inline in the resulting GitHub Actions workflow
- Apply the template data to generate the complete workflow without template references

### 4. Environment and Service Mapping

- Convert Drone services to GitHub Actions services in job configuration
- Map Drone environment variables to GitHub Actions environment variables
- Convert Drone triggers to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from Drone CI to GitHub Actions
- Mapping of original Drone files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues

### 6. Specific Considerations

- Preserve all AWS-related configurations and credential handling
- Maintain database setup and migration steps
- Keep all notification integrations (Slack, JIRA, etc.)
- Preserve concurrency limits and pipeline dependencies
- Handle multi-environment deployments (dev, staging, production)
- Maintain rollback capabilities

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── scoop-ci.yml
│   ├── spg-order-service.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── scoop-drone.yml
    ├── spg-awsma-java21.yaml
    ├── spg-order-service-drone.yml
    └── news-drone.yml
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all job dependencies are properly defined
- Confirm that all secrets are retrieved via vault-action
- Test that triggers and conditions are properly converted

Please provide the complete converted workflows and documentation as specified above.
