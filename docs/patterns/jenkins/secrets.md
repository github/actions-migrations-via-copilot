# Jenkins Credentials and Secrets Migration Guide

This guide provides patterns for migrating Jenkins credentials and environment variables to GitHub Actions secrets and variables.

## Jenkins Credential Types to GitHub Secrets Mapping

### String Credentials

```groovy
// Jenkins - String credential
environment {
    API_KEY = credentials('api-key-id')
}

steps {
    sh 'curl -H "Authorization: Bearer $API_KEY" https://api.example.com'
}
```

```yaml
# GitHub Actions - Secret
env:
  API_KEY: ${{ secrets.API_KEY }}

steps:
  - run: curl -H "Authorization: Bearer $API_KEY" https://api.example.com
```

### Username/Password Credentials

```groovy
// Jenkins - Username/Password credential
withCredentials([
    usernamePassword(
        credentialsId: 'docker-hub-creds',
        usernameVariable: 'DOCKER_USER',
        passwordVariable: 'DOCKER_PASS'
    )
]) {
    sh 'docker login -u $DOCKER_USER -p $DOCKER_PASS'
}
```

```yaml
# GitHub Actions - Separate secrets
- name: Docker Login
  env:
    DOCKER_USER: ${{ secrets.DOCKER_USER }}
    DOCKER_PASS: ${{ secrets.DOCKER_PASS }}
  run: |
    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin

# Or use docker/login-action
- name: Docker Login
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USER }}
    password: ${{ secrets.DOCKER_PASS }}
```

### SSH Private Key Credentials

```groovy
// Jenkins - SSH credential
sshagent(credentials: ['deploy-ssh-key']) {
    sh '''
        ssh user@server 'deploy.sh'
        scp build.tar.gz user@server:/opt/app/
    '''
}
```

```yaml
# GitHub Actions - SSH key as secret
- name: Setup SSH
  env:
    SSH_PRIVATE_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
  run: |
    mkdir -p ~/.ssh
    echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -H server >> ~/.ssh/known_hosts

- name: Deploy via SSH
  run: |
    ssh user@server 'deploy.sh'
    scp build.tar.gz user@server:/opt/app/
```

### Secret File Credentials

```groovy
// Jenkins - Secret file
withCredentials([
    file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG_FILE')
]) {
    sh 'kubectl --kubeconfig=$KUBECONFIG_FILE get pods'
}
```

```yaml
# GitHub Actions - File content as secret
- name: Setup kubeconfig
  env:
    KUBECONFIG_CONTENT: ${{ secrets.KUBECONFIG }}
  run: |
    echo "$KUBECONFIG_CONTENT" > kubeconfig.yaml
    export KUBECONFIG=kubeconfig.yaml
    kubectl get pods
```

### Certificate Credentials

```groovy
// Jenkins - Certificate credential
withCredentials([
    certificate(
        credentialsId: 'signing-cert',
        keystoreVariable: 'KEYSTORE',
        passwordVariable: 'KEYSTORE_PASS'
    )
]) {
    sh """
        jarsigner -keystore $KEYSTORE \
                  -storepass $KEYSTORE_PASS \
                  app.jar myalias
    """
}
```

```yaml
# GitHub Actions - Certificate and password as secrets
- name: Sign application
  env:
    KEYSTORE_CONTENT: ${{ secrets.SIGNING_CERT_KEYSTORE }}
    KEYSTORE_PASS: ${{ secrets.KEYSTORE_PASSWORD }}
  run: |
    echo "$KEYSTORE_CONTENT" | base64 -d > keystore.jks
    jarsigner -keystore keystore.jks \
              -storepass $KEYSTORE_PASS \
              app.jar myalias
    rm keystore.jks
```

## Environment Variables Migration

### Simple Environment Variables

```groovy
// Jenkins
environment {
    NODE_ENV = 'production'
    API_ENDPOINT = 'https://api.example.com'
    LOG_LEVEL = 'info'
}
```

```yaml
# GitHub Actions - Variables (non-sensitive)
env:
  NODE_ENV: ${{ vars.NODE_ENV }}
  API_ENDPOINT: ${{ vars.API_ENDPOINT }}
  LOG_LEVEL: ${{ vars.LOG_LEVEL }}
```

### Stage-Specific Environment Variables

```groovy
// Jenkins
pipeline {
    stages {
        stage('Build') {
            environment {
                BUILD_ENV = 'production'
            }
            steps {
                sh 'npm run build'
            }
        }
    }
}
```

```yaml
# GitHub Actions - Job-level env
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      BUILD_ENV: production
    steps:
      - run: npm run build
```

### Computed Environment Variables

```groovy
// Jenkins
environment {
    VERSION = "${env.BUILD_NUMBER}"
    IMAGE_TAG = "myapp:${env.GIT_COMMIT.take(7)}"
    DEPLOY_TIME = new Date().format('yyyy-MM-dd-HH-mm')
}
```

```yaml
# GitHub Actions - Computed in steps
- name: Set environment variables
  run: |
    echo "VERSION=${{ github.run_number }}" >> $GITHUB_ENV
    echo "IMAGE_TAG=myapp:${GITHUB_SHA:0:7}" >> $GITHUB_ENV
    echo "DEPLOY_TIME=$(date +%Y-%m-%d-%H-%M)" >> $GITHUB_ENV

- name: Use variables
  run: |
    echo "Version: $VERSION"
    echo "Image: $IMAGE_TAG"
    echo "Deploy time: $DEPLOY_TIME"
```

## Credential Binding Patterns

### Pattern 1: Multiple Credentials in Single Block

```groovy
// Jenkins
withCredentials([
    string(credentialsId: 'api-token', variable: 'API_TOKEN'),
    usernamePassword(
        credentialsId: 'db-creds',
        usernameVariable: 'DB_USER',
        passwordVariable: 'DB_PASS'
    ),
    file(credentialsId: 'config-file', variable: 'CONFIG')
]) {
    sh '''
        echo "API Token: $API_TOKEN"
        echo "DB User: $DB_USER"
        echo "Config: $CONFIG"
    '''
}
```

```yaml
# GitHub Actions - All as secrets/env
- name: Use credentials
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
    DB_USER: ${{ secrets.DB_USER }}
    DB_PASS: ${{ secrets.DB_PASS }}
    CONFIG_CONTENT: ${{ secrets.CONFIG_FILE }}
  run: |
    echo "$CONFIG_CONTENT" > config.yaml
    echo "API Token: $API_TOKEN"
    echo "DB User: $DB_USER"
    echo "Config: config.yaml"
```

### Pattern 2: Conditional Credential Usage

```groovy
// Jenkins
stage('Deploy') {
    when { branch 'main' }
    steps {
        withCredentials([
            string(credentialsId: 'prod-api-key', variable: 'API_KEY')
        ]) {
            sh 'deploy.sh production'
        }
    }
}
```

```yaml
# GitHub Actions
- name: Deploy to production
  if: github.ref == 'refs/heads/main'
  env:
    API_KEY: ${{ secrets.PROD_API_KEY }}
  run: deploy.sh production
```

### Pattern 3: Nested Credential Blocks

```groovy
// Jenkins
withCredentials([usernamePassword(credentialsId: 'aws-creds', usernameVariable: 'AWS_ID', passwordVariable: 'AWS_SECRET')]) {
    withCredentials([string(credentialsId: 's3-bucket', variable: 'BUCKET')]) {
        sh """
            aws configure set aws_access_key_id $AWS_ID
            aws configure set aws_secret_access_key $AWS_SECRET
            aws s3 cp build.tar.gz s3://$BUCKET/
        """
    }
}
```

```yaml
# GitHub Actions - Flatten to single env block
- name: Upload to S3
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    S3_BUCKET: ${{ vars.S3_BUCKET }}
  run: |
    aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
    aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
    aws s3 cp build.tar.gz s3://$S3_BUCKET/

# Or use AWS action
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1

- name: Upload to S3
  run: aws s3 cp build.tar.gz s3://${{ vars.S3_BUCKET }}/
```

## Environment-Specific Credentials

### Pattern: Multi-Environment Deployments

```groovy
// Jenkins
stage('Deploy') {
    steps {
        script {
            def environment = env.BRANCH_NAME == 'main' ? 'production' : 'staging'
            def credId = "${environment}-deploy-key"

            withCredentials([string(credentialsId: credId, variable: 'DEPLOY_KEY')]) {
                sh "deploy.sh ${environment}"
            }
        }
    }
}
```

```yaml
# GitHub Actions - Use environment feature
deploy-staging:
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/develop'
  environment: staging
  steps:
    - name: Deploy to staging
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
      run: deploy.sh staging

deploy-production:
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main'
  environment: production
  steps:
    - name: Deploy to production
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
      run: deploy.sh production
```

## Secrets Management Best Practices

### Naming Conventions

| Jenkins Pattern    | GitHub Actions Pattern        | Notes                            |
| ------------------ | ----------------------------- | -------------------------------- |
| `api-key`          | `API_KEY`                     | Use UPPER_SNAKE_CASE for secrets |
| `docker-hub-user`  | `DOCKER_HUB_USER`             | Descriptive names                |
| `prod-db-password` | `PROD_DB_PASSWORD`            | Environment prefix for clarity   |
| `dev-api-endpoint` | `DEV_API_ENDPOINT` (variable) | Non-sensitive as variable        |

### Organization vs Repository Secrets

```yaml
# Organization-level secrets (shared across repos)
# - DOCKER_HUB_USER
# - DOCKER_HUB_TOKEN
# - SLACK_WEBHOOK_URL
# - SONAR_TOKEN

# Repository-level secrets (project-specific)
# - DATABASE_PASSWORD
# - API_SECRET_KEY
# - DEPLOYMENT_TOKEN
# - SSH_PRIVATE_KEY

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # Using org-level secret
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USER }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}

      # Using repo-level secret
      - name: Deploy
        env:
          DEPLOYMENT_TOKEN: ${{ secrets.DEPLOYMENT_TOKEN }}
        run: deploy.sh
```

### Environment-Scoped Secrets

```yaml
# Define environments with secrets at repository level
# Environments: development, staging, production
# Each can have environment-specific secrets with same names

deploy-dev:
  runs-on: ubuntu-latest
  environment: development
  steps:
    - name: Deploy
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}  # development DATABASE_URL
        API_KEY: ${{ secrets.API_KEY }}            # development API_KEY
      run: deploy.sh

deploy-prod:
  runs-on: ubuntu-latest
  environment: production
  steps:
    - name: Deploy
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}  # production DATABASE_URL
        API_KEY: ${{ secrets.API_KEY }}            # production API_KEY
      run: deploy.sh
```

## Common Jenkins Environment Variables

| Jenkins Variable | GitHub Actions Equivalent          | Type        |
| ---------------- | ---------------------------------- | ----------- |
| `BUILD_ID`       | `github.run_id`                    | Context     |
| `BUILD_NUMBER`   | `github.run_number`                | Context     |
| `JOB_NAME`       | `github.workflow`                  | Context     |
| `WORKSPACE`      | `github.workspace`                 | Context     |
| `GIT_COMMIT`     | `github.sha`                       | Context     |
| `GIT_BRANCH`     | `github.ref_name`                  | Context     |
| `BRANCH_NAME`    | `github.ref_name`                  | Context     |
| `CHANGE_ID`      | `github.event.pull_request.number` | Context     |
| `BUILD_URL`      | Composed from `github.*`           | Context     |
| `JENKINS_HOME`   | `GITHUB_WORKSPACE`                 | Environment |

## Security Improvements During Migration

### 1. Least Privilege Access

```yaml
# Jenkins had global credentials access
# GitHub Actions restricts by environment and approval

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Requires approval + has scoped secrets
    permissions:
      contents: read
      deployments: write
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: deploy.sh
```

### 2. Secret Rotation

```yaml
# Document required secrets in README for rotation tracking
# Use GitHub's secret scanning to detect leaks

# Required Secrets:
# - API_TOKEN: Rotate every 90 days
# - DATABASE_PASSWORD: Rotate every 60 days
# - SSH_PRIVATE_KEY: Rotate on team changes
```

### 3. Audit Trail

```yaml
# GitHub Actions provides better audit trail
# Environment deployments show who approved

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Logs approvers and deployment time
    steps:
      - name: Deploy
        run: |
          echo "Deployed by: ${{ github.actor }}"
          echo "Approved by: (visible in deployment logs)"
          deploy.sh
```

## Migration Checklist

When migrating Jenkins credentials to GitHub Actions:

- [ ] Identify all Jenkins credentials used in pipeline
- [ ] Classify credentials by type (string, username/password, SSH, file, certificate)
- [ ] Determine scope: organization, repository, or environment-specific
- [ ] Create equivalent secrets in GitHub
- [ ] Convert credential bindings to environment variables
- [ ] Update secret references in workflow files
- [ ] Test credential access in non-production environment first
- [ ] Document all required secrets in MIGRATION-README.md
- [ ] Remove or archive Jenkins credentials after successful migration
- [ ] Update team documentation with new secret management process
- [ ] Implement secret rotation schedule
- [ ] Configure environment protection rules for sensitive deployments

## Troubleshooting

### Issue: Credential Not Available in Step
**Solution**: Ensure secret is defined at correct scope (environment, repository, organization)

### Issue: Secret Value Contains Special Characters
**Solution**: Use base64 encoding for complex secrets or escape properly in shell

### Issue: Need Dynamic Credential Selection
**Solution**: Use environment-based deployments or matrix strategy with conditional logic

### Issue: Shared Credentials Across Teams
**Solution**: Use organization-level secrets with repository access control

### Issue: Credential Rotation
**Solution**: Update secrets in GitHub settings; workflows pick up new values automatically
