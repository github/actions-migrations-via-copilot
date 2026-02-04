# Extending the Project

Add support for new CI/CD platforms by creating migration agents and knowledgebase content.

## Quick Reference

| Task                  | Files to Create                                               |
| --------------------- | ------------------------------------------------------------- |
| **New Agent**         | `agents/<platform>-migrator.md`                               |
| **Action Mappings**   | `knowledge/actions-mapping/<platform>.md`                     |
| **Security Patterns** | `knowledge/patterns/<platform>/secrets.md`                    |
| **Report Template**   | `knowledge/report-template/<platform>.md`                     |
| **Optional Patterns** | `knowledge/patterns/<platform>/{pipeline,plugins,scripts}.md` |

## Adding a New Migration Agent

### 1. Create Agent File

**Location:** `agents/<platform>-migrator.md`

**Required sections:**
- YAML frontmatter (name, description)
- Knowledge base references
- Platform expertise
- Migration process (5 phases)
- Key conversions
- Security requirements

**Template:** Copy `agents/jenkins-migrator.md` and adapt for your platform.

### 2. Create Knowledgebase Files

**Required:**
- `knowledge/actions-mapping/<platform>.md` - Command/task → Actions mappings
- `knowledge/patterns/<platform>/secrets.md` - Credential migration patterns
- `knowledge/report-template/<platform>.md` - Migration report structure

**Optional (create if needed):**
- `knowledge/patterns/<platform>/pipeline.md` - Complex pipeline patterns
- `knowledge/patterns/<platform>/plugins.md` - Plugin conversions
- `knowledge/patterns/<platform>/scripts.md` - Script conversion patterns

### 3. Update Documentation

Add your agent to:
- `README.md` - Available Migration Agents table
- `docs/operations.md` - Usage instructions

## Knowledgebase File Templates

### Action Mappings (`knowledge/actions-mapping/<platform>.md`)

Maps platform syntax to GitHub Actions equivalents.

**Include:**
- Pipeline structure comparison
- Common command/task mappings (use tables)
- Trigger/event mappings
- Environment variable handling
- Basic secret patterns

**Example:** `knowledge/actions-mapping/jenkins.md`

### Security Patterns (`knowledge/patterns/<platform>/secrets.md`)

Documents credential migration.

**Include:**
- Secret types in source platform
- GitHub Actions equivalents table
- Migration steps
- Security best practices
- Examples

**Example:** `knowledge/patterns/jenkins/secrets.md`

### Report Template (`knowledge/report-template/<platform>.md`)

Defines migration report structure.

**Include:**
- Migration summary
- Source analysis
- Conversion details
- Validation results
- Next steps

**Example:** `knowledge/report-template/jenkins.md`

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

2. **Deploy to `.github-private`**
   - Push changes to your organization's `.github-private` repository
   - Verify repository visibility is **Internal**

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
