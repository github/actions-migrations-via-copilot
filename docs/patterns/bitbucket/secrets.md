# Migrating Secrets and Variables from Bitbucket Pipelines to GitHub Actions

When migrating CI/CD pipelines from Bitbucket Pipelines to GitHub Actions, properly handling repository variables, deployment variables, and configuration is critical for security and functionality. This guide outlines the best practices and steps to effectively migrate Bitbucket variables and credentials.

## Understanding Bitbucket Variable and Secret Types

Bitbucket Pipelines uses several mechanisms for managing configuration:

1. **Repository Variables** - Defined in repository settings (secured and non-secured)
2. **Deployment Variables** - Scoped to specific deployment environments
3. **Workspace Variables** - Shared across all repositories in a workspace
4. **Bitbucket System Variables** - Built-in variables provided by Bitbucket (e.g., `$BITBUCKET_BRANCH`)
5. **SSH Keys** - For secure authentication

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
- SSH keys and deploy keys
- Docker registry passwords
- Cloud provider credentials
- Any sensitive data that should be encrypted
- All Bitbucket "secured" repository variables

### Use GitHub Variables For:
- API endpoints (non-authenticated)
- Build configurations (Debug/Release)
- Feature flags
- Environment names (dev, staging, production)
- Application version numbers
- Non-sensitive application settings
- Public configuration values
- Build tool versions
- Docker image names (non-credentials)
- All Bitbucket "non-secured" repository variables

## Repository Variables to GitHub Actions

### Non-Secured Repository Variables

**Bitbucket Pipelines (repository variables defined in settings):**
```yaml
# Variables: API_ENDPOINT, BUILD_CONFIGURATION (not secured)
pipelines:
  default:
    - step:
        name: Build
        script:
          - echo "API Endpoint: $API_ENDPOINT"
          - echo "Build Config: $BUILD_CONFIGURATION"
```

**GitHub Actions:**
```yaml
name: Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      API_ENDPOINT: ${{ vars.API_ENDPOINT }}
      BUILD_CONFIGURATION: ${{ vars.BUILD_CONFIGURATION }}
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: |
          echo "API Endpoint: $API_ENDPOINT"
          echo "Build Config: $BUILD_CONFIGURATION"
```

### Secured Repository Variables

**Bitbucket Pipelines (secured repository variables):**
```yaml
# Variables: DATABASE_PASSWORD, API_SECRET_KEY (secured)
pipelines:
  default:
    - step:
        name: Build
        script:
          - echo "Database password is hidden"
          - curl -H "Authorization: Bearer $API_SECRET_KEY" https://api.example.com
```

**GitHub Actions:**
```yaml
name: Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: |
          echo "Database password is hidden"
          curl -H "Authorization: Bearer ${{ secrets.API_SECRET_KEY }}" https://api.example.com
        env:
          DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
```

## Workspace Variables to Organization Secrets/Variables

**Bitbucket (workspace-level variables shared across repositories):**
```yaml
# Workspace variables: DOCKER_USERNAME, DOCKER_PASSWORD
pipelines:
  default:
    - step:
        name: Build and push
        script:
          - docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
          - docker push myimage:latest
```

**GitHub Actions (organization secrets/variables):**
```yaml
name: Build and Push

on: [push]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: myimage:latest
```

## Deployment Variables to Environment Secrets/Variables

### Environment-Specific Variables

**Bitbucket Pipelines (deployment variables):**
```yaml
pipelines:
  branches:
    main:
      - step:
          name: Deploy to production
          deployment: production
          script:
            # Uses production deployment variables:
            # DEPLOY_URL, DEPLOY_TOKEN (secured)
            - curl -X POST -H "Authorization: Bearer $DEPLOY_TOKEN" $DEPLOY_URL/deploy
```

**GitHub Actions (environment secrets/variables):**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: |
          curl -X POST -H "Authorization: Bearer ${{ secrets.DEPLOY_TOKEN }}" ${{ vars.DEPLOY_URL }}/deploy
```

### Multi-Environment Deployments

**Bitbucket Pipelines:**
```yaml
pipelines:
  branches:
    main:
      - step:
          deployment: production
          script:
            - ./deploy.sh $PROD_SERVER $PROD_API_KEY
    develop:
      - step:
          deployment: staging
          script:
            - ./deploy.sh $STAGING_SERVER $STAGING_API_KEY
```

**GitHub Actions:**
```yaml
name: Deploy

on:
  push:
    branches: [main, develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.ref_name == 'main' && 'production' || 'staging' }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./deploy.sh ${{ vars.DEPLOY_SERVER }} ${{ secrets.DEPLOY_API_KEY }}
```

## Bitbucket Built-in Variables to GitHub Contexts

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - step:
        name: Build info
        script:
          - echo "Branch: $BITBUCKET_BRANCH"
          - echo "Commit: $BITBUCKET_COMMIT"
          - echo "Build: $BITBUCKET_BUILD_NUMBER"
          - echo "Repo: $BITBUCKET_REPO_FULL_NAME"
          - echo "Clone dir: $BITBUCKET_CLONE_DIR"
```

**GitHub Actions:**
```yaml
name: Build Info

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build info
        run: |
          echo "Branch: ${{ github.ref_name }}"
          echo "Commit: ${{ github.sha }}"
          echo "Build: ${{ github.run_number }}"
          echo "Repo: ${{ github.repository }}"
          echo "Clone dir: ${{ github.workspace }}"
```

## SSH Keys and Secure Files

### SSH Key for Deployments

**Bitbucket Pipelines (SSH key in repository settings):**
```yaml
pipelines:
  default:
    - step:
        name: Deploy
        script:
          - ssh user@server "cd /app && git pull"
```

**GitHub Actions (SSH key as secret):**
```yaml
name: Deploy

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ vars.DEPLOY_HOST }} >> ~/.ssh/known_hosts
      - name: Deploy
        run: ssh ${{ vars.DEPLOY_USER }}@${{ vars.DEPLOY_HOST }} "cd /app && git pull"
```

## Secret Naming Conventions

When migrating, consider standardizing secret names:

| Bitbucket Variable          | GitHub Actions Name              | Type     |
| --------------------------- | -------------------------------- | -------- |
| `DOCKER_USERNAME`           | `DOCKER_USERNAME`                | Secret   |
| `DOCKER_PASSWORD`           | `DOCKER_PASSWORD`                | Secret   |
| `AWS_ACCESS_KEY_ID`         | `AWS_ACCESS_KEY_ID`              | Secret   |
| `AWS_SECRET_ACCESS_KEY`     | `AWS_SECRET_ACCESS_KEY`          | Secret   |
| `DATABASE_PASSWORD`         | `DATABASE_PASSWORD`              | Secret   |
| `API_ENDPOINT`              | `API_ENDPOINT`                   | Variable |
| `BUILD_CONFIGURATION`       | `BUILD_CONFIGURATION`            | Variable |
| `DEPLOY_URL` (production)   | `DEPLOY_URL` (environment var)   | Variable |
| `DEPLOY_TOKEN` (production) | `DEPLOY_TOKEN` (environment sec) | Secret   |

**Best Practice:** Use UPPER_SNAKE_CASE for consistency with environment variable conventions.

## Common Migration Patterns

### Pattern 1: Simple Build Configuration

**Before (Bitbucket):**
```yaml
# Repository variables: NODE_VERSION=16, BUILD_ENV=production
pipelines:
  default:
    - step:
        image: node:$NODE_VERSION
        script:
          - npm install
          - npm run build:$BUILD_ENV
```

**After (GitHub Actions):**
```yaml
name: Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ vars.NODE_VERSION }}
      - run: npm install
      - run: npm run build:${{ vars.BUILD_ENV }}
```

### Pattern 2: Secure API Integration

**Before (Bitbucket):**
```yaml
# Secured variables: API_KEY, API_SECRET
pipelines:
  default:
    - step:
        script:
          - curl -u "$API_KEY:$API_SECRET" https://api.example.com
```

**After (GitHub Actions):**
```yaml
name: API Integration
on: [push]
jobs:
  integrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: curl -u "${{ secrets.API_KEY }}:${{ secrets.API_SECRET }}" https://api.example.com
```

### Pattern 3: Multi-Stage Deployment

**Before (Bitbucket):**
```yaml
pipelines:
  branches:
    main:
      - step:
          deployment: production
          trigger: manual
          script:
            - ./deploy.sh $PROD_URL $PROD_TOKEN
```

**After (GitHub Actions):**
```yaml
name: Deploy Production
on:
  push:
    branches: [main]
  workflow_dispatch:
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh ${{ vars.PROD_URL }} ${{ secrets.PROD_TOKEN }}
```

### Pattern 4: Docker Build with Registry Credentials

**Before (Bitbucket):**
```yaml
# Secured variables: DOCKER_USERNAME, DOCKER_PASSWORD
pipelines:
  default:
    - step:
        services:
          - docker
        script:
          - docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
          - docker build -t myapp:$BITBUCKET_BUILD_NUMBER .
          - docker push myapp:$BITBUCKET_BUILD_NUMBER
```

**After (GitHub Actions):**
```yaml
name: Docker Build
on: [push]
jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: myapp:${{ github.run_number }}
```

---

*For security best practices, migration checklists, troubleshooting guidance, and additional resources, refer to [Migration Guardrails](docs/migration-guardrails.md) and [Migration Standards](docs/migration-standards.md) in the knowledge base.*
