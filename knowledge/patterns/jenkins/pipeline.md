# Jenkins Pipeline Conversion Patterns

This guide provides detailed patterns for converting Jenkins declarative and scripted pipelines to GitHub Actions workflows.

## Declarative Pipeline Patterns

### Basic Declarative Pipeline

```groovy
// Jenkins Declarative Pipeline
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'npm install'
                sh 'npm run build'
            }
        }
        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
        stage('Deploy') {
            steps {
                sh 'npm run deploy'
            }
        }
    }
}
```

```yaml
# GitHub Actions Workflow
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '16'
      - run: npm install
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build-artifacts
          path: dist/

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '16'
      - run: npm install
      - run: npm test

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build-artifacts
          path: dist/
      - run: npm run deploy
```

### Declarative Pipeline with Docker Agent

```groovy
// Jenkins
pipeline {
    agent {
        docker {
            image 'maven:3.8.1-jdk-11'
            args '-v $HOME/.m2:/root/.m2'
        }
    }

    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'target/*.jar', allowEmptyArchive: true
        }
    }
}
```

```yaml
# GitHub Actions
name: Maven Build
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: maven:3.8.1-jdk-11
      volumes:
        - maven-cache:/root/.m2

    steps:
      - uses: actions/checkout@v4
      - run: mvn clean package
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: jar-artifacts
          path: target/*.jar
```

### Declarative Pipeline with Multiple Agents

```groovy
// Jenkins
pipeline {
    agent none

    stages {
        stage('Build on Linux') {
            agent { label 'linux' }
            steps {
                sh './build.sh'
            }
        }
        stage('Test on Windows') {
            agent { label 'windows' }
            steps {
                bat 'test.bat'
            }
        }
    }
}
```

```yaml
# GitHub Actions
name: Multi-Platform Build
on: [push]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./build.sh
      - uses: actions/upload-artifact@v4
        with:
          name: linux-artifacts
          path: build/

  test-windows:
    runs-on: windows-latest
    needs: build-linux
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: linux-artifacts
          path: build/
      - run: test.bat
        shell: cmd
```

### Declarative Pipeline with Conditional Stages

```groovy
// Jenkins
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh 'deploy staging'
            }
        }
        stage('Deploy to Production') {
            when {
                allOf {
                    branch 'main'
                    environment name: 'DEPLOY_PROD', value: 'true'
                }
            }
            steps {
                sh 'deploy production'
            }
        }
    }
}
```

```yaml
# GitHub Actions
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
          name: build
          path: dist/

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: deploy staging

  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' && vars.DEPLOY_PROD == 'true'
    environment: production
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: deploy production
```

### Declarative Pipeline with Parallel Stages

```groovy
// Jenkins
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }
        stage('Parallel Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh 'npm run test:unit'
                    }
                }
                stage('Integration Tests') {
                    steps {
                        sh 'npm run test:integration'
                    }
                }
                stage('E2E Tests') {
                    steps {
                        sh 'npm run test:e2e'
                    }
                }
            }
        }
    }
}
```

```yaml
# GitHub Actions
name: Build and Test
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  unit-tests:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: npm run test:unit

  integration-tests:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: npm run test:integration

  e2e-tests:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: npm run test:e2e
```

## Scripted Pipeline Patterns

### Basic Scripted Pipeline

```groovy
// Jenkins Scripted Pipeline
node {
    stage('Checkout') {
        checkout scm
    }

    stage('Build') {
        sh 'npm install'
        sh 'npm run build'
    }

    stage('Test') {
        sh 'npm test'
    }

    stage('Deploy') {
        if (env.BRANCH_NAME == 'main') {
            sh 'npm run deploy'
        }
    }
}
```

```yaml
# GitHub Actions
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '16'
      - run: npm install
      - run: npm run build
      - run: npm test
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: npm run deploy
```

### Scripted Pipeline with Error Handling

```groovy
// Jenkins
node {
    try {
        stage('Build') {
            sh 'npm install'
            sh 'npm run build'
        }

        stage('Test') {
            sh 'npm test'
        }

        currentBuild.result = 'SUCCESS'
    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        stage('Cleanup') {
            sh 'npm run cleanup'
        }

        if (currentBuild.result == 'FAILURE') {
            mail to: 'team@example.com',
                 subject: "Build Failed: ${env.JOB_NAME}",
                 body: "Build failed. Check ${env.BUILD_URL}"
        }
    }
}
```

```yaml
# GitHub Actions
name: Build with Error Handling
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '16'

      - name: Build
        id: build
        run: |
          npm install
          npm run build

      - name: Test
        id: test
        run: npm test

      - name: Cleanup
        if: always()
        run: npm run cleanup

      - name: Send failure notification
        if: failure()
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: 'Build Failed: ${{ github.workflow }}'
          to: team@example.com
          from: CI/CD Pipeline
          body: 'Build failed. Check ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}'
```

### Scripted Pipeline with Parallel Execution

```groovy
// Jenkins
node {
    stage('Build') {
        sh 'npm run build'
    }

    stage('Tests') {
        parallel(
            'Unit Tests': {
                node {
                    sh 'npm run test:unit'
                }
            },
            'Integration Tests': {
                node {
                    sh 'npm run test:integration'
                }
            },
            'E2E Tests': {
                node {
                    sh 'npm run test:e2e'
                }
            }
        )
    }
}
```

```yaml
# GitHub Actions
name: Build and Parallel Tests
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  unit-tests:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: npm run test:unit

  integration-tests:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: npm run test:integration

  e2e-tests:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
      - run: npm run test:e2e
```

### Scripted Pipeline with Timeout and Retry

```groovy
// Jenkins
node {
    stage('Build') {
        timeout(time: 10, unit: 'MINUTES') {
            retry(3) {
                sh 'npm install'
            }
            sh 'npm run build'
        }
    }

    stage('Deploy') {
        timeout(time: 5, unit: 'MINUTES') {
            sh 'npm run deploy'
        }
    }
}
```

```yaml
# GitHub Actions
name: Build with Timeout and Retry
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '16'

      - name: Install dependencies with retry
        uses: nick-invision/retry@v2
        with:
          timeout_minutes: 5
          max_attempts: 3
          command: npm install

      - run: npm run build

  deploy:
    runs-on: ubuntu-latest
    needs: build
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - run: npm run deploy
```

### Scripted Pipeline with Multiple Nodes

```groovy
// Jenkins
stage('Parallel Builds') {
    parallel(
        'Linux Build': {
            node('linux') {
                checkout scm
                sh './build-linux.sh'
                archiveArtifacts 'linux-build/**'
            }
        },
        'Windows Build': {
            node('windows') {
                checkout scm
                bat 'build-windows.bat'
                archiveArtifacts 'windows-build/**'
            }
        },
        'macOS Build': {
            node('macos') {
                checkout scm
                sh './build-macos.sh'
                archiveArtifacts 'macos-build/**'
            }
        }
    )
}
```

```yaml
# GitHub Actions
name: Multi-Platform Builds
on: [push]

jobs:
  linux-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./build-linux.sh
      - uses: actions/upload-artifact@v4
        with:
          name: linux-build
          path: linux-build/

  windows-build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - run: build-windows.bat
        shell: cmd
      - uses: actions/upload-artifact@v4
        with:
          name: windows-build
          path: windows-build/

  macos-build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./build-macos.sh
      - uses: actions/upload-artifact@v4
        with:
          name: macos-build
          path: macos-build/
```

## Matrix Build Patterns

### Jenkins Matrix to GitHub Actions Matrix

```groovy
// Jenkins Declarative Matrix
pipeline {
    agent any

    stages {
        stage('Matrix Build') {
            matrix {
                axes {
                    axis {
                        name 'PLATFORM'
                        values 'linux', 'windows', 'macos'
                    }
                    axis {
                        name 'NODE_VERSION'
                        values '14', '16', '18'
                    }
                }
                stages {
                    stage('Test') {
                        steps {
                            echo "Testing on ${PLATFORM} with Node ${NODE_VERSION}"
                            sh "npm test"
                        }
                    }
                }
            }
        }
    }
}
```

```yaml
# GitHub Actions Matrix
name: Matrix Build
on: [push]

jobs:
  test:
    strategy:
      matrix:
        platform: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [14, 16, 18]
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm install
      - run: npm test
```

## Environment and Options Patterns

### Options Translation

```groovy
// Jenkins
pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
        timeout(time: 1, unit: 'HOURS')
        timestamps()
        skipDefaultCheckout()
    }

    stages {
        stage('Build') {
            steps {
                checkout scm
                sh 'make build'
            }
        }
    }
}
```

```yaml
# GitHub Actions
name: Build with Options
on: [push]

# Retention handled at repository/org level
# Timestamps always enabled

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      # Manual checkout (skip default would be omitting this)
      - uses: actions/checkout@v4
      - run: make build
```

## Post-Build Actions Pattern

```groovy
// Jenkins
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }
    }

    post {
        always {
            junit '**/test-results.xml'
            archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: true
        }
        success {
            echo 'Build succeeded!'
            slackSend color: 'good', message: "Build succeeded: ${env.JOB_NAME}"
        }
        failure {
            echo 'Build failed!'
            slackSend color: 'danger', message: "Build failed: ${env.JOB_NAME}"
        }
        cleanup {
            deleteDir()
        }
    }
}
```

```yaml
# GitHub Actions
name: Build with Post Actions
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build

      - name: Publish test results
        if: always()
        uses: dorny/test-reporter@v1
        with:
          name: Test Results
          path: '**/test-results.xml'
          reporter: java-junit

      - name: Archive artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dist-artifacts
          path: dist/
          if-no-files-found: ignore

      - name: Success notification
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Build succeeded: ${{ github.workflow }}",
              "color": "good"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: Failure notification
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Build failed: ${{ github.workflow }}",
              "color": "danger"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Best Practices

1. **Stage to Job Mapping**: Convert each Jenkins stage to a separate GitHub Actions job with proper dependencies
2. **Artifact Sharing**: Use upload/download artifact actions instead of stash/unstash
3. **Conditional Logic**: Replace Jenkins `when` conditions with GitHub Actions `if` expressions
4. **Error Handling**: Use `continue-on-error` and conditional steps instead of try/catch blocks
5. **Parallel Execution**: Create separate jobs without `needs:` dependency for parallel execution
6. **Timeout Configuration**: Set `timeout-minutes` at the job level for timeout control
7. **Environment Variables**: Use `env:` at workflow, job, or step level as appropriate
8. **Cleanup**: Use `if: always()` for cleanup steps that should run regardless of success/failure
9. **Agent Mapping**: Choose appropriate GitHub-hosted or self-hosted runners based on Jenkins agent labels
10. **Validation**: Test converted workflows with actionlint before deployment
