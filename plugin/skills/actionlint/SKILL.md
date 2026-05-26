---
name: actionlint
description: Install, run, and fix errors from actionlint — the GitHub Actions workflow linter. Load when validating `.github/workflows/*.yml` files after migration or generation.
---

# actionlint

[actionlint](https://github.com/rhysd/actionlint) is a static analysis tool for GitHub Actions workflow files. Always run it after generating or modifying workflows and resolve every finding before completing.

## Install

### Linux (pinned, checksum-verified)

```bash
ACTIONLINT_VERSION="1.7.11"
curl -fsSLO "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
curl -fsSLO "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_checksums.txt"
sha256sum --check --ignore-missing "actionlint_${ACTIONLINT_VERSION}_checksums.txt"
# Optional: gh attestation verify --repo rhysd/actionlint "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
tar xzf "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" -C /tmp actionlint
sudo install -m 755 /tmp/actionlint /usr/local/bin/actionlint
rm "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" "actionlint_${ACTIONLINT_VERSION}_checksums.txt"
```

### macOS

```bash
brew install actionlint
```

### Verify install

```bash
actionlint --version
```

## Run

```bash
# Lint all workflows
actionlint .github/workflows/*.yml

# Lint a specific file
actionlint .github/workflows/ci.yml

# Capture output for the migration report
actionlint .github/workflows/*.yml 2>&1 | tee /tmp/actionlint-output.txt
```

**Zero output = no errors.** Any output must be resolved.

## Output format

```
path/to/workflow.yml:LINE:COL: ERROR MESSAGE [rule-name]
   |
NN | <offending line>
   |       ^~~~
```

Each finding shows the file, line/column, a human-readable message, the rule name in `[brackets]`, and a code snippet pointing at the problem.

## Common errors and fixes

### `pin-actions` — action not pinned to a commit SHA

```
workflow.yml:10:9: action "actions/checkout@v4" is not pinned to a commit SHA [pin-actions]
```

Fix: resolve the SHA for the version tag and pin to it. Use `mcp_github_get_tag` to get the SHA, then:

```yaml
# Before
- uses: actions/checkout@v4

# After — SHA for v4.1.7, from mcp_github_get_tag on actions/checkout
# actions/checkout v4.1.7
- uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332
```

### `shellcheck` — shell script issues in `run:` steps

```
workflow.yml:12:9: shellcheck reported issue in this script: SC2086: ...
```

Fix: quote variables, use `${{ }}` for expressions, follow the shellcheck suggestion inline.

### `action` — unknown or malformed `uses:` reference

```
workflow.yml:8:9: can't parse action "owner/repo" [action]
```

Fix: ensure `uses: owner/repo@SHA` with a valid pinned SHA. Verify the action exists on GitHub Marketplace.

### `expression` — invalid `${{ }}` syntax

```
workflow.yml:20:14: unexpected end of expression [expression]
```

Fix: check bracket balance, quoting, and that context/property names are spelled correctly (e.g. `github.event.pull_request.head.sha`).

### `events` — invalid trigger or event filter

```
workflow.yml:3:5: unknown event "pull-request" [events]
```

Fix: use the exact GitHub event name (`pull_request`, not `pull-request`). Check the [events docs](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows).

### `permissions` — invalid permission scope or value

```
workflow.yml:6:5: unknown permission scope "pull-requests" [permissions]
```

Fix: permission keys are hyphenated (`pull-requests`, `id-token`); values must be `read`, `write`, or `none`.

### `job-needs` — `needs:` references a job that doesn't exist

```
workflow.yml:30:12: job "build" is not defined [job-needs]
```

Fix: ensure the job ID in `needs:` exactly matches a defined job key.

### `credentials` — `username`/`password` used without both fields

```
workflow.yml:18:9: "password" is required if "username" is set in credentials [credentials]
```

Fix: provide both `username` and `password` in the `credentials:` block, or remove both.

### `deprecated` — deprecated context or syntax

```
workflow.yml:25:14: "github.event.action" is not available for this event [deprecated]
```

Fix: follow the suggestion in the message to use the current equivalent.

## Iterating to zero errors

1. Run `actionlint`, read every finding.
2. Fix the highest-severity / most upstream issues first (parse errors before logic errors).
3. Re-run after each batch of fixes.
4. Paste the **final clean run output** (or `No issues found`) into the migration report under **Validation Results**.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `actionlint: command not found` | Not installed or not on PATH | Re-run the install steps above |
| `Error: no workflow files are found` | Glob matched nothing | Confirm files exist at `.github/workflows/*.yml` |
| Warnings about `shellcheck` not found | shellcheck not installed | `apt-get install shellcheck` or `brew install shellcheck` |
