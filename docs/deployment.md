# Deployment Guide

Deploy GitHub Actions Migration Agents to your GitHub Enterprise environment.

## Quick Setup

1. Create `.github-private` repository (Internal visibility)
2. Clone and configure this repository
3. Push to `.github-private`
4. Configure secrets and variables for automation
5. Create the `COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN` Copilot Agents secret in each target organization (manual)
6. Enable agents in Enterprise settings

## Prerequisites

- GitHub Enterprise Cloud with Copilot Business/Enterprise
- Enterprise Owner permissions
- Organization Admin permissions
- Git client

## Step 1: Create .github-private Repository

1. **Create repository** in your organization:
   - Name: `.github-private` (exact name required)
   - Visibility: **Internal** (required for agent access to knowledgebase)
   - Do not initialize with README

2. **Note the repository URL** for later steps

> **Why Internal?** Agents use GitHub MCP to access knowledgebase files. Internal visibility enables this while keeping content private to your enterprise.

## Step 2: Configure and Deploy

### Clone Repository

```bash
git clone https://github.com/github/actions-migrations-via-copilot.git
cd actions-migrations-via-copilot
```

### Update Organization References

Replace `{MY_ORGANIZATION}` with your organization slug:

```bash
# macOS/Linux
find agents -name "*.md" -type f -exec sed -i '' 's/{MY_ORGANIZATION}/YOUR-ORG-SLUG/g' {} +

# Verify
grep -r "{MY_ORGANIZATION}" agents/
```

Should return no results.

### Push to .github-private

```bash
git remote add enterprise https://github.com/YOUR-ORG-SLUG/.github-private.git
git push enterprise main
```

Verify at `https://github.com/YOUR-ORG-SLUG/.github-private`

## Step 3: Configure Repository Settings

### Create GitHub App (for automation workflows)

1. **Create app** at `https://github.com/organizations/YOUR-ORG-SLUG/settings/apps`:
   - Name: `CI/CD Migration Automation`
   - Webhook: Inactive
   - Repository permissions: Contents (R/W), Issues (R/W), Pull requests (R/W), Workflows (R/W)
   - Organization permissions: Members (Read), Custom properties (Read)
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

Expected variables: `GH_APP_ID`, `GH_MIGRATION_TYPE_DEFAULT`, `ORGANIZATIONS`, `BATCH_SIZE`

### Create Copilot Agents Secret (Manual)

The migration agents use the GitHub MCP server, which requires a Personal Access Token exposed as the `COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN` secret. This must be created as a **Copilot Agents secret** at the organization level. There is no API for this, so it must be configured manually for each organization listed in `.github/settings/config.yaml`.

First, create a dedicated PAT for MCP knowledgebase access:

1. Generate a **fine-grained PAT** (recommended) scoped only to the `.github-private` repository:
   - **Resource owner**: Your organization
   - **Repository access**: Only select repositories → `.github-private`
   - **Repository permissions**: Contents (Read-only), Metadata (Read-only)
   - **Expiration**: Per your organization policy
   - **SSO authorization**: Enable for the organization
2. If your organization requires classic PATs, generate one with the minimum scope `repo` and authorize SSO for the organization. Prefer the fine-grained option above.

> **Why a dedicated token?** Scoping this PAT to `.github-private` with read-only access limits the blast radius if it is ever exposed. Do not reuse `ISSUE_SUBMIT_TOKEN`, which has broader privileges needed for the automation workflows.

Then, for each organization:

1. Navigate to `https://github.com/organizations/YOUR-ORG-SLUG/settings/secrets/agents`
2. Click **New organization secret**
3. Configure the secret:
   - **Name**: `COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN`
   - **Value**: The dedicated PAT created above
4. Click **Add secret**

> **Note:** Repeat this step for every organization in the `organizations` list of `config.yaml`. The secret must be available to Copilot coding agent runs in repositories belonging to those organizations.

## Step 4: Enable Agents in Enterprise Settings

1. **Navigate to Enterprise AI controls**:
   - Click profile photo → Your enterprises → [Your Enterprise]
   - Click **AI controls**

2. **Enable custom agents**:
   - Find **"Custom agents"** section
   - Select your organization from dropdown
   - Verify agents appear:
     - Jenkins Migrator
     - Azure DevOps Migrator
     - CircleCI Migrator
     - GitLab Migrator
     - Travis CI Migrator
     - Bamboo Migrator
     - Bitbucket Migrator
     - Drone CI Migrator
     - Reusable Workflow Builder

3. **Wait 5-10 minutes** for agent registration to propagate

## Step 5: Test Your Deployment

1. Navigate to [github.com/copilot/agents](https://github.com/copilot/agents)
2. Verify your migration agents appear
3. Open a test repository with CI/CD configuration
4. Invoke an agent through Copilot Chat
5. Verify agent can access knowledgebase

## Maintaining Your Deployment

### Update Agents

When adding new agents (see [extending.md](extending.md)):

1. Add agent file to `agents/` directory
2. Create knowledgebase files in `knowledge/`
3. Update organization references
4. Commit and push to `.github-private`

```bash
# After adding new agent
git add agents/ knowledge/
git commit -m "Add <platform> migration agent"
git push enterprise main
```

Changes are live immediately.

### Update Knowledgebase

Update mappings and patterns as Actions evolves:

```bash
# Edit files in knowledge/
nano knowledge/actions-mapping/jenkins.md

# Commit and push
git add knowledge/
git commit -m "Update action mappings"
git push enterprise main
```

Agents automatically use latest knowledgebase content.

### Monitor Usage

- Review Copilot usage reports in Enterprise settings
- Collect feedback from migration teams
- Update knowledgebase based on real-world patterns
- Refine agents based on common issues

## Troubleshooting

| Issue                                                 | Solution                                                                       |
| ----------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Agents not appearing**                              | Verify `.github-private` exists, wait 10 minutes, check Enterprise AI settings |
| **Cannot access knowledgebase**                       | Ensure repository visibility is **Internal**, verify org slug in agent files   |
| **Organization slug still shows `{MY_ORGANIZATION}`** | Re-run `sed` command or manually edit agent files                              |
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
