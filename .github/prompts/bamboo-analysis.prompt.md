# Bamboo CI/CD Analysis and Migration Assessment

You are tasked with conducting a comprehensive analysis of Bamboo CI/CD configurations across the GitHub organizations specified in the project configuration to prepare for migration to GitHub Actions.

## Context

This analysis focuses specifically on Bamboo build plans, deployment projects, and their migration requirements. You will identify all Bamboo configurations, assess their complexity, and provide detailed migration guidance for transitioning to GitHub Actions.

**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `.github/settings/config.yaml` file under the `organizations` key. You must read this configuration file to determine which specific organizations to analyze.

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- First, read the `.github/settings/config.yaml` file to retrieve the list of organizations from the `organizations` key
- Enumerate repositories within only the organizations specified in the configuration
- Search for Bamboo configuration files and build specifications in these target organizations
- Access repository contents and Bamboo-specific configurations
- Retrieve repository metadata and activity levels for the configured organizations

All analysis outputs and deliverables must be saved to a folder called `inventory-analysis/bamboo` in the current workspace.

## Bamboo-Specific Discovery

### Configuration File Detection

Systematically search for and catalog Bamboo configurations:

- **bamboo-specs/**: Bamboo Specs configuration directories
- **Build Plan Specs**: Java-based and YAML build plan definitions
- **Deployment Project Specs**: Deployment project configurations
- **Repository Linking**: Repository linking and trigger configurations
- **Permission Specs**: User and group permission configurations
- **Variable Definitions**: Plan and deployment variable configurations

### Bamboo Configuration Analysis

For each Bamboo configuration discovered:

#### Build Plan Structure Assessment

- **Stage Organization**: Build, test, and deployment stage configurations
- **Job Definitions**: Individual job configurations and dependencies
- **Task Configurations**: Build tasks, test tasks, and deployment tasks
- **Artifact Definitions**: Build artifacts and artifact dependencies
- **Trigger Configurations**: Repository polling, webhook, and scheduled triggers

#### Build Environment Analysis

- **Agent Requirements**: Capability requirements and agent assignments
- **Docker Configurations**: Docker tasks and container usage
- **Repository Access**: Source code repository configurations and permissions
- **Build Variables**: Plan variables, deployment variables, and global variables
- **Notification Settings**: Email, IM, and webhook notification configurations

#### Bamboo-Specific Features

- **Bamboo Specs**: Java-based and YAML configuration as code
- **Deployment Projects**: Environment definitions and deployment configurations
- **Release Management**: Release versioning and artifact promotion
- **Plan Branches**: Automatic branch detection and plan branch creation
- **Quarantine**: Failed test quarantine and management
- **Elastic Instances**: Auto-scaling agent configurations

#### Integration Patterns

- **Atlassian Tools**: Jira, Bitbucket, Confluence integrations
- **External Tools**: Maven, Gradle, Ant, and custom tool integrations
- **Cloud Deployments**: AWS, Azure, and custom deployment integrations
- **Artifact Repositories**: Nexus, Artifactory, and custom repositories

### Migration Complexity Assessment

For each Bamboo configuration, assess:

#### Complexity Scoring

- **Simple**: Basic build plans with standard tasks
- **Medium**: Multi-stage plans with moderate integrations
- **Complex**: Advanced plans with deployment projects and custom tasks
- **Enterprise**: Complex plans with extensive Atlassian integration and compliance

#### Risk Assessment

- **Custom Task Dependencies**: Bamboo-specific tasks without GitHub equivalents
- **Atlassian Integration**: Deep Atlassian ecosystem dependencies
- **Agent Infrastructure**: Specialized agent capabilities and configurations
- **Compliance Requirements**: Enterprise compliance and audit requirements

## Repository Analysis Requirements

For each repository with Bamboo configurations:

### Bamboo Configuration Inventory

- Document all bamboo-specs configurations and build plan definitions
- Catalog deployment project configurations and environment definitions
- Identify agent capability requirements and specialized configurations
- Map repository triggers and integration patterns

### Business Impact Assessment

- **Repository Activity**: Commit frequency and team usage
- **Team Ownership**: Development teams and build plan maintenance responsibilities
- **Infrastructure Dependencies**: Agent infrastructure and deployment targets

## Output Requirements

### Bamboo Configuration Inventory CSV

Generate a detailed CSV file (`inventory-analysis/bamboo/bamboo-configuration-inventory.csv`) with columns:

- **Organization Name**
- **Repository Name**
- **Repository URL**
- **Specs Location**
- **Build Plan Names**
- **Deployment Projects**
- **Stage Count**
- **Job Count**
- **Agent Requirements**
- **Task Types**
- **Artifact Dependencies**
- **Integration Points**
- **Complexity Score** (Simple/Medium/Complex/Enterprise)
- **Dependencies**
- **Special Requirements**
- **Last Activity Date**
- **Team/Owner Information**
- **Notes/Comments**

### Bamboo Migration Assessment Report

Create a comprehensive report (`inventory-analysis/bamboo/bamboo-migration-assessment.md`) including:

- **Executive Summary**: Bamboo-specific findings and recommendations
- **Configuration Statistics**: Total count, complexity distribution, task usage
- **Migration Strategy**: Bamboo-to-GitHub Actions migration approach
- **Task Migration**: Bamboo tasks to GitHub Actions steps and actions
- **Infrastructure Migration**: Bamboo agents to GitHub Actions runners
- **Risk Assessment**: Bamboo-specific migration risks and mitigation
- **Timeline Recommendations**: Phased migration timeline for Bamboo configurations
- **Technical Requirements**: GitHub Actions setup for Bamboo migration

### Bamboo-to-GitHub Actions Mapping Guide

Create a technical guide (`inventory-analysis/bamboo/bamboo-github-actions-mapping.md`) including:

- **Specs Conversion**: Bamboo Specs to GitHub Actions workflow translation
- **Build Plan Migration**: Bamboo build plans to GitHub Actions workflows
- **Task Migration**: Bamboo tasks to GitHub Actions steps and marketplace actions
- **Agent Migration**: Bamboo agents to GitHub Actions runners
- **Variable Management**: Bamboo variables to GitHub Actions variables and secrets
- **Deployment Migration**: Bamboo deployment projects to GitHub Actions environments

### Bamboo Reusable Workflow Templates

Create workflow templates (`inventory-analysis/bamboo/workflow-templates/`) for common Bamboo patterns:

- **Java Maven Build**: Maven-based build and test workflows
- **Java Gradle Build**: Gradle-based build and deployment workflows
- **Multi-Stage Deployment**: Environment promotion workflows
- **Artifact Management**: Build artifact creation and distribution workflows
- **Integration Testing**: Complex integration test workflows

## Specific Bamboo Analysis Focus Areas

### Bamboo Specs Assessment

- **Specs Format**: Java-based vs. YAML configuration analysis
- **Plan Definitions**: Build plan structure and complexity
- **Deployment Specs**: Deployment project and environment configurations
- **Permission Specs**: User and group permission management

### Task and Integration Analysis

- **Task Types**: Build, test, deployment, and custom task inventory
- **Tool Integrations**: Maven, Gradle, Ant, Docker, and custom tools
- **Plugin Usage**: Bamboo plugins and their GitHub Actions equivalents
- **Custom Tasks**: Organization-specific custom task implementations

### Agent Infrastructure Assessment

- **Agent Types**: Local, remote, and elastic agent configurations
- **Capability Requirements**: Agent capabilities and tool installations
- **Resource Requirements**: CPU, memory, and storage needs
- **Scaling Patterns**: Auto-scaling and capacity management

### Deployment Project Analysis

- **Environment Definitions**: Development, staging, and production environments
- **Release Management**: Version management and artifact promotion
- **Approval Processes**: Manual approval gates and sign-off requirements
- **Environment Variables**: Environment-specific configurations and secrets

### Atlassian Ecosystem Integration

- **Jira Integration**: Issue tracking and release management integration
- **Bitbucket Integration**: Source code repository and trigger integration
- **Confluence Integration**: Documentation and release notes automation
- **User Management**: Atlassian user directory and permission integration

### Build and Artifact Management

- **Artifact Definitions**: Build artifacts and their dependencies
- **Artifact Repositories**: Integration with Nexus, Artifactory, and custom repos
- **Artifact Promotion**: Artifact versioning and environment promotion
- **Storage Requirements**: Artifact storage and retention policies

### Notification and Monitoring

- **Notification Configurations**: Email, IM, and webhook notifications
- **Build Monitoring**: Build status monitoring and alerting
- **Performance Metrics**: Build time and success rate tracking
- **Dashboard Integration**: Build dashboard and reporting requirements

### Security and Compliance

- **Permission Management**: User and group permission configurations
- **Audit Requirements**: Build audit trails and compliance tracking
- **Secret Management**: Variable encryption and secret handling
- **Access Controls**: Repository and environment access restrictions

### Performance and Optimization

- **Build Performance**: Build time optimization and parallelization
- **Agent Utilization**: Agent usage patterns and optimization opportunities
- **Resource Optimization**: CPU, memory, and storage optimization
- **Caching Strategies**: Dependency and build cache configurations

This focused Bamboo analysis will provide the detailed foundation needed for successful migration of Bamboo build plans and deployment projects to GitHub Actions while maintaining Atlassian ecosystem integration and improving CI/CD capabilities.
