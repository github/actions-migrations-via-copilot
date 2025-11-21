````markdown
# Bamboo to GitHub Actions Mapping Guide

This guide provides a mapping of common Bamboo build plan and deployment project syntax and configurations to their equivalent GitHub Actions. Use this as a reference when migrating your CI/CD pipelines from Bamboo to GitHub Actions.

## Common Commands Mapping

| Bamboo Concept         | GitHub Actions Equivalent                             | Description                     |
| ---------------------- | ----------------------------------------------------- | ------------------------------- |
| `plan:`                | `name:` + `jobs:`                                     | Top-level build plan definition |
| `stages:`              | `jobs:` with `needs:`                                 | Multi-stage build structure     |
| `jobs:`                | `jobs:` (job level)                                   | Build jobs within stages        |
| `tasks:`               | `steps:`                                              | Individual tasks within a job   |
| `triggers:`            | `on:`                                                 | Event triggers for pipeline     |
| `triggers: polling:`   | `on: push:` or `on: schedule:`                        | Repository polling triggers     |
| `triggers: manual:`    | `workflow_dispatch:`                                  | Manual trigger                  |
| `requirements:`        | `runs-on:`                                            | Agent capability requirements   |
| `variables:`           | `env:` and secrets/variables                          | Global and plan variables       |
| `artifact-definition:` | `actions/upload-artifact@v4`                          | Artifact publishing             |
| `artifact-download:`   | `actions/download-artifact@v4`                        | Artifact consumption            |
| `dependencies:`        | `needs:`                                              | Plan dependencies               |
| `script:`              | `run:`                                                | Inline script execution         |
| `deployment-project:`  | `jobs:` with `environment:`                           | Deployment projects             |
| `environments:`        | `environment:`                                        | Deployment environments         |
| `notifications:`       | GitHub Actions notifications or third-party actions   | Build notifications             |
| `branches:`            | `on: push: branches:`                                 | Branch filters                  |
| `repository:`          | Handled by `actions/checkout@v4`                      | Repository configuration        |
| `docker:`              | `container:` or Docker actions                        | Docker integration              |
| `permissions:`         | `permissions:`                                        | Repository permissions          |
| `test-results:`        | Test reporter actions or `actions/upload-artifact@v4` | Test result parsing             |
| `quarantine:`          | Custom test handling logic                            | Test quarantine functionality   |
| `expiry-period:`       | Artifact retention policies                           | Artifact retention              |
| `labels:`              | Environment or job tags                               | Build categorization            |
| `branches: pattern:`   | `on: push: branches:` with glob patterns              | Branch pattern matching         |
| `enabled:`             | Workflow enablement or conditional execution          | Enable/disable builds           |
| `suspended:`           | Workflow suspension or `if: false`                    | Suspend builds                  |
| `clean-working-dir:`   | Default behavior or explicit `run: rm -rf`            | Clean working directory         |
| `shared-credentials:`  | Organization or repository secrets                    | Shared credential management    |
| `final-tasks:`         | Steps with `if: always()`                             | Tasks that always run           |
| `other-repositories:`  | Multiple `actions/checkout@v4` steps                  | Multiple repository checkouts   |
| `other-branches:`      | Branch-specific checkout configurations               | Alternative branch checkouts    |
| `remote-triggers:`     | Repository dispatch or webhook triggers               | Remote build triggers           |
| `build-hanging:`       | Workflow timeout settings                             | Build timeout detection         |
| `build-queue-timeout:` | Job concurrency and queue management                  | Build queue timeout             |
| `custom-expiry:`       | Artifact retention policies                           | Custom artifact expiry          |

## Bamboo Tasks to GitHub Actions Mapping

| Bamboo Task               | GitHub Actions Equivalent                         | Notes                         |
| ------------------------- | ------------------------------------------------- | ----------------------------- |
| `script`                  | `run:`                                            | Shell script execution        |
| `checkout`                | `actions/checkout@v4`                             | Source code checkout          |
| `npm`                     | `actions/setup-node@v4` + `run: npm`              | NPM commands                  |
| `maven`                   | `actions/setup-java@v4` + `run: mvn`              | Maven commands                |
| `gradle`                  | `actions/setup-java@v4` + `run: gradle`           | Gradle commands               |
| `docker`                  | `docker/build-push-action@v5`                     | Docker build and push         |
| `scp`                     | `appleboy/scp-action@v0.1.7`                      | SCP file transfer             |
| `ssh`                     | `appleboy/ssh-action@v1.0.3`                      | SSH remote execution          |
| `ant`                     | `run: ant`                                        | Ant build tool                |
| `nant`                    | `run: nant`                                       | NAnt build tool               |
| `msbuild`                 | `microsoft/setup-msbuild@v1` + `run: msbuild`     | MSBuild                       |
| `command`                 | `run:`                                            | Arbitrary command execution   |
| `clean-working-directory` | `run: git clean -ffdx` or default behavior        | Clean workspace               |
| `vcs-tag`                 | `run: git tag` commands                           | VCS tagging                   |
| `inject-variables`        | `env:` or output variables                        | Variable injection            |
| `deploy-plugin`           | Equivalent deployment actions                     | Deployment tasks              |
| `heroku-deploy`           | `akhileshns/heroku-deploy@v3.13.15`               | Heroku deployment             |
| `aws-elastic-beanstalk`   | `einaregilsson/beanstalk-deploy@v21`              | AWS Elastic Beanstalk         |
| `junit-parser`            | `EnricoMi/publish-unit-test-result-action@v2`     | JUnit test result parsing     |
| `testng-parser`           | Test reporter actions                             | TestNG test result parsing    |
| `mocha-test-parser`       | `dorny/test-reporter@v1`                          | Mocha test result parsing     |
| `nunit-parser`            | Test reporter actions                             | NUnit test result parsing     |
| `phpunit-parser`          | Test reporter actions                             | PHPUnit test result parsing   |
| `sonar-runner`            | `SonarSource/sonarcloud-github-action@v2`         | SonarQube/SonarCloud analysis |
| `code-coverage`           | `codecov/codecov-action@v4`                       | Code coverage reporting       |
| `slack-notification`      | `slackapi/slack-github-action@v1`                 | Slack notifications           |
| `email-notification`      | GitHub Actions built-in or third-party            | Email notifications           |
| `hipchat-notification`    | Slack or Teams equivalent                         | HipChat replacement           |
| `jira-integration`        | `atlassian/gajira-*` actions                      | JIRA integration              |
| `compress-artifact`       | `run: tar/zip` + `actions/upload-artifact@v4`     | Artifact compression          |
| `download-item`           | `run: curl/wget`                                  | Download external files       |
| `rest-api-call`           | `run: curl` or `fjogeleit/http-request-action`    | REST API interaction          |
| `windows-script`          | `run:` with `shell: pwsh` or `cmd`                | Windows-specific scripts      |
| `powershell`              | `run:` with `shell: pwsh`                         | PowerShell execution          |
| `remote-agent`            | Self-hosted runners                               | Remote agent capabilities     |
| `elastic-bamboo`          | GitHub-hosted runners or cloud runners            | Elastic agent capacity        |
| `parallel-test-execution` | `strategy: matrix:`                               | Parallel test execution       |
| `build-artifact`          | `actions/upload-artifact@v4`                      | Build artifact publishing     |
| `deploy-artifact`         | `actions/download-artifact@v4` + deploy           | Artifact deployment           |
| `parse-test-results`      | Test reporter actions                             | Test result parsing           |
| `publish-coverage`        | `codecov/codecov-action@v4`                       | Code coverage publishing      |
| `database-migration`      | Database-specific actions or run commands         | Database migrations           |
| `kubernetes-deploy`       | `azure/k8s-deploy@v4` or kubectl commands         | Kubernetes deployment         |
| `terraform`               | `hashicorp/setup-terraform@v3` + `run: terraform` | Terraform infrastructure      |
| `ansible`                 | `run: ansible-playbook`                           | Ansible automation            |

## Configuration Examples

### Basic Build Plan Structure

**Bamboo (bamboo-specs):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Build Stage
    jobs:
      - name: Build Job
        tasks:
          - script:
              interpreter: SHELL
              scripts:
                - npm install
                - npm run build
```

**GitHub Actions:**
```yaml
name: My Project Build

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '16'

      - name: Install and Build
        run: |
          npm install
          npm run build
```

### Multi-Stage Build Plan with Dependencies

**Bamboo (bamboo-specs):**
```yaml
plan:
  key: MYPROJECT-CI
  name: My Project CI

stages:
  - name: Build
    jobs:
      - name: Compile
        tasks:
          - script:
              scripts:
                - echo "Building..."

  - name: Test
    jobs:
      - name: Run Tests
        tasks:
          - script:
              scripts:
                - echo "Testing..."

  - name: Package
    jobs:
      - name: Create Artifacts
        tasks:
          - script:
              scripts:
                - echo "Packaging..."
```

**GitHub Actions:**
```yaml
name: My Project CI

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Building..."

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - run: echo "Testing..."

  package:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - run: echo "Packaging..."
```

### Plan Dependencies

**Bamboo (plan dependencies):**
```yaml
plan:
  key: MYPROJECT-DEPLOY
  name: My Project Deployment

dependencies:
  - plan: MYPROJECT-BUILD

stages:
  - name: Deploy
    jobs:
      - name: Deploy to Production
        tasks:
          - script:
              scripts:
                - echo "Deploying..."
```

**GitHub Actions:**
```yaml
name: My Project Deployment

on:
  workflow_run:
    workflows: ["My Project Build"]
    types:
      - completed
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - uses: actions/checkout@v4
      - run: echo "Deploying..."
```

### Global Variables and Secrets

**Bamboo (bamboo-specs):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

variables:
  API_ENDPOINT: https://api.example.com
  BUILD_CONFIG: release

stages:
  - name: Build
    jobs:
      - name: Build Job
        tasks:
          - script:
              scripts:
                - echo "API: ${bamboo.API_ENDPOINT}"
                - echo "Config: ${bamboo.BUILD_CONFIG}"
                - echo "Secret: ${bamboo.SECRET_KEY}"
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
          echo "API: $API_ENDPOINT"
          echo "Config: $BUILD_CONFIGURATION"
          echo "Secret: ${{ secrets.SECRET_KEY }}"
```

### Repository Polling and Triggers

**Bamboo (repository polling):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

triggers:
  - polling:
      period: 180  # 3 minutes
  - manual: {}
  - remote: {}
```

**GitHub Actions:**
```yaml
name: My Project Build

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:  # Manual trigger
  repository_dispatch:  # Remote trigger
```

### Artifact Handling

**Bamboo (artifact definition):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Build
    jobs:
      - name: Build Job
        artifacts:
          - name: build-artifacts
            pattern: "dist/**/*"
            shared: true
            required: true
        tasks:
          - script:
              scripts:
                - npm run build

  - name: Deploy
    jobs:
      - name: Deploy Job
        tasks:
          - artifact-download:
              source: build-artifacts
              destination: artifacts/
          - script:
              scripts:
                - echo "Deploying artifacts..."
```

**GitHub Actions:**
```yaml
name: My Project Build and Deploy

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: build-artifacts
          path: dist/
          retention-days: 5

  deploy:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-artifacts
          path: artifacts/

      - name: Deploy
        run: echo "Deploying artifacts..."
```

### Deployment Projects

**Bamboo (deployment project):**
```yaml
deployment-project:
  key: MYPROJECT-DEPLOY
  name: My App Deployment

source-plan: MYPROJECT-BUILD

environments:
  - name: Production
    triggers:
      - manual: {}
    tasks:
      - script:
          scripts:
            - echo "Deploying to production..."
            - ./deploy.sh production
```

**GitHub Actions:**
```yaml
name: Production Deployment

on:
  workflow_dispatch:  # Manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Production
        run: |
          echo "Deploying to production..."
          ./deploy.sh production
```

### Agent Capabilities and Requirements

**Bamboo (agent requirements):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

stages:
  - name: Build
    jobs:
      - name: Build Job
        requirements:
          - system.builder.command.Docker: exists
          - os: Linux
        tasks:
          - script:
              scripts:
                - docker build -t myapp .
```

**GitHub Actions:**
```yaml
name: My Project Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest  # Linux with Docker pre-installed
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker Image
        run: docker build -t myapp .
```

### Test Result Parsing

**Bamboo (test result parsing):**
```yaml
plan:
  key: MYPROJECT-TEST
  name: My Project Tests

stages:
  - name: Test
    jobs:
      - name: Run Tests
        tasks:
          - script:
              scripts:
                - npm test
        test-results:
          - junit:
              pattern: "**/test-results/*.xml"
          - quarantine:
              enabled: true
```

**GitHub Actions:**
```yaml
name: My Project Tests

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Tests
        run: npm test

      - uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: '**/test-results/*.xml'
```

### Notifications

**Bamboo (notification configuration):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

notifications:
  - recipients:
      - hipchat:
          room: "Build Notifications"
    events:
      - plan-failed
      - plan-completed
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
      - run: npm run build

      - name: Notify on Failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "Build failed: ${{ github.repository }} - ${{ github.sha }}"
            }
```

### Docker Integration

**Bamboo (Docker task):**
```yaml
plan:
  key: MYPROJECT-DOCKER
  name: Docker Build

stages:
  - name: Build
    jobs:
      - name: Docker Build
        tasks:
          - docker:
              image: myapp
              tag: latest
              dockerfile: Dockerfile
              repository: myrepo/myapp
```

**GitHub Actions:**
```yaml
name: Docker Build

on: [push]

jobs:
  build:
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
          file: ./Dockerfile
          push: true
          tags: myrepo/myapp:latest
```

### Branch Patterns

**Bamboo (branch configuration):**
```yaml
plan:
  key: MYPROJECT-BUILD
  name: My Project Build

branches:
  create: for-pull-request
  delete:
    after-deleted-days: 7
    after-inactive-days: 30

  integration:
    merge-from: main
    push-on-success: false
```

**GitHub Actions:**
```yaml
name: My Project Build

on:
  push:
    branches:
      - main
      - 'release/**'
  pull_request:
    branches:
      - main
```

## Agent Requirements to Runner Mapping

| Bamboo Agent Requirement        | GitHub Actions Runner       | Notes                 |
| ------------------------------- | --------------------------- | --------------------- |
| `system.builder.command.Docker` | `runs-on: ubuntu-latest`    | Docker pre-installed  |
| `system.builder.node.Node`      | `actions/setup-node@v4`     | Node.js setup         |
| `system.builder.mvn3.Maven`     | `actions/setup-java@v4`     | Maven setup with Java |
| `system.builder.gradle.Gradle`  | `actions/setup-java@v4`     | Gradle with Java      |
| `os: Linux`                     | `runs-on: ubuntu-latest`    | Linux environment     |
| `os: Windows`                   | `runs-on: windows-latest`   | Windows environment   |
| `os: Mac`                       | `runs-on: macos-latest`     | macOS environment     |
| Custom capability               | Self-hosted runner or setup | Custom requirements   |

## Built-in Variables Mapping

| Bamboo Variable                              | GitHub Actions Equivalent  |
| -------------------------------------------- | -------------------------- |
| `${bamboo.buildNumber}`                      | `${{ github.run_number }}` |
| `${bamboo.buildKey}`                         | `${{ github.run_id }}`     |
| `${bamboo.planKey}`                          | `${{ github.workflow }}`   |
| `${bamboo.planName}`                         | `${{ github.workflow }}`   |
| `${bamboo.buildResultKey}`                   | `${{ github.run_id }}`     |
| `${bamboo.shortPlanName}`                    | `${{ github.workflow }}`   |
| `${bamboo.shortJobName}`                     | `${{ github.job }}`        |
| `${bamboo.planRepository.name}`              | `${{ github.repository }}` |
| `${bamboo.planRepository.revision}`          | `${{ github.sha }}`        |
| `${bamboo.planRepository.branch}`            | `${{ github.ref_name }}`   |
| `${bamboo.planRepository.branchName}`        | `${{ github.ref_name }}`   |
| `${bamboo.repository.git.branch}`            | `${{ github.ref_name }}`   |
| `${bamboo.repository.git.username}`          | `${{ github.actor }}`      |
| `${bamboo.agentId}`                          | `${{ runner.name }}`       |
| `${bamboo.build.working.directory}`          | `${{ github.workspace }}`  |
| `${bamboo.tmp.directory}`                    | `${{ runner.temp }}`       |
| `${bamboo.capability.system.git.executable}` | `git` (pre-installed)      |

## Conditional Execution Mapping

| Bamboo Condition         | GitHub Actions Equivalent             |
| ------------------------ | ------------------------------------- |
| Always run               | `if: always()`                        |
| Run on success           | Default behavior                      |
| Run on failure           | `if: failure()`                       |
| Variable-based condition | `if: env.VAR_NAME == 'value'`         |
| Branch-based condition   | `if: github.ref == 'refs/heads/main'` |
| Manual approval required | `environment:` with protection rules  |

---

*This mapping guide is maintained as part of the CI/CD Migration Knowledge Base.*

````
