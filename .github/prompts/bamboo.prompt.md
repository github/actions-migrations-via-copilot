You are tasked with converting Bamboo configuration files to GitHub Actions workflows. Please follow these specific requirements:

## Context

I have a repository with Bamboo build plans that need to be migrated to GitHub Actions. The repository contains various Bamboo configuration files, including build plans, deployment projects, and specifications. The goal is to convert these configurations into equivalent GitHub Actions workflows while adhering to specific standards and practices.

## Requirements

### 1. Conversion Standards

- Convert all Bamboo build plans to GitHub Actions workflows
- Maintain the same logical flow and dependencies between jobs and stages
- Preserve all build steps, deployment stages, and conditional logic
- Convert Bamboo plan dependencies to GitHub Actions job dependencies using `needs:`
- Handle Bamboo stages as separate GitHub Actions jobs

### 2. File Organization

- Create all GitHub Actions workflows in `.github/workflows/` directory
- Move the original Bamboo files to `.github/ci-archive/` directory (preserve original structure)
- Name workflow files descriptively (e.g., `build-plan.yml`, `deployment-project.yml`)

### 3. Template Handling

- For template-based configurations (Bamboo specs using shared configurations), expand the template inline in the resulting GitHub Actions workflow
- Apply the template variables to generate the complete workflow without template references
- Convert Bamboo global variables to GitHub Actions workflow variables

### 4. Environment and Service Mapping

- Convert Bamboo global variables to GitHub Actions environment variables and secrets
- Map Bamboo capabilities and requirements to appropriate GitHub Actions runner specifications
- Convert Bamboo triggers to appropriate GitHub Actions triggers (`on:` section)
- Handle conditional execution with `if:` statements
- Convert Bamboo deployment environments to GitHub Actions deployment environments

### 5. Documentation

Create a comprehensive README.md file in `.github/workflows/` that includes:

- Overview of the conversion from Bamboo to GitHub Actions
- Mapping of original Bamboo files to new GitHub Actions workflows
- Any breaking changes or considerations for the migration
- Troubleshooting guide for common issues
- Variable and capability mapping requirements

### 6. Specific Considerations

- Preserve all artifact handling and sharing between jobs
- Convert Bamboo repository configurations to appropriate checkout actions
- Maintain database setup and migration steps
- Keep all notification integrations (HipChat, email, etc.)
- Preserve approval processes and manual triggers
- Handle multi-environment deployments (dev, staging, production)
- Maintain rollback capabilities
- Convert Bamboo elastic instances to appropriate GitHub Actions runners
- Handle Bamboo quarantine and test result parsing

### 7. Bamboo Specific Mappings

- Convert Bamboo agents and capabilities to `runs-on:` with appropriate runner types
- Map Bamboo tasks to equivalent GitHub Actions or shell commands
- Convert plan dependencies to `needs:` in GitHub Actions
- Handle Bamboo conditions as `if:` conditions
- Convert Bamboo deployment projects to GitHub Actions deployment workflows
- Map Bamboo global variables to GitHub Actions organization/repository variables
- Convert Bamboo repository polling to GitHub Actions webhook triggers

## Expected Output Structure

```
.github/
├── workflows/
│   ├── README.md
│   ├── build-plan.yml
│   ├── deployment-project.yml
│   └── [other converted workflows]
└── ci-archive/
    ├── bamboo-specs/
    │   ├── build-plan.yaml
    │   ├── deployment-project.yaml
    │   └── [other spec files]
    └── [other original files]
```

## Validation Requirements

- Ensure all workflows are syntactically valid GitHub Actions YAML
- Verify that all job dependencies are properly defined
- Confirm that all global variables and secrets are properly referenced
- Test that triggers and conditions are properly converted
- Validate that deployment environments and approval processes are maintained
- Ensure artifact handling and test result parsing work correctly

Please provide the complete converted workflows and documentation as specified above.
