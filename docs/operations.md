# Operations Guide

This guide provides instructions for using CI/CD Migration Custom Agents to migrate repositories to GitHub Actions.

> **📖 New to this project?** Start with the [README](../README.md) for an overview, then follow the [Deployment Guide](deployment.md) to set up agents in your enterprise.

## Migration Methods

There are two ways to invoke migration agents:

1. **[Manual UI Invocation](#manual-ui-invocation)** - Migrate individual repositories through the GitHub Copilot interface
2. **[Automated Batch Migration](#automated-batch-migration)** - Migrate multiple repositories using the submit-repo workflow

## Manual UI Invocation

Use this method to migrate individual repositories with full control over the migration process.

### Step 1: Access the Agents Interface

1. **Navigate to GitHub Copilot agents**:
   ```
   https://github.com/copilot/agents
   ```

2. **Select your repository context**:
   - **Repository**: Choose the repository containing your CI/CD files
   - **Branch**: Select the branch where migration should occur (create a feature branch first)
   - **Agent**: Choose the appropriate migration agent:
     - Jenkins to GitHub Actions Migration Agent
     - Azure DevOps Migrator
     - CircleCI Migrator
     - GitLab Migrator
     - Travis CI Migrator
     - Bamboo Migrator
     - Bitbucket Migrator
     - Drone CI Migrator

### Step 2: Prepare Your Migration Request

Compose a clear migration request that includes:

- **What to migrate**: List all CI/CD configuration files
- **Special requirements**: Mention shared libraries, templates, or dependencies
- **Context**: Note any custom requirements (specific actions, deployment targets)

**Example for Jenkins**:
```
Please migrate our Jenkins pipelines to GitHub Actions.

Files to migrate:
- Jenkinsfile (declarative pipeline for main build)
- deploy/Jenkinsfile (deployment pipeline)
- vars/buildDocker.groovy (shared library)
- vars/deployApp.groovy (shared library)

We use the following Jenkins plugins:
- Docker Pipeline
- Kubernetes
- AWS Steps
```

**Example for Azure DevOps**:
```
Please migrate our Azure DevOps pipelines to GitHub Actions.

Files to migrate:
- azure-pipelines.yml (main build pipeline)
- pipelines/deploy-prod.yml (production deployment)
- templates/build-dotnet.yml (template)
- templates/deploy-azure.yml (template)

We use Azure App Service and Azure Key Vault.
```

### Step 3: Review Migration Output

After the agent completes, review the generated files:

1. **Workflows**: Check `.github/workflows/` for converted workflows
2. **Archive**: Review `.github/ci-archive/` for original configuration backups
3. **Migration Report**: Read `.github/ci-archive/MIGRATION-README.md` for:
   - Validation results
   - Required secrets
   - Known limitations
   - Testing recommendations

### Step 4: Configure Secrets

Add any required secrets to your repository:

1. Navigate to **Settings** → **Secrets and variables** → **Actions**
2. Add secrets referenced in the migrated workflows
3. Refer to the migration report for required secret names

### Step 5: Test and Validate

1. **Commit the changes**:
   ```bash
   git add .github/
   git commit -m "Migrate CI/CD to GitHub Actions"
   git push
   ```

2. **Monitor workflow runs** in the **Actions** tab

3. **Verify all jobs complete successfully**

4. **Create a pull request** and request team review

5. **Merge when validated**

## Automated Batch Migration

Use the `submit-repo` workflow to migrate multiple repositories across your organization automatically.

### How It Works

The batch migration system uses **custom properties** to track and control migrations:

1. **Custom Property**: `GH_MIGRATION_TYPE` is set on each repository to indicate the CI/CD platform type
2. **Workflow Scan**: The `submit-repo` workflow scans your organization for repositories with the custom property
3. **Agent Assignment**: For each repository, the workflow assigns the appropriate migration agent based on the property value
4. **Batch Processing**: Repositories are processed in batches (configurable batch size)

### Custom Property Values

The `GH_MIGRATION_TYPE` property can be set to:

- `Jenkins`
- `Azure DevOps`
- `CircleCI`
- `GitLab`
- `Travis CI`
- `Bamboo`
- `Bitbucket`
- `DroneCI`

Each value maps to a specific migration agent (configured in `.github/settings/config.yaml`).

### Step 1: Set Custom Properties on Repositories

Each repository in your organization has been configured with a custom property named `GH_MIGRATION_TYPE` and the value has been set to the `default_value` specified in the configuration file. For each repository that uses different CI/CD system you need to set the `GH_MIGRATION_TYPE` custom property to the appropriate value.

**Using GitHub CLI**:
```bash
# Set custom property for a single repository
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/YOUR-ORG/REPO-NAME/properties/values \
  -f properties[GH_MIGRATION_TYPE]=Jenkins

# Set for multiple repositories
for repo in repo1 repo2 repo3; do
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    /repos/YOUR-ORG/$repo/properties/values \
    -f properties[GH_MIGRATION_TYPE]=Jenkins
done
```

**Using GitHub UI** (if available in your organization):
1. Navigate to the repository
2. Go to **Settings** → **Custom properties**
3. Set `GH_MIGRATION_TYPE` to the appropriate CI/CD platform

### Step 2: Trigger the Submit-Repo Workflow

1. **Navigate to your .github-private repository**:
   ```
   https://github.com/YOUR-ORG/.github-private/actions
   ```

2. **Select the "Submit Repositories for Migration" workflow**

3. **Click "Run workflow"**:
   - **Branch**: Select `main`
   - Click **"Run workflow"**

### Step 3: Monitor Workflow Execution

1. **View workflow progress** in the Actions tab

2. **Check logs** to see which repositories are being processed:
   ```
   Found 15 repositories with GH_MIGRATION_TYPE property
   Processing batch 1 of 1 (15 repositories)
   - Assigning jenkins-migrator to repo: frontend-app
   - Assigning jenkins-migrator to repo: api-service
   - Assigning circleci-migrator to repo: mobile-app
   ...
   ```

3. **Verify agent assignments** for each repository in the logs

### Step 4: Review Migration Results

For each repository that was processed:

1. **Check for pull requests** created by the migration agent
2. **Review the migration report** in `.github/ci-archive/MIGRATION-README.md`
3. **Test the migrated workflows** in the pull request branch
4. **Merge successful migrations**

### Configuration

The batch migration behavior is controlled by `.github/settings/config.yaml`:

```yaml
# Custom Properties Configuration
gh_migration_type:
  default_value: 'Jenkins'  # Default if property not set
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

# Organizations to scan
organizations:
  - 'your-org-name'

# Batch Size
batch_size: 100
```

## Troubleshooting

### Custom Property Not Set

**Symptom**: Repository not picked up by submit-repo workflow

**Solution**: Verify the `GH_MIGRATION_TYPE` property is set:
```bash
gh api /repos/YOUR-ORG/REPO-NAME/properties/values
```

### Wrong Agent Assigned

**Symptom**: Incorrect migration agent used for repository

**Solution**:
1. Check the custom property value matches config.yaml
2. Verify `migration_type_prompts` mapping in config.yaml
3. Update the property and re-run the workflow

### Workflow Fails After Migration

**Symptom**: Migrated workflow fails in GitHub Actions

**Solution**:
1. Review workflow run logs
2. Check migration report for required secrets
3. Verify all secrets are configured in repository settings
4. Test locally using `actionlint` if available

### Agent Cannot Access Source Files

**Symptom**: Agent reports "Cannot find file" errors

**Solution**:
1. Verify CI/CD files exist in the repository
2. Ensure files are on the correct branch
3. Check file paths are correct (case-sensitive)

## Getting Help

### Resources

- **Migration Reports**: Check `.github/ci-archive/MIGRATION-README.md` in each repository
- **Knowledgebase**: Review `.github-private/knowledge/` for migration standards
- **GitHub Actions Docs**: [docs.github.com/actions](https://docs.github.com/actions)

### Support Channels

1. **Internal Team**: Consult with teams who have completed migrations
2. **GitHub Support**: Contact your Enterprise support team
3. **Agent Updates**: Submit feedback to improve agent capabilities

## Next Steps

- **Start with pilot migrations**: Test with 2-3 repositories using manual UI invocation
- **Scale with automation**: Use batch migration for larger rollouts
- **Iterate and improve**: Refine your process based on results
- **Maintain and evolve**: Keep knowledgebase updated as Actions ecosystem grows

For deployment and setup instructions, see [**Deployment Guide →**](deployment.md)


### Pre-Migration Checklist

- [ ] Identify all Jenkinsfiles (declarative and scripted)
- [ ] Locate shared library files in `vars/` directory
- [ ] Document Jenkins plugins currently in use
- [ ] List credential IDs used in pipelines
- [ ] Note any custom agents or Docker images
- [ ] Create migration feature branch

### Migration Steps

1. **Prepare Repository**:
   ```bash
   git checkout -b migrate/jenkins-to-actions
   git push -u origin migrate/jenkins-to-actions
   ```

2. **Invoke Jenkins Migrator**:
   - Go to [github.com/copilot/agents](https://github.com/copilot/agents)
   - Select your repository and `migrate/jenkins-to-actions` branch
   - Choose **"Jenkins to GitHub Actions Migration Agent"**
   - Provide migration request:
     ```
     Please migrate our Jenkins pipelines to GitHub Actions.

     Files to migrate:
     - Jenkinsfile (declarative pipeline for main build)
     - deploy/Jenkinsfile (deployment pipeline)
     - vars/buildDocker.groovy (shared library)
     - vars/deployApp.groovy (shared library)

     We use the following Jenkins plugins:
     - Docker Pipeline
     - Kubernetes
     - AWS Steps
     ```

3. **Review Agent Output**:
   - Check `.github/workflows/` for generated workflows
   - Review `.github/ci-archive/` for archived Jenkins files
   - Read `.github/ci-archive/MIGRATION-README.md` thoroughly

4. **Validate Workflows**:
   ```bash
   # Install actionlint
   brew install actionlint  # macOS

   # Lint workflows
   actionlint .github/workflows/*.yml
   ```

5. **Configure Secrets**:
   - Navigate to repository **Settings** → **Secrets and variables** → **Actions**
   - Add secrets referenced in migrated workflows
   - Refer to `MIGRATION-README.md` for required secret names

7. **Test in Feature Branch**:
   - Commit changes: `git commit -am "Migrate Jenkins to GitHub Actions"`
   - Push: `git push`
   - Monitor workflow runs in **Actions** tab
   - Verify all jobs complete successfully

8. **Review and Merge**:
   - Create pull request from `migrate/jenkins-to-actions` to `main`
   - Request team review
   - Address any issues or feedback
   - Merge when approved

## Maintenance and Monitoring

### Updating the Knowledgebase

As GitHub Actions evolves, keep the knowledgebase current:

1. **Monitor GitHub Actions updates**:
   - Subscribe to [GitHub Changelog](https://github.blog/changelog/)
   - Watch for new actions and features
   - Track deprecations and breaking changes

2. **Update action mappings**:
   ```bash
   # Navigate to .github-private repository
   cd .github-private

   # Edit mapping files
   vim docs/actions-mapping/jenkins.md  # Add new plugin mappings

   # Commit and push
   git add docs/actions-mapping/
   git commit -m "Update Jenkins plugin mappings"
   git push
   ```

3. **Document new patterns**:
   - Add successful migration patterns to `docs/patterns/`
   - Update best practices based on real-world migrations
   - Share learnings across teams

### Monitoring Migration Success

Track migration outcomes to improve process:

1. **Collect metrics**:
   - Migration completion rate
   - Workflow execution success rate
   - Build time comparisons (before/after)
   - Cost comparisons (old CI vs GitHub Actions)

2. **Gather feedback**:
   - Survey teams after migrations
   - Document common issues and solutions
   - Identify knowledgebase gaps

3. **Iterate on process**:
   - Update operations playbooks
   - Refine agent instructions
   - Improve validation steps

### Troubleshooting Common Issues

#### Workflow Fails After Migration

**Symptoms**: Migrated workflow fails in GitHub Actions

**Diagnosis Steps**:
1. Review workflow run logs in GitHub Actions UI
2. Check migration report (`.github/ci-archive/MIGRATION-README.md`)
3. Compare original CI/CD file with generated workflow
4. Verify all secrets are configured

**Common Fixes**:
- Add missing secrets to repository settings
- Update action versions to latest
- Fix YAML syntax errors flagged by actionlint
- Adjust runner labels (`runs-on`) for environment requirements

#### Agent Cannot Access Source Files

**Symptoms**: Agent reports "Cannot find file" or "Access denied"

**Diagnosis Steps**:
1. Verify files exist in selected branch
2. Check file paths are correct (case-sensitive)
3. Confirm repository permissions

**Common Fixes**:
- Push files to branch before invoking agent
- Use correct file paths in migration request
- Verify agent has repository access

#### Migration Report Missing Validation Results

**Symptoms**: `MIGRATION-README.md` lacks actionlint output

**Diagnosis Steps**:
1. Check if validation tools ran successfully
2. Review agent conversation for errors
3. Verify local testing requirements

**Common Fixes**:
- Re-run migration with explicit validation request
- Install actionlint locally and validate manually
- Update agent instructions to require validation

## Best Practices Summary

### Before Migration

- ✅ **Create feature branch** for migration work
- ✅ **Document current state** of CI/CD configuration
- ✅ **List all dependencies** (credentials, services, tools)
- ✅ **Backup configurations** outside repository

### During Migration

- ✅ **Review agent output thoroughly** before committing
- ✅ **Read migration reports** for warnings and recommendations
- ✅ **Test in feature branch first** before merging
- ✅ **Validate with actionlint** when possible

### After Migration

- ✅ **Monitor workflow runs** for 1-2 weeks
- ✅ **Compare performance metrics** with old CI system
- ✅ **Update team documentation** to reflect new workflows
- ✅ **Decommission old CI** only when fully validated
- ✅ **Share learnings** with other teams

## Getting Help

### Resources

- **Migration Reports**: Always start with `.github/ci-archive/MIGRATION-README.md`
- **Knowledgebase**: Review `.github-private/docs/` for migration standards
- **GitHub Actions Docs**: [docs.github.com/actions](https://docs.github.com/actions)
- **Community Forums**: [github.community](https://github.community)

### Support Channels

1. **Internal Team**: Consult with teams who have completed migrations
2. **GitHub Support**: Contact your Enterprise support team
3. **Agent Updates**: Submit feedback to improve agent capabilities

### Feedback Loop

Help improve migration agents:

1. **Document issues** encountered during migrations
2. **Share successful patterns** that could be added to knowledgebase
3. **Suggest agent improvements** based on experience
4. **Contribute to knowledgebase** with new mappings and patterns

## Next Steps

- **Start with pilot migrations**: Choose 2-3 simple pipelines to test the process
- **Iterate and improve**: Refine your migration playbook based on results
- **Scale across organization**: Apply learnings to larger migration efforts
- **Maintain and evolve**: Keep knowledgebase updated as Actions ecosystem grows

For deployment and setup instructions, see [**Deployment Guide →**](deployment.md)
