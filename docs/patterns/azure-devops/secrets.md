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

## Security Best Practices

### 1. Minimize Secret Exposure
```yaml
# ❌ Bad: Exposing secrets unnecessarily
- run: echo "My secret is ${{ secrets.API_KEY }}"

# ✅ Good: Use secrets only when needed
- run: curl -H "Authorization: Bearer ${{ secrets.API_KEY }}" https://api.example.com
```

### 2. Use Environment Scoping
```yaml
# ✅ Good: Scope secrets to specific environments
jobs:
  deploy:
    environment: production  # Uses production-scoped secrets
    steps:
      - run: echo "Deploying with ${{ secrets.PROD_API_KEY }}"
```

### 3. Rotate Secrets Regularly
- Document which secrets need rotation
- Use GitHub's audit log to track secret usage
- Implement secret expiration policies

### 4. Separate Secrets by Scope
- **Organization Secrets**: Shared infrastructure credentials
- **Repository Secrets**: Project-specific credentials
- **Environment Secrets**: Deployment-specific credentials

## Migration Checklist

### Pre-Migration
- [ ] Audit all Azure DevOps variables and variable groups
- [ ] Identify which values are sensitive (secrets) vs. configuration (variables)
- [ ] Document which variable groups are used by which pipelines
- [ ] Identify service connections and secure files
- [ ] Map Azure DevOps environments to GitHub environments

### During Migration
- [ ] Create GitHub Secrets for sensitive values
- [ ] Create GitHub Variables for non-sensitive configuration
- [ ] Use organization-level secrets/variables for shared resources
- [ ] Set up environment-specific secrets/variables
- [ ] Convert secure files to base64-encoded secrets
- [ ] Update workflow files to reference new secrets/variables
- [ ] Test secret access in workflows

### Post-Migration
- [ ] Verify all secrets are properly encrypted
- [ ] Confirm no secrets are logged or exposed
- [ ] Update team documentation
- [ ] Rotate all migrated secrets
- [ ] Remove Azure DevOps variables after successful migration
- [ ] Set up secret scanning and alerts

## Troubleshooting

### Secret Not Available
```yaml
# Check if secret exists and is accessible
- run: |
    if [ -z "${{ secrets.MY_SECRET }}" ]; then
      echo "Secret MY_SECRET is not set"
      exit 1
    fi
```

### Variable Precedence
GitHub Actions evaluates variables in this order:
1. Step-level `env:`
2. Job-level `env:`
3. Workflow-level `env:`
4. Repository/Organization variables
5. Default environment variables

### Secret Masking
GitHub automatically masks secrets in logs. If you need to debug:
```yaml
# ✅ Debug without exposing secret value
- run: |
    if [ -n "${{ secrets.API_KEY }}" ]; then
      echo "API_KEY is set (length: ${#API_KEY})"
    else
      echo "API_KEY is not set"
    fi
```

## Additional Resources

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub Actions Variables Documentation](https://docs.github.com/en/actions/learn-github-actions/variables)
- [GitHub Actions Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Security Hardening for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

---

*This secrets migration guide is maintained as part of the CI/CD Migration Knowledge Base.*
