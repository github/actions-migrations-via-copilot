#!/usr/bin/env bash
# Verifies the plugin ships content consistent with the cloud-agent knowledge
# base, and that the plugin instructs no tool it does not declare.
#
# Direction: knowledge/ is canonical. plugin/skills/** is derived from it.
#
# Note: the mcp_* check below proves the plugin does not *name* MCP tools. It
# is a declaration-hygiene check, not a capability boundary -- the agents hold
# `bash`, so their actual reach is whatever bash can reach.
#
# Requirements: bash, diff, grep, sed, head, tail, sort. No network, no jq, no
# Node. The preflight below fails closed if any are missing -- without it an
# absent grep would make the capability checks silently take their pass branch.
#
# Usage: bash scripts/check-content-parity.sh

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

for cmd in diff grep sed head tail sort; do
  command -v "$cmd" >/dev/null 2>&1 || {
    printf '::error::required command not found: %s\n' "$cmd"
    printf 'FAILED: missing dependency %s\n' "$cmd"
    exit 1
  }
done

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
    fail "$copy" "out of sync with $src"
    printf '        knowledge/ is canonical. If you edited the plugin copy, move that\n'
    printf '        change into %s first, then: cp %s %s\n' "$src" "'$src'" "'$copy'"
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
# Check both ends -- the bamboo bug was a matched open/close pair, and a file
# carrying only the trailing half would otherwise pass.
STRAY_FENCES=0
for f in knowledge/actions-mapping/*.md knowledge/report-template/*.md plugin/skills/*/*.md; do
  [ -f "$f" ] || continue
  CHECKED=$((CHECKED + 1))
  if head -1 "$f" | grep -qE '^`{3,}(markdown)?$'; then
    fail "$f" "file opens with a stray markdown fence -- remove the wrapper"
    STRAY_FENCES=$((STRAY_FENCES + 1))
  elif [ "$(tail -1 "$f")" = '```' ] && [ "$(grep -c '^```' "$f")" -eq 1 ]; then
    fail "$f" "file ends with an unmatched closing fence -- remove the wrapper"
    STRAY_FENCES=$((STRAY_FENCES + 1))
  fi
done
[ "$STRAY_FENCES" -eq 0 ] && pass "no stray fence wrappers"

echo
echo "==> Declared-capability invariants"

# apm.yml declares `mcp: []` and the plugin agents declare only local tools
# (bash/edit/view/create/grep/glob). A skill instructing an MCP call asks the
# agent to reach outside that boundary.
#
# Both naming conventions are matched: mcp_github_* as written in the cloud
# agent prompts, and github-mcp-server-* as the tools surface on the coding
# agent. Scoped to skills/ and agents/ because plugin/README.md legitimately
# discusses MCP in prose to explain that the plugin does not use it.
CHECKED=$((CHECKED + 1))
if grep -rnE 'mcp_[a-z_]+|github-mcp-server-[a-z_]+' plugin/skills/ plugin/agents/ 2>/dev/null; then
  fail "plugin/" "plugin declares 'mcp: []' but a skill or agent instructs an MCP tool call"
else
  pass "no MCP tool instructions in plugin/skills/ or plugin/agents/"
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
echo "==> Pinned actions catalog"

# The catalog is what makes offline pinning possible, so a malformed entry is
# worse than no entry -- it would ship a broken ref into a customer workflow.
# Regenerate with: bash scripts/refresh-pinned-actions.sh
CHECKED=$((CHECKED + 1))
CATALOG="plugin/skills/migration-core/pinned-actions.json"
if [ ! -f "$CATALOG" ]; then
  fail "$CATALOG" "pinned actions catalog is missing"
elif ! grep -q '"resolved_on"' "$CATALOG"; then
  fail "$CATALOG" "catalog has no resolved_on date, so staleness cannot be judged"
else
  TOTAL_SHAS=$(grep -c '"sha"' "$CATALOG")
  VALID_SHAS=$(grep -coE '"sha"[[:space:]]*:[[:space:]]*"[0-9a-f]{40}"' "$CATALOG")
  if [ "$TOTAL_SHAS" -eq 0 ]; then
    fail "$CATALOG" "catalog contains no action entries"
  elif [ "$TOTAL_SHAS" -ne "$VALID_SHAS" ]; then
    fail "$CATALOG" "catalog has $((TOTAL_SHAS - VALID_SHAS)) entr(ies) whose sha is not a 40-char commit hash"
  else
    pass "$TOTAL_SHAS pinned actions, all full commit SHAs"
  fi
fi

echo
echo "==> Package version coherence"

# apm.yml, plugin.json and marketplace.json all describe the same package. They
# are bumped by hand with no release automation, which is how they drifted apart
# (apm.yml sat at 1.2.0 while the other two said 1.4.0).
#
# The README's APM pin is deliberately NOT checked here: it references the last
# *published* tag, which legitimately lags the in-development version on main.
# Keeping it current is a release-time step.
CHECKED=$((CHECKED + 1))
APM_V=$(sed -n 's/^version:[[:space:]]*//p' apm.yml | head -1)
PLUGIN_V=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' plugin/plugin.json | head -1)
MARKET_VS=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' .github/plugin/marketplace.json | sort -u)

if [ "$(printf '%s\n' "$MARKET_VS" | wc -l | tr -d ' ')" -ne 1 ]; then
  fail ".github/plugin/marketplace.json" "marketplace.json declares more than one version: $(printf '%s ' $MARKET_VS)"
elif [ "$APM_V" = "$PLUGIN_V" ] && [ "$PLUGIN_V" = "$MARKET_VS" ]; then
  pass "apm.yml, plugin.json and marketplace.json all declare $APM_V"
else
  fail "apm.yml" "version mismatch -- apm.yml=$APM_V plugin.json=$PLUGIN_V marketplace.json=$MARKET_VS"
fi

echo
if [ "$FAILED" -gt 0 ]; then
  echo "FAILED: $FAILED of $CHECKED checks"
  exit 1
fi
echo "PASSED: $CHECKED checks"
