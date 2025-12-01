# Jenkins Groovy and Shared Library Conversion Patterns

This guide provides patterns for converting Jenkins Groovy scripts and shared library code to GitHub Actions workflows.

## Shared Library Expansion Strategy

Jenkins shared libraries must be expanded inline in GitHub Actions workflows. The general approach:

1. **Identify Library Calls**: Locate all `@Library` annotations and library method calls
2. **Retrieve Library Code**: Obtain the source code from the `vars/` directory
3. **Inline the Logic**: Convert Groovy code to shell scripts or marketplace actions
4. **Pass Parameters**: Map library parameters to workflow inputs or environment variables

### Example: Simple Shared Library

```groovy
// Jenkins: vars/deployApplication.groovy
def call(String environment, String version) {
    echo "Deploying version ${version} to ${environment}"
    sh """
        kubectl set image deployment/myapp myapp=myapp:${version}
        kubectl rollout status deployment/myapp
    """
}

// Jenkins: Jenkinsfile
@Library('shared-lib') _
pipeline {
    agent any
    stages {
        stage('Deploy') {
            steps {
                deployApplication('production', '1.2.3')
            }
        }
    }
}
```

```yaml
# GitHub Actions: Expanded inline
name: Deploy Application
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        env:
          ENVIRONMENT: production
          VERSION: 1.2.3
        run: |
          echo "Deploying version $VERSION to $ENVIRONMENT"
          kubectl set image deployment/myapp myapp=myapp:$VERSION
          kubectl rollout status deployment/myapp
```

## Groovy Script Conversion Patterns

### Variable Assignment and String Interpolation

```groovy
// Jenkins Groovy
def version = '1.0.0'
def imageName = "myapp:${version}"
def fullImagePath = "${env.DOCKER_REGISTRY}/${imageName}"

echo "Building ${fullImagePath}"
```

```yaml
# GitHub Actions (shell script)
- name: Build image
  env:
    VERSION: '1.0.0'
  run: |
    IMAGE_NAME="myapp:${VERSION}"
    FULL_IMAGE_PATH="${DOCKER_REGISTRY}/${IMAGE_NAME}"
    echo "Building ${FULL_IMAGE_PATH}"
```

### Conditional Logic

```groovy
// Jenkins Groovy
if (env.BRANCH_NAME == 'main') {
    echo 'Deploying to production'
    deployToProd()
} else if (env.BRANCH_NAME.startsWith('release-')) {
    echo 'Deploying to staging'
    deployToStaging()
} else {
    echo 'Skipping deployment'
}
```

```yaml
# GitHub Actions
- name: Deploy to production
  if: github.ref == 'refs/heads/main'
  run: |
    echo 'Deploying to production'
    ./deploy-to-prod.sh

- name: Deploy to staging
  if: startsWith(github.ref, 'refs/heads/release-')
  run: |
    echo 'Deploying to staging'
    ./deploy-to-staging.sh
```

### Loops and Iteration

```groovy
// Jenkins Groovy
def environments = ['dev', 'staging', 'prod']
for (env in environments) {
    echo "Deploying to ${env}"
    sh "deploy.sh ${env}"
}
```

```yaml
# GitHub Actions (matrix strategy)
deploy:
  strategy:
    matrix:
      environment: [dev, staging, prod]
  runs-on: ubuntu-latest
  steps:
    - name: Deploy to ${{ matrix.environment }}
      run: |
        echo "Deploying to ${{ matrix.environment }}"
        ./deploy.sh ${{ matrix.environment }}
```

### Try-Catch Error Handling

```groovy
// Jenkins Groovy
try {
    sh 'risky-command'
    currentBuild.result = 'SUCCESS'
} catch (Exception e) {
    echo "Error occurred: ${e.getMessage()}"
    currentBuild.result = 'FAILURE'
    throw e
} finally {
    echo 'Cleanup'
    sh 'cleanup.sh'
}
```

```yaml
# GitHub Actions
- name: Run risky command
  id: risky
  continue-on-error: true
  run: risky-command

- name: Handle error
  if: steps.risky.outcome == 'failure'
  run: |
    echo "Error occurred in risky command"
    exit 1

- name: Cleanup
  if: always()
  run: cleanup.sh
```

## Shared Library Pattern Examples

### Pattern 1: Build and Push Docker Image

```groovy
// Jenkins: vars/dockerBuildPush.groovy
def call(Map config) {
    def imageName = config.imageName
    def tag = config.tag ?: 'latest'
    def registry = config.registry ?: env.DOCKER_REGISTRY
    def dockerfile = config.dockerfile ?: 'Dockerfile'

    sh """
        docker build -t ${registry}/${imageName}:${tag} -f ${dockerfile} .
        docker push ${registry}/${imageName}:${tag}
    """
}

// Jenkins: Jenkinsfile
dockerBuildPush(
    imageName: 'myapp',
    tag: env.BUILD_NUMBER,
    dockerfile: 'Dockerfile.prod'
)
```

```yaml
# GitHub Actions: Expanded with marketplace action
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: Dockerfile.prod
    push: true
    tags: ${{ env.DOCKER_REGISTRY }}/myapp:${{ github.run_number }}
```

### Pattern 2: Slack Notification Library

```groovy
// Jenkins: vars/notifySlack.groovy
def call(String status, String message = '') {
    def color = status == 'SUCCESS' ? 'good' : 'danger'
    def emoji = status == 'SUCCESS' ? ':white_check_mark:' : ':x:'
    def text = message ?: "${emoji} Build ${status}: ${env.JOB_NAME} #${env.BUILD_NUMBER}"

    slackSend(
        color: color,
        message: text,
        channel: '#builds'
    )
}

// Jenkins: Jenkinsfile (in post section)
notifySlack(currentBuild.result)
```

```yaml
# GitHub Actions: Expanded with marketplace action
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "channel": "#builds",
        "text": "${{ job.status == 'success' && ':white_check_mark:' || ':x:' }} Build ${{ job.status }}: ${{ github.workflow }} #${{ github.run_number }}",
        "color": "${{ job.status == 'success' && 'good' || 'danger' }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Pattern 3: Multi-Environment Deployment Library

```groovy
// Jenkins: vars/deployToEnvironment.groovy
def call(String environment, Map config = [:]) {
    def namespace = config.namespace ?: environment
    def replicas = config.replicas ?: 3
    def version = config.version ?: env.BUILD_NUMBER

    withKubeConfig([credentialsId: "${environment}-kubeconfig"]) {
        sh """
            kubectl config use-context ${environment}
            kubectl set image deployment/myapp myapp=myapp:${version} -n ${namespace}
            kubectl scale deployment/myapp --replicas=${replicas} -n ${namespace}
            kubectl rollout status deployment/myapp -n ${namespace}
        """
    }
}

// Jenkins: Jenkinsfile
deployToEnvironment('production', [replicas: 5])
```

```yaml
# GitHub Actions: Expanded
- name: Deploy to production
  env:
    ENVIRONMENT: production
    NAMESPACE: production
    REPLICAS: 5
    VERSION: ${{ github.run_number }}
    KUBECONFIG: ${{ secrets.PRODUCTION_KUBECONFIG }}
  run: |
    echo "$KUBECONFIG" > kubeconfig.yaml
    export KUBECONFIG=kubeconfig.yaml
    kubectl config use-context $ENVIRONMENT
    kubectl set image deployment/myapp myapp=myapp:$VERSION -n $NAMESPACE
    kubectl scale deployment/myapp --replicas=$REPLICAS -n $NAMESPACE
    kubectl rollout status deployment/myapp -n $NAMESPACE
```

### Pattern 4: Automated Testing Library

```groovy
// Jenkins: vars/runTests.groovy
def call(Map config) {
    def testType = config.type ?: 'unit'
    def parallel = config.parallel ?: false
    def coverage = config.coverage ?: true

    if (parallel) {
        parallel(
            'Unit': { sh 'npm run test:unit' },
            'Integration': { sh 'npm run test:integration' }
        )
    } else {
        sh "npm run test:${testType}"
    }

    if (coverage) {
        sh 'npm run coverage'
        publishHTML([
            reportDir: 'coverage',
            reportFiles: 'index.html',
            reportName: 'Coverage Report'
        ])
    }
}

// Jenkins: Jenkinsfile
runTests(type: 'all', parallel: true, coverage: true)
```

```yaml
# GitHub Actions: Expanded
unit-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: npm run test:unit

integration-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: npm run test:integration

coverage:
  runs-on: ubuntu-latest
  needs: [unit-tests, integration-tests]
  steps:
    - uses: actions/checkout@v4
    - run: npm run coverage
    - uses: codecov/codecov-action@v4
      with:
        files: ./coverage/coverage.xml
```

## Advanced Groovy Patterns

### Closure Usage

```groovy
// Jenkins Groovy
def withRetry(int maxAttempts, Closure body) {
    int attempts = 0
    while (attempts < maxAttempts) {
        try {
            body()
            return
        } catch (Exception e) {
            attempts++
            if (attempts >= maxAttempts) throw e
            echo "Retry attempt ${attempts}/${maxAttempts}"
            sleep(time: 5, unit: 'SECONDS')
        }
    }
}

// Usage
withRetry(3) {
    sh 'flaky-command'
}
```

```yaml
# GitHub Actions: Use retry action
- name: Run flaky command with retry
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 2
    max_attempts: 3
    retry_wait_seconds: 5
    command: flaky-command
```

### Map Manipulation

```groovy
// Jenkins Groovy
def config = [
    dev: [url: 'https://dev.example.com', replicas: 1],
    prod: [url: 'https://prod.example.com', replicas: 3]
]

def environment = env.BRANCH_NAME == 'main' ? 'prod' : 'dev'
def deployConfig = config[environment]

echo "Deploying to ${deployConfig.url} with ${deployConfig.replicas} replicas"
```

```yaml
# GitHub Actions: Use JSON and jq
- name: Deploy with config
  run: |
    CONFIG='{"dev":{"url":"https://dev.example.com","replicas":1},"prod":{"url":"https://prod.example.com","replicas":3}}'
    if [ "${{ github.ref }}" == "refs/heads/main" ]; then
      ENVIRONMENT="prod"
    else
      ENVIRONMENT="dev"
    fi
    URL=$(echo $CONFIG | jq -r ".$ENVIRONMENT.url")
    REPLICAS=$(echo $CONFIG | jq -r ".$ENVIRONMENT.replicas")
    echo "Deploying to $URL with $REPLICAS replicas"
```

### Class Definition and Usage

```groovy
// Jenkins: vars/BuildConfig.groovy
class BuildConfig {
    String name
    String version
    List<String> environments

    BuildConfig(String name, String version) {
        this.name = name
        this.version = version
        this.environments = []
    }

    def addEnvironment(String env) {
        this.environments.add(env)
    }

    def getFullName() {
        return "${name}:${version}"
    }
}

// Jenkins: Jenkinsfile
def config = new BuildConfig('myapp', '1.0.0')
config.addEnvironment('dev')
config.addEnvironment('prod')

echo "Building ${config.getFullName()}"
```

```yaml
# GitHub Actions: Use environment variables and arrays
- name: Configure and build
  run: |
    NAME="myapp"
    VERSION="1.0.0"
    ENVIRONMENTS=("dev" "prod")
    FULL_NAME="${NAME}:${VERSION}"

    echo "Building $FULL_NAME"
    echo "Environments: ${ENVIRONMENTS[@]}"
```

## Common Groovy to Shell Conversions

| Groovy Pattern                          | Shell/Bash Equivalent                       |
| --------------------------------------- | ------------------------------------------- |
| `def var = 'value'`                     | `VAR="value"`                               |
| `"${var}"`                              | `"${VAR}"` or `"$VAR"`                      |
| `var.toUpperCase()`                     | `echo "$VAR" \| tr '[:lower:]' '[:upper:]'` |
| `var.trim()`                            | `echo "$VAR" \| xargs`                      |
| `var.split(',')`                        | `IFS=',' read -ra ARRAY <<< "$VAR"`         |
| `list.join(',')`                        | `IFS=','; echo "${ARRAY[*]}"`               |
| `var.contains('text')`                  | `[[ "$VAR" == *"text"* ]]`                  |
| `var.startsWith('pre')`                 | `[[ "$VAR" == pre* ]]`                      |
| `var.endsWith('suf')`                   | `[[ "$VAR" == *suf ]]`                      |
| `var.replace('old', 'new')`             | `echo "${VAR//old/new}"`                    |
| `new Date().format('yyyy-MM-dd')`       | `date +%Y-%m-%d`                            |
| `env.getEnvironment()`                  | `env` or `printenv`                         |
| `sh(script: 'cmd', returnStdout: true)` | `OUTPUT=$(cmd)`                             |
| `sh(script: 'cmd', returnStatus: true)` | `cmd; STATUS=$?`                            |

## Best Practices for Groovy Conversion

1. **Inline All Libraries**: Never reference external shared libraries in GitHub Actions
2. **Replace Groovy Logic**: Convert Groovy scripts to shell scripts or use marketplace actions
3. **Use Actions for Complex Tasks**: Prefer marketplace actions over custom shell scripts
4. **Parameter Mapping**: Convert library parameters to workflow inputs or environment variables
5. **Error Handling**: Replace try-catch with `continue-on-error` and conditional steps
6. **State Management**: Use artifacts and outputs instead of Groovy variables across stages
7. **Credential Access**: Use GitHub Secrets instead of Jenkins credential binding
8. **Context Awareness**: Map Jenkins environment variables to GitHub context expressions
9. **Validation**: Test converted logic with actionlint before deployment
10. **Documentation**: Document complex Groovy conversions in the migration README

## Troubleshooting Common Conversions

### Issue: Complex Groovy Logic
**Solution**: Break down into smaller shell scripts or use Python/Node.js scripts

### Issue: Jenkins Global Variables
**Solution**: Use GitHub Variables at organization or repository level

### Issue: Shared Library Dependencies
**Solution**: Inline all dependencies or find equivalent marketplace actions

### Issue: Dynamic Pipeline Generation
**Solution**: Use matrix strategies or workflow composition with reusable workflows

### Issue: Jenkins Plugin Integration
**Solution**: Find marketplace action equivalents or call APIs directly via curl
