# Migration Workflow

This document outlines the standard 5-phase workflow for migrating CI/CD pipelines from any source system to GitHub Actions. All migration agents follow this consistent process.

## Phase 1: Source Requirement (FIRST)

**Critical First Step:**

- **ALWAYS** request the existing CI/CD configuration file(s) if not provided
- **REFUSE** to proceed without actual source configuration files
- **NEVER** create workflows based on descriptions or assumptions

**What to Look For:**

- Drone CI: `.drone.yml`, `.drone.yaml`
- Jenkins: `Jenkinsfile`, `*.jenkinsfile`, YAML pipeline configs, shared library files
- CircleCI: `.circleci/config.yml`
- GitLab CI: `.gitlab-ci.yml`
- Travis CI: `.travis.yml`
- Azure Pipelines: `azure-pipelines.yml`, `.azure-pipelines/*.yml`
- Bitbucket Pipelines: `bitbucket-pipelines.yml`

## Phase 2: Analysis Phase

**Thorough Examination:**

1. Examine provided configuration files thoroughly
2. Identify pipeline structure, dependencies, and complexity
3. Note CI-system-specific features being used
4. Assess potential migration challenges for each step type
5. Parse stages, jobs, and step configurations
6. Analyze triggers, conditions, and branching strategies
7. Map agents/executors/containers to GitHub runners

**Key Analysis Points:**

- Pipeline/workflow orchestration and job dependencies
- Build tools, plugins, and external integrations
- Credential bindings, secrets, and environment variables
- Caching mechanisms and artifact handling
- Matrix builds and parallel execution strategies
- Resource requirements and runner specifications

## Phase 3: Conversion Phase

**Core Conversion Principles:**

- Convert **ONLY** the functionality present in the source configuration
- Maintain equivalent behavior and functionality
- **Use ONLY existing verified GitHub Actions** from verified creators on [GitHub Marketplace](https://github.com/marketplace?type=actions)
- **Use LATEST STABLE VERSIONS** of all chosen GitHub Actions
- **NEVER create custom actions** - always find existing marketplace solutions
- Implement proper job dependencies and conditional execution
- Include comments explaining conversion choices
- Suggest optimizations while preserving original intent

**Conversion Tasks:**

- Map CI-specific steps to GitHub Actions equivalents
- Convert triggers and event filters to GitHub Actions `on:` syntax
- Translate conditional logic to GitHub Actions expressions
- Convert environment variables and secrets references
- Map service containers and external dependencies
- Implement artifact and cache strategies
- Preserve deployment gates and approval processes

## Phase 4: Validation Phase

**Testing and Verification:**

1. Execute actionlint for YAML syntax validation
2. Verify all job dependencies are correctly defined
3. Break down complex pipelines into manageable chunks
4. Explain differences in execution models between platforms
5. Test trigger and condition conversions
6. Validate secrets and variable references

**Validation Checklist:**

- [ ] YAML syntax is valid (no parsing errors)
- [ ] All required actions are available and using latest stable versions
- [ ] All actions are from verified creators on GitHub Marketplace
- [ ] Job dependencies are correctly defined
- [ ] Environment variables, secrets, and variables are properly referenced
- [ ] Conditional expressions are syntactically correct
- [ ] Workflow triggers match original behavior

For complete validation requirements and tool setup, see [Workflow Validation Requirements](docs/README.md#workflow-validation-requirements).

## Phase 5: Documentation Phase (FINAL)

**Complete Migration Documentation:**

1. **MANDATORY**: Create `.github/ci-archive/MIGRATION-README.md` with the completed report
2. **MANDATORY**: Deliver the migration report via the Pull Request workflow below
3. Include actual validation output, not placeholders
4. **MOVE** original CI/CD files to `.github/ci-archive/` (DELETE from original locations)
5. **VERIFY** no original CI/CD files remain in root directory or elsewhere
6. Complete all sections of the migration report template
7. Document all secrets and variables that need to be configured
8. Provide next steps for team adoption

### Pull Request Workflow

The `MIGRATION-README.md` file is **always created** in `.github/ci-archive/` as a permanent reference. Additionally, deliver the report via Pull Request:

1. **Check for an existing Pull Request** on the current branch using the GitHub MCP tool
2. **If a PR already exists** → update the PR body with the completed report template
3. **If no PR exists** → create a new Pull Request using the completed report template as the PR body
4. **If the PR cannot be created or updated** (e.g., MCP tool unavailable, insufficient permissions, no remote branch) → the `MIGRATION-README.md` file already created in step 1 above serves as the report

**Documentation Standards:**

- Use the appropriate report template for your CI system
- Fill all sections with actual migration data (no placeholders)
- Include real validation output (actionlint results)
- Create mermaid diagrams reflecting actual pipeline structure
- Document project-specific secrets and variables
- Capture migration notes, decisions, and considerations

See the [Report Templates](knowledge/report-template/) for CI-system-specific templates.

## Workflow Completion

A migration is **NOT COMPLETE** until:

- All 5 phases have been executed in order
- Validation has been performed with real output
- `.github/ci-archive/MIGRATION-README.md` has been created with the completed report
- The migration report has been delivered via PR (created or updated) where possible
- Original CI/CD files have been archived and removed from original locations
- All deliverables have been provided to the user

---

*This workflow ensures consistent, high-quality migrations across all CI/CD systems.*
