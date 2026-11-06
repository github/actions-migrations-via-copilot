# Consumer Template

Drop the contents of this directory into the **root of any repo** that should
use the `actions-migrator` plugin.

Merge the settings into existing configuration rather than overwriting it. The
file names the marketplace and enables the plugin. Verify loading in your runtime;
the existence of this file alone is not an availability guarantee.

| Surface | What happens | Requires |
| --- | --- | --- |
| Copilot CLI | Install the marketplace plugin using the commands in the main README | A supported Copilot CLI version |
| Copilot cloud agent (github.com) | The runtime loads the configured plugin for the task | Repository or selected central configuration and cloud-agent access |
| VS Code | Configure/install the plugin through VS Code's plugin support | A supported runtime; verify hook behavior in that version |

## Files

| Path | Purpose |
| --- | --- |
| `.github/copilot/settings.json` | Declares the marketplace and enabled plugin for runtimes that consume this configuration. |

## Optional: org-wide rollout

Put the same `.github/copilot/settings.json` in your org's `.github` or
`.github-private` repo. Every repo in the org inherits it. Enterprise admins
can do the same in the designated `.github-private` to enforce it across all
orgs.

Merge precedence in CCA is **enterprise > org > repo**.

## Verify after configuring

Start a new session and inspect its resolved plugin revision, skill invocations,
and hook results. Test with a harmless fixture before customer work. A scorecard
alone may come from another installed plugin or an earlier run, so it is not
sufficient evidence. Configure cloud settings before starting the job; do not
assume a setting only present on a task branch controls initial plugin loading.
