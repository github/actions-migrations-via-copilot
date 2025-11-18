# DroneCI to GitHub Actions Mapping Guide
This guide provides a mapping of common DroneCI syntax and configurations to their equivalent GitHub Actions. Use this as a reference when migrating your CI/CD pipelines from DroneCI to GitHub Actions.

## Common Commands Mapping

| DroneCI Command/Concept                | GitHub Actions Equivalent                        | Description                           |
| -------------------------------------- | ------------------------------------------------ | ------------------------------------- |
| `pipeline`                             | `workflow`                                       | Top-level definition of CI/CD process |
| `kind: pipeline`                       | `name:` in workflow file                         | Defines the pipeline/workflow type    |
| `steps:`                               | `jobs:`                                          | Collection of execution steps         |
| `- name: build`                        | `jobs.<job_id>:`                                 | Individual step/job definition        |
| `commands:`                            | `run:`                                           | Shell commands to execute             |
| `image: node:16`                       | `container: node:16` or `runs-on: ubuntu-latest` | Execution environment                 |
| `when:`                                | `if:`                                            | Conditional execution                 |
| `trigger:`                             | `on:`                                            | Event triggers for pipeline           |
| `trigger: branch: main`                | `on: push: branches: [main]`                     | Branch-specific triggers              |
| `trigger: event: [push, pull_request]` | `on: [push, pull_request]`                       | Multiple event triggers               |
| `depends_on:`                          | `needs:`                                         | Job dependencies                      |
| `environment:`                         | `env:`                                           | Environment variables                 |
| `secrets:`                             | `secrets:`                                       | Secret management                     |
| `volumes:`                             | `services:` or persistent storage                | Volume mounting                       |
| `services:`                            | `services:`                                      | Service containers (databases, etc.)  |
| `clone: disable: true`                 | `actions/checkout` with custom settings          | Repository cloning control            |
| `workspace:`                           | `working-directory:`                             | Working directory configuration       |
| `failure: ignore`                      | `continue-on-error: true`                        | Error handling                        |
| `detach: true`                         | Background job pattern                           | Detached process execution            |
| `privileged: true`                     | Docker-in-Docker setup                           | Privileged container mode             |
| `pull: always`                         | `container: options:`                            | Image pull policy                     |
| `settings:`                            | Action inputs or `with:`                         | Plugin/action configuration           |
| `drone/git` plugin                     | `actions/checkout`                               | Git checkout action                   |
| `drone/docker` plugin                  | `docker/build-push-action`                       | Docker build and push                 |
| `plugins/slack`                        | `slackapi/slack-github-action`                   | Slack notifications                   |
| `drone exec`                           | Local testing not directly supported             | Local pipeline execution              |
| `.drone.yml`                           | `.github/workflows/*.yml`                        | Pipeline configuration file           |

## Configuration Examples

### Basic Pipeline Structure

**DroneCI:**
```yaml
kind: pipeline
name: default

steps:
  - name: build
    image: node:16
    commands:
      - npm install
      - npm test
```

**GitHub Actions:**
```yaml
name: default

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 16
      - run: npm install
      - run: npm test
```

