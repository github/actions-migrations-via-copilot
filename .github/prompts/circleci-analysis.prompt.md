# Circle**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `.github/settings/config.yaml` file under the `organizations` key. You must read this configuration file to determine which specific organizations to analyze.

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- First, read the `.github/settings/config.yaml` file to retrieve the list of organizations from the `organizations` key
- Enumerate repositories within only the organizations specified in the configuration
- Search for CircleCI configuration files and workflow definitions in these target organizations
- Access repository contents and CircleCI-specific configurations
- Retrieve repository metadata and activity levels for the configured organizations and Migration Assessment

You are tasked with conducting a comprehensive analysis of CircleCI pipelines across the GitHub organizations specified in the project configuration to prepare for migration to GitHub Actions.

## Context

This analysis focuses specifically on CircleCI configurations and their migration requirements. You will identify all CircleCI configurations, assess their complexity, and provide detailed migration guidance for transitioning to GitHub Actions.

**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `config.yaml` file under the `organizations` section:

- `antgrutta-actions`

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- Enumerate repositories within the specified organizations (`antgrutta-actions`)
- Search for CircleCI configuration files and workflow definitions in these organizations
- Access repository contents and CircleCI-specific configurations
- Retrieve repository metadata and activity levels for the target organizations

All analysis outputs and deliverables must be saved to a folder called `inventory-analysis/circleci` in the current workspace.

## CircleCI-Specific Discovery

### Configuration File Detection

Systematically search for and catalog CircleCI configurations:

- **.circleci/config.yml**: Main configuration files
- **.circleci/**: Configuration directories and additional files
- **Orb Configurations**: Orb usage and custom orb definitions
- **Workflow Definitions**: Workflow orchestration and job dependencies
- **Context References**: Shared environment variables and secrets
- **Pipeline Parameters**: Dynamic pipeline configurations

### CircleCI Pipeline Analysis

For each CircleCI configuration discovered:

#### Workflow Structure Assessment

- **Workflow Organization**: Job dependencies and workflow orchestration
- **Job Definitions**: Individual job configurations and requirements
- **Executor Types**: Docker, machine, macOS, Windows, and orb executors
- **Conditional Logic**: Workflow filters and conditional job execution
- **Matrix Builds**: Parameter variations and parallel job execution

#### Build Environment Analysis

- **Executor Requirements**: Docker images, machine types, and resource classes
- **Docker Usage**: Custom images, Docker layer caching, and registry usage
- **Resource Classes**: CPU and memory resource requirements
- **Caching Strategies**: Dependencies, workspace, and Docker layer caching
- **Environment Variables**: Job and workflow environment configurations

#### CircleCI-Specific Features

- **Orb Usage**: Community and custom orbs with version dependencies
- **Context Management**: Shared contexts and organization-level secrets
- **Artifacts**: Build artifacts, test results, and workspace persistence
- **Test Splitting**: Automatic test splitting and parallelism
- **Approval Jobs**: Manual approval workflows and hold jobs
- **SSH Debugging**: SSH access and debugging configurations

#### Integration Patterns

- **VCS Integration**: GitHub and Bitbucket integration patterns
- **Deployment Targets**: AWS, Azure, GCP, Heroku, and custom deployments
- **Notification Systems**: Slack, email, and webhook notifications
- **Monitoring Integration**: Performance monitoring and alerting

### Migration Complexity Assessment

For each CircleCI configuration, assess:

#### Complexity Scoring

- **Simple**: Basic build/test workflows with standard orbs
- **Medium**: Multi-job workflows with moderate orb usage
- **Complex**: Advanced workflows with custom orbs and complex dependencies
- **Enterprise**: Complex workflows with approval gates and advanced orchestration

#### Risk Assessment

- **Custom Orb Dependencies**: Custom or deprecated orbs without alternatives
- **Resource Class Requirements**: Specific compute resource needs
- **Test Splitting Complexity**: Advanced parallelism and test distribution
- **Context Dependencies**: Complex shared secret and variable management

## Repository Analysis Requirements

For each repository with CircleCI configurations:

### CircleCI Configuration Inventory

- Document all .circleci/config.yml files and workflow definitions
- Catalog orb dependencies and version requirements
- Identify context usage and shared environment variables
- Map workflow triggers and branch filtering rules

### Business Impact Assessment

- **Repository Activity**: Commit frequency and team usage
- **Team Ownership**: Development teams and workflow maintenance responsibilities
- **Deployment Patterns**: Environment promotion and release processes

## Output Requirements

### CircleCI Pipeline Inventory CSV

Generate a detailed CSV file (`inventory-analysis/circleci/circleci-pipeline-inventory.csv`) with columns:

- **Organization Name**
- **Repository Name**
- **Repository URL**
- **Config File Path**
- **Workflow Names**
- **Job Count**
- **Executor Types**
- **Orb Dependencies**
- **Context Dependencies**
- **Resource Class Requirements**
- **Caching Strategies**
- **Test Splitting Usage**
- **Complexity Score** (Simple/Medium/Complex/Enterprise)
- **Dependencies**
- **Special Requirements**
- **Last Activity Date**
- **Team/Owner Information**
- **Notes/Comments**

### CircleCI Migration Assessment Report

Create a comprehensive report (`inventory-analysis/circleci/circleci-migration-assessment.md`) including:

- **Executive Summary**: CircleCI-specific findings and recommendations
- **Workflow Statistics**: Total count, complexity distribution, orb usage
- **Migration Strategy**: CircleCI-to-GitHub Actions migration approach
- **Orb Mapping**: CircleCI orbs to GitHub Actions marketplace actions
- **Executor Migration**: CircleCI executors to GitHub Actions runners
- **Risk Assessment**: CircleCI-specific migration risks and mitigation
- **Timeline Recommendations**: Phased migration timeline for CircleCI workflows
- **Technical Requirements**: GitHub Actions setup for CircleCI migration

### CircleCI-to-GitHub Actions Mapping Guide

Create a technical guide (`inventory-analysis/circleci/circleci-github-actions-mapping.md`) including:

- **Configuration Conversion**: CircleCI config.yml to GitHub Actions workflow translation
- **Orb Alternatives**: Mapping of CircleCI orbs to GitHub Actions
- **Executor Migration**: CircleCI executors to GitHub Actions runners
- **Context Management**: CircleCI contexts to GitHub Actions secrets and variables
- **Workflow Orchestration**: CircleCI workflows to GitHub Actions job dependencies
- **Caching Strategies**: CircleCI caching to GitHub Actions caching

### CircleCI Reusable Workflow Templates

Create workflow templates (`inventory-analysis/circleci/workflow-templates/`) for common CircleCI patterns:

- **Node.js Application**: NPM/Yarn build and test workflows
- **Docker Build Pipeline**: Container build and registry push workflows
- **Mobile App Deployment**: iOS and Android build workflows
- **Multi-Platform Testing**: Cross-platform testing workflows
- **Deployment Pipeline**: Multi-environment deployment with approvals

## Specific CircleCI Analysis Focus Areas

### Orb Ecosystem Assessment

- **Orb Inventory**: All orbs in use across the organization
- **Orb Versions**: Version dependencies and compatibility
- **Custom Orbs**: Organization-specific orb definitions
- **GitHub Actions Alternatives**: Available actions for CircleCI orbs

### Executor and Resource Analysis

- **Executor Types**: Docker, machine, macOS, Windows usage patterns
- **Resource Classes**: CPU and memory resource requirements
- **Docker Images**: Custom and standard images in use
- **Performance Requirements**: Build time and resource optimization needs

### Workflow Orchestration Assessment

- **Job Dependencies**: Complex workflow dependencies and fan-in/fan-out patterns
- **Conditional Logic**: Branch filtering and conditional job execution
- **Approval Workflows**: Manual approval jobs and hold patterns
- **Parallel Execution**: Parallelism strategies and test splitting

### Context and Secret Management

- **Context Usage**: Organization and project contexts
- **Environment Variables**: Shared and job-specific variables
- **Secret Management**: Sensitive data handling and rotation
- **Access Controls**: Context permissions and team access

### Caching and Performance Optimization

- **Dependency Caching**: Package manager and custom caching strategies
- **Workspace Persistence**: Data sharing between jobs
- **Docker Layer Caching**: Container build optimization
- **Test Splitting**: Automatic test parallelization and timing data

### Integration and Deployment Patterns

- **Cloud Deployments**: AWS, Azure, GCP deployment integrations
- **Container Registries**: Docker Hub, ECR, ACR, GCR usage
- **Monitoring Integrations**: Application and infrastructure monitoring
- **Notification Patterns**: Slack, email, and webhook notification strategies

This focused CircleCI analysis will provide the detailed foundation needed for successful migration of CircleCI workflows to GitHub Actions while maintaining performance optimization and improving CI/CD capabilities.
