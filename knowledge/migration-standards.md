# Migration Standards & Deliverables

This document defines the mandatory deliverables, archival protocols, and completion standards for all CI/CD migrations to GitHub Actions.

## ✅ Mandatory Deliverables

Every migration must produce the following deliverables:

### 1. Complete Workflows

- Runnable GitHub Actions workflow files (`.github/workflows/*.yml`)
- Workflows that replicate source functionality accurately
- Proper job dependencies and execution order
- Appropriate triggers matching original behavior

### 2. Secret and Variable Migration

- Convert source CI secrets to GitHub Secrets
- Convert environment variables to GitHub Variables
- Document all required secrets and variables
- Provide clear configuration instructions

### 3. Conversion Explanations

- Clear documentation of migration decisions
- Explanation of behavioral changes (if any)
- Notes on platform differences and workarounds
- Comments in workflow files explaining conversion choices

### 4. Validation Results

- Execute linting (actionlint) with real output
- Include validation results in migration report
- Document any warnings or issues found
- Provide resolution steps for validation failures

### 5. Security Improvements

- Maintain original functionality while enhancing security
- Implement least-privilege permissions
- Use verified marketplace actions only
- Pin actions to commit SHAs when required
- Separate sensitive credentials using appropriate storage types

### 6. Performance Optimizations

- Suggest caching strategies for dependencies
- Recommend parallelization opportunities
- Optimize job execution order
- Suggestions that don't alter core behavior

### 7. File Archival

- **MOVE** original CI/CD files to `.github/ci-archive/`
- **DELETE** files from original locations (not copy)
- Preserve original files for reference only
- Ensure no CI/CD conflicts remain

### 8. Migration Documentation

- Always create `.github/ci-archive/MIGRATION-README.md` with the completed migration report
- Additionally deliver the report via Pull Request: check for an existing PR on the current branch, update its body if found, or create a new PR if not
- If the PR cannot be created or updated, the `MIGRATION-README.md` file serves as the sole report
- Fill all template sections with real data
- No placeholders or incomplete sections
- Include actual validation output

## 📋 Archival & Documentation Protocol

⚠️ **MIGRATION IS NOT COMPLETE UNTIL `.github/ci-archive/MIGRATION-README.md` IS CREATED AND THE MIGRATION REPORT HAS BEEN DELIVERED VIA PULL REQUEST WHERE POSSIBLE**

### File Archival Process

#### Step 1: Create Archive Directory

```bash
mkdir -p .github/ci-archive/
```

#### Step 2: Move Original CI/CD Files

Files must be **MOVED** (not copied) to the archive. Files must be **REMOVED** from original locations:

##### Examples by CI System

- Drone CI: `.drone.yml` → `.github/ci-archive/.drone.yml` (DELETE original)
- Jenkins: `Jenkinsfile` → `.github/ci-archive/Jenkinsfile` (DELETE original)
- CircleCI: `.circleci/config.yml` → `.github/ci-archive/circleci-config.yml` (DELETE original directory)
- GitLab CI: `.gitlab-ci.yml` → `.github/ci-archive/.gitlab-ci.yml` (DELETE original)
- Travis CI: `.travis.yml` → `.github/ci-archive/.travis.yml` (DELETE original)
- Azure Pipelines: `azure-pipelines.yml` → `.github/ci-archive/azure-pipelines.yml` (DELETE original)

#### Step 3: Verify Cleanup

- **VERIFY** no CI/CD files remain in root directory or anywhere else
- **ENSURE** CI/CD files exist ONLY in `.github/ci-archive/`
- Check for hidden directories (`.circleci/`, `.github/workflows/` conflicts)

### Documentation Requirements

#### Step 4: Deliver Migration Report

**Always** create `.github/ci-archive/MIGRATION-README.md` with the completed report. Additionally, deliver the report via Pull Request:

1. **Check for an existing Pull Request** on the current branch using the GitHub MCP tool
2. **If a PR already exists** → update the PR body with the completed report template
3. **If no PR exists** → create a new Pull Request using the completed report template as the PR body
4. **If the PR cannot be created or updated** (e.g., MCP tool unavailable, insufficient permissions, no remote branch) → the `MIGRATION-README.md` already created above serves as the report

Use the appropriate report template for your CI system:

- [Azure DevOps Migration Report Template](knowledge/report-template/azure-devops.md)
- [Bamboo Migration Report Template](knowledge/report-template/bamboo.md)
- [Bitbucket Migration Report Template](knowledge/report-template/bitbucket.md)
- [CircleCI Migration Report Template](knowledge/report-template/circleci.md)
- [Drone CI Migration Report Template](knowledge/report-template/droneci.md)
- [GitLab Migration Report Template](knowledge/report-template/gitlab.md)
- [Jenkins Migration Report Template](knowledge/report-template/jenkins.md)
- [Travis CI Migration Report Template](knowledge/report-template/travisci.md)

#### Step 5: Execute Validation

Execute validation steps and include **real output** in the PR body:

```bash
# Run actionlint
actionlint .github/workflows/*.yml

# Capture output for report
actionlint .github/workflows/*.yml > validation-output.txt 2>&1
```

#### Step 6: Fill Template Sections

Fill in all metrics, diagrams, and checklists with **actual data**:

- Migration overview metrics (before/after comparison)
- Conversion diagrams (mermaid charts)
- Step conversion mappings
- Secret and variable requirements
- Validation results
- Security improvements
- Performance enhancements
- Next steps

#### Step 7: Use Clear Formatting

Ensure the report is well-formatted, readable, and comprehensive.

## 🔒 MANDATORY Validation Output Integration

When creating the migration Pull Request, you MUST:

1. **EXECUTE** actionlint and include actual output in the report
2. **CALCULATE** and fill in the metrics table with real data from the migration
3. **CREATE** and update mermaid diagrams to reflect actual pipeline structure
4. **LIST** specific step conversions that were performed
5. **DOCUMENT** any project-specific migration notes
6. **VERIFY** all secrets and variables are documented
7. **INCLUDE** next steps for completing the migration

### Validation Output Format

````markdown
## ✅ Validation Results

### Linting Results

```
[Paste actual actionlint output here - no placeholders]
```

### Manual Verification Checklist

- [x] YAML syntax validated
- [x] All actions properly versioned
- [x] Job dependencies verified
- [x] Environment variables migrated
- [x] Secrets and variables properly referenced
- [x] Triggers match original behavior
````

⛔ **NO PLACEHOLDERS ALLOWED**: All validation output must be real execution results
⛔ **NO INCOMPLETE REPORTS**: Every section must be filled with actual data
⛔ **NO EXCEPTIONS**: This is required for EVERY migration, without exception

## 🧪 Workflow Validation Requirements

### Required Tools

Inform users they need these tools for proper validation (Linux only):

```bash
# Install actionlint for YAML linting (Linux)
# Pin to a specific version. Check https://github.com/rhysd/actionlint/releases for newer releases.
ACTIONLINT_VERSION="1.7.11"

# Download the binary and checksums file separately (do NOT pipe directly into tar)
curl -fsSLO "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
curl -fsSLO "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_checksums.txt"

# Verify SHA-256 checksum before extracting — abort if verification fails
sha256sum --check --ignore-missing "actionlint_${ACTIONLINT_VERSION}_checksums.txt"

# (Recommended) Also verify the artifact attestation using GitHub CLI (requires gh >= 2.49)
# gh attestation verify --repo rhysd/actionlint "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"

# Extract and install only after successful verification
tar xzf "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" -C /tmp actionlint
sudo install -m 755 /tmp/actionlint /usr/local/bin/actionlint

# Clean up downloaded artifacts
rm "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" "actionlint_${ACTIONLINT_VERSION}_checksums.txt"

# Install GitHub CLI (optional, for additional validation)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
sudo apt update && sudo apt install gh
```

### Validation Steps

To ensure the correctness and security of your migrated GitHub Actions workflows:

#### 1. Syntax Linting

Execute actionlint for GitHub Actions YAML validation:

```bash
# Using actionlint (recommended)
actionlint .github/workflows/your-workflow.yml
```

> ⚠️ Any syntax errors must be resolved before proceeding.

## 📋 Migration Completion Checklist

Before ending any migration conversation, verify ALL items are complete:

1. [ ] **Source Analysis**: Analyzed provided CI/CD configuration file(s)
2. [ ] **Workflow Conversion**: Created equivalent GitHub Actions workflow(s)
3. [ ] **Validation Execution**: Ran actionlint validation with real output
4. [ ] **Security Review**: Implemented proper GitHub secrets and variables management
5. [ ] **Performance Optimization**: Added caching and parallelization improvements
6. [ ] **File Archival**: MOVED original CI/CD files to `.github/ci-archive/`
7. [ ] **Original File Cleanup**: VERIFIED no CI/CD files remain in original locations
8. [ ] **Archived Migration Report**: VERIFIED `.github/ci-archive/MIGRATION-README.md` EXISTS AND IS COMPLETE
9. [ ] **Migration Pull Request**: CREATED PULL REQUEST WITH COMPLETE MIGRATION REPORT AS PR BODY
10. [ ] **Validation Results**: INCLUDED ACTUAL VALIDATION OUTPUT IN PR BODY
11. [ ] **Migration Report**: FILLED ALL SECTIONS OF REPORT TEMPLATE IN PR BODY

⛔ **MIGRATION IS NOT COMPLETE UNTIL ALL 11 ITEMS ARE CHECKED**

## Quality Standards

### Documentation Quality

- Clear, concise explanations
- Accurate technical details
- Complete coverage of all changes
- Professional formatting
- No typos or grammatical errors

### Code Quality

- Valid YAML syntax
- Proper indentation and formatting
- Meaningful job and step names
- Helpful comments where needed
- Follows GitHub Actions best practices

### Validation Quality

- Real output from validation tools
- All warnings addressed or documented
- Known issues clearly explained
- Workarounds provided where needed

---

*These standards ensure consistent, high-quality migrations that teams can rely on.*
