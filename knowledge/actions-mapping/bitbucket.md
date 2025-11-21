# Bitbucket Pipelines to GitHub Actions Mapping Guide

This guide provides a mapping of common Bitbucket Pipelines syntax and configurations to their equivalent GitHub Actions. Use this as a reference when migrating your CI/CD pipelines from Bitbucket Pipelines to GitHub Actions.

## Common Commands Mapping

| Bitbucket Pipelines Concept | GitHub Actions Equivalent                       | Description                       |
| --------------------------- | ----------------------------------------------- | --------------------------------- |
| `pipelines:`                | `jobs:`                                         | Top-level collection of workflows |
| `default:`                  | Workflow with `on: [push]`                      | Default pipeline for all branches |
| `branches:`                 | `on: push: branches:`                           | Branch-specific pipelines         |
| `pull-requests:`            | `on: pull_request:`                             | Pull request pipelines            |
| `custom:`                   | `on: workflow_dispatch:`                        | Manual trigger pipelines          |
| `step:`                     | `jobs.<job_id>:` with `steps:`                  | Individual execution step         |
| `name:`                     | `name:` (job or step level)                     | Display name for step/job         |
| `script:`                   | `run:`                                          | Shell commands to execute         |
| `image:`                    | `container:` or `runs-on:`                      | Execution environment             |
| `services:`                 | `services:`                                     | Service containers                |
| `caches:`                   | `actions/cache`                                 | Caching dependencies              |
| `artifacts:`                | `actions/upload-artifact` / `download-artifact` | Artifact management               |
| `parallel:`                 | Multiple jobs (implicit parallelization)        | Parallel execution                |
| `deployment:`               | `environment:`                                  | Deployment environments           |
| `trigger: manual`           | `on: workflow_dispatch:`                        | Manual workflow trigger           |
| `condition:`                | `if:`                                           | Conditional execution             |
| `size: 2x`                  | `runs-on:` with larger runner                   | Pipeline size/resources           |
| `max-time:`                 | `timeout-minutes:`                              | Execution timeout                 |
| `after-script:`             | Separate step with `if: always()`               | Cleanup/post-execution            |
| `variables:` (repository)   | `vars.*` or `secrets.*`                         | Repository variables              |
| `variables:` (deployment)   | `vars.*` or `secrets.*` (environment-scoped)    | Environment variables             |
| `$BITBUCKET_BRANCH`         | `${{ github.ref_name }}`                        | Current branch name               |
| `$BITBUCKET_COMMIT`         | `${{ github.sha }}`                             | Commit SHA                        |
| `$BITBUCKET_BUILD_NUMBER`   | `${{ github.run_number }}`                      | Build number                      |
| `$BITBUCKET_CLONE_DIR`      | `${{ github.workspace }}`                       | Workspace directory               |
| `$BITBUCKET_REPO_SLUG`      | `${{ github.event.repository.name }}`           | Repository name                   |
| `$BITBUCKET_REPO_OWNER`     | `${{ github.repository_owner }}`                | Repository owner                  |
| `bitbucket-pipelines.yml`   | `.github/workflows/*.yml`                       | Pipeline configuration file       |

## Configuration Examples

### Basic Pipeline Structure

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - step:
        name: Build and test
        image: node:16
        script:
          - npm install
          - npm run build
          - npm test
```

**GitHub Actions:**
```yaml
name: CI Pipeline

on: [push, pull_request]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    container: node:16
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm run build
      - run: npm test
```

### Branch-Specific Pipelines

**Bitbucket Pipelines:**
```yaml
pipelines:
  branches:
    main:
      - step:
          name: Deploy to production
          deployment: production
          script:
            - ./deploy.sh production
    develop:
      - step:
          name: Deploy to staging
          deployment: staging
          script:
            - ./deploy.sh staging
```

**GitHub Actions:**
```yaml
name: Deploy

on:
  push:
    branches:
      - main
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.ref_name == 'main' && 'production' || 'staging' }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: |
          if [ "${{ github.ref_name }}" == "main" ]; then
            ./deploy.sh production
          else
            ./deploy.sh staging
          fi
```

### Parallel Steps

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - parallel:
        - step:
            name: Unit tests
            script:
              - npm run test:unit
        - step:
            name: Lint
            script:
              - npm run lint
        - step:
            name: Security scan
            script:
              - npm audit
```

**GitHub Actions:**
```yaml
name: CI Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm run test:unit

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm run lint

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm audit
```

### Services (Databases)

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - step:
        name: Integration tests
        image: node:16
        services:
          - postgres
        script:
          - npm run test:integration

definitions:
  services:
    postgres:
      image: postgres:14
      environment:
        POSTGRES_PASSWORD: test123
```

**GitHub Actions:**
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test123
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 16
      - run: npm install
      - run: npm run test:integration
```

### Caching

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - step:
        name: Build
        caches:
          - node
        script:
          - npm install
          - npm run build

definitions:
  caches:
    node: node_modules
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
      - uses: actions/setup-node@v4
        with:
          node-version: 16
          cache: 'npm'
      - run: npm install
      - run: npm run build
```

### Artifacts

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - step:
        name: Build
        script:
          - npm run build
        artifacts:
          - dist/**
    - step:
        name: Deploy
        script:
          - ./deploy.sh dist
```

**GitHub Actions:**
```yaml
name: Build and Deploy

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - run: ./deploy.sh dist
```

### Manual Triggers

**Bitbucket Pipelines:**
```yaml
pipelines:
  custom:
    deploy-production:
      - step:
          name: Deploy to production
          deployment: production
          trigger: manual
          script:
            - ./deploy.sh production
```

**GitHub Actions:**
```yaml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'production'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh ${{ github.event.inputs.environment }}
```

### Conditional Execution

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - step:
        name: Deploy
        condition:
          changesets:
            includePaths:
              - "src/**"
        script:
          - ./deploy.sh
```

**GitHub Actions:**
```yaml
name: Deploy

on:
  push:
    paths:
      - 'src/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

### Docker Build and Push

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - step:
        name: Build and push Docker image
        services:
          - docker
        script:
          - docker build -t myapp:$BITBUCKET_BUILD_NUMBER .
          - docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
          - docker push myapp:$BITBUCKET_BUILD_NUMBER
```

**GitHub Actions:**
```yaml
name: Docker Build and Push

on: [push]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
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

## Bitbucket Built-in Variables to GitHub Contexts

| Bitbucket Variable                 | GitHub Actions Equivalent                        |
| ---------------------------------- | ------------------------------------------------ |
| `$BITBUCKET_BRANCH`                | `${{ github.ref_name }}`                         |
| `$BITBUCKET_TAG`                   | `${{ github.ref_name }}` (when triggered by tag) |
| `$BITBUCKET_COMMIT`                | `${{ github.sha }}`                              |
| `$BITBUCKET_BUILD_NUMBER`          | `${{ github.run_number }}`                       |
| `$BITBUCKET_CLONE_DIR`             | `${{ github.workspace }}`                        |
| `$BITBUCKET_REPO_SLUG`             | `${{ github.event.repository.name }}`            |
| `$BITBUCKET_REPO_FULL_NAME`        | `${{ github.repository }}`                       |
| `$BITBUCKET_REPO_OWNER`            | `${{ github.repository_owner }}`                 |
| `$BITBUCKET_REPO_UUID`             | No direct equivalent                             |
| `$BITBUCKET_PROJECT_KEY`           | No direct equivalent                             |
| `$BITBUCKET_PR_ID`                 | `${{ github.event.pull_request.number }}`        |
| `$BITBUCKET_PR_DESTINATION_BRANCH` | `${{ github.base_ref }}`                         |
| `$BITBUCKET_PIPELINE_UUID`         | `${{ github.run_id }}`                           |
| `$BITBUCKET_STEP_UUID`             | No direct equivalent                             |
| `$CI`                              | `${{ env.CI }}` (always 'true')                  |

## Key Differences

### Execution Model
- **Bitbucket**: Steps run sequentially by default; use `parallel:` for concurrent execution
- **GitHub Actions**: Jobs run in parallel by default; use `needs:` to create dependencies

### Custom Steps vs Reusable Workflows
- **Bitbucket**: Custom steps defined in separate repositories
- **GitHub Actions**: Reusable workflows and composite actions

### Pipeline Size
- **Bitbucket**: Configurable with `size: 2x` for more resources
- **GitHub Actions**: Different runner types (standard, larger runners)

### Deployment Environments
- **Bitbucket**: `deployment:` keyword with environment name
- **GitHub Actions**: `environment:` keyword with protection rules

### Artifact Retention
- **Bitbucket**: Artifacts expire after defined period
- **GitHub Actions**: Configurable retention (default 90 days)

## Migration Best Practices

1. **Convert parallel steps to separate jobs** - Bitbucket's `parallel:` blocks become independent jobs in GitHub Actions
2. **Expand custom steps inline** - Custom step references should be replaced with the actual step content
3. **Use verified marketplace actions** - Replace Bitbucket Pipes with equivalent GitHub Actions from verified creators
4. **Migrate variables appropriately** - Secured variables become Secrets, regular variables become Variables
5. **Configure service health checks** - GitHub Actions services should include health check options
6. **Implement proper caching** - Use `actions/cache` or language-specific setup actions with built-in caching
7. **Set up environment protection** - Use GitHub Environments to replicate Bitbucket deployment settings
8. **Test manual triggers** - Convert Bitbucket custom pipelines with manual triggers to `workflow_dispatch`

## Common Bitbucket Pipes to GitHub Actions

| Bitbucket Pipe                          | GitHub Actions Equivalent              |
| --------------------------------------- | -------------------------------------- |
| `atlassian/aws-elasticbeanstalk-deploy` | `einaregilsson/beanstalk-deploy`       |
| `atlassian/slack-notify-pipe`           | `slackapi/slack-github-action`         |
| `atlassian/aws-s3-deploy`               | `jakejarvis/s3-sync-action`            |
| `atlassian/aws-lambda-deploy`           | `appleboy/lambda-action`               |
| `atlassian/ssh-run`                     | `appleboy/ssh-action`                  |
| `atlassian/heroku-deploy`               | `akhileshns/heroku-deploy`             |
| `microsoft/azure-web-apps-deploy`       | `azure/webapps-deploy`                 |
| `sonarsource/sonarcloud-scan`           | `sonarsource/sonarcloud-github-action` |

---

*This mapping guide is maintained as part of the CI/CD Migration Knowledge Base. For security standards and migration best practices, refer to the Migration Guardrails and Migration Standards documentation.*
