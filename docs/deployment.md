# Deployment Guide

Install the migration plugin for local or cloud use. Batch orchestration is
optional and still runs as a GitHub Actions workflow.

## Quick Setup

1. Enable the plugin using repository or selected central configuration.
2. Start a test session and confirm the required skills are available.
3. For batch work, configure the orchestration repository's secrets and skill mappings.
4. Run a small migration and inspect the resulting workflow, report, and runtime logs.

## Prerequisites

- Copilot access for the runtime you intend to use; plugins are not enterprise-only.
- Permission to configure the target repository, or the selected central organization/enterprise configuration.
- For batch work, GitHub App access for repository discovery and a user token for cloud-agent issue assignment.

## Step 1: Enable the Plugin

For cloud jobs, use the settings in the [consumer template](../consumer-template/README.md).
They belong in `.github/copilot/settings.json` in the target repository, or the
selected central configuration repository. Review existing settings before merging
the plugin entry; do not overwrite unrelated plugins or user configuration.

The settings register a marketplace and enable `actions-migrator` from it. The
runtime obtains the package and loads its skills and hooks. Configuration alone is
not proof it loaded: confirm the resolved package revision and skill invocation in
the cloud logs. Organization or enterprise settings may affect repository choices.

For CLI and VS Code, use the [plugin installation guide](../plugin/README.md).

## Step 2: Prepare Batch Orchestration (Optional)

### Clone Repository

```bash
git clone https://github.com/github/actions-migrations-via-copilot.git
cd actions-migrations-via-copilot
```

No organization substitution in migration guides is needed. All guides are bundled
in `plugin/skills/`. Keep the plugin configuration source and batch workflow checkout
clear: having plugin files in the orchestration checkout does not install them in
the target cloud job.

### Choose an Orchestration Repository

```bash
git remote add enterprise https://github.com/YOUR-ORG-SLUG/.github-private.git
git push enterprise main
```

The example uses `.github-private` for continuity with existing deployments. Do
not overwrite an existing central configuration repository. Use your approved
deployment/update process to bring in the automation and preserve existing settings.

## Step 3: Configure Repository Settings

### Create GitHub App (for automation workflows)

1. **Create app** at `https://github.com/organizations/YOUR-ORG-SLUG/settings/apps`:
   - Name: `CI/CD Migration Automation`
   - Webhook: Inactive
   - Repository permissions: Contents (R/W), Issues (R/W), Pull requests (R/W), Workflows (R/W)
   - Organization permissions: Custom properties (Read), Members (Read)
   - Where to install: "This enterprise"

2. **Generate private key** and save the `.pem` file

3. **Install app** in your organizations (select "All repositories")

4. **Note the App ID** from the app settings page

### Create Personal Access Token

Generate a Classic PAT with:

- Scopes: `repo`, `admin:org`
- SSO authorization: Enable for all organizations
- Expiration: Per your organization policy

### Add Secrets

Navigate to `https://github.com/YOUR-ORG-SLUG/.github-private/settings/secrets/actions`

| Secret Name          | Value                                             |
| -------------------- | ------------------------------------------------- |
| `GH_APP_PEM`         | Contents of `.pem` file (include BEGIN/END lines) |
| `ISSUE_SUBMIT_TOKEN` | PAT value                                         |

### Configure Settings

Edit `.github/settings/config.yaml`:

```yaml
gh_app_id: '123456'  # Your GitHub App ID

migration_type_skills:
   Jenkins: jenkins-migration

gh_migration_type:
  default_value: 'Jenkins'
  description: 'The type of migration for this repository'
  other_values:
    - 'Jenkins'
    - 'Azure DevOps'
    - 'CircleCI'
    - 'GitLab'
    - 'Travis CI'
    - 'Bamboo'
    - 'Bitbucket'
    - 'DroneCI'

organizations:
  - 'YOUR-ORG-SLUG'

batch_size: 100
```

Commit and push:

```bash
git add .github/settings/config.yaml
git commit -m "Configure automation settings"
git push enterprise main
```

### Bootstrap Repository Variables

Run the Settings workflow to create variables from config:

1. Go to `https://github.com/YOUR-ORG-SLUG/.github-private/actions`
2. Click **"Configuration Settings"** workflow
3. Click **"Run workflow"** → Select `main` → **"Run workflow"**
4. Verify success (green checkmark)
5. Check variables at `https://github.com/YOUR-ORG-SLUG/.github-private/settings/variables/actions`

Expected variables include `GH_APP_ID`, `MIGRATION_TYPE_SKILLS`, `ORGANIZATIONS`, and `BATCH_SIZE`.

The sample configuration contains mappings for all eight migration platforms.
`MIGRATION_TYPE_SKILLS` maps platform labels to installed skills, not filenames.
Recognized old `migration_type_prompts` / `MIGRATION_TYPE_PROMPTS` values still
work as aliases and emit a warning; the script never reads the old prompt files.
If both mappings exist, they must describe the same platform/skill pairs. Resolve
conflicts by updating or removing the old variable before running the batch.

### Runtime Credentials

The bundled guides do not require a knowledge-fetch MCP token. Keep authentication
needed for the actual migration: issue assignment uses `ISSUE_SUBMIT_TOKEN`, and
runtime GitHub operations or action-version resolution may need separately approved
access. Do not remove credentials used by unrelated integrations.

## Step 4: Verify Plugin Loading

Start a new session after configuring the plugin. Confirm the resolved plugin
revision and the expected skill names in runtime logs. A plugin is not the same as
a registered custom agent: this batch workflow uses the default cloud agent and
does not assume the plugin's agents appear in the GitHub picker.

## Step 5: Test Your Deployment

1. Choose a small test repository with real source CI configuration.
2. Ask Copilot to use the installed `migration-core`, platform migration, and `actionlint` skills.
3. Verify actual skill invocation, hook execution, generated workflow, archival, and safe report content.
4. Test unavailable-plugin behavior in an isolated environment with no inherited plugin. The task instructs the agent to stop; this is not a deterministic runtime availability check.
5. Do not equate successful issue assignment or workflow status with successful migration. Review the output before accepting it.

## Maintaining Your Deployment

### Update Agents

When adding new agents (see [extending.md](extending.md)):

1. Edit agent entry files in `plugin/agents/` and guidance in `plugin/skills/`.
2. Run plugin validation and hook tests.
3. Review and publish changes through your approved plugin distribution process.
4. Start a new test session and verify the loaded revision before rollout.

```bash
# After adding new agent
git add plugin/
git commit -m "Add <platform> migration agent"
git push
```

Do not assume caches refresh immediately or that an unmerged branch is used by the marketplace.

### Update Knowledgebase

Update mappings and patterns as Actions evolves:

```bash
# Edit the single maintained plugin guide
nano plugin/skills/jenkins-migration/mapping.md

# Commit and push
git add plugin/skills/
git commit -m "Update action mappings"
git push
```

New sessions use the package revision resolved by their runtime. Existing published
tags remain immutable. Before upgrading a legacy deployment, record its working
release or commit and retain that checkout for rollback; this refactor does not
publish a release or change customer configuration automatically.

### Monitor Usage

- Review Copilot usage reports in Enterprise settings
- Collect feedback from migration teams
- Update knowledgebase based on real-world patterns
- Refine agents based on common issues

## Troubleshooting

| Issue                                                 | Solution                                                                       |
| ----------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Skills unavailable** | Check the selected configuration source, plugin-resolution errors, and loaded revision. Do not substitute a generic migration. |
| **Plugin agents not in picker** | Plugin loading and named-agent registration are separate. Batch submission uses the default agent with explicit skill references. |
| **Conflicting mappings** | Reconcile `MIGRATION_TYPE_SKILLS` and the legacy `MIGRATION_TYPE_PROMPTS` variable before running again. |
| **Validation errors in migrations**                   | Review migration report, update knowledgebase mappings                         |

## Security Best Practices

- Keep `.github-private` Internal visibility (never Public)
- Review repository access regularly
- Monitor agent usage in audit logs
- Validate GitHub Secrets configuration in migrated workflows
- Use environment protection rules for sensitive workflows

## Next Steps

- **[Operations Guide](operations.md)** - Learn how to use migration agents
- **[Extending Guide](extending.md)** - Add support for new CI/CD platforms
- Train teams on agent invocation
- Establish migration workflows
- Monitor and iterate based on feedback
