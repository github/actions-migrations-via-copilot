You are tasked with converting Travis CI configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with Travis CI pipelines that need to be migrated to GitHub Actions. The repository contains .travis.yml configuration files with various build matrices, deployment configurations, and lifecycle hooks. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all Travis CI build configurations to GitHub Actions workflows
- Maintain the same logical flow and dependencies between build stages
- Preserve all build steps, test execution, and deployment stages
- Convert Travis CI build matrix to GitHub Actions matrix strategy
- Handle Travis CI build stages as separate GitHub Actions jobs with appropriate dependencies

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original Travis CI files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `ci-matrix.yml`, `deploy-releases.yml`)

### 3. Template Handling

- For complex build matrices and stage configurations, organize them logically in GitHub Actions workflows
- Apply Travis CI environment variables and build configurations to generate complete workflows
- Convert Travis CI global and matrix-specific environment variables to GitHub Actions variables

### 4. Environment and Service Mapping

- Convert Travis CI environment variables to GitHub Actions environment variables and secrets
- Map Travis CI language and runtime specifications to appropriate GitHub Actions setup actions
- Convert Travis CI triggers and branch configurations to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements based on Travis CI conditions
- Convert Travis CI deployment providers to GitHub Actions deployment jobs

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from Travis CI to GitHub Actions
- Mapping of original Travis CI files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues
- Environment variable and secret mapping requirements
- Deployment provider replacement strategies

### 6. Specific Considerations

- Preserve all cache configurations and dependency management
- Convert Travis CI service dependencies (databases, message queues, etc.)
- Maintain test execution and coverage reporting
- Keep all notification integrations and deployment notifications
- Preserve deployment conditions and branch-based deployments
- Handle multi-environment deployments and provider-specific configurations
- Maintain addon configurations (apt packages, etc.)
- Convert Travis CI encrypted variables to GitHub Actions secrets
- Handle Travis CI build stages and job lifecycle appropriately

### 7. Travis CI Specific Mappings

- Convert Travis CI language specifications to appropriate GitHub Actions setup actions (setup-node, setup-python, etc.)
- Map Travis CI build matrix to GitHub Actions matrix strategy
- Convert Travis CI `script:`, `before_script:`, `after_script:` to appropriate GitHub Actions steps
- Handle Travis CI `if:` conditions as GitHub Actions `if:` conditions
- Convert Travis CI deployment providers to equivalent GitHub Actions deployment steps
- Map Travis CI services to GitHub Actions services configuration
- Convert Travis CI caching to GitHub Actions cache action
- Handle Travis CI notifications (email, Slack, webhooks) as GitHub Actions notifications
- Convert Travis CI build stages to separate GitHub Actions jobs with `needs:` dependencies

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── ci-matrix.yml
│   ├── deploy-releases.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── .travis.yml
    ├── travis/
    │   └── [additional travis configurations]
    └── [other original files]
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all build matrix configurations are properly defined
- Confirm that all environment variables and secrets are properly referenced
- Test that triggers and deployment conditions are properly converted
- Validate that service dependencies and caching work correctly
- Ensure test execution and reporting mechanisms are maintained
- Verify that deployment providers are properly replaced with equivalent GitHub Actions

Please provide the complete converted workflows and documentation as specified above.
