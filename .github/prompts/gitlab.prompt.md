
You are tasked with converting GitLab CI/CD configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with GitLab CI/CD pipelines that need to be migrated to GitHub Actions. The repository contains .gitlab-ci.yml configuration files with various job definitions, stages, and include statements. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all GitLab CI/CD pipelines to GitHub Actions workflows
- Maintain the same logical flow and dependencies between jobs and stages
- Preserve all build steps, deployment stages, and conditional logic
- Convert GitLab stage dependencies to GitHub Actions job dependencies using `needs:`
- Handle GitLab stages as separate GitHub Actions jobs or organize jobs logically

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original GitLab files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `ci-pipeline.yml`, `deploy-production.yml`)

### 3. Template Handling

- For included files and templates, expand them inline in the resulting GitHub Actions workflow
- Apply the template variables and job extensions to generate the complete workflow
- Convert GitLab variables and extends to GitHub Actions workflow variables and reusable components

### 4. Environment and Service Mapping

- Convert GitLab variables to GitHub Actions environment variables and secrets
- Map GitLab runners and tags to appropriate GitHub Actions runners (`runs-on:`)
- Convert GitLab triggers and rules to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements based on GitLab rules and only/except
- Convert GitLab environments to GitHub Actions environments with protection rules

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from GitLab CI/CD to GitHub Actions
- Mapping of original GitLab files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues
- Variable and secret mapping requirements
- Runner and environment mapping strategies

### 6. Specific Considerations

- Preserve all artifact handling and dependency configurations
- Convert GitLab cache configurations to GitHub Actions cache
- Maintain database setup and service configurations
- Keep all notification integrations and deployment notifications
- Preserve manual jobs and approval processes
- Handle multi-environment deployments (dev, staging, production)
- Maintain rollback capabilities
- Convert GitLab container registry usage appropriately
- Handle GitLab merge request pipelines and branch protections

### 7. GitLab Specific Mappings

- Convert GitLab `image:` and `services:` to appropriate GitHub Actions container and services configurations
- Map GitLab job scripts to equivalent GitHub Actions run steps
- Convert GitLab `stage:` to logical job grouping with `needs:` dependencies
- Handle GitLab `rules:`, `only:`, and `except:` as `if:` conditions
- Convert GitLab environments to GitHub Actions environments
- Map GitLab variables (project, group, instance) to appropriate GitHub Actions secrets and variables
- Convert GitLab triggers (push, merge request, schedule, API) to GitHub Actions equivalents
- Handle GitLab parallel and matrix jobs using GitHub Actions matrix strategy

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── ci-pipeline.yml
│   ├── deploy-production.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── .gitlab-ci.yml
    ├── .gitlab/
    │   └── ci/
    │       └── [included templates]
    └── [other original files]
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all job dependencies and stage logic are properly defined
- Confirm that all variables and secrets are properly referenced
- Test that rules and conditions are properly converted
- Validate that environments and deployment protections are maintained
- Ensure caching strategies and artifact handling work correctly
- Verify that merge request workflows and branch protections are properly implemented

Please provide the complete converted workflows and documentation as specified above.
