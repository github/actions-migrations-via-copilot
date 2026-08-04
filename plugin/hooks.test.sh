#!/usr/bin/env bash
# =============================================================================
# hooks.test.sh — regression tests for plugin/hooks.json
#
# Verifies every hook behaves correctly against BOTH payload schemas:
#   - Copilot CLI / Cloud agent:  { "toolName": "...", "toolArgs": "<json string>", "sessionId": ... }
#   - VS Code Agent Plugins:      { "tool_name": "...", "tool_input": { ... }, "session_id": ... }
#
# Why this exists: the two surfaces send different field names, different arg
# encodings (string vs object), different tool names, and expect different
# output shapes. A change that silently breaks one surface would otherwise go
# unnoticed. This test pins the contract.
#
# Run:   ./plugin/hooks.test.sh
# Exit:  0 = all pass, 1 = one or more failures
#
# Requires: jq, bash
# =============================================================================

set -uo pipefail

HOOKS_JSON="$(cd "$(dirname "$0")" && pwd)/hooks.json"
PASS=0
FAIL=0

if ! command -v jq >/dev/null 2>&1; then
  echo "FATAL: jq is required to run these tests" >&2
  exit 1
fi
if [ ! -f "$HOOKS_JSON" ]; then
  echo "FATAL: hooks.json not found at $HOOKS_JSON" >&2
  exit 1
fi

# get_hook <event> <index>  -> prints the bash body
get_hook() { jq -r ".hooks.\"$1\"[$2].bash" "$HOOKS_JSON"; }

# run_case <label> <payload-json> <hook-bash> <expect: deny|allow|context|block>
run_case() {
  local label="$1" payload="$2" hook="$3" expect="$4"
  local out decision
  out=$(printf '%s' "$payload" | bash -c "$hook" 2>/dev/null)
  case "$expect" in
    deny)
      decision=$(printf '%s' "$out" | jq -r '.permissionDecision // .hookSpecificOutput.permissionDecision // "none"' 2>/dev/null)
      [ "$decision" = "deny" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
    allow)
      decision=$(printf '%s' "$out" | jq -r '.permissionDecision // .hookSpecificOutput.permissionDecision // "none"' 2>/dev/null)
      [ "$decision" = "none" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
    context)
      decision=$(printf '%s' "$out" | jq -r '.additionalContext // .hookSpecificOutput.additionalContext // "none"' 2>/dev/null)
      [ "$decision" != "none" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
    block)
      decision=$(printf '%s' "$out" | jq -r '.decision // .hookSpecificOutput.decision // "none"' 2>/dev/null)
      [ "$decision" = "block" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
    nocontext)
      decision=$(printf '%s' "$out" | jq -r '.additionalContext // .hookSpecificOutput.additionalContext // "none"' 2>/dev/null)
      [ "$decision" = "none" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
  esac
  FAIL=$((FAIL+1))
  echo "  FAIL $label"
  echo "       expected=$expect got=>>>$out<<<"
}

SECRET=$(get_hook preToolUse 0)
DESTRUCTIVE=$(get_hook preToolUse 1)
QUALITY=$(get_hook postToolUse 0)

echo "== preToolUse: secret detection =="
# CLI schema (toolArgs is a JSON string)
run_case "CLI  deny hardcoded password"      '{"toolName":"create","toolArgs":"{\"path\":\"c.yml\",\"content\":\"password: SuperSecret12345\"}"}' "$SECRET" deny
run_case "CLI  allow secrets-ref"            '{"toolName":"create","toolArgs":"{\"path\":\"w.yml\",\"content\":\"password: ${{ secrets.DB }}\"}"}' "$SECRET" allow
run_case "CLI  deny bash heredoc secret"     '{"toolName":"bash","toolArgs":"{\"command\":\"cat <<EOF > w.yml\\npassword: SuperSecret12345\\nEOF\"}"}' "$SECRET" deny
# VS Code schema (tool_input is an object)
run_case "VSC  deny hardcoded password"      '{"tool_name":"create_file","tool_input":{"filePath":"c.yml","content":"password: SuperSecret12345"}}' "$SECRET" deny
run_case "VSC  allow secrets-ref"            '{"tool_name":"create_file","tool_input":{"filePath":"w.yml","content":"password: ${{ secrets.DB }}"}}' "$SECRET" allow
run_case "VSC  allow no-content"             '{"tool_name":"create_file","tool_input":{"filePath":"x.txt"}}' "$SECRET" allow
run_case "VSC  deny shell redirect secret"   '{"tool_name":"run_in_terminal","tool_input":{"command":"printf \"token: hardcoded-secret-123\" > .github/workflows/x.yml","mode":"sync"}}' "$SECRET" deny

# --- regression: heredoc with secret + unrelated ${} elsewhere must still be blocked ---
run_case "CLI  deny heredoc secret w/ \${} nearby" \
  '{"toolName":"bash","toolArgs":"{\"command\":\"cat <<EOF > .env\\npassword: SuperSecret12345\\nblob: ${{ github.ref }}\\nEOF\"}"}' "$SECRET" deny
run_case "VSC  deny heredoc secret w/ \${} nearby" \
  '{"tool_name":"run_in_terminal","tool_input":{"command":"cat <<EOF > .env\npassword: SuperSecret12345\nblob: ${{ github.ref }}\nEOF","mode":"sync"}}' "$SECRET" deny

# --- regression: without jq, preToolUse must fail closed (deny), not silently allow ---
run_no_jq_case() {
  local label="$1" hook="$2" expect="$3"
  local TMPBIN
  TMPBIN=$(mktemp -d)
  for cmd in cat echo grep sed awk tr basename dirname bash ls mktemp head tail wc rm mkdir sort uniq date find printf; do
    local p; p=$(command -v "$cmd" 2>/dev/null)
    [ -n "$p" ] && ln -sf "$p" "$TMPBIN/$cmd"
  done
  local out; out=$(printf '%s' '{"toolName":"create","toolArgs":"{}"}' | PATH="$TMPBIN" bash -c "$hook" 2>/dev/null)
  rm -rf "$TMPBIN"
  local decision
  case "$expect" in
    deny)
      decision=$(printf '%s' "$out" | jq -r '.permissionDecision // .hookSpecificOutput.permissionDecision // "none"' 2>/dev/null)
      [ "$decision" = "deny" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
    block)
      decision=$(printf '%s' "$out" | jq -r '.decision // .hookSpecificOutput.decision // "none"' 2>/dev/null)
      [ "$decision" = "block" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
    context)
      decision=$(printf '%s' "$out" | jq -r '.additionalContext // .hookSpecificOutput.additionalContext // "none"' 2>/dev/null)
      [ "$decision" != "none" ] && { PASS=$((PASS+1)); echo "  ok   $label"; return; }
      ;;
  esac
  FAIL=$((FAIL+1))
  echo "  FAIL $label"
  echo "       expected=$expect got=>>>$out<<<"
}
run_no_jq_case "no-jq secret hook fails closed (deny)"      "$SECRET"      deny
run_no_jq_case "no-jq destructive hook fails closed (deny)" "$DESTRUCTIVE" deny

echo "== preToolUse: destructive op guard =="
run_case "CLI  deny rm README.md"            '{"toolName":"bash","toolArgs":"{\"command\":\"rm README.md\"}"}' "$DESTRUCTIVE" deny
run_case "CLI  deny rm Jenkinsfile"          '{"toolName":"bash","toolArgs":"{\"command\":\"rm Jenkinsfile\"}"}' "$DESTRUCTIVE" deny
run_case "VSC  deny rm README.md"            '{"tool_name":"run_in_terminal","tool_input":{"command":"rm README.md","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  allow git mv to ci-archive"   '{"tool_name":"run_in_terminal","tool_input":{"command":"git mv Jenkinsfile .github/ci-archive/Jenkinsfile","mode":"sync"}}' "$DESTRUCTIVE" allow
run_case "VSC  deny rm Jenkinsfile w/redir"  '{"tool_name":"run_in_terminal","tool_input":{"command":"rm Jenkinsfile 2>&1","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  deny git mv README.md"        '{"tool_name":"run_in_terminal","tool_input":{"command":"git mv README.md .github/ci-archive/README.md","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  deny path traversal"          '{"tool_name":"run_in_terminal","tool_input":{"command":"rm -f .github/ci-archive/../../README.md","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  allow rm inside ci-archive"   '{"tool_name":"run_in_terminal","tool_input":{"command":"rm -rf .github/ci-archive/old","mode":"sync"}}' "$DESTRUCTIVE" allow
run_case "VSC  deny find -delete"            '{"tool_name":"run_in_terminal","tool_input":{"command":"find . -name x -delete","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  deny sudo rm wrapper"         '{"tool_name":"run_in_terminal","tool_input":{"command":"sudo rm README.md","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  deny /bin/rm wrapper"         '{"tool_name":"run_in_terminal","tool_input":{"command":"/bin/rm README.md","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  deny command rm wrapper"      '{"tool_name":"run_in_terminal","tool_input":{"command":"command rm README.md","mode":"sync"}}' "$DESTRUCTIVE" deny
run_case "VSC  allow non-terminal tool noop" '{"tool_name":"create_file","tool_input":{"filePath":"x.txt","content":"hi"}}' "$DESTRUCTIVE" allow

echo "== postToolUse: workflow quality check =="
WORKDIR=$(mktemp -d)
mkdir -p "$WORKDIR/.github/workflows"
# dirty workflow: unpinned action, no permissions block
cat > "$WORKDIR/.github/workflows/dirty.yml" <<'YML'
name: CD
on: [push]
jobs:
  d:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
YML
# clean workflow
cat > "$WORKDIR/.github/workflows/clean.yml" <<'YML'
name: CI
permissions:
  contents: read
on: [push]
jobs:
  b:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
YML
run_case "CLI  flags dirty workflow"  '{"toolName":"create","toolArgs":"{\"path\":\"'"$WORKDIR"'/.github/workflows/dirty.yml\"}"}' "$QUALITY" context
run_case "VSC  flags dirty workflow"  '{"tool_name":"create_file","tool_input":{"filePath":"'"$WORKDIR"'/.github/workflows/dirty.yml"}}' "$QUALITY" context
run_case "VSC  clean workflow no-flag" '{"tool_name":"create_file","tool_input":{"filePath":"'"$WORKDIR"'/.github/workflows/clean.yml"}}' "$QUALITY" nocontext
run_case "VSC  non-workflow file noop" '{"tool_name":"create_file","tool_input":{"filePath":"'"$WORKDIR"'/README.md"}}' "$QUALITY" nocontext
run_no_jq_case "no-jq quality hook emits advisory (context)"      "$QUALITY"     context


echo "== agentStop (CLI): quality gate =="
GATE=$(get_hook agentStop 0)
run_case "CLI  agentStop blocks dirty" '{"sessionId":"g1","cwd":"'"$WORKDIR"'"}' "$GATE" block
run_case "CLI  agentStop safety valve after 3 attempts" '{"sessionId":"g1","cwd":"'"$WORKDIR"'"}' "$GATE" block
run_case "CLI  agentStop safety valve after 3 attempts (2)" '{"sessionId":"g1","cwd":"'"$WORKDIR"'"}' "$GATE" block
run_case "CLI  agentStop attempt 4 allows" '{"sessionId":"g1","cwd":"'"$WORKDIR"'"}' "$GATE" allow
run_no_jq_case "no-jq quality gate fails closed (block)"          "$GATE"        block


echo "== sessionEnd (CLI) + Stop (VS Code): scorecard =="
SC_CLI=$(get_hook sessionEnd 0)
SC_STOP=$(get_hook Stop 0)
# CLI sessionEnd writes a scorecard
printf '{"sessionId":"t-cli","cwd":"%s","reason":"complete"}' "$WORKDIR" | bash -c "$SC_CLI" >/dev/null 2>&1
if grep -q "dirty.yml" "$WORKDIR/.github/MIGRATION-SCORECARD.md" 2>/dev/null; then
  PASS=$((PASS+1)); echo "  ok   CLI  sessionEnd writes per-file scorecard"
else
  FAIL=$((FAIL+1)); echo "  FAIL CLI  sessionEnd writes per-file scorecard"
fi
# VS Code Stop appends a second entry
BEFORE=$(grep -c '^## ' "$WORKDIR/.github/MIGRATION-SCORECARD.md" 2>/dev/null || echo 0)
run_case "VSC  Stop blocks dirty workflow" '{"session_id":"t-vsc","cwd":"'"$WORKDIR"'","stop_hook_active":false}' "$SC_STOP" block
AFTER=$(grep -c '^## ' "$WORKDIR/.github/MIGRATION-SCORECARD.md" 2>/dev/null || echo 0)
if [ "$AFTER" -eq "$BEFORE" ]; then
  PASS=$((PASS+1)); echo "  ok   VSC  Stop does not append on blocked run"
else
  FAIL=$((FAIL+1)); echo "  FAIL VSC  Stop does not append on blocked run"
fi

# Make dirty workflow clean, then Stop should append
cat > "$WORKDIR/.github/workflows/dirty.yml" <<'YML'
name: CD
permissions:
  contents: read
on: [push]
jobs:
  d:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
YML

BEFORE=$(grep -c '^## ' "$WORKDIR/.github/MIGRATION-SCORECARD.md" 2>/dev/null || echo 0)
printf '{"session_id":"t-vsc","cwd":"%s","stop_hook_active":false}' "$WORKDIR" | bash -c "$SC_STOP" >/dev/null 2>&1
AFTER=$(grep -c '^## ' "$WORKDIR/.github/MIGRATION-SCORECARD.md" 2>/dev/null || echo 0)
if [ "$AFTER" -gt "$BEFORE" ]; then
  PASS=$((PASS+1)); echo "  ok   VSC  Stop appends scorecard after clean fix"
else
  FAIL=$((FAIL+1)); echo "  FAIL VSC  Stop appends scorecard after clean fix"
fi
# VS Code Stop must NOT loop when stop_hook_active=true
BEFORE=$(grep -c '^## ' "$WORKDIR/.github/MIGRATION-SCORECARD.md" 2>/dev/null || echo 0)
printf '{"session_id":"t-vsc","cwd":"%s","stop_hook_active":true}' "$WORKDIR" | bash -c "$SC_STOP" >/dev/null 2>&1
AFTER=$(grep -c '^## ' "$WORKDIR/.github/MIGRATION-SCORECARD.md" 2>/dev/null || echo 0)
if [ "$AFTER" -eq "$BEFORE" ]; then
  PASS=$((PASS+1)); echo "  ok   VSC  Stop no-ops when stop_hook_active=true"
else
  FAIL=$((FAIL+1)); echo "  FAIL VSC  Stop no-ops when stop_hook_active=true"
fi

rm -rf "$WORKDIR"
rm -f /tmp/.migration-quality-gate-t-cli /tmp/.migration-quality-gate-t-vsc
rm -f /tmp/.migration-quality-gate-g1

echo
echo "------------------------------------------------------------"
echo "Hook contract tests: $PASS passed, $FAIL failed"
echo "------------------------------------------------------------"
[ "$FAIL" -eq 0 ]
