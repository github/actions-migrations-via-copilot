You are tasked with converting Azure DevOps Pipeline configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with Azure DevOps pipelines that need to be migrated to GitHub Actions. The repository contains various Azure DevOps configuration files, including pipeline definitions, templates, and YAML builds. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all Azure DevOps pipelines to GitHub Actions workflows
- Maintain the same logical flow and dependencies between jobs and stages
- Preserve all build steps, deployment stages, and conditional logic
- Convert Azure DevOps pipeline dependencies to GitHub Actions job dependencies using `needs:`
- Handle Azure DevOps stages as separate GitHub Actions jobs

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original Azure DevOps files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `build-and-deploy.yml`, `ci-pipeline.yml`)

### 3. Template Handling

- For template-based configurations (azure-pipelines.yml using template references), expand the template inline in the resulting GitHub Actions workflow
- Apply the template parameters to generate the complete workflow without template references
- Convert Azure DevOps template parameters to GitHub Actions workflow inputs or variables

### 4. Environment and Service Mapping

- Convert Azure DevOps service connections to GitHub Actions secrets and environment variables
- Map Azure DevOps variables and variable groups to GitHub Actions environment variables and secrets
- Convert Azure DevOps triggers to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements
- Convert Azure DevOps deployment jobs to GitHub Actions deployment jobs with environments

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from Azure DevOps to GitHub Actions
- Mapping of original Azure DevOps files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues
- Service connection and secret mapping requirements

### 6. Specific Considerations

- Preserve all Azure-related configurations and credential handling
- Convert Azure DevOps service connections to appropriate GitHub Actions secrets
- Maintain database setup and migration steps
- Keep all notification integrations (Teams, email, etc.)
- Preserve approval gates and deployment conditions
- Handle multi-environment deployments (dev, staging, production)
- Maintain rollback capabilities
- Convert Azure DevOps artifacts to GitHub Actions artifacts
- Handle Azure DevOps pool specifications to appropriate GitHub Actions runners

### 7. Azure DevOps Specific Mappings

- Convert `pool:` specifications to `runs-on:` with appropriate runner types
- Map Azure DevOps tasks to equivalent GitHub Actions or shell commands
- Convert `dependsOn:` to `needs:` in GitHub Actions
- Handle `condition:` statements as `if:` conditions
- Convert Azure DevOps environments to GitHub Actions environments
- Map Azure DevOps variable groups to GitHub Actions organization/repository variables

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── build-and-deploy.yml
│   ├── ci-pipeline.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── azure-pipelines.yml
    ├── build-template.yml
    ├── deploy-template.yml
    └── [other original files]
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all job dependencies are properly defined
- Confirm that all secrets and service connections are properly referenced
- Test that triggers and conditions are properly converted
- Validate that deployment environments and approval processes are maintained

Please provide the complete converted workflows and documentation as specified above.
