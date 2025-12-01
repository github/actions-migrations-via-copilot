````markdown
# Migrating Secrets and Variables from Bamboo to GitHub Actions

When migrating CI/CD pipelines from Bamboo to GitHub Actions, properly handling global variables, secrets, and configuration is critical for security and functionality. This guide outlines the best practices and steps to effectively migrate Bamboo variables and credentials.

## Understanding Bamboo Variable and Secret Types

Bamboo uses several mechanisms for managing configuration:

1. **Global Variables** - Defined in Bamboo administration, available to all plans
2. **Plan Variables** - Defined at the plan level in bamboo-specs
3. **Deployment Environment Variables** - Scoped to specific deployment environments
4. **Shared Credentials** - Username/password pairs stored in Bamboo
5. **Bamboo System Variables** - Built-in variables provided by Bamboo
6. **Repository Access Credentials** - SSH keys and repository credentials
7. **Capability Variables** - Agent-specific capabilities

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
- Shared credentials (usernames and passwords)
- Repository access tokens
- Any sensitive data that should be encrypted

### Use GitHub Variables For:
- API endpoints (non-authenticated)
- Build configurations (Debug/Release)
- Feature flags
- Environment names (dev, staging, production)
- Application version numbers
- Non-sensitive application settings
- Public configuration values
- Build tool versions
- Agent capability replacements

## Global Variables to GitHub Actions

### Simple Global Variables

**Bamboo (global variables defined in administration):**
```yaml
# Referenced in bamboo-specs
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Build
    jobs:
      - name: Build Job
        tasks:
          - script:
              scripts:
                - echo "API Endpoint: ${bamboo.API_ENDPOINT}"
                - echo "Build Config: ${bamboo.BUILD_CONFIGURATION}"
```

**GitHub Actions:**
```yaml
name: My Project Build

env:
  API_ENDPOINT: ${{ vars.API_ENDPOINT }}
  BUILD_CONFIGURATION: ${{ vars.BUILD_CONFIGURATION }}

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          echo "API Endpoint: $API_ENDPOINT"
          echo "Build Config: $BUILD_CONFIGURATION"
```

### Secret Global Variables

**Bamboo (global variables marked as secret):**
```yaml
# Sensitive values stored as global variables in Bamboo
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Build
    jobs:
      - name: Build Job
        tasks:
          - script:
              scripts:
                - echo "Database password is hidden: ${bamboo.DATABASE_PASSWORD}"
                - echo "API Key: ${bamboo.API_SECRET_KEY}"
```

**GitHub Actions:**
```yaml
name: My Project Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          echo "Database password is hidden: ${{ secrets.DATABASE_PASSWORD }}"
          echo "API Key: ${{ secrets.API_SECRET_KEY }}"
```

## Plan Variables to GitHub Actions

### Plan-Level Variables

**Bamboo (plan variables in bamboo-specs):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

variables:
  nodejs_version: '16.x'
  build_target: 'production'

stages:
  - name: Build
    jobs:
      - name: Build Job
        tasks:
          - script:
              scripts:
                - echo "Node version: ${bamboo.nodejs_version}"
                - echo "Target: ${bamboo.build_target}"
```

**GitHub Actions:**
```yaml
name: My Project Build

env:
  NODEJS_VERSION: '16.x'
  BUILD_TARGET: 'production'

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODEJS_VERSION }}

      - name: Build
        run: echo "Target: $BUILD_TARGET"
```

## Deployment Environment Variables to GitHub Environments

Bamboo deployment environments can have environment-specific variables. GitHub Actions uses environment-scoped secrets and variables.

**Bamboo (deployment project with environment variables):**
```yaml
deployment-project:
  key: MYPROJECT-DEPLOY
  name: My App Deployment

source-plan: MYPROJECT-BUILD

environments:
  - name: Production
    variables:
      deployment_url: https://prod.example.com
      database_host: prod-db.example.com
    triggers:
      - manual: {}
    tasks:
      - script:
          scripts:
            - echo "Deploying to ${bamboo.deployment_url}"
            - echo "Database: ${bamboo.database_host}"
            - ./deploy.sh ${bamboo.PROD_API_KEY}
```

**GitHub Actions:**
```yaml
name: Production Deployment

on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Production
        env:
          DEPLOYMENT_URL: ${{ vars.DEPLOYMENT_URL }}
          DATABASE_HOST: ${{ vars.DATABASE_HOST }}
        run: |
          echo "Deploying to $DEPLOYMENT_URL"
          echo "Database: $DATABASE_HOST"
          ./deploy.sh ${{ secrets.PROD_API_KEY }}
```

## Shared Credentials to GitHub Secrets

Bamboo shared credentials (username/password pairs) become GitHub Secrets.

**Bamboo (shared credentials):**
```yaml
# Shared credentials configured in Bamboo administration
# Referenced in tasks
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Deploy
    jobs:
      - name: Deploy Job
        tasks:
          - script:
              scripts:
                - docker login -u ${bamboo.docker_hub_username} -p ${bamboo.docker_hub_password}
```

**GitHub Actions:**
```yaml
name: My Project Build

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_PASSWORD }}
```

## Organization-Wide Variables

**Bamboo (global variables shared across all plans):**
```yaml
# Global variables in Bamboo administration
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Build
    jobs:
      - name: Build Job
        tasks:
          - script:
              scripts:
                - echo "Artifact Registry: ${bamboo.ARTIFACT_REGISTRY_URL}"
                - echo "Organization: ${bamboo.ORGANIZATION_NAME}"
```

**GitHub Actions (organization variables and secrets):**
```yaml
name: My Project Build

env:
  ARTIFACT_REGISTRY_URL: ${{ vars.ARTIFACT_REGISTRY_URL }}  # Organization Variable
  ORGANIZATION_NAME: ${{ vars.ORGANIZATION_NAME }}          # Organization Variable

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          echo "Artifact Registry: $ARTIFACT_REGISTRY_URL"
          echo "Organization: $ORGANIZATION_NAME"
```

## Repository Access Credentials

**Bamboo (repository access credentials):**
```yaml
# Configured in Bamboo repository settings
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

repositories:
  - name: Main Repository
    type: git
    url: git@github.com:org/repo.git
    authentication:
      type: ssh
      private-key: ${bamboo.ssh_private_key}
```

**GitHub Actions:**
```yaml
name: My Project Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: org/repo
          ssh-key: ${{ secrets.SSH_PRIVATE_KEY }}
```

## Multi-Environment Configuration Pattern

Use different secrets/variables for different deployment environments.

**Bamboo (multiple deployment environments):**
```yaml
deployment-project:
  key: MYPROJECT-DEPLOY
  name: My App Deployment

environments:
  - name: Development
    variables:
      env_name: dev
      api_url: https://dev-api.example.com
    tasks:
      - script:
          scripts:
            - ./deploy.sh ${bamboo.env_name} ${bamboo.DEV_SECRET}

  - name: Staging
    variables:
      env_name: staging
      api_url: https://staging-api.example.com
    tasks:
      - script:
          scripts:
            - ./deploy.sh ${bamboo.env_name} ${bamboo.STAGING_SECRET}

  - name: Production
    variables:
      env_name: production
      api_url: https://api.example.com
    tasks:
      - script:
          scripts:
            - ./deploy.sh ${bamboo.env_name} ${bamboo.PROD_SECRET}
```

**GitHub Actions:**
```yaml
name: Multi-Environment Deployment

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        type: choice
        options:
          - development
          - staging
          - production

jobs:
  deploy-dev:
    if: github.event.inputs.environment == 'development'
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          ENV_NAME: ${{ vars.ENV_NAME }}
          API_URL: ${{ vars.API_URL }}
        run: ./deploy.sh $ENV_NAME ${{ secrets.DEV_SECRET }}

  deploy-staging:
    if: github.event.inputs.environment == 'staging'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          ENV_NAME: ${{ vars.ENV_NAME }}
          API_URL: ${{ vars.API_URL }}
        run: ./deploy.sh $ENV_NAME ${{ secrets.STAGING_SECRET }}

  deploy-production:
    if: github.event.inputs.environment == 'production'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          ENV_NAME: ${{ vars.ENV_NAME }}
          API_URL: ${{ vars.API_URL }}
        run: ./deploy.sh $ENV_NAME ${{ secrets.PROD_SECRET }}
```

## Runtime Variables and System Context

**Bamboo (system variables):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Build
    jobs:
      - name: Build Job
        tasks:
          - script:
              scripts:
                - echo "Build Number: ${bamboo.buildNumber}"
                - echo "Build Key: ${bamboo.buildKey}"
                - echo "Plan Name: ${bamboo.planName}"
                - echo "Branch: ${bamboo.planRepository.branchName}"
                - echo "Revision: ${bamboo.planRepository.revision}"
```

**GitHub Actions (context variables):**
```yaml
name: My Project Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Display Build Info
        run: |
          echo "Run Number: ${{ github.run_number }}"
          echo "Run ID: ${{ github.run_id }}"
          echo "Workflow: ${{ github.workflow }}"
          echo "Branch: ${{ github.ref_name }}"
          echo "Commit SHA: ${{ github.sha }}"
```

## Variable Naming Conventions

When migrating, consider standardizing variable names:

| Bamboo Variable Name  | GitHub Actions Name   | Type     |
| --------------------- | --------------------- | -------- |
| `API_SECRET_KEY`      | `API_SECRET_KEY`      | Secret   |
| `DATABASE_PASSWORD`   | `DATABASE_PASSWORD`   | Secret   |
| `API_ENDPOINT`        | `API_ENDPOINT`        | Variable |
| `BUILD_CONFIGURATION` | `BUILD_CONFIGURATION` | Variable |
| `docker_hub_username` | `DOCKER_HUB_USERNAME` | Secret   |
| `docker_hub_password` | `DOCKER_HUB_PASSWORD` | Secret   |
| `deployment_url`      | `DEPLOYMENT_URL`      | Variable |
| `ssh_private_key`     | `SSH_PRIVATE_KEY`     | Secret   |

**Best Practice:** Use UPPER_SNAKE_CASE for consistency with environment variable conventions.

## Common Migration Patterns

### 1. Minimize Secret Exposure
```yaml
```

## SSH Keys and Secure Files
```

### 2. Use Environment Scoping
```yaml
# ✅ Good: Scope secrets to specific environments
jobs:
  deploy:
    environment: production  # Uses production-scoped secrets
    steps:
      - run: echo "Deploying with production credentials"
```

### 3. Rotate Secrets Regularly
- Document which secrets need rotation
- Use GitHub's audit log to track secret usage
- Implement secret expiration policies

### 4. Separate Secrets by Scope
- **Organization Secrets**: Shared infrastructure credentials (Docker Hub, registries)
- **Repository Secrets**: Project-specific credentials
- **Environment Secrets**: Deployment-specific credentials

## SSH Keys and Secure Files

**Bamboo (SSH keys stored as shared credentials or secure files):**
```yaml
# SSH key configured as shared credential
plan:
  key: MYPROJECT-DEPLOY
  name: My Project Deploy

stages:
  - name: Deploy
    jobs:
      - name: Deploy via SSH
        tasks:
          - scp:
              host: ${bamboo.DEPLOY_HOST}
              username: ${bamboo.DEPLOY_USER}
              private-key: ${bamboo.DEPLOY_SSH_KEY}
              source-path: dist/
              target-path: /var/www/html/
```

**GitHub Actions (SSH key as secret):**
```yaml
name: My Project Deploy

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup SSH Key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.DEPLOY_SSH_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.DEPLOY_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy via SCP
        run: |
          scp -r dist/* ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }}:/var/www/html/
```

## Common Migration Patterns

### Pattern 1: Database Connection String
**Bamboo:**
```yaml
# Global variable: DATABASE_URL
${bamboo.DATABASE_URL}
```

**GitHub Actions:**
```yaml
# Repository Secret: DATABASE_URL
${{ secrets.DATABASE_URL }}
```

### Pattern 2: Multi-Environment API Keys
**Bamboo:**
```yaml
# Dev environment variable: DEV_API_KEY
# Prod environment variable: PROD_API_KEY
${bamboo.DEV_API_KEY}
${bamboo.PROD_API_KEY}
```

**GitHub Actions:**
```yaml
# Environment-scoped secrets
jobs:
  deploy-dev:
    environment: development
    steps:
      - run: echo "${{ secrets.API_KEY }}"  # Uses dev-scoped API_KEY

  deploy-prod:
    environment: production
    steps:
      - run: echo "${{ secrets.API_KEY }}"  # Uses prod-scoped API_KEY
```

### Pattern 3: Build Configuration
**Bamboo:**
```yaml
# Plan variable: BUILD_CONFIGURATION
variables:
  BUILD_CONFIGURATION: Release
```

**GitHub Actions:**
```yaml
# Repository Variable: BUILD_CONFIGURATION
env:
  BUILD_CONFIGURATION: ${{ vars.BUILD_CONFIGURATION }}
```

---

*For security best practices, migration checklists, troubleshooting guidance, and additional resources, refer to [Migration Guardrails](docs/migration-guardrails.md) and [Migration Standards](docs/migration-standards.md) in the knowledge base.*

````
