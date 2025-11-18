# Migrating Secrets and Variables from Azure DevOps to GitHub Actions

When migrating CI/CD pipelines from Azure DevOps to GitHub Actions, properly handling secrets and variables is critical for security and functionality. This guide outlines the best practices and steps to effectively migrate secrets and variables.

## Understanding Azure DevOps Secret and Variable Types

Azure DevOps uses several mechanisms for managing configuration:

1. **Pipeline Variables** - Defined in the pipeline YAML or UI
2. **Variable Groups** - Shared across multiple pipelines
3. **Secret Variables** - Marked as secret in the UI or variable groups
4. **Secure Files** - Files stored securely in Azure DevOps
5. **Service Connections** - Credentials for external services

## GitHub Actions Secret and Variable Storage

GitHub Actions provides:

1. **Repository Secrets** - Available to workflows in a single repository
2. **Organization Secrets** - Shared across repositories in an organization
3. **Environment Secrets** - Scoped to specific deployment environments
4. **Repository Variables** - Non-sensitive configuration values
5. **Organization Variables** - Shared non-sensitive configuration
6. **Environment Variables** - Scoped to specific deployment environments

## Migration Strategy: When to Use Secrets vs. Variables

### Use GitHub Secrets For:
- Database passwords and connection strings
- API keys and tokens
- Service account credentials
- Encryption keys
- OAuth tokens
- SSH keys
- Any sensitive data that should be encrypted

### Use GitHub Variables For:
- API endpoints (non-authenticated)
- Build configurations (Debug/Release)
- Feature flags
- Environment names
- Application version numbers
- Non-sensitive application settings
- Public configuration values

## Pipeline Variables to GitHub Actions

### Simple Pipeline Variables

**Azure DevOps:**
```yaml
variables:
  buildConfiguration: 'Release'
  vmImageName: 'ubuntu-latest'

steps:
- script: |
    echo "Build configuration: $(buildConfiguration)"
    echo "VM Image: $(vmImageName)"
```

**GitHub Actions:**
```yaml
env:
  BUILD_CONFIGURATION: 'Release'
  VM_IMAGE_NAME: 'ubuntu-latest'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Build configuration: $BUILD_CONFIGURATION"
          echo "VM Image: $VM_IMAGE_NAME"
```

### Secret Pipeline Variables

**Azure DevOps (marked as secret in UI):**
```yaml
variables:
- name: adminPassword
  value: 'secret-value'  # Marked as secret in Azure DevOps UI

steps:
- script: |
    echo "Password is hidden: $(adminPassword)"
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Password is hidden: ${{ secrets.ADMIN_PASSWORD }}"
```

## Variable Groups to GitHub Secrets and Variables

Azure DevOps variable groups can contain both regular variables and secret variables. These should be separated into GitHub Secrets and Variables based on sensitivity.

### Variable Group Example

**Azure DevOps:**
```yaml
variables:
- group: MyApplicationConfig

steps:
- script: |
    echo "API Endpoint: $(ApiEndpoint)"
    echo "API Key: $(ApiKey)"
    echo "Environment: $(Environment)"
```

**GitHub Actions (Migrated):**
```yaml
env:
  API_ENDPOINT: ${{ vars.API_ENDPOINT }}          # Non-sensitive → Variable
  ENVIRONMENT: ${{ vars.ENVIRONMENT }}            # Non-sensitive → Variable

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "API Endpoint: $API_ENDPOINT"
          echo "API Key: ${{ secrets.API_KEY }}"  # Sensitive → Secret
          echo "Environment: $ENVIRONMENT"
```

### Organization-Level Variable Groups

**Azure DevOps (organization variable group):**
```yaml
variables:
- group: OrganizationWideSecrets

steps:
- script: |
    echo "Docker Username: $(DockerUsername)"
    echo "Docker Password: $(DockerPassword)"
    echo "Registry URL: $(RegistryUrl)"
```

**GitHub Actions (organization secrets and variables):**
```yaml
env:
  REGISTRY_URL: ${{ vars.REGISTRY_URL }}  # Organization Variable

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Docker Username: ${{ secrets.DOCKER_USERNAME }}"  # Org Secret
          echo "Docker Password: ${{ secrets.DOCKER_PASSWORD }}"  # Org Secret
          echo "Registry URL: $REGISTRY_URL"
```

## Environment-Specific Secrets and Variables

Azure DevOps environments can have associated variable groups. GitHub Actions uses environment-scoped secrets and variables.

**Azure DevOps:**
```yaml
stages:
- stage: Deploy
  jobs:
  - deployment: DeployJob
    environment: 'production'
    variables:
    - group: ProductionSecrets
    strategy:
      runOnce:
        deploy:
          steps:
          - script: |
              echo "Database: $(DatabaseConnectionString)"
              echo "API Key: $(ProductionApiKey)"
```

**GitHub Actions:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: |
          echo "Database: ${{ secrets.DATABASE_CONNECTION_STRING }}"
          echo "API Key: ${{ secrets.PRODUCTION_API_KEY }}"
```

## Service Connections to GitHub Secrets

Azure DevOps service connections store credentials for external services. These become GitHub Secrets.

**Azure DevOps:**
```yaml
steps:
- task: AzureCLI@2
  inputs:
    azureSubscription: 'MyAzureConnection'
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      az account show
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/login@v1
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - run: az account show
```

## Secure Files to GitHub Secrets

Azure DevOps secure files (certificates, key files, etc.) can be stored as GitHub Secrets.

**Azure DevOps:**
```yaml
steps:
- task: DownloadSecureFile@1
  name: certificateFile
  inputs:
    secureFile: 'my-certificate.pfx'

- script: |
    echo "Certificate path: $(certificateFile.secureFilePath)"
```

**GitHub Actions (encode file as base64):**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Restore certificate file
        run: |
          echo "${{ secrets.CERTIFICATE_BASE64 }}" | base64 -d > my-certificate.pfx
          echo "Certificate restored to $(pwd)/my-certificate.pfx"
```

## Multi-Environment Configuration Pattern

Use different secrets/variables for different environments.

**Azure DevOps:**
```yaml
stages:
- stage: DeployDev
  variables:
  - group: DevEnvironment
  jobs:
  - deployment: Deploy
    environment: 'dev'

- stage: DeployProd
  variables:
  - group: ProdEnvironment
  jobs:
  - deployment: Deploy
    environment: 'production'
```

**GitHub Actions:**
```yaml
jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - run: echo "Using dev environment secrets"
      - run: echo "API: ${{ secrets.API_KEY }}"  # dev-scoped

  deploy-prod:
    runs-on: ubuntu-latest
    environment: production
    needs: deploy-dev
    steps:
      - run: echo "Using production environment secrets"
      - run: echo "API: ${{ secrets.API_KEY }}"  # production-scoped
```

## Runtime Variables and Dynamic Values

**Azure DevOps (system variables):**
```yaml
steps:
- script: |
    echo "Build ID: $(Build.BuildId)"
    echo "Build Number: $(Build.BuildNumber)"
    echo "Source Branch: $(Build.SourceBranch)"
    echo "Repository: $(Build.Repository.Name)"
```

**GitHub Actions (context variables):**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Run ID: ${{ github.run_id }}"
          echo "Run Number: ${{ github.run_number }}"
          echo "Source Branch: ${{ github.ref }}"
          echo "Repository: ${{ github.repository }}"
```

## Secret Naming Conventions

When migrating, consider standardizing secret names:

| Azure DevOps Name          | GitHub Actions Name          | Type     |
| -------------------------- | ---------------------------- | -------- |
| `apiKey`                   | `API_KEY`                    | Secret   |
| `databaseConnectionString` | `DATABASE_CONNECTION_STRING` | Secret   |
| `ApiEndpoint`              | `API_ENDPOINT`               | Variable |
| `buildConfiguration`       | `BUILD_CONFIGURATION`        | Variable |
| `docker_username`          | `DOCKER_USERNAME`            | Secret   |
| `docker_password`          | `DOCKER_PASSWORD`            | Secret   |

**Best Practice:** Use UPPER_SNAKE_CASE for consistency with environment variable conventions.

---

*For security best practices, migration checklists, troubleshooting guidance, and additional resources, refer to [Migration Guardrails](docs/migration-guardrails.md) and [Migration Standards](docs/migration-standards.md) in the knowledge base.*
