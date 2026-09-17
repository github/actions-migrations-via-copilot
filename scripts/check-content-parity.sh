#!/usr/bin/env bash
# Verifies the plugin ships content consistent with the cloud-agent knowledge
# base, and that the plugin declares no capabilities it cannot legitimately use.
#
# Requirements: bash + diff only. No network, no jq, no Node.
#
# Usage: bash scripts/check-content-parity.sh

set -uo pipefail

cd "$(dirname "$0")/.."

FAILED=0
CHECKED=0

PLATFORMS=(azure-devops bamboo bitbucket circleci droneci gitlab jenkins travisci)

fail() {
  printf '::error file=%s::%s\n' "$1" "$2"
  printf '  FAIL  %s\n' "$2"
  FAILED=$((FAILED + 1))
}

pass() {
  printf '  ok    %s\n' "$1"
}

# A copied file must be byte-identical to its knowledge/ source. The plugin
# ships content locally instead of fetching it over MCP, so the two trees are
# the same material in two packaging formats -- any divergence means cloud and
# CLI users are following different guidance.
check_pair() {
  local src="$1" copy="$2"
  CHECKED=$((CHECKED + 1))

  if [ ! -f "$src" ]; then
    fail "$src" "missing knowledge source: $src"
    return
  fi
  if [ ! -f "$copy" ]; then
    fail "$copy" "missing plugin copy: $copy"
    return
  fi
  if diff -q "$src" "$copy" >/dev/null 2>&1; then
    pass "$copy"
  else
    fail "$copy" "out of sync with $src -- run: cp '$src' '$copy'"
    diff -u "$src" "$copy" | head -20 | sed 's/^/        /'
  fi
}

echo "==> Content parity: knowledge/ vs plugin/skills/"

for p in "${PLATFORMS[@]}"; do
  check_pair "knowledge/actions-mapping/$p.md"  "plugin/skills/$p-migration/mapping.md"
  check_pair "knowledge/report-template/$p.md"  "plugin/skills/$p-migration/report-template.md"
done

check_pair "knowledge/patterns/jenkins/pipeline.md" "plugin/skills/jenkins-migration/pipeline.md"
check_pair "knowledge/patterns/jenkins/groovy.md"   "plugin/skills/jenkins-migration/groovy.md"

echo
echo "==> Stray markdown fence wrappers"

# A whole-file ```markdown wrapper makes the copy differ from its source and
# leaks a code fence into the model's context. This is what drifted on bamboo.
for f in knowledge/actions-mapping/*.md knowledge/report-template/*.md plugin/skills/*/*.md; do
  [ -f "$f" ] || continue
  CHECKED=$((CHECKED + 1))
  if head -1 "$f" | grep -qE '^`{3,}(markdown)?$'; then
    fail "$f" "file opens with a stray markdown fence -- remove the wrapper"
  fi
done
[ "$FAILED" -eq 0 ] && pass "no stray fence wrappers"

echo
echo "==> Declared-capability invariants"

# apm.yml declares `mcp: []` and the plugin agents declare only local tools
# (bash/edit/view/create/grep/glob). A skill instructing an mcp_* call asks the
# agent to reach outside that boundary.
CHECKED=$((CHECKED + 1))
if grep -rn 'mcp_[a-z_]*' plugin/ 2>/dev/null; then
  fail "plugin/" "plugin declares 'mcp: []' but a skill instructs an MCP tool call"
else
  pass "no mcp_* references in plugin/"
fi

# The org placeholder is substituted at cloud deploy time. It has no meaning in
# the plugin, and a literal {MY_ORGANIZATION} reaching a user is a broken doc.
CHECKED=$((CHECKED + 1))
if grep -rn '{MY_ORGANIZATION}' plugin/ knowledge/ 2>/dev/null; then
  fail "plugin/" "{MY_ORGANIZATION} placeholder must not appear in plugin/ or knowledge/"
else
  pass "no {MY_ORGANIZATION} in plugin/ or knowledge/"
fi

# An agent that fetches from knowledge/ must carry the placeholder -- without it
# the MCP fetch resolves against the wrong owner and silently returns nothing.
# Agents that never read knowledge/ (e.g. reusable-workflow-builder, which scans
# user-supplied repos) legitimately have no placeholder.
CHECKED=$((CHECKED + 1))
MISSING_PLACEHOLDER=0
for f in agents/*.md; do
  [ -f "$f" ] || continue
  grep -q 'knowledge/' "$f" || continue
  grep -q '{MY_ORGANIZATION}' "$f" || {
    fail "$f" "agent fetches knowledge/ but is missing the {MY_ORGANIZATION} placeholder"
    MISSING_PLACEHOLDER=1
  }
done
[ "$MISSING_PLACEHOLDER" -eq 0 ] && pass "all knowledge-fetching agents carry the placeholder"

echo
if [ "$FAILED" -gt 0 ]; then
  echo "FAILED: $FAILED of $CHECKED checks"
  exit 1
fi
echo "PASSED: $CHECKED checks"
