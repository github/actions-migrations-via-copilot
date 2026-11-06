# Extending the Project

Add support for new CI/CD platforms by creating migration agents and knowledgebase content.

## Quick Reference

| Task                  | Files to Create                                               |
| --------------------- | ------------------------------------------------------------- |
| **New Agent** | `plugin/agents/<platform>-migrator.agent.md` |
| **Skill Entry** | `plugin/skills/<platform>-migration/SKILL.md` |
| **Action Mappings** | `plugin/skills/<platform>-migration/mapping.md` |
| **Security Patterns** | `plugin/skills/<platform>-migration/secrets.md` |
| **Report Template** | `plugin/skills/<platform>-migration/report-template.md` |
| **Optional Patterns** | Reference files beside the platform skill |

### One maintained package

Edit the plugin files directly. The same installed skills serve local and cloud
sessions; do not recreate separate cloud content or a fingerprint refresh step.
Shared process references belong in `plugin/skills/migration-core/`.
Keep each guide referenced by its owning skill and resolve paths relative to the
installed skill, not the consumer repository.

```bash
bash scripts/check-plugin-content.sh
bash scripts/refresh-pinned-actions.test.sh
bash plugin/hooks.test.sh
node --test .github/scripts/submit-repositories.test.js
```

When adding a batch-supported platform, update the explicit mapping in
`.github/scripts/migration-targets.js`, `.github/settings/config.yaml`, the
required-file list in the plugin checker, and their tests together.

## Adding a New Migration Agent

### 1. Create Agent File

**Location:** `plugin/agents/<platform>-migrator.agent.md`

**Required sections:**
- YAML frontmatter (name, description)
- Knowledge base references
- Platform expertise
- Migration process (5 phases)
- Key conversions
- Security requirements

**Template:** Follow `plugin/agents/jenkins-migrator.agent.md` and reference installed skills.

### 2. Create Knowledgebase Files

**Required:**
- `plugin/skills/<platform>-migration/mapping.md` - Command/task mappings
- `plugin/skills/<platform>-migration/secrets.md` - Credential migration patterns
- `plugin/skills/<platform>-migration/report-template.md` - Migration report structure

**Optional (create if needed):**
- `plugin/skills/<platform>-migration/pipeline.md` - Complex pipeline patterns
- `plugin/skills/<platform>-migration/plugins.md` - Plugin conversions
- `plugin/skills/<platform>-migration/scripts.md` - Script conversion patterns

### 3. Update Documentation

Add your agent to:
- `README.md` - Available Migration Agents table
- `docs/operations.md` - Usage instructions

## Knowledgebase File Templates

### Action Mappings (`plugin/skills/<platform>-migration/mapping.md`)

Maps platform syntax to GitHub Actions equivalents.

**Include:**
- Pipeline structure comparison
- Common command/task mappings (use tables)
- Trigger/event mappings
- Environment variable handling
- Basic secret patterns

**Example:** `plugin/skills/jenkins-migration/mapping.md`

### Security Patterns (`plugin/skills/<platform>-migration/secrets.md`)

Documents credential migration.

**Include:**
- Secret types in source platform
- GitHub Actions equivalents table
- Migration steps
- Security best practices
- Examples

**Example:** `plugin/skills/jenkins-migration/secrets.md`

### Report Template (`plugin/skills/<platform>-migration/report-template.md`)

Defines migration report structure.

**Include:**
- Migration summary
- Source analysis
- Conversion details
- Validation results
- Next steps

**Example:** `plugin/skills/jenkins-migration/report-template.md`

### Optional Pattern Files

Create when patterns are too complex for action mappings:

| File               | Purpose                                                  | When to Create                 |
| ------------------ | -------------------------------------------------------- | ------------------------------ |
| `pipeline.md`      | Multi-stage pipelines, matrix builds, parallel execution | Complex pipeline structures    |
| `plugins.md`       | Plugin/extension conversions                             | Many platform-specific plugins |
| `scripts.md`       | Inline scripts, script files                             | Custom scripting language      |
| `notifications.md` | Slack, email, webhooks                                   | Complex notification setup     |
| `environment.md`   | Environment variables, config files                      | Complex env configuration      |

**Keep patterns focused:** One pattern type per file. Reference Jenkins patterns for examples.

## Testing Your Changes

1. **Local validation**
   - Verify file structure matches existing agents
   - Check markdown and YAML syntax
   - Confirm all knowledgebase file paths exist

2. **Install the candidate plugin**
   - Use an isolated local plugin path or an approved cloud test marketplace
   - Verify the loaded revision; a feature-branch edit is not automatically available through a default-branch marketplace

3. **Test migration**
   - Create test repo with sample CI/CD config
   - Invoke agent from test repo
   - Verify deliverables:
     - Workflows in `.github/workflows/`
     - Archives in `.github/ci-archive/`
     - Migration report with actionlint results

4. **Iterate**
   - Document issues
   - Update knowledgebase patterns
   - Refine agent instructions
   - Re-test

## Best Practices

**Agent Design:**
- Follow the 5-phase migration workflow
- Reference knowledgebase (don't hardcode mappings)
- Include validation requirements
- Document all deliverables

**Knowledgebase:**
- Use tables for mappings
- Show before/after examples
- Document edge cases
- Keep security patterns detailed
- Don't duplicate content (cross-reference instead)

**Documentation:**
- Update README.md with new agent
- Add usage guide to operations.md
- Keep examples real-world and focused

## Getting Help

- **Questions?** [Discussions](https://github.com/github/actions-migrations-via-copilot/discussions)
- **Issues?** [Open an issue](https://github.com/github/actions-migrations-via-copilot/issues/new/choose)
- **Review?** Open a draft PR

## Related Docs

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [deployment.md](deployment.md) - Deploy agents
- [operations.md](operations.md) - Use agents
