# Workflow Validation

This document defines the required validation tools, installation steps, and execution procedures for verifying migrated GitHub Actions workflows. All migration agents reference this document during the validation phase.

## Required Tools

### actionlint — YAML Syntax Linting

actionlint validates GitHub Actions workflow YAML for syntax errors, type mismatches, and structural issues.

**Installation (Linux):**
```bash
curl -sL https://github.com/rhymond/actionlint/releases/latest/download/actionlint_linux_amd64.tar.gz | tar xz -C /tmp && sudo mv /tmp/actionlint /usr/local/bin/
```

**Usage:**
```bash
# Lint all workflows
actionlint .github/workflows/*.yml

# Lint a specific workflow
actionlint .github/workflows/your-workflow.yml

# Capture output for the migration report
actionlint .github/workflows/*.yml > validation-output.txt 2>&1
```

**Any syntax errors must be resolved before proceeding.**

### CodeQL — Actions Workflow Security Scanning

CodeQL supports scanning GitHub Actions workflow files using the `actions` language. This detects security vulnerabilities that actionlint does not catch, including:
- **Script injection** — untrusted input (e.g., `github.event.pull_request.title`) used directly in `run:` steps
- **Excessive permissions** — overly broad `GITHUB_TOKEN` permissions
- **Credential exposure** — secrets referenced in insecure contexts
- **Other workflow security anti-patterns**

**Installation:**
```bash
# Via GitHub CLI extension (recommended)
gh extension install github/gh-codeql

# Or download directly from https://github.com/github/codeql-action/releases
```

**Usage:**
```bash
# Create CodeQL database for Actions workflows
codeql database create codeql-actions-db --language=actions --source-root=.

# Analyze the database for security issues (SARIF output for upload)
codeql database analyze codeql-actions-db --format=sarif-latest --output=codeql-actions-results.sarif

# Analyze the database (CSV output for the migration report)
codeql database analyze codeql-actions-db --format=csv --output=codeql-actions-results.csv
```

**Any high or critical CodeQL findings must be resolved before proceeding.**

### GitHub CLI (Optional)

```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
sudo apt update && sudo apt install gh
```

## Validation Execution Checklist

During the migration validation phase, execute both tools and verify:

- [ ] **actionlint** passes with no errors
- [ ] **CodeQL Actions scan** passes with no high/critical findings
- [ ] All required actions are available and using latest stable versions
- [ ] All actions are from verified creators on GitHub Marketplace
- [ ] Job dependencies are correctly defined
- [ ] Environment variables, secrets, and variables are properly referenced
- [ ] Conditional expressions are syntactically correct
- [ ] Workflow triggers match original behavior

## Migration Report Integration

Include **real output** from both tools in the migration report. Use the validation section from the appropriate [report template](report-template/):

```markdown
## ✅ Validation Results

### Linting Results:
```
[Paste actual actionlint output here — no placeholders]
```

### CodeQL Actions Scan Results:
```
[Paste actual CodeQL actions scan output here — no placeholders]
```
```

⛔ **NO PLACEHOLDERS ALLOWED**: All validation output must be real execution results.

## Ongoing Security: Enable CodeQL in the Repository

After migration, recommend enabling CodeQL Actions scanning in the target repository for continuous workflow security analysis:

> **Settings → Code security → CodeQL analysis → Enable Actions language**

This ensures new workflow changes are automatically scanned for security vulnerabilities.
