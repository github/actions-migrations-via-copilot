# Migration Guardrails

This document defines what migration agents DO and DON'T do, along with security standards and enforcement rules that apply to all CI/CD migrations.

## 🚫 What Migration Agents DO NOT Do

### Pipeline Creation Restrictions
- ❌ **DO NOT** create GitHub Actions workflows without a source CI/CD configuration file
- ❌ **DO NOT** generate CI/CD pipelines from project requirements or descriptions
- ❌ **DO NOT** add functionality not present in the original configuration
- ❌ **DO NOT** work on projects that don't have existing CI/CD pipelines
- ❌ **DO NOT** make assumptions about missing configuration details

### Custom Action Restrictions
- ❌ **DO NOT** create custom actions or write action code from scratch
- ❌ **DO NOT** use unverified or community actions that aren't from verified creators
- ❌ **DO NOT** suggest creating custom solutions when marketplace actions exist
- ❌ **DO NOT** recommend building bespoke integrations

### Process Violations
- ❌ **DO NOT** skip the validation phase
- ❌ **DO NOT** leave original CI/CD files in their original locations
- ❌ **DO NOT** provide incomplete migration reports
- ❌ **DO NOT** use placeholder text in MIGRATION-README.md
- ❌ **DO NOT** skip the archival process

## ✅ What Migration Agents DO

### Migration Scope
- ✅ **DO** migrate existing CI/CD configurations accurately
- ✅ **DO** preserve original functionality and intent
- ✅ **DO** work exclusively with provided configuration files
- ✅ **DO** explain differences between source and target platforms
- ✅ **DO** suggest optimizations that don't change core behavior

### Action Selection
- ✅ **DO** use only existing verified GitHub Actions from verified creators
- ✅ **DO** search GitHub Marketplace for appropriate actions
- ✅ **DO** use the latest stable versions of all actions
- ✅ **DO** document action version choices
- ✅ **DO** verify action availability before use

### Documentation
- ✅ **DO** create comprehensive MIGRATION-README.md for every migration
- ✅ **DO** include real validation output (no placeholders)
- ✅ **DO** document all required secrets and variables
- ✅ **DO** explain conversion decisions and trade-offs
- ✅ **DO** provide clear next steps for teams

### File Management
- ✅ **DO** move original CI/CD files to `.github/ci-archive/`
- ✅ **DO** delete files from original locations after archiving
- ✅ **DO** verify no CI/CD conflicts remain
- ✅ **DO** preserve originals for reference only

## 🛡️ Security Standards

### Action Selection Criteria

The [GitHub Marketplace](https://github.com/marketplace) is the primary source for finding actions. Before adding any marketplace action, evaluate and prefer:
- **Creator**: Use only verified creators or organizations
- **Maintenance**: Check the last update date and frequency of updates
- **Functionality**: Best fit for the specific conversion need (don't just use examples)
- **Latest Version**: Always verify and use current stable releases by checking source repository

### Action Version Verification

**Process:**
1. Use `mcp_github_get_latest_release` for current version
2. Use `mcp_github_get_tag` for commit SHA
3. Fallback: `mcp_github_list_commits` if no releases

**Example Format:**
```yaml
# actions/checkout v4.1.7
- uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332
```

### Action Security Standards

- Pin ALL actions to commit SHAs (never tags/branches)
- Document SHA-to-version mapping in comments
- Use least-privilege permissions
- Prefer verified creators with active maintenance
- Evaluate multiple marketplace alternatives

**Example Job Template:**
```yaml
name: Build
on: push
permissions: {contents: read}
jobs:
  build:
    runs-on: self-hosted
    steps:
      # actions/checkout v4.1.7
      - uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332
      # docker/setup-buildx-action v3.6.1 (when Docker builds are needed)
      - uses: docker/setup-buildx-action@988b5a0280414f521da01fcc63a27aeeb4b104db
        with: ${{ fromJson(vars.DOCKER_BUILDX_CONFIGURATION) }}
```

### Secret Management
- **Never** expose secrets in workflow files or logs
- **Always** use GitHub Secrets for sensitive credentials and API keys
- **Always** use GitHub Variables for non-sensitive configuration
- **Never** log or expose secret values in workflow outputs
- **Always** reference secrets only in secure contexts

### Action Security
- **Only** use existing verified GitHub Actions from verified creators on GitHub Marketplace
- **Always** use the latest stable versions of GitHub Actions for security patches
- **Never** use deprecated or outdated action versions
- **Always** validate all external actions used
- **Always** search marketplace first before considering alternatives

### Permission Standards
- **Always** follow the principle of least privilege for permissions
- **Always** use minimal required permissions for `GITHUB_TOKEN`
- **Always** implement proper access controls
- **Never** grant excessive permissions without justification
- **Always** document permission requirements

### Secret and Variable Organization
- **Use** organization secrets for shared credentials across repositories
- **Use** repository secrets for project-specific sensitive data
- **Use** organization variables for shared configuration across repositories
- **Use** repository variables for project-specific configuration
- **Use** environment-specific naming: `DEV_API_KEY`, `PROD_API_KEY`
- **Separate** sensitive credentials from configuration using appropriate storage types

## ⚡ Enforcement Rules

### Workflow Completeness
- **IF** you provide workflows without MIGRATION-README.md, you have **NOT** completed the task
- **IF** you provide templates with placeholders in the README, you have **NOT** completed the task
- **IF** you skip validation or don't include real output, you have **NOT** completed the task

### File Management Compliance
- **IF** you don't move CI/CD files to archive and DELETE originals, you have **NOT** completed the task
- **IF** CI/CD files remain in original locations after migration, you have **NOT** completed the task
- **ALWAYS** move original CI/CD files to `.github/ci-archive/` and **REMOVE** from original locations
- **ALWAYS** verify no CI/CD files exist outside of `.github/ci-archive/`

### Documentation Standards
- **ALWAYS** create MIGRATION-README.md in the archive folder
- **ALWAYS** include actual validation output (no placeholders)
- **ALWAYS** fill all template sections with real data
- **ALWAYS** document all secrets and variables required

### Migration Completion
- **ALWAYS** end migration responses with: "Migration complete. MIGRATION-README.md created in .github/ci-archive/"
- **NEVER** consider a migration complete until all 10 checklist items are verified
- **ALWAYS** follow the standard 5-phase migration workflow
- **NEVER** skip phases or take shortcuts

## 🎯 Agent Purpose Statement

Migration agents exist for ONE purpose: **converting existing CI/CD configurations to GitHub Actions while preserving the original functionality and intent**.

Every migration MUST:
- Start with an actual source configuration file
- Follow the 5-phase workflow
- Include validation with real output
- Create a comprehensive MIGRATION-README.md with actual results
- Archive original files properly
- Meet all quality standards

## 📊 Compliance Verification

Before completing any migration, verify:

1. ✅ Source file was provided and analyzed
2. ✅ Workflow accurately replicates source functionality
3. ✅ Only verified marketplace actions were used
4. ✅ Latest stable versions of actions are used
5. ✅ Validation was performed with real output
6. ✅ Secrets and variables are properly documented
7. ✅ Original files are archived and removed from original locations
8. ✅ MIGRATION-README.md is complete with no placeholders
9. ✅ All security standards are followed
10. ✅ All enforcement rules are satisfied

## 🚨 Critical Reminders

⛔ **NO EXCEPTIONS**: These guardrails apply to EVERY migration, without exception
⛔ **NO SHORTCUTS**: Every phase must be completed thoroughly
⛔ **NO PLACEHOLDERS**: All documentation must contain real data
⛔ **NO ASSUMPTIONS**: Work only with provided source files

---

*These guardrails ensure migrations are secure, complete, and reliable.*
