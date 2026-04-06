#!/usr/bin/env bash
# =============================================================================
# audit-log.sh — postToolUse hook
#
# Runs after every tool call. Logs tool usage to a structured JSONL audit trail
# at .github/ci-archive/migration-audit.jsonl.
#
# Tracks: what tools were used, what files were touched, whether they succeeded,
# and timing — useful for compliance, debugging, and understanding agent behavior.
# =============================================================================

set -euo pipefail

INPUT=$(cat)

TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')
TOOL_NAME=$(echo "$INPUT" | jq -r '.toolName')
RESULT_TYPE=$(echo "$INPUT" | jq -r '.toolResult.resultType // "unknown"')

# Extract file path if the tool touched a file
FILE_PATH=""
case "$TOOL_NAME" in
  edit|create|view|read)
    FILE_PATH=$(echo "$INPUT" | jq -r '.toolArgs' | jq -r '.path // .filePath // empty' 2>/dev/null)
    ;;
  bash)
    # Try to extract meaningful context from bash commands (first 100 chars)
    FILE_PATH=$(echo "$INPUT" | jq -r '.toolArgs' | jq -r '.command // empty' 2>/dev/null | head -c 100)
    ;;
esac

# Ensure archive directory exists
mkdir -p .github/ci-archive

# Append structured log entry (JSONL format — one JSON object per line)
jq -n -c \
  --arg ts "$TIMESTAMP" \
  --arg tool "$TOOL_NAME" \
  --arg result "$RESULT_TYPE" \
  --arg file "$FILE_PATH" \
  '{timestamp: $ts, tool: $tool, result: $result, file: $file}' \
  >> .github/ci-archive/migration-audit.jsonl
