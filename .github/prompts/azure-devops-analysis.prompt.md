# Azure DevOps CI/CD Analysis and Migration Assessment

You are tasked with conducting a comprehensive analysis of Azure DevOps CI/CD pipelines across the GitHub organizations specified in the project configuration to prepare for migration to GitHub Actions.

## Context

This analysis focuses specifically on Azure DevOps pipelines and their migration requirements. You will identify all Azure DevOps configurations, assess their complexity, and provide detailed migration guidance for transitioning to GitHub Actions.

**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `.github/settings/config.yaml` file under the `organizations` key. You must read this configuration file to determine which specific organizations to analyze.

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- First, read the `.github/settings/config.yaml` file to retrieve the list of organizations from the `organizations` key
- Enumerate repositories within only the organizations specified in the configuration
- Search for Azure DevOps configuration files and pipeline definitions in these target organizations
- Access repository contents and Azure DevOps-specific configurations
- Retrieve repository metadata and activity levels for the configured organizations

All analysis outputs and deliverables must be saved to a folder called `inventory-analysis/azure-devops` in the current workspace.

## Azure DevOps-Specific Discovery

### Configuration File Detection

Systematically search for and catalog Azure DevOps configurations:

- **azure-pipelines.yml**: Main pipeline definition files
- **azure-pipelines/**: Pipeline configuration directories
- **Template Files**: YAML pipeline templates and includes
- **Variable Groups**: Variable group references and configurations
- **Service Connections**: External service integration configurations
- **Build Triggers**: CI/CD trigger configurations

### Azure DevOps Pipeline Analysis

For each Azure DevOps pipeline discovered:

#### Pipeline Structure Assessment

- **Pipeline Type**: Build, deployment, or multi-stage pipelines
- **Stage Organization**: Build, test, deploy stages and dependencies
- **Job Structure**: Agent jobs, deployment jobs, and job dependencies
- **Template Usage**: Pipeline templates and template parameters
- **Conditional Logic**: Condition expressions and runtime parameters

#### Build Environment Analysis

- **Agent Pools**: Microsoft-hosted vs. self-hosted agents
- **Agent Specifications**: VM images, capabilities, and demands
- **Container Usage**: Container jobs and sidecar containers
- **Tool Installations**: Tool installers and cached tool usage
- **Environment Variables**: Pipeline and job-level variables

#### Azure DevOps-Specific Features

- **Variable Groups**: Shared variables and secret variables
- **Service Connections**: Azure, Docker, Kubernetes, and custom connections
- **Artifacts**: Build artifacts, pipeline artifacts, and feeds
- **Deployment Groups**: Target deployment environments
- **Approval Gates**: Pre-deployment and post-deployment approvals
- **Release Management**: Classic release pipelines and environments

#### Integration Patterns

- **Azure Services**: Azure Resource Manager, Azure Key Vault, Azure Container Registry
- **External Services**: SonarCloud, WhiteSource, and third-party integrations
- **Notification Systems**: Email, Teams, Slack notifications
- **Artifact Repositories**: Azure Artifacts, NuGet, npm, Maven feeds

### Migration Complexity Assessment

For each Azure DevOps pipeline, assess:

#### Complexity Scoring

- **Simple**: Basic build/test pipelines with standard tasks
- **Medium**: Multi-stage pipelines with moderate Azure service integration
- **Complex**: Advanced pipelines with custom tasks and extensive Azure integration
- **Enterprise**: Complex pipelines with approval workflows and compliance requirements

#### Risk Assessment

- **Custom Tasks**: Azure DevOps extensions without GitHub Actions equivalents
- **Azure Service Dependencies**: Deep Azure integration requiring reconfiguration
- **Variable Group Complexity**: Complex variable inheritance and scoping
- **Approval Process Dependencies**: Manual approval workflows

## Repository Analysis Requirements

For each repository with Azure DevOps configurations:

### Azure DevOps Configuration Inventory

- Document all azure-pipelines.yml files and template references
- Catalog variable group dependencies and service connections
- Identify custom task extensions and marketplace task usage
- Map build triggers and repository webhooks

### Business Impact Assessment

- **Repository Activity**: Commit frequency and team usage
- **Team Ownership**: Development teams and pipeline maintenance responsibilities
- **Environment Integration**: Production and staging environment connections

## Output Requirements

### Azure DevOps Pipeline Inventory CSV

Generate a detailed CSV file (`inventory-analysis/azure-devops/azure-devops-pipeline-inventory.csv`) with columns:

- **Organization Name**
- **Repository Name**
- **Repository URL**
- **Pipeline File Path**
- **Pipeline Name**
- **Pipeline Type** (Build/Deploy/Multi-stage)
- **Stage Count**
- **Agent Pool Requirements**
- **Variable Group Dependencies**
- **Service Connection Dependencies**
- **Custom Task Extensions**
- **Template Dependencies**
- **Complexity Score** (Simple/Medium/Complex/Enterprise)
- **Azure Service Dependencies**
- **Special Requirements**
- **Last Activity Date**
- **Team/Owner Information**
- **Notes/Comments**

### Azure DevOps Migration Assessment Report

Create a comprehensive report (`inventory-analysis/azure-devops/azure-devops-migration-assessment.md`) including:

- **Executive Summary**: Azure DevOps-specific findings and recommendations
- **Pipeline Statistics**: Total count, complexity distribution, task usage
- **Migration Strategy**: Azure DevOps-to-GitHub Actions migration approach
- **Task Mapping**: Azure DevOps tasks to GitHub Actions marketplace actions
- **Service Integration**: Strategy for Azure service connections in GitHub Actions
- **Risk Assessment**: Azure DevOps-specific migration risks and mitigation
- **Timeline Recommendations**: Phased migration timeline for Azure DevOps pipelines
- **Technical Requirements**: GitHub Actions setup for Azure DevOps migration

### Azure DevOps-to-GitHub Actions Mapping Guide

Create a technical guide (`inventory-analysis/azure-devops/azure-devops-github-actions-mapping.md`) including:

- **YAML Conversion**: Azure Pipelines YAML to GitHub Actions workflow translation
- **Task Alternatives**: Mapping of Azure DevOps tasks to GitHub Actions
- **Agent Migration**: Azure DevOps agents to GitHub Actions runners
- **Variable Management**: Variable groups to GitHub Actions variables and secrets
- **Service Connections**: Azure service connections to GitHub Actions secrets and OIDC
- **Artifact Handling**: Azure Artifacts to GitHub Actions artifacts and packages

### Azure DevOps Reusable Workflow Templates

Create workflow templates (`inventory-analysis/azure-devops/workflow-templates/`) for common Azure DevOps patterns:

- **Azure App Service Deployment**: Web app deployment workflows
- **Azure Kubernetes Service**: Container deployment to AKS
- **Azure Function Apps**: Serverless function deployment
- **Azure Resource Manager**: Infrastructure deployment workflows
- **Multi-Environment Pipeline**: Development to production with approvals

## Specific Azure DevOps Analysis Focus Areas

### Task and Extension Assessment

- **Built-in Tasks**: Standard Azure DevOps tasks in use
- **Marketplace Extensions**: Third-party and custom extensions
- **Custom Tasks**: Organization-specific task extensions
- **GitHub Actions Alternatives**: Available actions for Azure DevOps tasks

### Azure Service Integration Analysis

- **Service Connections**: All configured service connections
- **Azure Subscriptions**: Connected Azure subscriptions and permissions
- **Resource Access**: Azure resources accessed by pipelines
- **Authentication Methods**: Service principals, managed identities, and certificates

### Variable and Secret Management

- **Variable Groups**: Shared variable groups and their scope
- **Pipeline Variables**: Pipeline-specific variables and runtime parameters
- **Secret Variables**: Encrypted variables and secret management
- **Library Security**: Variable group permissions and access controls

### Approval and Release Process Analysis

- **Approval Gates**: Pre-deployment and post-deployment approvals
- **Environment Definitions**: Target environments and deployment groups
- **Release Strategies**: Blue-green, canary, and rolling deployment patterns
- **Compliance Requirements**: Change management and audit requirements

### Template and Reusability Assessment

- **Template Library**: Shared pipeline templates across the organization
- **Template Parameters**: Parameterization and customization patterns
- **Include Patterns**: Template inclusion and inheritance strategies
- **Standardization Opportunities**: Common patterns for GitHub Actions templates

This focused Azure DevOps analysis will provide the detailed foundation needed for successful migration of Azure DevOps pipelines to GitHub Actions while maintaining Azure service integration and improving CI/CD capabilities.
