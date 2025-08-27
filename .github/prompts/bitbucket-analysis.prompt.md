# Bitbuc**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `.github/settings/config.yaml` file under the `organizations` key. You must read this configuration file to determine which specific organizations to analyze.

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- First, read the `.github/settings/config.yaml` file to retrieve the list of organizations from the `organizations` key
- Enumerate repositories within only the organizations specified in the configuration
- Search for Bitbucket Pipelines configuration files and pipeline definitions in these target organizations
- Access repository contents and Bitbucket-specific configurations
- Retrieve repository metadata and activity levels for the configured organizationses Analysis and Migration Assessment

You are tasked with conducting a comprehensive analysis of Bitbucket Pipelines across the GitHub organizations specified in the project configuration to prepare for migration to GitHub Actions.

## Context

This analysis focuses specifically on Bitbucket Pipelines configurations and their migration requirements. You will identify all Bitbucket Pipelines configurations, assess their complexity, and provide detailed migration guidance for transitioning to GitHub Actions.

**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `config.yaml` file under the `organizations` section:

- `antgrutta-actions`

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- Enumerate repositories within the specified organizations (`antgrutta-actions`)
- Search for Bitbucket Pipelines configuration files and pipeline definitions in these organizations
- Access repository contents and Bitbucket-specific configurations
- Retrieve repository metadata and activity levels for the target organizations

All analysis outputs and deliverables must be saved to a folder called `inventory-analysis/bitbucket` in the current workspace.

## Bitbucket Pipelines-Specific Discovery

### Configuration File Detection

Systematically search for and catalog Bitbucket Pipelines configurations:

- **bitbucket-pipelines.yml**: Main pipeline configuration files
- **Custom Pipeline Steps**: Custom Docker-based pipeline steps
- **Deployment Configurations**: Environment-specific deployment configs
- **Pipeline Variables**: Repository and deployment variables
- **Pipeline Schedules**: Scheduled pipeline configurations
- **Repository Access Keys**: SSH key configurations for deployments

### Bitbucket Pipelines Analysis

For each Bitbucket Pipelines configuration discovered:

#### Pipeline Structure Assessment

- **Pipeline Organization**: Default, branch, tag, and custom pipelines
- **Step Definitions**: Sequential and parallel step execution
- **Service Dependencies**: Database and service container configurations
- **Conditional Logic**: Branch-specific and conditional step execution
- **Manual Triggers**: Manual pipeline steps and deployment gates

#### Build Environment Analysis

- **Docker Images**: Default and custom Docker images
- **Service Containers**: Database, cache, and service configurations
- **Resource Requirements**: Memory limits and execution time constraints
- **Caching Strategies**: Dependencies and custom caching configurations
- **Environment Variables**: Build and deployment environment settings

#### Bitbucket-Specific Features

- **Custom Steps**: Docker-based custom pipeline steps
- **Artifacts**: Build artifacts and artifact passing between steps
- **Deployment Environments**: Environment definitions and restrictions
- **Pipeline Variables**: Repository and deployment variable management
- **SSH Keys**: Repository access keys and deployment keys
- **Notifications**: Email and integration notifications

#### Integration Patterns

- **Atlassian Tools**: Jira, Confluence, and Bamboo integrations
- **Cloud Deployments**: AWS, Azure, Heroku, and custom deployments
- **Container Registries**: Docker Hub, AWS ECR, and custom registries
- **External Services**: SonarCloud, security scanning, and monitoring tools

### Migration Complexity Assessment

For each Bitbucket Pipelines configuration, assess:

#### Complexity Scoring

- **Simple**: Basic build/test pipelines with standard steps
- **Medium**: Multi-step pipelines with service dependencies
- **Complex**: Advanced pipelines with custom steps and complex deployments
- **Enterprise**: Complex pipelines with multiple environments and integrations

#### Risk Assessment

- **Custom Step Dependencies**: Bitbucket-specific custom steps without alternatives
- **Atlassian Integration**: Deep Atlassian ecosystem integration
- **Deployment Restrictions**: Environment-specific access and deployment restrictions
- **Variable Management**: Complex variable hierarchy and scoping

## Repository Analysis Requirements

For each repository with Bitbucket Pipelines configurations:

### Bitbucket Pipelines Configuration Inventory

- Document all bitbucket-pipelines.yml files and pipeline definitions
- Catalog custom step usage and dependencies
- Identify deployment environment configurations and restrictions
- Map pipeline triggers and branch-specific configurations

### Business Impact Assessment

- **Repository Activity**: Commit frequency and team usage
- **Team Ownership**: Development teams and pipeline maintenance responsibilities
- **Environment Dependencies**: Production and staging environment requirements

## Output Requirements

### Bitbucket Pipelines Inventory CSV

Generate a detailed CSV file (`inventory-analysis/bitbucket/bitbucket-pipeline-inventory.csv`) with columns:

- **Organization Name**
- **Repository Name**
- **Repository URL**
- **Config File Path**
- **Pipeline Types** (default/branches/tags/custom)
- **Step Count**
- **Docker Images Used**
- **Service Dependencies**
- **Custom Steps Usage**
- **Deployment Environments**
- **Variable Dependencies**
- **Caching Configuration**
- **Complexity Score** (Simple/Medium/Complex/Enterprise)
- **Dependencies**
- **Special Requirements**
- **Last Activity Date**
- **Team/Owner Information**
- **Notes/Comments**

### Bitbucket Pipelines Migration Assessment Report

Create a comprehensive report (`inventory-analysis/bitbucket/bitbucket-migration-assessment.md`) including:

- **Executive Summary**: Bitbucket Pipelines-specific findings and recommendations
- **Pipeline Statistics**: Total count, complexity distribution, custom step usage
- **Migration Strategy**: Bitbucket Pipelines-to-GitHub Actions migration approach
- **Custom Step Migration**: Custom step alternatives and replacement strategies
- **Environment Migration**: Deployment environment migration to GitHub Actions
- **Risk Assessment**: Bitbucket-specific migration risks and mitigation
- **Timeline Recommendations**: Phased migration timeline for Bitbucket pipelines
- **Technical Requirements**: GitHub Actions setup for Bitbucket migration

### Bitbucket Pipelines-to-GitHub Actions Mapping Guide

Create a technical guide (`inventory-analysis/bitbucket/bitbucket-github-actions-mapping.md`) including:

- **Configuration Conversion**: Bitbucket Pipelines YAML to GitHub Actions workflow
- **Step Migration**: Bitbucket steps to GitHub Actions steps and actions
- **Service Migration**: Bitbucket services to GitHub Actions service containers
- **Variable Management**: Bitbucket variables to GitHub Actions variables and secrets
- **Environment Migration**: Bitbucket deployments to GitHub Actions environments
- **Custom Step Alternatives**: Replacement strategies for custom pipeline steps

### Bitbucket Pipelines Reusable Workflow Templates

Create workflow templates (`inventory-analysis/bitbucket/workflow-templates/`) for common Bitbucket patterns:

- **Docker Build Pipeline**: Container build and registry push workflows
- **Node.js Application**: NPM build and deployment workflows
- **AWS Deployment**: S3, ECS, and Lambda deployment workflows
- **Multi-Environment Pipeline**: Development to production promotion workflows
- **Atlassian Integration**: Jira and Confluence integration workflows

## Specific Bitbucket Pipelines Analysis Focus Areas

### Custom Step Assessment

- **Custom Step Inventory**: All custom steps in use across repositories
- **Step Functionality**: What each custom step provides and its dependencies
- **Docker Image Analysis**: Custom Docker images and their requirements
- **GitHub Actions Alternatives**: Available marketplace actions for custom steps

### Service and Infrastructure Analysis

- **Service Containers**: Database, cache, and application service usage
- **Docker Image Requirements**: Standard and custom image dependencies
- **Resource Constraints**: Memory and execution time limit analysis
- **Network Configuration**: Service communication and external access patterns

### Deployment and Environment Management

- **Environment Definitions**: Deployment environments and their configurations
- **Deployment Restrictions**: Environment-specific access controls and approvals
- **Variable Hierarchy**: Repository, deployment, and secured variable management
- **SSH Key Management**: Repository access keys and deployment key usage

### Atlassian Ecosystem Integration

- **Jira Integration**: Issue tracking and workflow integration patterns
- **Confluence Integration**: Documentation and release note automation
- **Bamboo Integration**: Build plan and deployment project connections
- **User Management**: Atlassian user and permission integration

### Variable and Secret Management

- **Variable Types**: Repository and deployment variables
- **Secured Variables**: Encrypted variable handling and access controls
- **Variable Inheritance**: Default and environment-specific variable overrides
- **External Secret Sources**: Integration with external secret management systems

### Caching and Performance Optimization

- **Cache Strategies**: Dependency caching and custom cache configurations
- **Build Optimization**: Step optimization and parallel execution patterns
- **Resource Usage**: Memory and execution time optimization opportunities
- **Performance Benchmarks**: Build time and resource usage baselines

### Integration and External Service Patterns

- **Cloud Platform Integration**: AWS, Azure, Heroku deployment patterns
- **Container Registry Usage**: Docker Hub, ECR, and custom registry integration
- **Monitoring Integration**: Application and infrastructure monitoring setup
- **Security Scanning**: Code quality and security scanning tool integration

### Migration-Specific Considerations

- **Repository Migration**: Bitbucket to GitHub repository migration considerations
- **Team Migration**: User and team migration from Bitbucket to GitHub
- **Permission Mapping**: Bitbucket permissions to GitHub repository permissions
- **Webhook Migration**: Bitbucket webhooks to GitHub Actions triggers

This focused Bitbucket Pipelines analysis will provide the detailed foundation needed for successful migration of Bitbucket Pipelines to GitHub Actions while addressing Atlassian ecosystem integration and improving CI/CD capabilities.
