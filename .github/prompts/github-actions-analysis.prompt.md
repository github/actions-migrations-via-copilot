# GitHub Actions Analysis and Optimization Assessment

You are tasked with conducting a comprehensive analysis of existing GitHub Actions workflows across the GitHub organizations specified in the project configuration to identify optimization opportunities and standardization potential.

## Context

This analysis focuses specifically on existing GitHub Actions configurations and their optimization requirements. You will identify all GitHub Actions workflows, assess their efficiency, and provide recommendations for standardization, optimization, and best practices implementation.

**Organizations to Analyze**: This analysis should be limited to the organizations listed in the `.github/settings/config.yaml` file under the `organizations` key. You must read this configuration file to determine which specific organizations to analyze.

## Tool Requirements

**Important**: Use the available GitHub MCP server tools to gather repository and organizational information for the specified organizations only. Leverage these tools to:

- First, read the `.github/settings/config.yaml` file to retrieve the list of organizations from the `organizations` key
- Enumerate repositories within only the organizations specified in the configuration
- Search for GitHub Actions workflow files and configurations in these target organizations
- Access repository contents and workflow-specific configurations
- Retrieve repository metadata and activity levels for the configured organizations

All analysis outputs and deliverables must be saved to a folder called `inventory-analysis/github-actions` in the current workspace.

## GitHub Actions-Specific Discovery

### Configuration File Detection

Systematically search for and catalog GitHub Actions configurations:

- **.github/workflows/**: Workflow definition files
- **.github/actions/**: Custom action definitions
- **Reusable Workflows**: Organization-level reusable workflows
- **Composite Actions**: Local composite action definitions
- **Workflow Templates**: Organization workflow templates
- **Action Metadata**: action.yml and action.yaml files

### GitHub Actions Workflow Analysis

For each GitHub Actions workflow discovered:

#### Workflow Structure Assessment

- **Trigger Configurations**: Event triggers, schedules, and manual dispatches
- **Job Definitions**: Job dependencies, matrices, and parallel execution
- **Step Configurations**: Action usage, shell commands, and custom steps
- **Environment Usage**: Environment definitions and protection rules
- **Conditional Logic**: If conditions and dynamic workflow execution

#### Action and Dependency Analysis

- **Marketplace Actions**: Third-party action usage and version pinning
- **Custom Actions**: Organization-specific and repository-specific actions
- **Shell Commands**: Direct shell command usage and script execution
- **Docker Actions**: Container-based actions and image dependencies
- **JavaScript Actions**: Node.js-based actions and npm dependencies

#### GitHub Actions-Specific Features

- **Secrets Management**: Repository and organization secrets usage
- **Variables**: Repository and organization variables configuration
- **Environments**: Environment protection rules and approvals
- **Artifacts**: Build artifacts and workflow artifact sharing
- **Caching**: Dependency caching and custom cache strategies
- **Matrix Strategies**: Parallel execution and build matrices

#### Integration Patterns

- **GitHub Features**: Issues, pull requests, releases, and Pages integration
- **External Services**: Cloud deployments, monitoring, and notification services
- **Package Registries**: NPM, Docker, Maven, and other package publishing
- **Security Scanning**: CodeQL, dependency scanning, and security actions

### Optimization Assessment

For each GitHub Actions workflow, assess:

#### Efficiency Scoring

- **Optimized**: Well-structured workflows following best practices
- **Good**: Mostly optimized with minor improvement opportunities
- **Needs Improvement**: Several optimization opportunities identified
- **Poor**: Significant efficiency and best practice issues

#### Optimization Opportunities

- **Performance Improvements**: Caching, parallelization, and execution optimization
- **Security Enhancements**: Action pinning, secret management, and security best practices
- **Maintainability**: Reusable workflows, standardization, and documentation
- **Cost Optimization**: Runner efficiency and resource usage optimization

#### Standardization Potential

- **Reusable Workflow Candidates**: Common patterns suitable for organization-wide reuse
- **Template Opportunities**: Workflow patterns that could become templates
- **Action Consolidation**: Custom actions that could be shared or replaced
- **Best Practice Compliance**: Adherence to GitHub Actions best practices

## Repository Analysis Requirements

For each repository with GitHub Actions workflows:

### GitHub Actions Configuration Inventory

- Document all workflow files and their purposes
- Catalog custom actions and their usage patterns
- Identify marketplace action dependencies and versions
- Map workflow triggers and execution patterns

### Optimization Impact Assessment

- **Workflow Performance**: Execution time and resource usage analysis
- **Security Posture**: Security best practices and vulnerability assessment
- **Maintainability**: Code reuse and standardization opportunities
- **Cost Efficiency**: Runner usage and optimization potential

## Output Requirements

### GitHub Actions Workflow Inventory CSV

Generate a detailed CSV file (`inventory-analysis/github-actions/github-actions-inventory.csv`) with columns:

- **Organization Name**
- **Repository Name**
- **Repository URL**
- **Workflow File Path**
- **Workflow Name**
- **Trigger Types**
- **Job Count**
- **Marketplace Actions Used**
- **Custom Actions Used**
- **Security Score** (Optimized/Good/Needs Improvement/Poor)
- **Performance Score** (Optimized/Good/Needs Improvement/Poor)
- **Reusability Potential** (High/Medium/Low/None)
- **Cost Impact** (High/Medium/Low)
- **Last Activity Date**
- **Execution Frequency**
- **Team/Owner Information**
- **Optimization Recommendations**
- **Notes/Comments**

### GitHub Actions Optimization Assessment Report

Create a comprehensive report (`inventory-analysis/github-actions/github-actions-optimization-assessment.md`) including:

- **Executive Summary**: GitHub Actions optimization findings and recommendations
- **Workflow Statistics**: Total count, efficiency distribution, action usage
- **Optimization Strategy**: Enterprise-wide GitHub Actions optimization approach
- **Standardization Opportunities**: Reusable workflows and template recommendations
- **Security Assessment**: Security best practices and vulnerability analysis
- **Performance Analysis**: Execution efficiency and cost optimization opportunities
- **Best Practices Compliance**: Gap analysis and improvement recommendations
- **Implementation Timeline**: Phased optimization and standardization plan

### GitHub Actions Best Practices Guide

Create a technical guide (`inventory-analysis/github-actions/github-actions-best-practices.md`) including:

- **Workflow Design**: Best practices for workflow structure and organization
- **Security Guidelines**: Action pinning, secret management, and security scanning
- **Performance Optimization**: Caching, parallelization, and runner efficiency
- **Reusability Patterns**: Reusable workflows and composite actions design
- **Monitoring and Debugging**: Workflow monitoring and troubleshooting strategies
- **Cost Optimization**: Runner selection and resource usage optimization

### Enterprise Reusable Workflow Library

Create reusable workflow specifications (`inventory-analysis/github-actions/reusable-workflows/`) for common patterns:

- **CI/CD Templates**: Standard build, test, and deployment workflows
- **Security Workflows**: Code scanning, dependency checking, and compliance workflows
- **Release Management**: Automated release and changelog generation workflows
- **Infrastructure Workflows**: Terraform, CloudFormation, and infrastructure deployment
- **Compliance Workflows**: Audit, approval, and governance workflows

## Specific GitHub Actions Analysis Focus Areas

### Action Usage and Dependency Analysis

- **Marketplace Action Inventory**: All marketplace actions in use across the organization
- **Version Management**: Action version pinning and update strategies
- **Custom Action Assessment**: Organization-specific action quality and reusability
- **Dependency Security**: Action security and vulnerability assessment

### Workflow Performance Analysis

- **Execution Times**: Workflow execution duration analysis and optimization opportunities
- **Resource Usage**: Runner resource utilization and efficiency assessment
- **Parallelization**: Job and step parallelization optimization
- **Caching Effectiveness**: Cache hit rates and optimization strategies

### Security and Compliance Assessment

- **Action Security**: Marketplace action security and trust assessment
- **Secret Management**: Secret usage patterns and security best practices
- **Permission Analysis**: Workflow permissions and least privilege assessment
- **Compliance Requirements**: Regulatory and organizational compliance adherence

### Reusability and Standardization

- **Common Patterns**: Workflow patterns suitable for standardization
- **Template Opportunities**: Organization workflow template development
- **Composite Actions**: Reusable action development opportunities
- **Knowledge Sharing**: Documentation and training requirements

### Cost and Resource Optimization

- **Runner Usage**: GitHub-hosted vs. self-hosted runner analysis
- **Execution Efficiency**: Workflow optimization for cost reduction
- **Resource Allocation**: CPU, memory, and storage optimization
- **Billing Analysis**: Usage patterns and cost optimization recommendations

### Integration and Ecosystem Analysis

- **GitHub Feature Usage**: Issues, PRs, releases, and Pages integration patterns
- **External Integrations**: Cloud services, monitoring, and third-party tool integration
- **Package Management**: NPM, Docker, Maven, and other package publishing patterns
- **Notification Systems**: Slack, email, and webhook notification optimization

### Monitoring and Observability

- **Workflow Monitoring**: Success rates, failure patterns, and alerting
- **Performance Metrics**: Execution time trends and performance degradation
- **Error Analysis**: Common failure patterns and resolution strategies
- **Usage Analytics**: Workflow usage patterns and adoption metrics

### Enterprise Governance

- **Workflow Standards**: Organization-wide workflow standards and guidelines
- **Approval Processes**: Environment protection and approval workflow analysis
- **Access Controls**: Repository and workflow permission management
- **Audit Requirements**: Compliance tracking and audit trail management

This focused GitHub Actions analysis will provide the detailed foundation needed for optimizing existing GitHub Actions workflows, implementing enterprise-wide best practices, and maximizing the value of GitHub Actions investments across the organization.
