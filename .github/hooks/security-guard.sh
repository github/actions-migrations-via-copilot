#!/usr/bin/env bash
# =============================================================================
# security-guard.sh — preToolUse hook
#
# Runs before EVERY tool call the migration agent makes. Can approve or deny
# tool executions by outputting a JSON permissionDecision.
#
# Enforces:
#   - No external network calls (curl, wget, etc.) to unknown hosts
#   - No destructive system commands (rm -rf /, sudo, etc.)
#   - No editing files outside allowed directories
#   - No use of unverified action creators in workflow files
#   - No secrets/tokens in file content
# =============================================================================

set -euo pipefail

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.toolName')
TOOL_ARGS=$(echo "$INPUT" | jq -r '.toolArgs')

# ---- Helper: deny with reason ----
deny() {
  jq -n --arg reason "$1" '{"permissionDecision":"deny","permissionDecisionReason":$reason}'
  exit 0
}

# ---------------------------------------------------------------------------
# 1. Bash command guardrails
# ---------------------------------------------------------------------------
if [ "$TOOL_NAME" = "bash" ]; then
  COMMAND=$(echo "$TOOL_ARGS" | jq -r '.command // empty')

  # Block destructive system commands
  if echo "$COMMAND" | grep -qE '(^|\s)(rm -rf /|sudo |mkfs |dd if=|chmod 777|chown )'; then
    deny "Destructive system command blocked: $COMMAND"
  fi

  # Block external network calls to unknown hosts
  # Allow: github.com, api.github.com (for MCP), localhost
  if echo "$COMMAND" | grep -qE '(curl|wget|nc |ncat )\s' ; then
    if ! echo "$COMMAND" | grep -qE '(github\.com|githubusercontent\.com|localhost|127\.0\.0\.1|actionlint)'; then
      deny "External network call not permitted during migration. Only github.com and localhost are allowed."
    fi
  fi

  # Block package installation (agent should only use existing tools)
  if echo "$COMMAND" | grep -qE '(pip install|gem install|cargo install|go install)\s'; then
    # Allow actionlint installation — it's needed for validation
    if ! echo "$COMMAND" | grep -q 'actionlint'; then
      deny "Package installation not permitted during migration (except actionlint)."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 2. File edit/create guardrails
# ---------------------------------------------------------------------------
if [ "$TOOL_NAME" = "edit" ] || [ "$TOOL_NAME" = "create" ]; then
  FILE_PATH=$(echo "$TOOL_ARGS" | jq -r '.path // .filePath // empty')

  if [ -n "$FILE_PATH" ]; then
    # Normalize: strip leading ./
    FILE_PATH="${FILE_PATH#./}"

    # Allow: .github/workflows/*, .github/ci-archive/*, .github/hooks/*,
    #        knowledge/*, copilot-instructions, README, package.json, .gitignore
    # Deny everything else — migration agents should not modify app source code
    case "$FILE_PATH" in
      .github/workflows/*) ;; # allowed
      .github/ci-archive/*) ;; # allowed
      .github/hooks/*) ;; # allowed
      .github/copilot-instructions.md) ;; # allowed
      knowledge/*) ;; # allowed
      README.md) ;; # allowed
      .gitignore) ;; # allowed
      .github/actions/*)
        # Guardrail: DO NOT create custom actions or write action code from scratch
        deny "Migration agents must not create custom actions. Use verified marketplace actions instead. Blocked: $FILE_PATH"
        ;;
      *)
        deny "Migration agents may only create/edit files in .github/workflows/, .github/ci-archive/, and documentation files. Blocked: $FILE_PATH"
        ;;
    esac
  fi

  # Check for hardcoded secrets/tokens in file content
  CONTENT=$(echo "$TOOL_ARGS" | jq -r '.content // .newContent // empty' 2>/dev/null)
  if [ -n "$CONTENT" ]; then
    # Detect common secret patterns (API keys, tokens, passwords)
    if echo "$CONTENT" | grep -qiE '(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|github_pat_|sk-[a-zA-Z0-9]{48}|AKIA[A-Z0-9]{16}|password\s*[:=]\s*["\x27][^"\x27]{8,})'; then
      deny "Potential hardcoded secret detected in file content. Use GitHub Secrets instead."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 3. Workflow content guardrails (when creating/editing .yml files)
# ---------------------------------------------------------------------------
if [ "$TOOL_NAME" = "create" ] || [ "$TOOL_NAME" = "edit" ]; then
  FILE_PATH=$(echo "$TOOL_ARGS" | jq -r '.path // .filePath // empty')

  if echo "$FILE_PATH" | grep -qE '\.ya?ml$'; then
    CONTENT=$(echo "$TOOL_ARGS" | jq -r '.content // .newContent // empty' 2>/dev/null)

    if [ -n "$CONTENT" ]; then
      # Check for actions not pinned to SHAs (uses: org/action@v4 instead of @sha)
      UNPINNED=$(echo "$CONTENT" | grep -E '^\s*-?\s*uses:' | grep -vE '@[a-f0-9]{40}' | grep -vE '^\s*#' || true)
      if [ -n "$UNPINNED" ]; then
        deny "Workflow contains actions not pinned to commit SHAs. Pin all actions to 40-char SHAs per security standards."
      fi

      # Check for overly permissive permissions
      if echo "$CONTENT" | grep -qE 'permissions:\s*write-all'; then
        deny "Workflow uses 'permissions: write-all'. Use least-privilege permissions per security standards."
      fi
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Default: allow
# ---------------------------------------------------------------------------
# No output = allow (per docs, only "deny" is processed)
