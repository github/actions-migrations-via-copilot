# Migrating Contexts and Secrets from CircleCI to GitHub Actions

When migrating CI/CD pipelines from CircleCI to GitHub Actions, properly handling contexts, secrets, and environment variables is critical for security and functionality. This guide outlines the best practices and steps to effectively migrate these configurations.

## Understanding CircleCI Context and Secret Types

CircleCI uses several mechanisms for managing configuration:

1. **Contexts** - Organization-level shared secrets and environment variables
2. **Project Environment Variables** - Project-specific configuration in CircleCI UI
3. **Workflow Environment Variables** - Defined in `.circleci/config.yml`
4. **Job Environment Variables** - Scoped to specific jobs
5. **Built-in Environment Variables** - CircleCI system variables (CIRCLE_*)

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
- API keys and tokens
- Database passwords and connection strings
- Service account credentials
- OAuth tokens
- SSH keys
- Cloud provider credentials
- Any data from CircleCI contexts that is sensitive

### Use GitHub Variables For:
- API endpoints (non-authenticated)
- Build configurations
- Feature flags
- Environment names
- Application version numbers
- Non-sensitive data from CircleCI contexts
- Public configuration values

## CircleCI Contexts to GitHub Secrets and Variables

### Organization-Level Contexts

**CircleCI:**
```yaml
version: 2.1

workflows:
  build-deploy:
    jobs:
      - build:
          context:
            - docker-hub-creds
            - aws-credentials

jobs:
  build:
    docker:
      - image: cimg/node:16.0
    steps:
      - run: |
          echo "Docker user: $DOCKER_USER"
          echo "AWS Region: $AWS_REGION"
```

**GitHub Actions:**
```yaml
name: Build and Deploy

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Docker user: ${{ secrets.DOCKER_USER }}"
          echo "AWS Region: ${{ vars.AWS_REGION }}"
```

### Multiple Contexts

**CircleCI:**
```yaml
workflows:
  deploy:
    jobs:
      - deploy-staging:
          context:
            - staging-context
            - shared-credentials
      - deploy-production:
          context:
            - production-context
            - shared-credentials
```

**GitHub Actions:**
```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: echo "Deploying to staging"
      - run: echo "API Key: ${{ secrets.API_KEY }}"  # staging-scoped
      - run: echo "Shared: ${{ secrets.SHARED_CREDENTIAL }}"  # org-level

  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "Deploying to production"
      - run: echo "API Key: ${{ secrets.API_KEY }}"  # production-scoped
      - run: echo "Shared: ${{ secrets.SHARED_CREDENTIAL }}"  # org-level
```

## Project Environment Variables to GitHub Secrets and Variables

**CircleCI (set in UI):**
```yaml
jobs:
  build:
    docker:
      - image: cimg/node:16.0
    steps:
      - run: |
          echo "Build config: $BUILD_CONFIGURATION"
          echo "API endpoint: $API_ENDPOINT"
          echo "Secret key: $SECRET_KEY"
```

**GitHub Actions:**
```yaml
env:
  BUILD_CONFIGURATION: ${{ vars.BUILD_CONFIGURATION }}
  API_ENDPOINT: ${{ vars.API_ENDPOINT }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Build config: $BUILD_CONFIGURATION"
          echo "API endpoint: $API_ENDPOINT"
          echo "Secret key: ${{ secrets.SECRET_KEY }}"
```

## Workflow and Job Environment Variables

**CircleCI:**
```yaml
version: 2.1

workflows:
  build:
    jobs:
      - build-job

jobs:
  build-job:
    docker:
      - image: cimg/node:16.0
    environment:
      NODE_ENV: production
      LOG_LEVEL: info
    steps:
      - run: npm run build
```

**GitHub Actions:**
```yaml
jobs:
  build-job:
    runs-on: ubuntu-latest
    env:
      NODE_ENV: production
      LOG_LEVEL: info
    steps:
      - run: npm run build
```

## Built-in Variables Migration

**CircleCI:**
```yaml
steps:
  - run: |
      echo "Build number: $CIRCLE_BUILD_NUM"
      echo "Branch: $CIRCLE_BRANCH"
      echo "Commit: $CIRCLE_SHA1"
      echo "Repository: $CIRCLE_PROJECT_REPONAME"
      echo "User: $CIRCLE_USERNAME"
```

**GitHub Actions:**
```yaml
steps:
  - run: |
      echo "Build number: ${{ github.run_number }}"
      echo "Branch: ${{ github.ref_name }}"
      echo "Commit: ${{ github.sha }}"
      echo "Repository: ${{ github.event.repository.name }}"
      echo "User: ${{ github.actor }}"
```

## Service Credentials (Docker, AWS, etc.)

### Docker Hub Credentials

**CircleCI:**
```yaml
jobs:
  build:
    docker:
      - image: cimg/base:current
        auth:
          username: $DOCKER_USER
          password: $DOCKER_PASS
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USER }}
          password: ${{ secrets.DOCKER_PASS }}
```

### AWS Credentials

**CircleCI:**
```yaml
jobs:
  deploy:
    docker:
      - image: cimg/aws:latest
    steps:
      - run: |
          aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
          aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
          aws s3 sync ./build s3://my-bucket
```

**GitHub Actions:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ vars.AWS_REGION }}

      - run: aws s3 sync ./build s3://my-bucket
```

## SSH Keys

**CircleCI:**
```yaml
jobs:
  deploy:
    steps:
      - add_ssh_keys:
          fingerprints:
            - "SO:ME:FIN:G:ER:PR:IN:T"
      - run: ssh user@server "deploy-script.sh"
```

**GitHub Actions:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}

      - run: ssh user@server "deploy-script.sh"
```

## Environment-Specific Configuration

**CircleCI:**
```yaml
workflows:
  deploy:
    jobs:
      - deploy:
          filters:
            branches:
              only: development
          context: dev-context
      - deploy:
          filters:
            branches:
              only: staging
          context: staging-context
      - deploy:
          filters:
            branches:
              only: main
          context: production-context
```

**GitHub Actions:**
```yaml
jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/development'
    environment: dev
    steps:
      - run: echo "Deploying to dev with ${{ secrets.API_KEY }}"

  deploy-staging:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'
    environment: staging
    steps:
      - run: echo "Deploying to staging with ${{ secrets.API_KEY }}"

  deploy-production:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - run: echo "Deploying to production with ${{ secrets.API_KEY }}"
```

## Conditional Secrets Access

**CircleCI:**
```yaml
steps:
  - run:
      name: Conditional deployment
      command: |
        if [ "$CIRCLE_BRANCH" == "main" ]; then
          echo "Using production credentials"
          ./deploy.sh --key $PROD_API_KEY
        else
          echo "Using dev credentials"
          ./deploy.sh --key $DEV_API_KEY
        fi
```

**GitHub Actions:**
```yaml
steps:
  - name: Conditional deployment
    run: |
      if [ "${{ github.ref_name }}" == "main" ]; then
        echo "Using production credentials"
        ./deploy.sh --key ${{ secrets.PROD_API_KEY }}
      else
        echo "Using dev credentials"
        ./deploy.sh --key ${{ secrets.DEV_API_KEY }}
      fi
```

## Secret Naming Conventions

When migrating, consider standardizing secret names:

| CircleCI Context Variable | GitHub Actions Name     | Type     |
| ------------------------- | ----------------------- | -------- |
| `DOCKER_USER`             | `DOCKER_USER`           | Secret   |
| `DOCKER_PASS`             | `DOCKER_PASS`           | Secret   |
| `AWS_ACCESS_KEY_ID`       | `AWS_ACCESS_KEY_ID`     | Secret   |
| `AWS_SECRET_ACCESS_KEY`   | `AWS_SECRET_ACCESS_KEY` | Secret   |
| `API_ENDPOINT`            | `API_ENDPOINT`          | Variable |
| `BUILD_ENV`               | `BUILD_ENV`             | Variable |
| `SLACK_WEBHOOK`           | `SLACK_WEBHOOK`         | Secret   |

**Best Practice:** Use UPPER_SNAKE_CASE for consistency with environment variable conventions.

---

*For security best practices, migration checklists, troubleshooting guidance, and additional resources, refer to [Migration Guardrails](docs/migration-guardrails.md) and [Migration Standards](docs/migration-standards.md) in the knowledge base.*
