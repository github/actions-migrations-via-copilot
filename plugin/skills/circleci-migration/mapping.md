# CircleCI to GitHub Actions Mapping Guide

This guide provides a mapping of common CircleCI syntax and configurations to their equivalent GitHub Actions. Use this as a reference when migrating your CI/CD pipelines from CircleCI to GitHub Actions.

## Common Commands Mapping

| CircleCI Concept        | GitHub Actions Equivalent                     | Description                              |
| ----------------------- | --------------------------------------------- | ---------------------------------------- |
| `workflows:`            | `on:` + `jobs:`                               | Workflow definition and orchestration    |
| `jobs:`                 | `jobs:`                                       | Collection of execution units            |
| `steps:`                | `steps:`                                      | Individual tasks within a job            |
| `executors:`            | `runs-on:` + `container:`                     | Execution environment                    |
| `docker:` executor      | `container:`                                  | Docker container environment             |
| `machine:` executor     | `runs-on:`                                    | VM-based environment                     |
| `macos:` executor       | `runs-on: macos-*`                            | macOS environment                        |
| `windows:` executor     | `runs-on: windows-*`                          | Windows environment                      |
| `orbs:`                 | Inline expansion or marketplace actions       | Reusable configuration packages          |
| `commands:`             | Composite actions or inline steps             | Reusable command definitions             |
| `parameters:`           | `inputs:` or `env:`                           | Parameterized configuration              |
| `requires:`             | `needs:`                                      | Job dependencies                         |
| `filters:`              | `if:` + `on:` conditions                      | Conditional execution                    |
| `when:`                 | `if:`                                         | Conditional step execution               |
| `context:`              | Secrets and Variables                         | Shared environment variables and secrets |
| `environment:`          | `env:`                                        | Environment variables                    |
| `working_directory:`    | `working-directory:`                          | Working directory specification          |
| `parallelism:`          | `strategy: matrix:`                           | Parallel job execution                   |
| `resource_class:`       | `runs-on:` selection                          | Resource allocation                      |
| `save_cache:`           | `actions/cache@v4` (save)                     | Cache creation                           |
| `restore_cache:`        | `actions/cache@v4` (restore)                  | Cache restoration                        |
| `store_artifacts:`      | `actions/upload-artifact@v4`                  | Artifact storage                         |
| `store_test_results:`   | `actions/upload-artifact@v4` + test reporters | Test result storage                      |
| `persist_to_workspace:` | `actions/upload-artifact@v4`                  | Workspace persistence                    |
| `attach_workspace:`     | `actions/download-artifact@v4`                | Workspace attachment                     |
| `add_ssh_keys:`         | SSH key setup in secrets                      | SSH key management                       |
| `checkout:`             | `actions/checkout@v4`                         | Repository checkout                      |
| `setup_remote_docker:`  | Docker-in-Docker setup                        | Remote Docker environment                |
| `run:`                  | `run:`                                        | Shell command execution                  |
| `type: approval`        | Environment protection rules                  | Manual approval gate                     |

## CircleCI Orbs to GitHub Actions Mapping

| CircleCI Orb            | GitHub Actions Equivalent                   | Notes                 |
| ----------------------- | ------------------------------------------- | --------------------- |
| `circleci/node@x`       | `actions/setup-node@v4`                     | Node.js setup         |
| `circleci/python@x`     | `actions/setup-python@v5`                   | Python setup          |
| `circleci/go@x`         | `actions/setup-go@v5`                       | Go setup              |
| `circleci/ruby@x`       | `ruby/setup-ruby@v1`                        | Ruby setup            |
| `circleci/aws-cli@x`    | `aws-actions/configure-aws-credentials@v4`  | AWS CLI setup         |
| `circleci/docker@x`     | `docker/build-push-action@v5`               | Docker operations     |
| `circleci/kubernetes@x` | `azure/k8s-set-context@v3` + kubectl        | Kubernetes operations |
| `circleci/slack@x`      | `slackapi/slack-github-action@v1`           | Slack notifications   |
| `circleci/azure-cli@x`  | `azure/cli@v1`                              | Azure CLI setup       |
| `circleci/gcp-cli@x`    | `google-github-actions/setup-gcloud@v1`     | GCP CLI setup         |
| `circleci/android@x`    | `actions/setup-java@v4` + Android SDK setup | Android development   |
| `circleci/gradle@x`     | `gradle/gradle-build-action@v2`             | Gradle build          |
| `circleci/maven@x`      | `actions/setup-java@v4` + Maven             | Maven build           |

## Configuration Examples

### Basic Job Structure

**CircleCI:**
```yaml
version: 2.1

jobs:
  build:
    docker:
      - image: cimg/node:16.0
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: npm install
      - run:
          name: Run tests
          command: npm test

workflows:
  version: 2
  build-workflow:
    jobs:
      - build
```

**GitHub Actions:**
```yaml
name: CI

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: cimg/node:16.0
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: npm install

      - name: Run tests
        run: npm test
```

### Job Dependencies

**CircleCI:**
```yaml
workflows:
  version: 2
  build-test-deploy:
    jobs:
      - build
      - test:
          requires:
            - build
      - deploy:
          requires:
            - test
          filters:
            branches:
              only: main
```

**GitHub Actions:**
```yaml
name: CI/CD

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building..."

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - run: echo "Testing..."

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - run: echo "Deploying..."
```

### Executors to Runners

**CircleCI:**
```yaml
executors:
  node-executor:
    docker:
      - image: cimg/node:16.0
    resource_class: large

jobs:
  build:
    executor: node-executor
    steps:
      - checkout
      - run: npm install
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: cimg/node:16.0
    steps:
      - uses: actions/checkout@v4
      - run: npm install
```

### Caching Dependencies

**CircleCI:**
```yaml
steps:
  - checkout
  - restore_cache:
      keys:
        - v1-dependencies-{{ checksum "package-lock.json" }}
        - v1-dependencies-
  - run: npm install
  - save_cache:
      paths:
        - node_modules
      key: v1-dependencies-{{ checksum "package-lock.json" }}
```

**GitHub Actions:**
```yaml
steps:
  - uses: actions/checkout@v4

  - uses: actions/cache@v4
    with:
      path: node_modules
      key: v1-dependencies-${{ hashFiles('package-lock.json') }}
      restore-keys: |
        v1-dependencies-

  - run: npm install
```

### Artifacts and Workspaces

**CircleCI:**
```yaml
jobs:
  build:
    steps:
      - run: npm run build
      - persist_to_workspace:
          root: .
          paths:
            - dist
      - store_artifacts:
          path: dist

  deploy:
    steps:
      - attach_workspace:
          at: .
      - run: ./deploy.sh dist
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist

  deploy:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist

      - run: ./deploy.sh dist
```

### Matrix Builds (Parallelism)

**CircleCI:**
```yaml
jobs:
  test:
    docker:
      - image: cimg/node:16.0
    parallelism: 4
    steps:
      - run: |
          TESTFILES=$(circleci tests glob "test/**/*.js" | circleci tests split)
          npm test $TESTFILES
```

**GitHub Actions:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [14, 16, 18, 20]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}

      - run: npm test
```

### Service Containers

**CircleCI:**
```yaml
jobs:
  build:
    docker:
      - image: cimg/node:16.0
      - image: postgres:13
        environment:
          POSTGRES_PASSWORD: postgres
      - image: redis:6
    steps:
      - run: npm test
```

**GitHub Actions:**
```yaml
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

      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

### Conditional Execution

**CircleCI:**
```yaml
jobs:
  deploy:
    steps:
      - run:
          name: Deploy to production
          command: ./deploy.sh
          when: on_success
      - run:
          name: Rollback
          command: ./rollback.sh
          when: on_fail
```

**GitHub Actions:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        if: success()
        run: ./deploy.sh

      - name: Rollback
        if: failure()
        run: ./rollback.sh
```

### Approval Jobs

**CircleCI:**
```yaml
workflows:
  version: 2
  build-and-deploy:
    jobs:
      - build
      - hold:
          type: approval
          requires:
            - build
      - deploy:
          requires:
            - hold
```

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building..."

  deploy:
    runs-on: ubuntu-latest
    needs: build
    environment: production  # Requires approval in GitHub settings
    steps:
      - run: echo "Deploying..."
```

## Executor Type Mapping

| CircleCI Executor                     | GitHub Actions Runner                                 |
| ------------------------------------- | ----------------------------------------------------- |
| `docker: - image: cimg/base`          | `runs-on: ubuntu-latest`                              |
| `machine: image: ubuntu-2204:current` | `runs-on: ubuntu-22.04`                               |
| `macos: xcode: "14.0.0"`              | `runs-on: macos-12`                                   |
| `windows: version: "2022"`            | `runs-on: windows-2022`                               |
| `docker: - image: custom:latest`      | `runs-on: ubuntu-latest` + `container: custom:latest` |

## Context Variables Mapping

| CircleCI Context Variable     | GitHub Actions Equivalent                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------- |
| Context secrets               | `${{ secrets.SECRET_NAME }}` (Organization or Repository secrets)                     |
| Context environment variables | `${{ vars.VARIABLE_NAME }}` (Organization or Repository variables)                    |
| `CIRCLE_BUILD_NUM`            | `${{ github.run_number }}`                                                            |
| `CIRCLE_BUILD_URL`            | `${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}` |
| `CIRCLE_BRANCH`               | `${{ github.ref_name }}`                                                              |
| `CIRCLE_SHA1`                 | `${{ github.sha }}`                                                                   |
| `CIRCLE_TAG`                  | `${{ github.ref_name }}` (when triggered by tag)                                      |
| `CIRCLE_USERNAME`             | `${{ github.actor }}`                                                                 |
| `CIRCLE_PROJECT_REPONAME`     | `${{ github.event.repository.name }}`                                                 |
| `CIRCLE_REPOSITORY_URL`       | `${{ github.repositoryUrl }}`                                                         |
| `CIRCLE_WORKING_DIRECTORY`    | `${{ github.workspace }}`                                                             |



---

*This mapping guide is maintained as part of the CI/CD Migration Knowledge Base.*
