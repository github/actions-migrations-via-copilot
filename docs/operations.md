# Operations Guide

How to use migration agents to convert CI/CD pipelines to GitHub Actions.

## Quick Reference

| Method     | Use For                   | How                                                                             |
| ---------- | ------------------------- | ------------------------------------------------------------------------------- |
| **Manual** | Individual repos, testing | Invoke agent via [github.com/copilot/agents](https://github.com/copilot/agents) |
| **Batch**  | Multiple repos, scale     | Run Submit Repositories workflow in `.github-private`                           |

## Manual Migration

### 1. Prepare Repository

Create a feature branch:

```bash
git checkout -b migrate/to-actions
git push -u origin migrate/to-actions
```

### 2. Invoke Agent

1. Go to [github.com/copilot/agents](https://github.com/copilot/agents)
2. Select your repository and branch
3. Choose the appropriate migration agent:
   - Jenkins Migrator
   - Azure DevOps Migrator
   - CircleCI Migrator
   - GitLab Migrator
   - Travis CI Migrator
   - Bamboo Migrator
   - Bitbucket Migrator
   - Drone CI Migrator

4. Provide clear instructions:

**Example:**

```
Migrate our Jenkins pipeline to GitHub Actions.

Files:
- Jenkinsfile (main build)
- deploy/Jenkinsfile (deployment)
- vars/buildDocker.groovy (shared library)

We use Docker, Kubernetes, and AWS plugins.
```

### 3. Review Output

Check generated files:

- **Workflows**: `.github/workflows/*.yml`
- **Archive**: `.github/ci-archive/` (original files preserved)
- **Report**: Pull Request body and `.github/ci-archive/MIGRATION-README.md` (fallback if PR creation/update isn’t possible; includes validation, secrets, next steps)

### 4. Configure Secrets

Add secrets to repository settings:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add secrets listed in migration report

### 5. Test and Merge

```bash
git add .github/
git commit -m "Migrate to GitHub Actions"
git push
```

Monitor workflow runs, create PR, and merge when validated.

## Batch Migration

Automate migrations across multiple repositories using custom properties.

### How It Works

1. Set `GH_MIGRATION_TYPE` custom property on repositories
2. Run "Submit Repositories for Migration" workflow
3. Workflow creates issues assigned to Copilot with agent prompts
4. Copilot processes migrations using the appropriate agent

### Supported Migration Types

Set `GH_MIGRATION_TYPE` to: `Jenkins`, `Azure DevOps`, `CircleCI`, `GitLab`, `Travis CI`, `Bamboo`, `Bitbucket`, or `DroneCI`

### Set Custom Properties

**Using GitHub CLI:**

```bash
# Single repository
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/YOUR-ORG/REPO-NAME/properties/values \
  -f properties[GH_MIGRATION_TYPE]=Jenkins

# Multiple repositories
for repo in repo1 repo2 repo3; do
  gh api --method PUT \
    -H "Accept: application/vnd.github+json" \
    /repos/YOUR-ORG/$repo/properties/values \
    -f properties[GH_MIGRATION_TYPE]=Jenkins
done
```

### Run Migration Workflow

1. Go to `https://github.com/YOUR-ORG/.github-private/actions`
2. Select **"Submit Repositories for Migration"**
3. Click **"Run workflow"** → Select `main` → **"Run workflow"**

### Monitor Progress

Check workflow logs to see repositories being processed:

```
Found 15 repositories with GH_MIGRATION_TYPE property
Processing batch 1 of 1 (15 repositories)
- Assigning jenkins-migrator to repo: frontend-app
- Assigning circleci-migrator to repo: mobile-app
```

Review migration results in each repository's pull requests.

### Configuration

Edit `.github/settings/config.yaml` in `.github-private`:

```yaml
gh_migration_type:
  default_value: 'Jenkins'
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
  - 'your-org-name'

batch_size: 100
```

## Troubleshooting

| Issue                                          | Solution                                                                               |
| ---------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Repository not picked up by batch workflow** | Verify `GH_MIGRATION_TYPE` property is set: `gh api /repos/ORG/REPO/properties/values` |
| **Wrong agent assigned**                       | Check property value matches config.yaml mappings                                      |
| **Workflow fails after migration**             | Review migration report for required secrets, check workflow logs                      |
| **Agent can't access source files**            | Verify files exist on correct branch, check file paths (case-sensitive)                |
| **Missing validation results**                 | Re-run migration with explicit validation request                                      |

## Best Practices

**Before migration:**

- Create feature branch
- Document current CI/CD state
- List all credentials and dependencies

**During migration:**

- Review agent output thoroughly
- Read migration report carefully
- Test in feature branch first

**After migration:**

- Monitor workflow runs for 1-2 weeks
- Compare performance with old CI
- Update team documentation
- Decommission old CI only when validated

## Getting Help

- **Migration Reports**: Review the Pull Request created at migration completion
- **Knowledgebase**: Review `knowledge/` in `.github-private`
- **Discussions**: [github.com/copilot/agents discussions](https://github.com/github/actions-migrations-via-copilot/discussions)
- **Issues**: Report problems or request improvements

## Related Docs

- [deployment.md](deployment.md) - Deploy agents
- [extending.md](extending.md) - Add new platforms
