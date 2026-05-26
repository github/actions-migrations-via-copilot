# GitLab CI/CD to GitHub Actions Mapping Guide

This guide provides a mapping of common GitLab CI/CD syntax and configurations to their equivalent GitHub Actions. Use this as a reference when migrating your CI/CD pipelines from GitLab CI/CD to GitHub Actions.

## Common Commands Mapping

| GitLab CI/CD Concept  | GitHub Actions Equivalent                       | Description                      |
| --------------------- | ----------------------------------------------- | -------------------------------- |
| `stages:`             | `jobs:` with `needs:`                           | Pipeline stages and dependencies |
| `job_name:`           | `jobs.<job_id>:`                                | Individual job definition        |
| `script:`             | `run:`                                          | Shell commands to execute        |
| `image:`              | `container:` or `runs-on:`                      | Execution environment            |
| `services:`           | `services:`                                     | Service containers               |
| `before_script:`      | Initial step with `run:`                        | Commands before main script      |
| `after_script:`       | Final step with `if: always()`                  | Cleanup commands                 |
| `rules:`              | `if:`                                           | Conditional execution            |
| `only:` / `except:`   | `on:` with branch filters                       | Branch/tag triggers              |
| `needs:`              | `needs:`                                        | Job dependencies                 |
| `dependencies:`       | `needs:` with artifacts                         | Artifact dependencies            |
| `artifacts:`          | `actions/upload-artifact` / `download-artifact` | Artifact management              |
| `cache:`              | `actions/cache`                                 | Caching dependencies             |
| `variables:`          | `env:` or `vars.*` / `secrets.*`                | Environment variables            |
| `extends:`            | Reusable workflows or inline expansion          | Job inheritance                  |
| `include:`            | Reusable workflows or inline expansion          | Template inclusion               |
| `trigger:`            | `workflow_dispatch:` or repository dispatch     | Pipeline triggering              |
| `when: manual`        | `environment:` with protection rules            | Manual approval                  |
| `when: on_failure`    | `if: failure()`                                 | Run on failure                   |
| `when: always`        | `if: always()`                                  | Always run                       |
| `allow_failure: true` | `continue-on-error: true`                       | Allow step to fail               |
| `timeout:`            | `timeout-minutes:`                              | Job timeout                      |
| `retry:`              | Custom logic or marketplace actions             | Retry on failure                 |
| `environment:`        | `environment:`                                  | Deployment environment           |
| `tags:`               | `runs-on:` with runner labels                   | Runner selection                 |
| `parallel:`           | `strategy: matrix:`                             | Parallel job execution           |
| `.gitlab-ci.yml`      | `.github/workflows/*.yml`                       | Pipeline configuration file      |

## Configuration Examples

### Basic Pipeline Structure

**GitLab CI/CD:**
```yaml
stages:
  - build
  - test
  - deploy

build-job:
  stage: build
  image: node:16
  script:
    - npm install
    - npm run build
  artifacts:
    paths:
      - dist/
```

**GitHub Actions:**
```yaml
name: CI Pipeline

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 16
      - run: npm install
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

### Stage Dependencies

**GitLab CI/CD:**
```yaml
stages:
  - build
  - test

build:
  stage: build
  script:
    - echo "Building"

test:
  stage: test
  needs:
    - build
  script:
    - echo "Testing"
```

**GitHub Actions:**
```yaml
name: CI Pipeline

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building"

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - run: echo "Testing"
```

### Rules and Conditions

**GitLab CI/CD:**
```yaml
deploy:
  script:
    - ./deploy.sh
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG
```

**GitHub Actions:**
```yaml
name: Deploy

on:
  push:
    branches: [main]
    tags: ['*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

### Services (Databases)

**GitLab CI/CD:**
```yaml
test:
  image: node:16
  services:
    - postgres:14
  variables:
    POSTGRES_PASSWORD: test123
  script:
    - npm run test:integration
```

**GitHub Actions:**
```yaml
name: Integration Tests

on: [push]

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
      - run: npm run test:integration
```

### Before/After Script

**GitLab CI/CD:**
```yaml
test:
  before_script:
    - echo "Setting up"
  script:
    - npm test
  after_script:
    - echo "Cleaning up"
```

**GitHub Actions:**
```yaml
name: Test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        run: echo "Setting up"
      - name: Test
        run: npm test
      - name: Cleanup
        if: always()
        run: echo "Cleaning up"
```

### Caching

**GitLab CI/CD:**
```yaml
build:
  image: node:16
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
  script:
    - npm install
    - npm run build
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
      - uses: actions/setup-node@v4
        with:
          node-version: 16
          cache: 'npm'
      - run: npm install
      - run: npm run build
```

### Artifacts Between Jobs

**GitLab CI/CD:**
```yaml
build:
  stage: build
  script:
    - npm run build
  artifacts:
    paths:
      - dist/

deploy:
  stage: deploy
  dependencies:
    - build
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

### Environments and Manual Deployments

**GitLab CI/CD:**
```yaml
deploy-production:
  stage: deploy
  script:
    - ./deploy.sh production
  environment:
    name: production
    url: https://example.com
  when: manual
  only:
    - main
```

**GitHub Actions:**
```yaml
name: Deploy Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production
```

### Parallel Jobs (Matrix)

**GitLab CI/CD:**
```yaml
test:
  parallel:
    matrix:
      - NODE_VERSION: ['14', '16', '18']
  image: node:${NODE_VERSION}
  script:
    - npm test
```

**GitHub Actions:**
```yaml
name: Test Matrix

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [14, 16, 18]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test
```

### Conditional Execution

**GitLab CI/CD:**
```yaml
test:
  script:
    - npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

**GitHub Actions:**
```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

### Docker Build and Push

**GitLab CI/CD:**
```yaml
docker-build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
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
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

## GitLab Predefined Variables to GitHub Contexts

| GitLab Variable                        | GitHub Actions Equivalent                       |
| -------------------------------------- | ----------------------------------------------- |
| `$CI_COMMIT_REF_NAME`                  | `${{ github.ref_name }}`                        |
| `$CI_COMMIT_BRANCH`                    | `${{ github.ref_name }}` (on push)              |
| `$CI_COMMIT_TAG`                       | `${{ github.ref_name }}` (on tag)               |
| `$CI_COMMIT_SHA`                       | `${{ github.sha }}`                             |
| `$CI_COMMIT_SHORT_SHA`                 | `${{ github.sha }}` (substring in script)       |
| `$CI_PIPELINE_ID`                      | `${{ github.run_id }}`                          |
| `$CI_PIPELINE_IID`                     | `${{ github.run_number }}`                      |
| `$CI_PROJECT_NAME`                     | `${{ github.event.repository.name }}`           |
| `$CI_PROJECT_PATH`                     | `${{ github.repository }}`                      |
| `$CI_PROJECT_DIR`                      | `${{ github.workspace }}`                       |
| `$CI_PROJECT_URL`                      | `${{ github.event.repository.html_url }}`       |
| `$CI_MERGE_REQUEST_IID`                | `${{ github.event.pull_request.number }}`       |
| `$CI_MERGE_REQUEST_SOURCE_BRANCH_NAME` | `${{ github.head_ref }}`                        |
| `$CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | `${{ github.base_ref }}`                        |
| `$CI_REGISTRY_USER`                    | `${{ github.actor }}`                           |
| `$CI_REGISTRY_PASSWORD`                | `${{ secrets.GITHUB_TOKEN }}`                   |
| `$CI_REGISTRY_IMAGE`                   | `ghcr.io/${{ github.repository }}`              |
| `$CI_DEFAULT_BRANCH`                   | `${{ github.event.repository.default_branch }}` |
| `$CI_SERVER_HOST`                      | `github.com`                                    |
| `$CI_API_V4_URL`                       | `https://api.github.com`                        |
| `$GITLAB_USER_LOGIN`                   | `${{ github.actor }}`                           |
| `$GITLAB_USER_EMAIL`                   | `${{ github.event.pusher.email }}`              |

## Key Differences

### Execution Model
- **GitLab**: Stages run sequentially; jobs within stages run in parallel
- **GitHub Actions**: Jobs run in parallel by default; use `needs:` to create dependencies

### Template System
- **GitLab**: `include:` and `extends:` for reusability
- **GitHub Actions**: Reusable workflows and composite actions

### Runner Selection
- **GitLab**: `tags:` to select specific runners
- **GitHub Actions**: `runs-on:` to specify runner type

### Variables Scope
- **GitLab**: Project, group, and instance-level variables
- **GitHub Actions**: Repository, organization, and environment-level secrets/variables

### Artifact Management
- **GitLab**: Built-in artifact paths and expiration
- **GitHub Actions**: Explicit upload/download actions

## Migration Best Practices

1. **Expand includes inline** - GitLab `include:` statements should be expanded in resulting workflows
2. **Convert extends to inline** - Job inheritance should be flattened in GitHub Actions
3. **Map stages to job dependencies** - Use `needs:` to maintain execution order
4. **Convert rules to conditions** - GitLab `rules:` become `if:` conditions and workflow triggers
5. **Migrate variables appropriately** - Sensitive variables become Secrets, others become Variables
6. **Configure service health checks** - GitHub Actions services should include health check options
7. **Implement proper caching** - Use `actions/cache` or setup actions with built-in caching
8. **Set up environment protection** - Use GitHub Environments to replicate GitLab environment settings
9. **Handle manual gates** - Use `workflow_dispatch` or environment protection for manual approvals
10. **Replace GitLab functions** - Convert GitLab-specific functions to GitHub context equivalents

## Common GitLab Templates to GitHub Actions

| GitLab Template                              | GitHub Actions Equivalent                       |
| -------------------------------------------- | ----------------------------------------------- |
| `Auto-DevOps.gitlab-ci.yml`                  | Multiple marketplace actions                    |
| `Security/SAST.gitlab-ci.yml`                | `github/codeql-action`                          |
| `Security/Dependency-Scanning.gitlab-ci.yml` | `actions/dependency-review-action`              |
| `Security/Secret-Detection.gitlab-ci.yml`    | `trufflesecurity/trufflehog`                    |
| `Verify/Browser-Performance.gitlab-ci.yml`   | Lighthouse CI actions                           |
| `Deploy/ECS.gitlab-ci.yml`                   | `aws-actions/amazon-ecs-deploy-task-definition` |
| `Deploy/Cloud-Run.gitlab-ci.yml`             | `google-github-actions/deploy-cloudrun`         |

---

*This mapping guide is maintained as part of the CI/CD Migration Knowledge Base. For security standards and migration best practices, refer to the Migration Guardrails and Migration Standards documentation.*
