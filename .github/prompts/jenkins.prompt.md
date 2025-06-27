You are tasked with converting Jenkins configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with Jenkins pipelines that need to be migrated to GitHub Actions. The repository contains various Jenkins configuration files, including Jenkinsfiles (declarative and scripted), pipeline configurations, and shared library usage. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all Jenkins pipelines to GitHub Actions workflows
- Maintain the same logical flow and dependencies between stages and steps
- Preserve all build steps, deployment stages, and conditional logic
- Convert Jenkins stage dependencies to GitHub Actions job dependencies using `needs:`
- Handle Jenkins parallel stages as separate GitHub Actions jobs

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original Jenkins files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `build-pipeline.yml`, `deploy-production.yml`)

### 3. Template Handling

- For shared library usage and reusable pipeline components, expand them inline in the resulting GitHub Actions workflow
- Apply the shared library functions and pipeline parameters to generate the complete workflow
- Convert Jenkins parameters and environment variables to GitHub Actions workflow inputs and variables

### 4. Environment and Service Mapping

- Convert Jenkins environment variables and credentials to GitHub Actions environment variables and secrets
- Map Jenkins agents and node labels to appropriate GitHub Actions runners (`runs-on:`)
- Convert Jenkins triggers (SCM polling, webhooks, cron) to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements based on Jenkins when conditions
- Convert Jenkins environments and deployment stages to GitHub Actions environments

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from Jenkins to GitHub Actions
- Mapping of original Jenkins files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues
- Credential and secret mapping requirements
- Shared library replacement strategies

### 6. Specific Considerations

- Preserve all artifact handling and workspace management
- Convert Jenkins build tools and plugin usage
- Maintain database setup and service configurations
- Keep all notification integrations (email, Slack, etc.)
- Preserve approval processes and manual triggers
- Handle multi-environment deployments (dev, staging, production)
- Maintain rollback capabilities
- Convert Jenkins credential stores to GitHub Actions secrets
- Handle Jenkins master-slave configurations appropriately

### 7. Jenkins Specific Mappings

- Convert Jenkins `agent` specifications to appropriate GitHub Actions `runs-on:` configurations
- Map Jenkins pipeline steps to equivalent GitHub Actions steps or shell commands
- Convert Jenkins `stage` blocks to GitHub Actions jobs with appropriate dependencies
- Handle Jenkins `when` conditions as `if:` conditions
- Convert Jenkins credential bindings to GitHub Actions secret references
- Map Jenkins shared libraries to equivalent GitHub Actions or custom actions
- Convert Jenkins triggers (SCM, cron, upstream) to GitHub Actions triggers
- Handle Jenkins matrix builds using GitHub Actions matrix strategy
- Convert Jenkins post-build actions to appropriate GitHub Actions job conclusions

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── build-pipeline.yml
│   ├── deploy-production.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── Jenkinsfile
    ├── vars/
    │   └── [shared library files]
    ├── jenkins/
    │   └── [pipeline configurations]
    └── [other original files]
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all stage dependencies and pipeline flow are properly defined
- Confirm that all credentials and secrets are properly referenced
- Test that triggers and conditions are properly converted
- Validate that deployment environments and approval processes are maintained
- Ensure artifact handling and workspace management work correctly
- Verify that shared library functionality is properly replaced with equivalent actions or scripts

Please provide the complete converted workflows and documentation as specified above.
