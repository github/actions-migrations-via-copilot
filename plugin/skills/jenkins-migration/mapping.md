# Jenkins to GitHub Actions Mapping Guide

This guide provides comprehensive mappings for converting Jenkins pipeline syntax (both declarative and scripted) to GitHub Actions workflows.

## Pipeline Structure Mappings

### Declarative Pipeline Structure

| Jenkins Declarative | GitHub Actions                    | Notes                             |
| ------------------- | --------------------------------- | --------------------------------- |
| `pipeline { }`      | `name:` + `on:` + `jobs:`         | Top-level workflow structure      |
| `agent { }`         | `runs-on:`                        | Runner/agent specification        |
| `stages { }`        | `jobs:`                           | Collection of stages becomes jobs |
| `stage('name') { }` | `job_name:`                       | Individual stage becomes a job    |
| `steps { }`         | `steps:`                          | Steps within a job                |
| `post { }`          | `if: always()` or job conclusions | Post-build actions                |
| `environment { }`   | `env:`                            | Environment variables             |
| `options { }`       | Workflow/job settings             | Timeout, retry, etc.              |
| `parameters { }`    | `workflow_dispatch.inputs:`       | Manual trigger parameters         |
| `triggers { }`      | `on:`                             | Workflow triggers                 |
| `tools { }`         | Setup actions                     | Tool installations                |
| `when { }`          | `if:`                             | Conditional execution             |

### Scripted Pipeline Structure

| Jenkins Scripted          | GitHub Actions                         | Notes                 |
| ------------------------- | -------------------------------------- | --------------------- |
| `node('label') { }`       | `runs-on: label`                       | Node allocation       |
| `node { }`                | `runs-on: ubuntu-latest`               | Default node          |
| `stage('name') { }`       | Job with `name:`                       | Stage definition      |
| `parallel { }`            | Multiple jobs without `needs:`         | Parallel execution    |
| `try { } catch { }`       | `continue-on-error:` + `if: failure()` | Error handling        |
| `timeout(time: X) { }`    | `timeout-minutes: X`                   | Timeout configuration |
| `retry(X) { }`            | Custom retry logic with `if:`          | Retry on failure      |
| `dir('path') { }`         | `working-directory:`                   | Working directory     |
| `withEnv([]) { }`         | `env:`                                 | Environment variables |
| `withCredentials([]) { }` | `env:` with `secrets.*`                | Credential binding    |

## Agent and Node Mappings

### Agent Specifications

| Jenkins Agent                          | GitHub Actions Runner                     | Notes                    |
| -------------------------------------- | ----------------------------------------- | ------------------------ |
| `agent any`                            | `runs-on: ubuntu-latest`                  | Default runner           |
| `agent { label 'linux' }`              | `runs-on: ubuntu-latest`                  | Linux runner             |
| `agent { label 'windows' }`            | `runs-on: windows-latest`                 | Windows runner           |
| `agent { label 'macos' }`              | `runs-on: macos-latest`                   | macOS runner             |
| `agent { docker { image 'node:16' } }` | `container: { image: 'node:16' }`         | Container execution      |
| `agent { dockerfile true }`            | `docker/build-push-action` + `container:` | Build and use Dockerfile |
| `agent none`                           | No `runs-on:` at workflow level           | Job-level runners only   |

### Node Labels

```groovy
// Jenkins Scripted
node('maven-slave') {
    // Build steps
}

// GitHub Actions
jobs:
  build:
    runs-on: ubuntu-latest  # or self-hosted runner with label
```

## Step and Command Mappings

### Common Commands

| Jenkins Step           | GitHub Actions Step                            | Example                 |
| ---------------------- | ---------------------------------------------- | ----------------------- |
| `sh 'command'`         | `run: command`                                 | Shell command           |
| `bat 'command'`        | `run: command` with `shell: cmd`               | Windows batch           |
| `powershell 'command'` | `run: command` with `shell: pwsh`              | PowerShell              |
| `echo 'message'`       | `run: echo "message"`                          | Print message           |
| `pwd()`                | `run: pwd`                                     | Print working directory |
| `checkout scm`         | `uses: actions/checkout@v4`                    | Checkout code           |
| `git url: '...'`       | `uses: actions/checkout@v4` with `repository:` | Checkout specific repo  |
| `deleteDir()`          | `run: rm -rf *`                                | Clean workspace         |
| `dir('path') { }`      | `working-directory: path`                      | Change directory        |
| `sleep time: X`        | `run: sleep X`                                 | Delay execution         |
| `error 'message'`      | `run: exit 1`                                  | Fail the build          |
| `unstable 'message'`   | `continue-on-error: true`                      | Mark as unstable        |

### Build Tool Integration

| Jenkins Step            | GitHub Actions                                     | Notes         |
| ----------------------- | -------------------------------------------------- | ------------- |
| `maven 'clean install'` | `actions/setup-java@v4` + `run: mvn clean install` | Maven build   |
| `gradle 'build'`        | `actions/setup-java@v4` + `run: ./gradlew build`   | Gradle build  |
| `npm 'install'`         | `actions/setup-node@v4` + `run: npm install`       | npm commands  |
| `yarn 'install'`        | `actions/setup-node@v4` + `run: yarn install`      | Yarn commands |
| `docker.build()`        | `docker/build-push-action@v5`                      | Docker build  |
| `docker.withRegistry()` | `docker/login-action@v3`                           | Docker login  |

### Artifact and Test Publishing

| Jenkins Step                          | GitHub Actions Action                  | Notes                  |
| ------------------------------------- | -------------------------------------- | ---------------------- |
| `archiveArtifacts artifacts: '*.jar'` | `actions/upload-artifact@v4`           | Archive artifacts      |
| `junit 'test-results.xml'`            | `dorny/test-reporter@v1`               | JUnit test results     |
| `publishHTML(target: [...])`          | `actions/upload-pages-artifact@v3`     | Publish HTML reports   |
| `stash name: 'build'`                 | `actions/upload-artifact@v4`           | Stash files            |
| `unstash 'build'`                     | `actions/download-artifact@v4`         | Retrieve stashed files |
| `fingerprint '*.jar'`                 | `actions/upload-artifact@v4` with hash | File fingerprinting    |

## Trigger Mappings

### SCM Triggers

| Jenkins Trigger          | GitHub Actions                      | Notes               |
| ------------------------ | ----------------------------------- | ------------------- |
| `pollSCM('H/5 * * * *')` | `on: push:` + `on: pull_request:`   | Automatic on push   |
| `cron('H 2 * * *')`      | `on: schedule: - cron: '0 2 * * *'` | Scheduled builds    |
| No trigger (manual)      | `on: workflow_dispatch:`            | Manual trigger      |
| `upstream(...)`          | `on: workflow_run:`                 | Upstream dependency |
| GitHub webhook           | `on: push:` / `on: pull_request:`   | Default in Actions  |

### Conditional Triggers

```groovy
// Jenkins Declarative
when {
    branch 'main'
}

// GitHub Actions
if: github.ref == 'refs/heads/main'
```

## Conditional Execution

### When Conditions

| Jenkins When                                         | GitHub Actions If                                   | Notes                     |
| ---------------------------------------------------- | --------------------------------------------------- | ------------------------- |
| `when { branch 'main' }`                             | `if: github.ref == 'refs/heads/main'`               | Branch condition          |
| `when { branch pattern: 'release-*' }`               | `if: startsWith(github.ref, 'refs/heads/release-')` | Branch pattern            |
| `when { environment name: 'DEPLOY', value: 'true' }` | `if: env.DEPLOY == 'true'`                          | Environment check         |
| `when { expression { return X == Y } }`              | `if: ${{ env.X == env.Y }}`                         | Expression evaluation     |
| `when { allOf { ... } }`                             | `if: condition1 && condition2`                      | Multiple conditions (AND) |
| `when { anyOf { ... } }`                             | `if: condition1 \|\| condition2`                    | Multiple conditions (OR)  |
| `when { not { ... } }`                               | `if: '!condition'`                                  | Negation                  |
| `when { changeset "src/**" }`                        | `paths: ['src/**']` in trigger                      | File change detection     |
| `when { tag "v*" }`                                  | `if: startsWith(github.ref, 'refs/tags/v')`         | Tag matching              |

## Post-Build Actions

### Post Sections

| Jenkins Post              | GitHub Actions                  | Notes            |
| ------------------------- | ------------------------------- | ---------------- |
| `post { always { } }`     | `if: always()`                  | Always run       |
| `post { success { } }`    | `if: success()`                 | On success       |
| `post { failure { } }`    | `if: failure()`                 | On failure       |
| `post { unstable { } }`   | `if: failure()` or custom logic | On unstable      |
| `post { changed { } }`    | Compare with previous run       | On status change |
| `post { fixed { } }`      | Compare with previous run       | On fixed         |
| `post { regression { } }` | Compare with previous run       | On regression    |
| `post { cleanup { } }`    | Final step with `if: always()`  | Cleanup actions  |

## Parallel Execution

### Declarative Parallel

```groovy
// Jenkins
stage('Parallel Tests') {
    parallel {
        stage('Unit') {
            steps { sh 'npm run test:unit' }
        }
        stage('Integration') {
            steps { sh 'npm run test:integration' }
        }
    }
}

// GitHub Actions
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: npm run test:unit

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - run: npm run test:integration
```

### Scripted Parallel

```groovy
// Jenkins
parallel(
    'Unit': { sh 'npm run test:unit' },
    'Integration': { sh 'npm run test:integration' }
)

// GitHub Actions - same as above
```

## Matrix Builds

```groovy
// Jenkins
matrix {
    axes {
        axis {
            name 'PLATFORM'
            values 'linux', 'windows', 'mac'
        }
        axis {
            name 'NODE_VERSION'
            values '14', '16', '18'
        }
    }
    stages {
        stage('Test') {
            steps {
                sh "node --version"
            }
        }
    }
}

// GitHub Actions
jobs:
  test:
    strategy:
      matrix:
        platform: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [14, 16, 18]
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: node --version
```

## Environment Variables

### Jenkins Environment Variables to GitHub Context

| Jenkins Variable         | GitHub Actions Context                                                                | Notes               |
| ------------------------ | ------------------------------------------------------------------------------------- | ------------------- |
| `${env.BUILD_ID}`        | `${{ github.run_id }}`                                                                | Build/run ID        |
| `${env.BUILD_NUMBER}`    | `${{ github.run_number }}`                                                            | Build number        |
| `${env.BUILD_URL}`       | `${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}` | Build URL           |
| `${env.JOB_NAME}`        | `${{ github.workflow }}`                                                              | Job/workflow name   |
| `${env.WORKSPACE}`       | `${{ github.workspace }}`                                                             | Workspace directory |
| `${env.GIT_COMMIT}`      | `${{ github.sha }}`                                                                   | Commit SHA          |
| `${env.GIT_BRANCH}`      | `${{ github.ref_name }}`                                                              | Branch name         |
| `${env.GIT_URL}`         | `${{ github.server_url }}/${{ github.repository }}`                                   | Repository URL      |
| `${env.BRANCH_NAME}`     | `${{ github.ref_name }}`                                                              | Branch name         |
| `${env.CHANGE_ID}`       | `${{ github.event.pull_request.number }}`                                             | PR number           |
| `${env.CHANGE_AUTHOR}`   | `${{ github.event.pull_request.user.login }}`                                         | PR author           |
| `${env.CHANGE_TARGET}`   | `${{ github.base_ref }}`                                                              | PR target branch    |
| `${env.TAG_NAME}`        | `${{ github.ref_name }}` (when tag)                                                   | Tag name            |
| `${currentBuild.result}` | `${{ job.status }}`                                                                   | Job result          |

## Options and Settings

| Jenkins Option                       | GitHub Actions                     | Notes                    |
| ------------------------------------ | ---------------------------------- | ------------------------ |
| `timeout(time: 30, unit: 'MINUTES')` | `timeout-minutes: 30`              | Job timeout              |
| `retry(3)`                           | Custom retry logic                 | Retry on failure         |
| `timestamps()`                       | Built-in                           | Timestamps always shown  |
| `disableConcurrentBuilds()`          | `concurrency:` group               | Prevent concurrent runs  |
| `buildDiscarder(...)`                | Repository settings                | Retention policy         |
| `skipDefaultCheckout()`              | Omit `actions/checkout`            | Skip checkout            |
| `skipStagesAfterUnstable()`          | `if: success()` on subsequent jobs | Skip on failure          |
| `checkoutToSubdirectory('dir')`      | `actions/checkout` with `path:`    | Checkout to subdirectory |
| `preserveStashes()`                  | Use artifacts                      | Preserve between builds  |

## Input and Parameters

```groovy
// Jenkins
parameters {
    string(name: 'VERSION', defaultValue: '1.0', description: 'Release version')
    choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'])
    booleanParam(name: 'SKIP_TESTS', defaultValue: false)
}

// GitHub Actions
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Release version'
        required: true
        default: '1.0'
      environment:
        description: 'Environment'
        required: true
        type: choice
        options:
          - dev
          - staging
          - prod
      skip-tests:
        description: 'Skip tests'
        required: false
        type: boolean
        default: false
```

## Plugin Replacements

Common Jenkins plugins and their GitHub Actions equivalents:

| Jenkins Plugin           | GitHub Actions Alternative                              |
| ------------------------ | ------------------------------------------------------- |
| Docker Pipeline          | `docker/build-push-action@v5`, `docker/login-action@v3` |
| Kubernetes Plugin        | `azure/k8s-deploy@v4` or kubectl commands               |
| Slack Notification       | `slackapi/slack-github-action@v1`                       |
| Email Extension          | `dawidd6/action-send-mail@v3`                           |
| SonarQube Scanner        | `sonarsource/sonarcloud-github-action@v2`               |
| Artifactory              | `jfrog/setup-jfrog-cli@v3`                              |
| AWS Steps                | `aws-actions/configure-aws-credentials@v4`              |
| Azure CLI                | `azure/cli@v1`                                          |
| Google Cloud SDK         | `google-github-actions/setup-gcloud@v1`                 |
| Terraform                | `hashicorp/setup-terraform@v3`                          |
| Ansible                  | Run ansible-playbook commands                           |
| Performance Plugin       | Custom metrics or third-party actions                   |
| HTML Publisher           | `actions/upload-pages-artifact@v3`                      |
| Cobertura                | `codecov/codecov-action@v4`                             |
| Warnings Next Generation | Various linter actions                                  |

## Service Containers

```groovy
// Jenkins (Docker agent with services)
agent {
    docker {
        image 'maven:3-alpine'
        args '-v /var/run/docker.sock:/var/run/docker.sock'
    }
}

// GitHub Actions
jobs:
  build:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

## Best Practices for Migration

1. **Expand Shared Libraries**: Inline all shared library calls in GitHub Actions workflows
2. **Convert Groovy Logic**: Replace Groovy scripts with shell scripts or marketplace actions
3. **Use Marketplace Actions**: Prefer verified actions over custom scripts
4. **Version Pinning**: Always use specific versions or commit SHAs for actions
5. **Secret Management**: Migrate credentials to GitHub Secrets immediately
6. **Environment Protection**: Set up environment protection rules for deployments
7. **Artifact Management**: Use upload/download artifact actions for file sharing
8. **Caching**: Implement caching for dependencies to improve performance
9. **Matrix Strategy**: Use matrix builds for multi-platform testing
10. **Validate Early**: Run actionlint for validation before deployment
