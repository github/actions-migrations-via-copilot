---
name: reusable-workflow-patterns
description: Catalog of common CI/CD patterns (build, test, deploy, security, quality), the reusable workflow template, selection criteria, and usage-documentation template. Load when scanning GitHub organizations to identify recurring CI/CD patterns and generate standardized `reusable-*.yml` workflows with corresponding `docs/<name>-usage.md` files.
---

# Reusable Workflow Patterns

This skill provides the catalog, template, and documentation standards used by the Reusable Workflow Builder agent to detect cross-platform CI/CD patterns and produce standardized GitHub Actions reusable workflows.

## Supported CI/CD systems for pattern discovery

| System         | File patterns                                   |
| -------------- | ----------------------------------------------- |
| GitHub Actions | `.github/workflows/*.yml`                       |
| GitLab CI/CD   | `.gitlab-ci.yml`                                |
| Azure DevOps   | `azure-pipelines.yml`, `.azure-pipelines/*.yml` |
| Jenkins        | `Jenkinsfile`, `.jenkins/*.groovy`              |
| CircleCI       | `.circleci/config.yml`                          |
| Travis CI      | `.travis.yml`                                   |
| Drone CI       | `.drone.yml`                                    |
| Others         | Bitbucket, TeamCity, Bamboo, Buildkite          |

## Pattern categories

- **🏗️ Build** — npm/Maven/Docker/language-specific build processes
- **🧪 Test** — unit, integration, E2E, security, performance testing
- **🚀 Deploy** — cloud (AWS/Azure/GCP), containers, serverless, infrastructure
- **🔒 Security** — SAST/DAST, dependency scanning, compliance checks
- **📊 Quality** — code coverage, linting, quality gates

## Selection criteria

A pattern becomes a reusable workflow when it shows:

- **High frequency** — 10+ repositories
- **Significant complexity** — 5+ steps
- **Low variation** — standardizable
- **Clear parameters** — configurable inputs

## Pattern-recognition workflow

1. **Repository enumeration** — list all repos in target organizations
2. **Universal pipeline discovery** — find CI/CD files across all systems
3. **Cross-platform content analysis** — parse configurations
4. **Universal pattern extraction** — identify common structures and steps
5. **Cross-system frequency analysis** — count pattern occurrences
6. **Translation scoring** — rank by frequency, complexity reduction, conversion feasibility
7. **Platform mapping** — map equivalent concepts to GitHub Actions

## Reusable workflow template

```yaml
name: Reusable Node.js Build Workflow
on:
  workflow_call:
    inputs:
      node-version:
        description: 'Node.js version to use'
        required: false
        default: '18'
        type: string
      build-command:
        description: 'Custom build command'
        required: false
        default: 'npm run build'
        type: string
    outputs:
      build-success:
        description: 'Build success status'
        value: ${{ jobs.build.outputs.success }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # ✅ Only verified actions from trusted publishers
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
      - run: npm install
      - run: ${{ inputs.build-command }}
```

## Output file rules

For **every** reusable workflow produced, create **exactly two** files:

1. `.github/workflows/reusable-<name>.yml` — the reusable workflow (`workflow_call` trigger only)
2. `docs/<name>-usage.md` — the usage documentation (one per workflow, 1:1)

**Never** create: `README.md`, `WORKFLOWS.md`, consolidated docs, scripts (`.sh`, `.bat`, `.ps1`, `.py`, `.js`), custom actions, caller workflows, or workflow templates.

## Usage documentation template

Each `docs/<name>-usage.md` must contain:

````markdown
# Reusable [Workflow Name] Usage Guide

## Pattern Analysis Summary
- **Frequency**: Found in X repositories across Y organizations
- **Source CI/CD Systems**: [List systems: GitHub Actions, GitLab CI, Jenkins, etc.]
- **Complexity Reduction**: [Explain how this replaces X previous steps]

## Migration Benefits
- **From GitLab CI**: [If applicable, before/after]
- **From Jenkins**: [If applicable, before/after]
- **From Azure DevOps**: [If applicable, before/after]
- **Standardization**: [Consistency improvements]

## Basic Usage Example
```yaml
name: Example Workflow
on: [push, pull_request]

jobs:
  job-name:
    uses: ./.github/workflows/reusable-[name].yml
    with:
      param1: 'value1'
      param2: 'custom-value'
```

## Advanced Usage Example
```yaml
name: Production Workflow
on:
  push:
    branches: [main]

jobs:
  job-name:
    uses: ./.github/workflows/reusable-[name].yml
    with:
      param1: 'production-value'
      param2: 'advanced-setting'
    secrets:
      SECRET_NAME: ${{ secrets.SECRET_NAME }}
```

## Input Parameters Reference
| Parameter | Description   | Required | Default     | Example    |
| --------- | ------------- | -------- | ----------- | ---------- |
| param1    | [Description] | Yes      | -           | `'value'`  |
| param2    | [Description] | No       | `'default'` | `'custom'` |

## Output Reference
| Output  | Description   | Type   |
| ------- | ------------- | ------ |
| output1 | [Description] | string |

## Migration Examples
### From GitLab CI
**Before (.gitlab-ci.yml):**
```yaml
[Show original GitLab CI configuration]
```

**After (GitHub Actions):**
```yaml
[Show how to use this reusable workflow instead]
```

### From Jenkins
**Before (Jenkinsfile):**
```groovy
[Show original Jenkins configuration]
```

**After (GitHub Actions):**
```yaml
[Show how to use this reusable workflow instead]
```

## Best Practices
- [Specific best practices for using this workflow]
- [Security considerations]
- [Performance tips]
````

## Quality and security requirements

- **Verified publishers only**: prioritize `actions/*`, `azure/*`, `aws-actions/*`, `google-github-actions/*`
- **Latest stable versions** of all actions, pinned to commit SHA (see `migration-core` guardrails)
- **Trigger**: `workflow_call` only
- **Location**: `.github/workflows/reusable-<name>.yml`
- **Validation**: every workflow must pass `actionlint`
