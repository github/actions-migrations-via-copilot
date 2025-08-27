# GitLab CI/CD Analysis and Migration Assessment

You are tasked with conducting a comprehensive analysis of GitLab CI/CD pipelines across the GitHub organizations specified in the project configuration to prepare for migration to GitHub Actions.

## Context

This analysis focuses specifically on GitLab CI/CD configurations and their migration requirements. You will identify all GitLab CI/CD configurations, assess their complexity, and provide detailed migration guidance for transitioning to GitHub Actions.

**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `.github/settings/config.yaml` file under the `organizations` key. You must read this configuration file to determine which specific organizations to analyze.

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- First, read the `.github/settings/config.yaml` file to retrieve the list of organizations from the `organizations` key
- Enumerate repositories within only the organizations specified in the configuration
- Search for GitLab CI/CD configuration files and pipeline definitions in these target organizations
- Access repository contents and GitLab-specific configurations
- Retrieve repository metadata and activity levels for the configured organizations

All analysis outputs and deliverables must be saved to a folder called `inventory-analysis/gitlab` in the current workspace.

## GitLab CI/CD-Specific Discovery

### Configuration File Detection

Systematically search for and catalog GitLab CI/CD configurations:

- **.gitlab-ci.yml**: Main pipeline definition files
- **Include Files**: External YAML files included in pipelines
- **Template Files**: GitLab CI/CD templates and job templates
- **Variables**: Project and group-level CI/CD variables
- **Environments**: Deployment environment configurations
- **Pipeline Schedules**: Scheduled pipeline configurations

### GitLab CI/CD Pipeline Analysis

For each GitLab CI/CD configuration discovered:

#### Pipeline Structure Assessment

- **Stage Organization**: Build, test, deploy stages and custom stages
- **Job Definitions**: Individual job configurations and dependencies
- **Pipeline Types**: Basic, parent-child, and multi-project pipelines
- **Rules and Conditions**: Complex conditional logic and pipeline rules
- **DAG Dependencies**: Directed acyclic graph job dependencies

#### Build Environment Analysis

- **Runner Requirements**: Shared, group, and project-specific runners
- **Docker Usage**: Docker images, services, and registry configurations
- **Kubernetes Integration**: Kubernetes executor and cluster configurations
- **Cache Configuration**: Dependencies and custom caching strategies
- **Artifacts**: Build artifacts, reports, and artifact dependencies

#### GitLab CI/CD-Specific Features

- **Include Patterns**: Local, remote, template, and project includes
- **Extends Keyword**: Job inheritance and template usage
- **Services**: Database and service container configurations
- **Environment Deployments**: Environment definitions and deployment tracking
- **Release Management**: GitLab releases and deployment boards
- **Security Scanning**: SAST, DAST, dependency scanning, and license management

#### Integration Patterns

- **GitLab Features**: Issues, merge requests, and GitLab Pages integration
- **External Services**: AWS, Azure, GCP, and Kubernetes deployments
- **Container Registries**: GitLab Container Registry and external registries
- **Package Registries**: NPM, Maven, PyPI, and other package management

### Migration Complexity Assessment

For each GitLab CI/CD configuration, assess:

#### Complexity Scoring

- **Simple**: Basic build/test pipelines with standard jobs
- **Medium**: Multi-stage pipelines with moderate feature usage
- **Complex**: Advanced pipelines with includes, extends, and complex rules
- **Enterprise**: Complex pipelines with security scanning and compliance features

#### Risk Assessment

- **Complex Include Patterns**: Nested includes and template dependencies
- **GitLab-Specific Features**: Features without direct GitHub equivalents
- **Custom Runner Requirements**: Specialized runner configurations
- **Security Scanning Dependencies**: GitLab security features migration

## Repository Analysis Requirements

For each repository with GitLab CI/CD configurations:

### GitLab CI/CD Configuration Inventory

- Document all .gitlab-ci.yml files and include dependencies
- Catalog template usage and job inheritance patterns
- Identify variable dependencies and environment configurations
- Map pipeline triggers and merge request integration

### Business Impact Assessment

- **Repository Activity**: Commit frequency and team usage
- **Team Ownership**: Development teams and pipeline maintenance responsibilities
- **Security Requirements**: Security scanning and compliance needs

## Output Requirements

### GitLab CI/CD Pipeline Inventory CSV

Generate a detailed CSV file (`inventory-analysis/gitlab/gitlab-pipeline-inventory.csv`) with columns:

- **Organization Name**
- **Repository Name**
- **Repository URL**
- **Config File Path**
- **Stage Definitions**
- **Job Count**
- **Runner Requirements**
- **Include Dependencies**
- **Template Usage**
- **Service Dependencies**
- **Environment Definitions**
- **Security Scanning Features**
- **Complexity Score** (Simple/Medium/Complex/Enterprise)
- **Dependencies**
- **Special Requirements**
- **Last Activity Date**
- **Team/Owner Information**
- **Notes/Comments**

### GitLab CI/CD Migration Assessment Report

Create a comprehensive report (`inventory-analysis/gitlab/gitlab-migration-assessment.md`) including:

- **Executive Summary**: GitLab CI/CD-specific findings and recommendations
- **Pipeline Statistics**: Total count, complexity distribution, feature usage
- **Migration Strategy**: GitLab CI/CD-to-GitHub Actions migration approach
- **Feature Mapping**: GitLab CI/CD features to GitHub Actions equivalents
- **Security Migration**: Security scanning feature migration strategy
- **Risk Assessment**: GitLab CI/CD-specific migration risks and mitigation
- **Timeline Recommendations**: Phased migration timeline for GitLab pipelines
- **Technical Requirements**: GitHub Actions setup for GitLab migration

### GitLab CI/CD-to-GitHub Actions Mapping Guide

Create a technical guide (`inventory-analysis/gitlab/gitlab-github-actions-mapping.md`) including:

- **YAML Conversion**: GitLab CI YAML to GitHub Actions workflow translation
- **Job Migration**: GitLab jobs to GitHub Actions jobs and steps
- **Runner Migration**: GitLab runners to GitHub Actions runners
- **Variable Management**: GitLab CI variables to GitHub Actions variables and secrets
- **Environment Migration**: GitLab environments to GitHub Actions environments
- **Security Features**: GitLab security scanning to GitHub Actions security features

### GitLab CI/CD Reusable Workflow Templates

Create workflow templates (`inventory-analysis/gitlab/workflow-templates/`) for common GitLab patterns:

- **Auto DevOps**: GitLab Auto DevOps equivalent workflows
- **Docker Build Pipeline**: Container build and registry workflows
- **Kubernetes Deployment**: GitLab Auto Deploy equivalent workflows
- **Security Scanning**: SAST, DAST, and dependency scanning workflows
- **Pages Deployment**: GitLab Pages equivalent GitHub Pages workflows

## Specific GitLab CI/CD Analysis Focus Areas

### Include and Template System Assessment

- **Include Patterns**: Local, remote, template, and project includes
- **Template Libraries**: Shared templates across the organization
- **Job Inheritance**: Extends keyword usage and inheritance patterns
- **Parameterization**: Template parameters and variable substitution

### Runner and Infrastructure Analysis

- **Runner Types**: Shared, group, project, and specific runners
- **Runner Tags**: Tag-based job assignment and requirements
- **Executor Types**: Docker, Kubernetes, shell, and custom executors
- **Scaling Requirements**: Auto-scaling and capacity planning needs

### Environment and Deployment Management

- **Environment Definitions**: Deployment environments and their configurations
- **Deployment Strategies**: Manual, automatic, and timed deployments
- **Environment Variables**: Environment-specific variables and secrets
- **Deployment Tracking**: Deployment boards and environment monitoring

### Security and Compliance Features

- **Security Scanning**: SAST, DAST, secret detection, and license scanning
- **Compliance Features**: Compliance pipelines and audit requirements
- **Vulnerability Management**: Security dashboard and vulnerability tracking
- **Access Controls**: Project and group-level permissions

### Variable and Secret Management

- **Variable Hierarchy**: Instance, group, and project variable inheritance
- **Protected Variables**: Environment and branch protection rules
- **Masked Variables**: Secret masking and secure variable handling
- **File Variables**: File-based variable and configuration management

### Artifact and Cache Management

- **Artifact Types**: Job artifacts, reports, and pipeline artifacts
- **Cache Strategies**: Global, job-level, and key-based caching
- **Artifact Dependencies**: Cross-job artifact sharing and dependencies
- **Storage Requirements**: Artifact storage and retention policies

### Integration and Platform Features

- **GitLab Platform Integration**: Issues, merge requests, and GitLab features
- **Container Registry**: GitLab Container Registry usage and patterns
- **Package Registry**: NPM, Maven, PyPI, and other package management
- **Monitoring Integration**: Prometheus, Grafana, and custom monitoring

This focused GitLab CI/CD analysis will provide the detailed foundation needed for successful migration of GitLab pipelines to GitHub Actions while maintaining security features and improving CI/CD capabilities.
