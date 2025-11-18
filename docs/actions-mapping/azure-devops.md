# Azure DevOps to GitHub Actions Mapping Guide

This guide provides a mapping of common Azure DevOps Pipelines syntax and configurations to their equivalent GitHub Actions. Use this as a reference when migrating your CI/CD pipelines from Azure DevOps to GitHub Actions.

## Common Commands Mapping

| Azure DevOps Concept  | GitHub Actions Equivalent                               | Description                     |
| --------------------- | ------------------------------------------------------- | ------------------------------- |
| `trigger:`            | `on:`                                                   | Event triggers for pipeline     |
| `stages:`             | `jobs:` with `needs:`                                   | Multi-stage pipeline structure  |
| `jobs:`               | `jobs:`                                                 | Collection of execution units   |
| `steps:`              | `steps:`                                                | Individual tasks within a job   |
| `pool:`               | `runs-on:`                                              | Execution environment           |
| `pool: vmImage`       | `runs-on:`                                              | Virtual machine image selection |
| `variables:`          | `env:`                                                  | Environment variables           |
| `variables: - group:` | Organization/Repository secrets and variables           | Variable groups                 |
| `dependsOn:`          | `needs:`                                                | Job dependencies                |
| `condition:`          | `if:`                                                   | Conditional execution           |
| `task:`               | `uses:` or `run:`                                       | Task/action execution           |
| `script:`             | `run:`                                                  | Inline script execution         |
| `bash:`               | `run:` with `shell: bash`                               | Bash script execution           |
| `pwsh:`               | `run:` with `shell: pwsh`                               | PowerShell script execution     |
| `deployment:`         | `jobs:` with `environment:`                             | Deployment jobs                 |
| `environment:`        | `environment:`                                          | Deployment environment          |
| `strategy: matrix:`   | `strategy: matrix:`                                     | Matrix builds                   |
| `container:`          | `container:`                                            | Container jobs                  |
| `services:`           | `services:`                                             | Service containers              |
| `template:`           | Inline expansion                                        | Template references             |
| `parameters:`         | `inputs:` or `env:`                                     | Template parameters             |
| `resources:`          | `uses:` or manual setup                                 | Pipeline resources              |
| `artifact:`           | `actions/upload-artifact` / `actions/download-artifact` | Artifact management             |

## Azure DevOps Tasks to GitHub Actions Mapping

| Azure DevOps Task              | GitHub Actions Equivalent                      | Notes                        |
| ------------------------------ | ---------------------------------------------- | ---------------------------- |
| `NodeTool@0`                   | `actions/setup-node@v4`                        | Node.js setup                |
| `UseDotNet@2`                  | `actions/setup-dotnet@v4`                      | .NET Core setup              |
| `UsePythonVersion@0`           | `actions/setup-python@v5`                      | Python setup                 |
| `JavaToolInstaller@0`          | `actions/setup-java@v4`                        | Java setup                   |
| `GoTool@0`                     | `actions/setup-go@v5`                          | Go setup                     |
| `Npm@1`                        | `run: npm <command>`                           | NPM commands                 |
| `DotNetCoreCLI@2`              | `run: dotnet <command>`                        | .NET Core CLI commands       |
| `Maven@3`                      | `run: mvn <command>`                           | Maven commands               |
| `Gradle@2`                     | `run: gradle <command>`                        | Gradle commands              |
| `VSBuild@1`                    | `run: msbuild` or `microsoft/setup-msbuild@v1` | Visual Studio build          |
| `VSTest@2`                     | `run: vstest.console.exe`                      | Visual Studio test           |
| `PublishBuildArtifacts@1`      | `actions/upload-artifact@v4`                   | Publish artifacts            |
| `DownloadBuildArtifacts@1`     | `actions/download-artifact@v4`                 | Download artifacts           |
| `PublishTestResults@2`         | `actions/upload-artifact@v4` + test reporters  | Publish test results         |
| `PublishCodeCoverageResults@1` | `codecov/codecov-action@v4` or similar         | Code coverage                |
| `Docker@2`                     | `docker/build-push-action@v5`                  | Docker build and push        |
| `Kubernetes@1`                 | `azure/k8s-deploy@v4` or kubectl commands      | Kubernetes deployment        |
| `AzureCLI@2`                   | `azure/cli@v1` or `run: az <command>`          | Azure CLI commands           |
| `AzurePowerShell@5`            | `run:` with Azure PowerShell modules           | Azure PowerShell             |
| `AzureWebApp@1`                | `azure/webapps-deploy@v2`                      | Azure Web App deployment     |
| `AzureFunctionApp@1`           | `azure/functions-action@v1`                    | Azure Functions deployment   |
| `AzureRmWebAppDeployment@4`    | `azure/webapps-deploy@v2`                      | Azure App Service deployment |
| `GitHubRelease@1`              | `softprops/action-gh-release@v1`               | GitHub release creation      |
| `PowerShell@2`                 | `run:` with `shell: pwsh`                      | PowerShell script            |
| `Bash@3`                       | `run:` with `shell: bash`                      | Bash script                  |
| `CmdLine@2`                    | `run:`                                         | Command line script          |
| `CopyFiles@2`                  | `run: cp` or file operations                   | Copy files                   |
| `ArchiveFiles@2`               | `run: tar/zip` commands                        | Archive files                |
| `ExtractFiles@1`               | `run: unzip/tar` commands                      | Extract archives             |
| `DownloadSecureFile@1`         | Secure files as secrets                        | Secure file download         |
| `NuGetCommand@2`               | `run: nuget` commands                          | NuGet operations             |
| `NuGetToolInstaller@1`         | `nuget/setup-nuget@v1`                         | NuGet installer              |
| `Cache@2`                      | `actions/cache@v4`                             | Caching dependencies         |
| `SonarCloudPrepare@1`          | `SonarSource/sonarcloud-github-action@v2`      | SonarCloud analysis          |
| `SonarCloudAnalyze@1`          | Part of SonarCloud action                      | SonarCloud analysis          |

## Configuration Examples

### Basic Pipeline Structure

**Azure DevOps:**
```yaml
trigger:
  branches:
    include:
    - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: NodeTool@0
  inputs:
    versionSpec: '16.x'

- script: |
    npm install
    npm test
  displayName: 'Build and Test'
```

**GitHub Actions:**
```yaml
name: CI

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '16.x'

      - name: Build and Test
        run: |
          npm install
          npm test
```

### Multi-Stage Pipeline with Dependencies

**Azure DevOps:**
```yaml
stages:
- stage: Build
  jobs:
  - job: BuildJob
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - script: echo "Building..."

- stage: Test
  dependsOn: Build
  jobs:
  - job: TestJob
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - script: echo "Testing..."

- stage: Deploy
  dependsOn: Test
  jobs:
  - deployment: DeployJob
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - script: echo "Deploying..."
```

**GitHub Actions:**
```yaml
name: CI/CD

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

  deploy:
    runs-on: ubuntu-latest
    needs: test
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: echo "Deploying..."
```

### Variable Groups and Secrets

**Azure DevOps:**
```yaml
variables:
- group: MyVariableGroup
- name: buildConfiguration
  value: 'Release'

steps:
- script: |
    echo "Configuration: $(buildConfiguration)"
    echo "Secret: $(secretVariable)"
```

**GitHub Actions:**
```yaml
env:
  BUILD_CONFIGURATION: 'Release'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Configuration: $BUILD_CONFIGURATION"
          echo "Secret: ${{ secrets.SECRET_VARIABLE }}"
```

### Matrix Builds

**Azure DevOps:**
```yaml
strategy:
  matrix:
    node_14:
      node_version: '14.x'
    node_16:
      node_version: '16.x'
    node_18:
      node_version: '18.x'

steps:
- task: NodeTool@0
  inputs:
    versionSpec: $(node_version)
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [14.x, 16.x, 18.x]
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
```

### Template Expansion

**Azure DevOps Template:**
```yaml
# build-template.yml
parameters:
  buildConfiguration: 'Release'

steps:
- script: echo "Building with $(buildConfiguration)"
- task: DotNetCoreCLI@2
  inputs:
    command: 'build'
    configuration: ${{ parameters.buildConfiguration }}
```

**Azure DevOps Pipeline Using Template:**
```yaml
stages:
- stage: Build
  jobs:
  - job: BuildJob
    steps:
    - template: build-template.yml
      parameters:
        buildConfiguration: 'Release'
```

**GitHub Actions (Expanded Inline):**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: echo "Building with Release"

      - name: Build with .NET
        run: dotnet build --configuration Release
```

### Service Containers

**Azure DevOps:**
```yaml
resources:
  containers:
  - container: redis
    image: redis

pool:
  vmImage: 'ubuntu-latest'

container: redis

services:
  postgres:
    image: postgres:13
    env:
      POSTGRES_PASSWORD: postgres

steps:
- script: echo "Using services..."
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis

      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - run: echo "Using services..."
```

### Artifact Publishing and Consumption

**Azure DevOps:**
```yaml
# Publishing job
steps:
- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: '$(Build.ArtifactStagingDirectory)'
    ArtifactName: 'drop'

# Consuming job
steps:
- task: DownloadBuildArtifacts@1
  inputs:
    artifactName: 'drop'
    downloadPath: '$(System.ArtifactsDirectory)'
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Building..."

      - uses: actions/upload-artifact@v4
        with:
          name: drop
          path: dist/

  deploy:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: drop
          path: dist/
```

## Pool/Agent to Runner Mapping

| Azure DevOps Pool           | GitHub Actions Runner     |
| --------------------------- | ------------------------- |
| `vmImage: 'ubuntu-latest'`  | `runs-on: ubuntu-latest`  |
| `vmImage: 'ubuntu-22.04'`   | `runs-on: ubuntu-22.04`   |
| `vmImage: 'ubuntu-20.04'`   | `runs-on: ubuntu-20.04`   |
| `vmImage: 'windows-latest'` | `runs-on: windows-latest` |
| `vmImage: 'windows-2022'`   | `runs-on: windows-2022`   |
| `vmImage: 'windows-2019'`   | `runs-on: windows-2019`   |
| `vmImage: 'macOS-latest'`   | `runs-on: macos-latest`   |
| `vmImage: 'macOS-13'`       | `runs-on: macos-13`       |
| `vmImage: 'macOS-12'`       | `runs-on: macos-12`       |

## Condition/Expression Mapping

| Azure DevOps Condition                                                    | GitHub Actions Equivalent                |
| ------------------------------------------------------------------------- | ---------------------------------------- |
| `condition: succeeded()`                                                  | Default behavior (no `if:` needed)       |
| `condition: failed()`                                                     | `if: failure()`                          |
| `condition: always()`                                                     | `if: always()`                           |
| `condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')`       | `if: github.ref == 'refs/heads/main'`    |
| `condition: and(succeeded(), eq(variables.isMain, true))`                 | `if: success() && env.IS_MAIN == 'true'` |
| `condition: or(eq(variables.isMaster, true), eq(variables.isMain, true))` | `if: env.IS_MASTER == 'true'             |  | env.IS_MAIN == 'true'` |

## Built-in Variables Mapping

| Azure DevOps Variable               | GitHub Actions Equivalent  |
| ----------------------------------- | -------------------------- |
| `$(Build.SourceBranch)`             | `${{ github.ref }}`        |
| `$(Build.SourceBranchName)`         | `${{ github.ref_name }}`   |
| `$(Build.SourceVersion)`            | `${{ github.sha }}`        |
| `$(Build.Repository.Name)`          | `${{ github.repository }}` |
| `$(Build.BuildId)`                  | `${{ github.run_id }}`     |
| `$(Build.BuildNumber)`              | `${{ github.run_number }}` |
| `$(Build.Reason)`                   | `${{ github.event_name }}` |
| `$(Build.SourcesDirectory)`         | `${{ github.workspace }}`  |
| `$(Agent.OS)`                       | `${{ runner.os }}`         |
| `$(Agent.TempDirectory)`            | `${{ runner.temp }}`       |
| `$(System.DefaultWorkingDirectory)` | `${{ github.workspace }}`  |
| `$(Pipeline.Workspace)`             | `${{ github.workspace }}`  |



---

*This mapping guide is maintained as part of the CI/CD Migration Knowledge Base.*
