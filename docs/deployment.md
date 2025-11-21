# Deployment Guide

This guide provides step-by-step instructions for deploying CI/CD Migration Custom Agents to your GitHub Enterprise environment.

## Prerequisites

Before beginning deployment, ensure you have:

- **GitHub Enterprise Cloud** with GitHub Copilot Business or Enterprise subscription
- **Enterprise Owner permissions** to configure custom agents
- **Organization Admin permissions** for the target organization
- **Git client** installed on your local machine
- **Access to create repositories** in your enterprise organization

## Deployment Steps

### Step 1: Create the .github-private Repository

The `.github-private` repository serves as the central location for custom agents and the migration knowledgebase.

1. **Navigate to your enterprise organization** on GitHub.com

2. **Create a new repository**:
   - Click **"New repository"**
   - Repository name: **`.github-private`** (exactly as shown, including the leading dot)
   - Visibility: **Internal** (REQUIRED - allows agents to access knowledgebase)
   - Initialize: Do not initialize with README, .gitignore, or license

3. **Verify repository settings**:
   - Confirm visibility is set to **Internal**
   - Note the repository URL for the next steps

> **Why Internal visibility?** Agents use the GitHub MCP (Model Context Protocol) server to access knowledgebase files during migrations. Internal visibility ensures agents can read these files while keeping them private to your enterprise.

### Step 2: Clone and Prepare the Source Repository

1. **Clone this repository** to your local machine:
   ```bash
   git clone https://github.com/github/actions-migrations-via-copilot.git
   cd actions-migrations-via-copilot
   ```

2. **Review the directory structure**:
   ```bash
   tree -L 2
   ```

   You should see:
   ```
   .
   ├── agents/          # Agent definition files
   ├── docs/            # Deployment and operations documentation
   ├── knowledge/       # Migration knowledgebase
   ├── scratch/         # Temporary files (not deployed)
   └── README.md
   ```

### Step 3: Configure Organization References

Before deploying, update all agent files to reference your organization.

1. **Identify your organization slug**:
   - Your organization slug is visible in URLs: `github.com/{organization-slug}`
   - Example: For `github.com/acme-corp`, the slug is `acme-corp`

2. **Update agent files** with your organization slug:
   ```bash
   # Replace {MY_ORGANIZATION} in all agent files
   find agents -name "*.md" -type f -exec sed -i '' 's/{MY_ORGANIZATION}/YOUR-ORG-SLUG/g' {} +
   ```

   Replace `YOUR-ORG-SLUG` with your actual organization slug.

3. **Verify the changes**:
   ```bash
   grep -r "YOUR-ORG-SLUG" agents/
   ```

   Ensure all references have been updated.

### Step 4: Deploy to .github-private Repository

1. **Add your .github-private repository as a remote**:
   ```bash
   git remote add enterprise https://github.com/YOUR-ORG-SLUG/.github-private.git
   ```

2. **Push to your .github-private repository**:
   ```bash
   git push enterprise main
   ```

   This deploys the entire repository structure:
   - `agents/` → `.github-private/agents/`
   - `knowledge/` → `.github-private/knowledge/`
   - `docs/` → `.github-private/docs/`
   - `.github/` → `.github-private/.github/`
   - `README.md` → `.github-private/README.md`

3. **Verify deployment** on GitHub:
   - Navigate to `https://github.com/YOUR-ORG-SLUG/.github-private`
   - Confirm directory structure.
   - Check that agent files contain your organization slug (not `{MY_ORGANIZATION}`)

### Step 5: Configure Repository Variables and Secrets

The automation workflows require GitHub App credentials and a Personal Access Token for cross-organization operations.

#### 5.1 Create GitHub App for Automation Workflows

1. **Navigate to GitHub App creation**:
   - Go to your organization settings: `https://github.com/organizations/YOUR-ORG-SLUG/settings/apps`
   - Click **"New GitHub App"**

2. **Configure GitHub App settings**:
   - **GitHub App name**: `CI/CD Migration Automation` (or your preferred name)
   - **Homepage URL**: `https://github.com/YOUR-ORG-SLUG/.github-private`
   - **Webhook**: Uncheck "Active" (not needed for this app)

3. **Set Repository permissions**:
   - **Contents**: Read and write
   - **Issues**: Read and write
   - **Pull requests**: Read and write
   - **Workflows**: Read and write
   - **Metadata**: Read-only (automatically selected)

4. **Set Organization permissions**:
   - **Members**: Read-only (for accessing organization repositories)

5. **Configure "Where can this GitHub App be installed?"**:
   - Select **"Any account"** (allows installation across multiple organizations)

6. **Create the app**:
   - Click **"Create GitHub App"**
   - Note the **App ID** displayed on the app's page

7. **Generate private key**:
   - Scroll to **"Private keys"** section
   - Click **"Generate a private key"**
   - A `.pem` file will download automatically - save this securely

8. **Install the app in your organizations**:
   - Click **"Install App"** in the left sidebar
   - For each organization that will use the migration tools:
     - Click **"Install"** next to the organization name
     - Select **"All repositories"** or choose specific repositories
     - Click **"Install"**
   - Repeat for all target organizations (including the organization hosting `.github-private`)

9. **Authorize the app** (if using multiple organizations):
   - Navigate to each organization's settings
   - Go to **"GitHub Apps"** → **"Installed GitHub Apps"**
   - Confirm the app appears with appropriate permissions

#### 5.2 Create Personal Access Token

1. **Generate a Classic Personal Access Token**:
   - Navigate to **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
   - Click **"Generate new token (classic)"**
   - Token name: `Migration Automation - Issue Submission & MCP Access`
   - Scopes required:
     - `repo` (Full control of private repositories)
     - `read:org` (Read organization data)
     - `admin:org` (Full control of organization settings - required for settings.yml workflow)
   - Expiration: Set according to your organization's policy
   - Click **"Generate token"** and copy the token value

2. **Configure SSO authorization** (if applicable):
   - Click **"Configure SSO"** next to the token
   - Authorize for all organizations the tool will interact with
   - Click **"Authorize"** for each organization

#### 5.3 Add Secrets to .github-private Repository

1. **Navigate to repository secrets**:
   - Go to `https://github.com/YOUR-ORG-SLUG/.github-private/settings/secrets/actions`
   - Click **"New repository secret"**

2. **Add GitHub App private key**:
   - Name: `GH_APP_PEM`
   - Value: Paste the entire contents of the `.pem` file you downloaded (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` lines)
   - Click **"Add secret"**

3. **Add Personal Access Token**:
   - Click **"New repository secret"**
   - Name: `ISSUE_SUBMIT_TOKEN`
   - Value: Paste the PAT you generated
   - Click **"Add secret"**

#### 5.4 Update Configuration File

1. **Edit the configuration file** in your local clone:
   ```bash
   cd actions-migrations-via-copilot
   nano .github/settings/config.yaml  # or use your preferred editor
   ```

2. **Update the following values**:
   ```yaml
   # GitHub App Configuration
   gh_app_id: '123456'  # Replace with your GitHub App ID from step 5.1.6

   # Custom Properties Configuration
   gh_migration_type:
     default_value: 'Jenkins'  # Set your default migration type
     description: 'The type of migration for this repository. This is used to track the migration status.'
     other_values:
       - 'Jenkins'
       - 'Azure DevOps'
       - 'CircleCI'
       - 'GitLab'
       - 'Travis CI'
       - 'Bamboo'
       - 'Bitbucket'
       - 'DroneCI'

   # Migration Type Prompts
   migration_type_prompts:
     'Jenkins': 'jenkins-migrator.md'
     'Azure DevOps': 'azure-devops-migrator.md'
     'CircleCI': 'circleci-migrator.md'
     'GitLab': 'gitlab-migrator.md'
     'Travis CI': 'travisci-migrator.md'
     'Bamboo': 'bamboo-migrator.md'
     'Bitbucket': 'bitbucket-migrator.md'
     'DroneCI': 'droneci-migrator.md'

   # Organizations
   organizations:
     - 'YOUR-ORG-SLUG'  # Add all organizations the tool will interact with

   # Batch Size
   batch_size: 100  # Adjust based on your needs
   ```

3. **Save and commit changes**:
   ```bash
   git add .github/settings/config.yaml
   git commit -m "Configure automation settings for organization"
   git push enterprise main
   ```

#### 5.5 Run Settings Workflow to Initialize Repository Variables

The `settings.yml` workflow reads your `config.yaml` file and creates all necessary repository variables automatically.

1. **Navigate to Actions in .github-private repository**:
   - Go to `https://github.com/YOUR-ORG-SLUG/.github-private/actions`
   - Click on **"Settings"** workflow in the left sidebar

2. **Run the workflow manually**:
   - Click **"Run workflow"** button (top right)
   - Select branch: `main`
   - Click **"Run workflow"** to confirm

3. **Monitor workflow execution**:
   - Click on the running workflow to view logs
   - Verify successful completion (green checkmark)
   - The workflow uses `ISSUE_SUBMIT_TOKEN` for authentication

4. **Verify repository variables were created**:
   - Navigate to `https://github.com/YOUR-ORG-SLUG/.github-private/settings/variables/actions`
   - Confirm the following variables exist (populated from `config.yaml`):
     - `GH_APP_ID`
     - `GH_MIGRATION_TYPE_DEFAULT`
     - `GH_MIGRATION_TYPE_DESCRIPTION`
     - `ORGANIZATIONS`
     - `BATCH_SIZE`
     - Additional migration type mappings

> **Note**: The `ISSUE_SUBMIT_TOKEN` secret must have `admin:org` scope to create repository variables. This was configured in step 5.2.

#### 5.6 Verify Configuration

1. **Test GitHub App authentication**:
   - Trigger a test workflow run in `.github-private`
   - Verify the workflow can authenticate using the `GH_APP_PEM` secret
   - Check workflow logs for successful authentication

2. **Test PAT access**:
   - Verify the PAT can access repositories across authorized organizations
   - Test MCP access to knowledge base files
   - Confirm issue creation works using the token

3. **Verify repository variables**:
   - Check that workflows can access the variables created by the settings workflow
   - Ensure variable values match your `config.yaml` settings

### Step 6: Configure Enterprise Copilot Settings

Enable custom agents for your enterprise organization.

1. **Navigate to Enterprise settings**:
   - Click your profile photo → **Your enterprises**
   - Select your enterprise
   - Click **Settings** → **Copilot** → **AI controls**

2. **Enable custom agents**:
   - Scroll to **"Custom agents"** section
   - Click **"Add organization"**
   - Select the organization containing your `.github-private` repository
   - Click **"Add"**

3. **Verify agent availability**:
   - Navigate to [https://github.com/copilot/agents](https://github.com/copilot/agents)
   - Confirm your migration agents appear in the list:
     - Jenkins to GitHub Actions Migration Agent
     - Azure DevOps Migrator
     - CircleCI Migrator
     - GitLab Migrator
     - Travis CI Migrator
     - Bamboo Migrator
     - Bitbucket Migrator
     - Drone CI Migrator
     - Reusable Workflow Builder

## Post-Deployment Configuration

### Update Knowledgebase

As GitHub Actions evolves, update the knowledgebase to reflect new features:

1. **Navigate to your .github-private repository**
2. **Edit knowledgebase files** in `knowledge/`:
   - `actions-mapping/*.md` - Add new action equivalents
   - `patterns/**/*.md` - Document new migration patterns
   - `migration-standards.md` - Update quality standards

3. **Commit and push changes**:
   ```bash
   git add knowledge/
   git commit -m "Update knowledgebase with new patterns"
   git push
   ```

Agents automatically reference the latest knowledgebase content on each invocation.

### Maintain Agent Definitions

As new capabilities are needed, update agent definitions:

1. **Edit agent files** in `agents/` directory
2. **Update instructions** to reflect new features or improved patterns
3. **Test changes** by invoking the updated agent
4. **Commit and push** to `.github-private` repository

Changes take effect immediately for all users.

### Monitor Agent Usage

Track agent adoption across your enterprise:

1. **Review agent activity** in Copilot usage reports
2. **Collect feedback** from teams using migration agents
3. **Identify common issues** or enhancement requests
4. **Update knowledgebase** based on real-world migration patterns

## Security Considerations

### Repository Access

- **Internal visibility required**: Agents need read access to knowledgebase
- **Do not make .github-private public**: Contains enterprise-specific guidance
- **Review access logs**: Monitor who can access `.github-private` repository

### PAT Management (Reusable Workflow Builder)

- **Rotate PATs regularly**: Follow your organization's token rotation policy
- **Use least-privilege scope**: Grant only `repo` scope for read access
- **Monitor PAT usage**: Review audit logs for unexpected access patterns
- **Revoke immediately if compromised**: Disable and regenerate if suspicious activity detected

### Secrets in Migrations

- **Review migration reports**: Check how credentials are handled in conversions
- **Validate GitHub Secrets**: Ensure sensitive values are properly stored
- **Update access controls**: Configure environment protection rules for workflows

## Troubleshooting

### Agent Not Appearing in Copilot

**Symptom**: Migration agents don't appear at [github.com/copilot/agents](https://github.com/copilot/agents)

**Solutions**:
1. Verify `.github-private` repository exists in configured organization
2. Check enterprise Copilot settings include the organization
3. Confirm agent `.md` files exist in `agents/` directory
4. Wait 5-10 minutes for agent registration to propagate

### Agent Cannot Access Knowledgebase

**Symptom**: Agent responds with "Cannot access knowledgebase" or similar error

**Solutions**:
1. Verify `.github-private` repository visibility is **Internal** (not Private)
2. Check organization slug in agent files matches your actual organization
3. Confirm `knowledge/` directory exists in `.github-private` repository
4. Test MCP access manually using GitHub API

### Reusable Workflow Builder Cannot Scan Organizations

**Symptom**: Agent reports "Access denied" or "Cannot list repositories"

**Solutions**:
1. Verify `COPILOT_MCP_GITHUB_PERSONAL_ACCESS_TOKEN` secret exists
2. Check PAT has `repo` scope enabled
3. Ensure PAT has SSO authorization for target organizations
4. Confirm PAT has not expired

### Migration Validation Fails

**Symptom**: Generated workflows contain errors or don't pass validation

**Solutions**:
1. Review `MIGRATION-README.md` for specific validation errors
2. Check that source CI/CD files are valid and complete
3. Update knowledgebase with missing action mappings
4. Test workflows locally using `act` tool

### Organization Slug Mismatch

**Symptom**: Agent references `{MY_ORGANIZATION}` instead of your organization

**Solutions**:
1. Re-run the `sed` command from Step 3 to replace placeholders
2. Manually edit agent files in `.github-private` repository
3. Commit and push updated agent definitions
4. Verify changes by viewing files on GitHub.com

## Next Steps

Once deployment is complete:

1. **Review the [Operations Guide](operations.md)** for instructions on using migration agents
2. **Train your teams** on invoking agents for CI/CD migrations
3. **Establish migration workflows** for systematic pipeline conversions
4. **Monitor and iterate** based on migration results and user feedback

For operational procedures, see [**Operations Guide →**](operations.md)
