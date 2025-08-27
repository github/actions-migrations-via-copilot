# Drone **Organizations to Analyze**: This analysis should be limited to the organizations listed in the `.github/settings/config.yaml` file under the `organizations` key. You must read this configuration file to determine which specific organizations to analyze.

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- First, read the `.github/settings/config.yaml` file to retrieve the list of organizations from the `organizations` key
- Enumerate repositories within only the organizations specified in the configuration
- Search for Drone CI configuration files and pipeline definitions in these target organizations
- Access repository contents and Drone CI-specific configurations
- Retrieve repository metadata and activity levels for the configured organizations and Migration Assessment

You are tasked with conducting a comprehensive analysis of Drone CI pipelines across the GitHub organizations specified in the project configuration to prepare for migration to GitHub Actions.

## Context

This analysis focuses specifically on Drone CI configurations and their migration requirements. You will identify all Drone CI configurations, assess their complexity, and provide detailed migration guidance for transitioning to GitHub Actions.

**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `config.yaml` file under the `organizations` section:

- `antgrutta-actions`

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- Enumerate repositories within the specified organizations (`antgrutta-actions`)
- Search for Drone CI configuration files and pipeline definitions in these organizations
- Access repository contents and Drone CI-specific configurations
- Retrieve repository metadata and activity levels for the target organizations

All analysis outputs and deliverables must be saved to a folder called `inventory-analysis/drone` in the current workspace.

## Drone CI-Specific Discovery

### Configuration File Detection

Systematically search for and catalog Drone CI configurations:

- **.drone.yml**: Main pipeline configuration files
- **.drone.star**: Starlark-based pipeline configurations
- **Pipeline Templates**: Reusable pipeline templates and includes
- **Secret Configurations**: Secret and environment variable configurations
- **Plugin Configurations**: Custom and community plugin usage
- **Trigger Configurations**: Event-based and conditional triggers

### Drone CI Pipeline Analysis

For each Drone CI configuration discovered:

#### Pipeline Structure Assessment

- **Pipeline Types**: Docker, Kubernetes, SSH, and Exec pipelines
- **Step Definitions**: Build, test, deploy, and custom step configurations
- **Service Dependencies**: Database and service container configurations
- **Conditional Logic**: Branch, event, and condition-based execution
- **Matrix Builds**: Parallel execution and matrix strategies

#### Build Environment Analysis

- **Container Images**: Docker images and container configurations
- **Kubernetes Integration**: Kubernetes pipeline and pod configurations
- **SSH Pipelines**: Remote execution and SSH-based deployments
- **Environment Variables**: Pipeline and step-level environment settings
- **Volume Configurations**: Data persistence and volume mounting

#### Drone CI-Specific Features

- **Plugin Ecosystem**: Community and custom plugin usage
- **Secret Management**: Drone secret and external secret integration
- **Triggers**: Webhook, cron, and custom trigger configurations
- **Promotion Events**: Pipeline promotion and environment progression
- **Signature Verification**: Pipeline signature and security configurations
- **Registry Integration**: Docker registry and image management

#### Integration Patterns

- **Source Control**: GitHub, GitLab, Bitbucket, and Gitea integration
- **Cloud Platforms**: AWS, Azure, GCP, and Kubernetes deployments
- **Container Registries**: Docker Hub, ECR, ACR, GCR, and custom registries
- **External Services**: Slack, email, and webhook notifications

### Migration Complexity Assessment

For each Drone CI configuration, assess:

#### Complexity Scoring

- **Simple**: Basic Docker pipelines with standard plugins
- **Medium**: Multi-step pipelines with service dependencies
- **Complex**: Advanced pipelines with custom plugins and Kubernetes integration
- **Enterprise**: Complex pipelines with signature verification and compliance features

#### Risk Assessment

- **Custom Plugin Dependencies**: Drone-specific plugins without GitHub equivalents
- **Kubernetes Pipeline Complexity**: Advanced Kubernetes integration patterns
- **SSH Pipeline Dependencies**: Remote execution and deployment dependencies
- **Security Configuration**: Signature verification and compliance requirements

## Repository Analysis Requirements

For each repository with Drone CI configurations:

### Drone CI Configuration Inventory

- Document all .drone.yml and .drone.star files and pipeline definitions
- Catalog plugin dependencies and custom plugin usage
- Identify secret dependencies and external integrations
- Map pipeline triggers and conditional execution patterns

### Business Impact Assessment

- **Repository Activity**: Commit frequency and team usage
- **Team Ownership**: Development teams and pipeline maintenance responsibilities
- **Infrastructure Dependencies**: Kubernetes clusters and deployment targets

## Output Requirements

### Drone CI Pipeline Inventory CSV

Generate a detailed CSV file (`inventory-analysis/drone/drone-pipeline-inventory.csv`) with columns:

- **Organization Name**
- **Repository Name**
- **Repository URL**
- **Config File Path**
- **Pipeline Type** (docker/kubernetes/ssh/exec)
- **Step Count**
- **Container Images Used**
- **Service Dependencies**
- **Plugin Dependencies**
- **Secret Dependencies**
- **Trigger Configurations**
- **Matrix Configurations**
- **Complexity Score** (Simple/Medium/Complex/Enterprise)
- **Dependencies**
- **Special Requirements**
- **Last Activity Date**
- **Team/Owner Information**
- **Notes/Comments**

### Drone CI Migration Assessment Report

Create a comprehensive report (`inventory-analysis/drone/drone-migration-assessment.md`) including:

- **Executive Summary**: Drone CI-specific findings and recommendations
- **Pipeline Statistics**: Total count, complexity distribution, plugin usage
- **Migration Strategy**: Drone CI-to-GitHub Actions migration approach
- **Plugin Migration**: Drone plugins to GitHub Actions marketplace actions
- **Infrastructure Migration**: Drone servers to GitHub Actions infrastructure
- **Risk Assessment**: Drone CI-specific migration risks and mitigation
- **Timeline Recommendations**: Phased migration timeline for Drone pipelines
- **Technical Requirements**: GitHub Actions setup for Drone migration

### Drone CI-to-GitHub Actions Mapping Guide

Create a technical guide (`inventory-analysis/drone/drone-github-actions-mapping.md`) including:

- **Configuration Conversion**: Drone YAML to GitHub Actions workflow translation
- **Plugin Migration**: Drone plugins to GitHub Actions steps and actions
- **Pipeline Type Migration**: Docker, Kubernetes, SSH pipelines to GitHub Actions
- **Secret Management**: Drone secrets to GitHub Actions secrets and variables
- **Service Migration**: Drone services to GitHub Actions service containers
- **Trigger Migration**: Drone triggers to GitHub Actions event triggers

### Drone CI Reusable Workflow Templates

Create workflow templates (`inventory-analysis/drone/workflow-templates/`) for common Drone patterns:

- **Docker Build Pipeline**: Container build and registry push workflows
- **Kubernetes Deployment**: Kubernetes deployment and service workflows
- **Multi-Cloud Deployment**: AWS, Azure, GCP deployment workflows
- **Microservices Pipeline**: Multi-service build and deployment workflows
- **Promotion Pipeline**: Environment promotion and release workflows

## Specific Drone CI Analysis Focus Areas

### Plugin Ecosystem Assessment

- **Plugin Inventory**: All plugins in use across repositories
- **Community Plugins**: Standard community plugin usage patterns
- **Custom Plugins**: Organization-specific custom plugin implementations
- **Plugin Alternatives**: GitHub Actions marketplace alternatives

### Pipeline Type Analysis

- **Docker Pipelines**: Container-based pipeline configurations
- **Kubernetes Pipelines**: Kubernetes-native pipeline execution
- **SSH Pipelines**: Remote execution and deployment patterns
- **Exec Pipelines**: Local execution and bare-metal deployments

### Container and Infrastructure Analysis

- **Container Images**: Docker images and registry dependencies
- **Kubernetes Integration**: Cluster configurations and pod specifications
- **Resource Requirements**: CPU, memory, and storage needs
- **Network Configuration**: Service communication and external access

### Secret and Security Management

- **Secret Types**: Repository and organization secrets
- **External Secret Integration**: HashiCorp Vault and other secret backends
- **Signature Verification**: Pipeline signature and trust configurations
- **Access Controls**: Repository and pipeline permission management

### Trigger and Event Management

- **Trigger Types**: Push, pull request, tag, and cron triggers
- **Conditional Execution**: Branch, path, and event-based conditions
- **Promotion Events**: Manual promotion and environment progression
- **Webhook Integration**: External webhook and event handling

### Service and Dependency Management

- **Service Containers**: Database, cache, and application services
- **Volume Management**: Data persistence and shared storage
- **Network Configuration**: Service discovery and communication
- **External Dependencies**: Third-party services and API integrations

### Performance and Optimization

- **Pipeline Performance**: Execution time and resource optimization
- **Parallel Execution**: Matrix builds and concurrent step execution
- **Caching Strategies**: Docker layer caching and dependency caching
- **Resource Utilization**: CPU, memory, and storage optimization

### Integration and Deployment Patterns

- **Cloud Platform Integration**: Multi-cloud deployment strategies
- **Container Registry Integration**: Registry authentication and image management
- **Monitoring Integration**: Pipeline monitoring and alerting
- **Notification Patterns**: Slack, email, and webhook notification strategies

### Migration-Specific Considerations

- **Infrastructure Migration**: Drone server to GitHub Actions transition
- **Runner Migration**: Drone agents to GitHub Actions runners
- **Plugin Development**: Custom plugin conversion to GitHub Actions
- **Security Migration**: Signature verification to GitHub Actions security features

This focused Drone CI analysis will provide the detailed foundation needed for successful migration of Drone CI pipelines to GitHub Actions while maintaining container-native capabilities and improving CI/CD performance.
