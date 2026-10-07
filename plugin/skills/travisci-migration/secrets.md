# Travis CI Secrets and Environment Variables Migration Guide

This guide provides patterns for migrating Travis CI encrypted variables and environment variables to GitHub Actions secrets and variables.

## Travis CI Encrypted Variables

Travis CI uses encrypted variables for sensitive data that are encrypted in the `.travis.yml` file.

### Single Encrypted Variable

```yaml
# Travis CI
env:
  global:
    - secure: "encrypted_string_here"

# This decrypts to something like:
# API_KEY=secret_value

# GitHub Actions - Create as repository secret
env:
  API_KEY: ${{ secrets.API_KEY }}
```

### Multiple Encrypted Variables

```yaml
# Travis CI
env:
  global:
    - secure: "encrypted_api_key"
    - secure: "encrypted_db_password"
    - secure: "encrypted_deploy_token"

# GitHub Actions - Each as separate secret
env:
  API_KEY: ${{ secrets.API_KEY }}
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
  DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

## Environment Variable Patterns

### Global Environment Variables

```yaml
# Travis CI
env:
  global:
    - NODE_ENV=production
    - API_VERSION=v2
    - LOG_LEVEL=info

# GitHub Actions - Workflow-level env
env:
  NODE_ENV: production
  API_VERSION: v2
  LOG_LEVEL: info

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo $NODE_ENV
```

### Matrix Environment Variables

```yaml
# Travis CI
env:
  - TEST_SUITE=unit
  - TEST_SUITE=integration
  - TEST_SUITE=e2e

# GitHub Actions - Matrix strategy
strategy:
  matrix:
    test-suite: [unit, integration, e2e]

env:
  TEST_SUITE: ${{ matrix.test-suite }}

steps:
  - run: npm run test:${{ matrix.test-suite }}
```

### Combined Global and Matrix Variables

```yaml
# Travis CI
env:
  global:
    - API_ENDPOINT=https://api.example.com
    - TIMEOUT=30
  matrix:
    - NODE_ENV=development
    - NODE_ENV=production

# GitHub Actions
env:
  API_ENDPOINT: https://api.example.com
  TIMEOUT: 30

strategy:
  matrix:
    node-env: [development, production]

steps:
  - run: echo "Env: ${{ matrix.node-env }}"
    env:
      NODE_ENV: ${{ matrix.node-env }}
```

## Secret Migration Patterns

### Pattern 1: API Keys and Tokens

```yaml
# Travis CI
env:
  global:
    - secure: "encrypted_github_token"
    - secure: "encrypted_npm_token"
    - secure: "encrypted_docker_token"

# GitHub Actions
# Create secrets in repository settings:
# - GITHUB_TOKEN (automatically provided)
# - NPM_TOKEN
# - DOCKER_TOKEN

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Publish to npm
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: |
          echo "//registry.npmjs.org/:_authToken=$NPM_TOKEN" > .npmrc
          npm publish

      - name: Docker login
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}
```

### Pattern 2: Database Credentials

```yaml
# Travis CI
env:
  global:
    - secure: "encrypted_db_host"
    - secure: "encrypted_db_user"
    - secure: "encrypted_db_password"

# GitHub Actions
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_HOST: ${{ secrets.DB_HOST }}
      DATABASE_USER: ${{ secrets.DB_USER }}
      DATABASE_PASSWORD: ${{ secrets.DB_PASSWORD }}

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: ${{ secrets.DB_USER }}
          POSTGRES_PASSWORD: ${{ secrets.DB_PASSWORD }}
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

### Pattern 3: Cloud Provider Credentials

```yaml
# Travis CI - AWS
env:
  global:
    - secure: "encrypted_aws_access_key_id"
    - secure: "encrypted_aws_secret_access_key"

# GitHub Actions
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1

- run: aws s3 ls
```

### Pattern 4: SSH Keys

```yaml
# Travis CI
before_deploy:
  - openssl aes-256-cbc -K $encrypted_key -iv $encrypted_iv -in deploy_key.enc -out deploy_key -d
  - chmod 600 deploy_key
  - eval $(ssh-agent -s)
  - ssh-add deploy_key

# GitHub Actions
- name: Setup SSH
  env:
    SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
  run: |
    mkdir -p ~/.ssh
    echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -H ${{ secrets.DEPLOY_HOST }} >> ~/.ssh/known_hosts

- name: Deploy
  run: |
    ssh user@${{ secrets.DEPLOY_HOST }} 'bash deploy.sh'
```

## Deployment Secret Patterns

### Heroku Deployment

```yaml
# Travis CI
deploy:
  provider: heroku
  api_key:
    secure: "encrypted_heroku_api_key"
  app: my-app

# GitHub Actions
- uses: akhileshns/heroku-deploy@v3.13.15
  with:
    heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
    heroku_app_name: my-app
    heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

### GitHub Releases

```yaml
# Travis CI
deploy:
  provider: releases
  api_key:
    secure: "encrypted_github_token"
  file: release.zip

# GitHub Actions
- uses: softprops/action-gh-release@v1
  with:
    files: release.zip
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Docker Hub

```yaml
# Travis CI
env:
  global:
    - secure: "encrypted_docker_username"
    - secure: "encrypted_docker_password"

script:
  - docker build -t myapp .
  - echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  - docker push myapp

# GitHub Actions
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_TOKEN }}

- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myapp:latest
```

## Environment-Specific Secrets

### Development vs Production

```yaml
# Travis CI - Using branch conditions
env:
  global:
    - secure: "dev_api_key"    # Used on develop branch
    - secure: "prod_api_key"   # Used on main branch

script:
  - |
    if [ "$TRAVIS_BRANCH" = "main" ]; then
      export API_KEY=$PROD_API_KEY
    else
      export API_KEY=$DEV_API_KEY
    fi

# GitHub Actions - Using environments
jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: development
    steps:
      - uses: actions/checkout@v4
      - run: deploy.sh
        env:
          API_KEY: ${{ secrets.API_KEY }}  # development API_KEY

  deploy-prod:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: deploy.sh
        env:
          API_KEY: ${{ secrets.API_KEY }}  # production API_KEY
```

## Secret Naming Conventions

### Travis CI to GitHub Actions Mapping

| Travis CI Pattern               | GitHub Actions Pattern     | Type     |
| ------------------------------- | -------------------------- | -------- |
| `secure: "..."` for API_KEY     | `API_KEY`                  | Secret   |
| `secure: "..."` for DB_PASSWORD | `DB_PASSWORD`              | Secret   |
| `NODE_ENV=production`           | `NODE_ENV`                 | Variable |
| `API_ENDPOINT=https://...`      | `API_ENDPOINT`             | Variable |
| Branch-specific secure vars     | Environment-scoped secrets | Secret   |
| Build matrix env vars           | Matrix variables           | Variable |

### Recommended Naming

```yaml
# Secrets (sensitive data)
secrets:
  - API_KEY
  - DATABASE_PASSWORD
  - DEPLOY_TOKEN
  - SSH_PRIVATE_KEY
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - DOCKER_HUB_TOKEN
  - HEROKU_API_KEY
  - SLACK_WEBHOOK_URL
  - NPM_TOKEN

# Variables (non-sensitive configuration)
variables:
  - NODE_ENV
  - API_ENDPOINT
  - API_VERSION
  - BUILD_CONFIGURATION
  - LOG_LEVEL
  - TIMEOUT_SECONDS
  - MAX_RETRIES
```

## Organization vs Repository Secrets

### Organization-Level Secrets

Use for credentials shared across multiple repositories:

```yaml
# Shared across all repositories in organization
# - DOCKER_HUB_USERNAME
# - DOCKER_HUB_TOKEN
# - NPM_TOKEN (for publishing)
# - SLACK_WEBHOOK_URL
# - SONAR_TOKEN

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}  # Org secret
          password: ${{ secrets.DOCKER_HUB_TOKEN }}      # Org secret
```

### Repository-Level Secrets

Use for project-specific credentials:

```yaml
# Project-specific secrets
# - DATABASE_PASSWORD
# - API_SECRET_KEY
# - DEPLOYMENT_TOKEN
# - SSH_PRIVATE_KEY

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: deploy.sh
        env:
          DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}  # Repo secret
          API_SECRET_KEY: ${{ secrets.API_SECRET_KEY }}        # Repo secret
```

## Converting Travis Encrypted Files

### Encrypted File Pattern

```yaml
# Travis CI - Encrypted file
before_install:
  - openssl aes-256-cbc -K $encrypted_12345_key -iv $encrypted_12345_iv
    -in secrets.json.enc -out secrets.json -d

script:
  - cat secrets.json
  - ./deploy.sh

# GitHub Actions - File content as secret
steps:
  - name: Create secrets file
    env:
      SECRETS_JSON: ${{ secrets.SECRETS_JSON }}
    run: |
      echo "$SECRETS_JSON" > secrets.json
      chmod 600 secrets.json

  - run: cat secrets.json
  - run: ./deploy.sh

  - name: Cleanup
    if: always()
    run: rm -f secrets.json
```

## Security Best Practices

### 1. Least Privilege Access

```yaml
# Use environment protection for sensitive deployments
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Requires approval
    permissions:
      contents: read
      deployments: write
    steps:
      - uses: actions/checkout@v4
      - run: deploy.sh
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

### 2. Secret Rotation

```yaml
# Document secret rotation schedule in README
# Required Secrets and Rotation Schedule:
# - API_TOKEN: Rotate every 90 days
# - DATABASE_PASSWORD: Rotate every 60 days
# - SSH_PRIVATE_KEY: Rotate on team changes
# - DEPLOY_TOKENS: Rotate after each release
```

### 3. Avoid Logging Secrets

```yaml
# Bad - Secret may appear in logs
- run: echo "API_KEY=${{ secrets.API_KEY }}"

# Good - Use secret in environment
- run: |
    # API_KEY is available but not logged
    curl -H "Authorization: Bearer $API_KEY" https://api.example.com
  env:
    API_KEY: ${{ secrets.API_KEY }}
```

### 4. Mask Additional Values

```yaml
# Mask custom values in logs
- name: Mask additional values
  run: |
    echo "::add-mask::${{ secrets.CUSTOM_VALUE }}"
    echo "Processing with custom value"
```

## Migration Checklist

When migrating Travis CI encrypted variables and environment variables:

- [ ] Identify all `secure:` encrypted variables in `.travis.yml`
- [ ] Document what each encrypted variable contains
- [ ] Determine scope: organization, repository, or environment-specific
- [ ] Create equivalent secrets in GitHub (Settings → Secrets and variables → Actions)
- [ ] Convert environment variables to GitHub Variables for non-sensitive data
- [ ] Update workflow files to reference secrets with `${{ secrets.* }}`
- [ ] Use variables with `${{ vars.* }}` for non-sensitive configuration
- [ ] Test secret access in non-production environment first
- [ ] Document all required secrets in the migration Pull Request
- [ ] Set up environment protection rules for production deployments
- [ ] Remove or archive Travis CI encrypted variables after migration
- [ ] Update team documentation with new secret management process
- [ ] Implement secret rotation schedule

## Common Patterns

### Pattern: Code Coverage Reporting

```yaml
# Travis CI
env:
  global:
    - secure: "encrypted_codecov_token"

after_success:
  - bash <(curl -s https://codecov.io/bash)

# GitHub Actions
- uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage/coverage.xml
```

### Pattern: Slack Notifications

```yaml
# Travis CI
notifications:
  slack:
    rooms:
      - secure: "encrypted_slack_webhook"

# GitHub Actions
- uses: slackapi/slack-github-action@v1
  if: always()
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Build ${{ job.status }}: ${{ github.workflow }}",
        "color": "${{ job.status == 'success' && 'good' || 'danger' }}"
      }
```

### Pattern: Multi-Stage Deployment

```yaml
# Travis CI
stages:
  - test
  - name: deploy-staging
    if: branch = develop
  - name: deploy-production
    if: branch = main AND type = push

# GitHub Actions
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  deploy-staging:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - run: deploy-staging.sh
        env:
          STAGING_API_KEY: ${{ secrets.STAGING_API_KEY }}

  deploy-production:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - run: deploy-production.sh
        env:
          PRODUCTION_API_KEY: ${{ secrets.PRODUCTION_API_KEY }}
```

## Troubleshooting

### Issue: Secret Not Available in Workflow

**Solution**: Verify secret is created at correct scope (repository/organization/environment)

### Issue: Secret Value Has Special Characters

**Solution**: Use base64 encoding or ensure proper escaping in shell scripts

### Issue: Need Different Secrets Per Environment

**Solution**: Use GitHub Environments with environment-specific secrets

### Issue: Secret Appears in Logs

**Solution**: Use `::add-mask::` or avoid echoing variables that contain secrets

### Issue: Deployment Provider Credentials

**Solution**: Check marketplace for official actions that handle authentication securely
