# Consumer Template

Drop the contents of this directory into the **root of any repo** that should
use the `actions-migrator` plugin.

It enables the plugin (and its hooks) automatically on three surfaces:

| Surface | What happens | Requires |
| --- | --- | --- |
| Copilot CLI | `enabledPlugins` auto-installs on next `copilot` startup | CLI ≥ 1.0.60 |
| Copilot cloud agent (github.com) | sweagentd loads plugin into the job sandbox; hooks fire | Repo, org, or enterprise scope. `CopilotSWEAgentPluginsEnabled` enabled. |
| VS Code Agent Plugins (preview) | Plugin shows up in `@agentPlugins` recommendations | `chat.plugins.enabled: true` (org policy) |

## Files

| Path | Purpose |
| --- | --- |
| `.github/copilot/settings.json` | Declares the plugin in `enabledPlugins`. The single line that wires up all three surfaces. |

## Optional: org-wide rollout

Put the same `.github/copilot/settings.json` in your org's `.github` or
`.github-private` repo. Every repo in the org inherits it. Enterprise admins
can do the same in the designated `.github-private` to enforce it across all
orgs.

Merge precedence in CCA is **enterprise > org > repo**.

## Sanity check after merging

```bash
# After a migration session, the consumer repo should have:
test -s .github/MIGRATION-SCORECARD.md && echo SCORECARD_OK
```
