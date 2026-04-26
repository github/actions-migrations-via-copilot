# Migrating Secrets and Variables from GitLab CI/CD to GitHub Actions

When migrating CI/CD pipelines from GitLab CI/CD to GitHub Actions, properly handling variables, secrets, and configuration at all levels is critical for security and functionality. This guide outlines the best practices and steps to effectively migrate GitLab variables and credentials.

## Understanding GitLab Variable and Secret Types

GitLab CI/CD uses several mechanisms for managing configuration:

1. **Project Variables** - Defined at the project level (protected, masked, expanded)
2. **Group Variables** - Shared across all projects in a group
3. **Instance Variables** - Available to all projects (GitLab self-managed)
4. **Environment Variables** - Scoped to specific environments
5. **CI/CD Variables in .gitlab-ci.yml** - Hardcoded or computed variables
6. **Protected Variables** - Only available to protected branches/tags
7. **Masked Variables** - Hidden in job logs
8. **GitLab Predefined Variables** - Built-in variables provided by GitLab

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
- Container registry credentials
- Cloud provider credentials
- Any GitLab masked or protected variables containing sensitive data
- All credentials that should never appear in logs

### Use GitHub Variables For:
- API endpoints (non-authenticated)
- Build configurations (Debug/Release)
- Feature flags
- Environment names (dev, staging, production)
- Application version numbers
- Non-sensitive application settings
- Public configuration values
- Build tool versions
- GitLab variables that are not masked

## Project Variables to GitHub Actions

### Simple Project Variables

**GitLab CI/CD (project variables defined in settings):**
```yaml
# Variables: API_ENDPOINT, BUILD_CONFIGURATION (not masked)
test:
  script:
    - echo "API Endpoint: $API_ENDPOINT"
    - echo "Build Config: $BUILD_CONFIGURATION"
```

**GitHub Actions:**
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      API_ENDPOINT: ${{ vars.API_ENDPOINT }}
      BUILD_CONFIGURATION: ${{ vars.BUILD_CONFIGURATION }}
    steps:
      - uses: actions/checkout@v4
      - name: Test
        run: |
          echo "API Endpoint: $API_ENDPOINT"
          echo "Build Config: $BUILD_CONFIGURATION"
```

### Masked Project Variables

**GitLab CI/CD (masked project variables):**
```yaml
# Variables: DATABASE_PASSWORD, API_SECRET_KEY (masked)
deploy:
  script:
    - echo "Deploying with credentials"
    - ./deploy.sh --api-key $API_SECRET_KEY --db-pass $DATABASE_PASSWORD
```

**GitHub Actions:**
```yaml
name: Deploy

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: |
          echo "Deploying with credentials"
          ./deploy.sh --api-key ${{ secrets.API_SECRET_KEY }} --db-pass ${{ secrets.DATABASE_PASSWORD }}
```

## Group Variables to Organization Secrets/Variables

**GitLab (group-level variables shared across projects):**
```yaml
# Group variables: DOCKER_USERNAME, DOCKER_PASSWORD (masked)
docker-build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
    - docker build -t myimage:latest .
    - docker push myimage:latest
```

**GitHub Actions (organization secrets/variables):**
```yaml
name: Docker Build and Push

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

## Environment Variables to Environment Secrets/Variables

### Environment-Specific Variables

**GitLab CI/CD (environment-scoped variables):**
```yaml
deploy-production:
  stage: deploy
  script:
    # Uses production environment variables:
    # DEPLOY_URL, DEPLOY_TOKEN (masked)
    - curl -X POST -H "Authorization: Bearer $DEPLOY_TOKEN" $DEPLOY_URL/deploy
  environment:
    name: production
  only:
    - main
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

**GitLab CI/CD:**
```yaml
deploy:
  stage: deploy
  script:
    - ./deploy.sh $DEPLOY_HOST $DEPLOY_KEY
  environment:
    name: $CI_COMMIT_REF_NAME
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      variables:
        DEPLOY_HOST: production.example.com
    - if: $CI_COMMIT_BRANCH == "develop"
      variables:
        DEPLOY_HOST: staging.example.com
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
        run: ./deploy.sh ${{ vars.DEPLOY_HOST }} ${{ secrets.DEPLOY_KEY }}
```

## Protected Variables to Branch Protection

**GitLab CI/CD (protected variables):**
```yaml
# Variable PROD_API_KEY is protected (only available on protected branches)
deploy:
  script:
    - ./deploy.sh --api-key $PROD_API_KEY
  only:
    - main
    - /^release-.*$/
```

**GitHub Actions (environment protection rules):**
```yaml
name: Deploy

on:
  push:
    branches:
      - main
      - 'release-**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Environment with protection rules
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./deploy.sh --api-key ${{ secrets.PROD_API_KEY }}
```

## GitLab Predefined Variables to GitHub Contexts

**GitLab CI/CD:**
```yaml
build:
  script:
    - echo "Branch: $CI_COMMIT_REF_NAME"
    - echo "Commit: $CI_COMMIT_SHA"
    - echo "Pipeline ID: $CI_PIPELINE_ID"
    - echo "Project: $CI_PROJECT_PATH"
    - echo "Workspace: $CI_PROJECT_DIR"
    - echo "User: $GITLAB_USER_LOGIN"
```

**GitHub Actions:**
```yaml
name: Build

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
          echo "Run ID: ${{ github.run_id }}"
          echo "Project: ${{ github.repository }}"
          echo "Workspace: ${{ github.workspace }}"
          echo "User: ${{ github.actor }}"
```

## File-Level Variables

**GitLab CI/CD (variables in .gitlab-ci.yml):**
```yaml
variables:
  NODE_VERSION: "16"
  BUILD_ENV: "production"

build:
  image: node:${NODE_VERSION}
  script:
    - npm run build:${BUILD_ENV}
```

**GitHub Actions:**
```yaml
name: Build

on: [push]

env:
  NODE_VERSION: "16"
  BUILD_ENV: "production"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - run: npm run build:${{ env.BUILD_ENV }}
```

## Secret Naming Conventions

When migrating, consider standardizing secret names:

| GitLab Variable              | GitHub Actions Name                 | Type     |
| ---------------------------- | ----------------------------------- | -------- |
| `DOCKER_USERNAME`            | `DOCKER_USERNAME`                   | Secret   |
| `DOCKER_PASSWORD`            | `DOCKER_PASSWORD`                   | Secret   |
| `AWS_ACCESS_KEY_ID`          | `AWS_ACCESS_KEY_ID`                 | Secret   |
| `AWS_SECRET_ACCESS_KEY`      | `AWS_SECRET_ACCESS_KEY`             | Secret   |
| `DATABASE_URL`               | `DATABASE_URL`                      | Secret   |
| `API_ENDPOINT`               | `API_ENDPOINT`                      | Variable |
| `BUILD_CONFIGURATION`        | `BUILD_CONFIGURATION`               | Variable |
| `DEPLOY_URL` (environment)   | `DEPLOY_URL` (environment variable) | Variable |
| `DEPLOY_TOKEN` (environment) | `DEPLOY_TOKEN` (environment secret) | Secret   |

**Best Practice:** Use UPPER_SNAKE_CASE for consistency with environment variable conventions.

## Common Migration Patterns

### Pattern 1: Simple Build Configuration

**Before (GitLab):**
```yaml
# Project variables: NODE_VERSION=16, BUILD_TARGET=production
build:
  image: node:$NODE_VERSION
  script:
    - npm install
    - npm run build -- --target=$BUILD_TARGET
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
      - run: npm run build -- --target=${{ vars.BUILD_TARGET }}
```

### Pattern 2: Secure API Integration

**Before (GitLab):**
```yaml
# Masked variables: API_KEY, API_SECRET
integration-test:
  script:
    - curl -u "$API_KEY:$API_SECRET" https://api.example.com/test
```

**After (GitHub Actions):**
```yaml
name: Integration Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: curl -u "${{ secrets.API_KEY }}:${{ secrets.API_SECRET }}" https://api.example.com/test
```

### Pattern 3: Container Registry Authentication

**Before (GitLab):**
```yaml
# Group variables: CI_REGISTRY_USER, CI_REGISTRY_PASSWORD (built-in)
docker-build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
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
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### Pattern 4: Multi-Stage with Shared Variables

**Before (GitLab):**
```yaml
# Group variables: SHARED_CONFIG, SHARED_SECRET (masked)
variables:
  LOCAL_VAR: "value"

build:
  stage: build
  script:
    - echo "Config: $SHARED_CONFIG, Local: $LOCAL_VAR"
    - ./build.sh

test:
  stage: test
  script:
    - echo "Testing with secret: $SHARED_SECRET"
    - ./test.sh
```

**After (GitHub Actions):**
```yaml
name: Build and Test
on: [push]

env:
  LOCAL_VAR: "value"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: |
          echo "Config: ${{ vars.SHARED_CONFIG }}, Local: $LOCAL_VAR"
          ./build.sh

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test
        run: |
          echo "Testing with secret"
          ./test.sh
        env:
          SHARED_SECRET: ${{ secrets.SHARED_SECRET }}
```

### Pattern 5: Dynamic Environment Deployment

**Before (GitLab):**
```yaml
# Environment-specific variables set in GitLab UI
deploy:
  script:
    - ./deploy.sh $DEPLOY_HOST $DEPLOY_PORT
  environment:
    name: $CI_COMMIT_REF_NAME
```

**After (GitHub Actions):**
```yaml
name: Deploy
on:
  push:
    branches: [main, staging, develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.ref_name }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./deploy.sh ${{ vars.DEPLOY_HOST }} ${{ vars.DEPLOY_PORT }}
```

## Variable Precedence

### GitLab CI/CD Precedence (highest to lowest):
1. Trigger variables (API/scheduled pipeline)
2. Project-level variables
3. Group-level variables
4. Instance-level variables
5. Pipeline-defined variables
6. Job-defined variables
7. Predefined variables

### GitHub Actions Precedence (highest to lowest):
1. Step-level `env:`
2. Job-level `env:`
3. Workflow-level `env:`
4. Environment variables
5. Repository variables
6. Organization variables
7. Default environment variables

## Special Considerations

### Expanding Variables
- **GitLab**: Variables expand by default unless marked as unexpanded
- **GitHub Actions**: Use `${{ }}` syntax for context variables, `$VAR` for environment variables

### File Variables
- **GitLab**: Can store variables as files using `file` type
- **GitHub Actions**: Store as secrets and write to files in workflow steps

### Variable Visibility
- **GitLab**: Protected and masked flags control visibility
- **GitHub Actions**: Secrets are always masked; use environment protection rules for access control

---

*For security best practices, migration checklists, troubleshooting guidance, and additional resources, refer to [Migration Guardrails](docs/migration-guardrails.md) and [Migration Standards](docs/migration-standards.md) in the knowledge base.*
