#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
for command in jq grep sed head tail find dirname; do
  command -v "$command" >/dev/null 2>&1 || {
    printf '::error::required command not found: %s\n' "$command" >&2
    exit 1
  }
done

FAILED=0
CHECKED=0
fail() {
  printf '::error file=%s::%s\n' "$1" "$2"
  FAILED=$((FAILED + 1))
}
required_file() {
  CHECKED=$((CHECKED + 1))
  [ -s "$1" ] || fail "$1" 'required plugin file is missing or empty'
}

for field in agents skills hooks; do
  CHECKED=$((CHECKED + 1))
  relative=$(jq -er --arg field "$field" '.[$field] | select(type == "string" and length > 0)' plugin/plugin.json) || {
    fail plugin/plugin.json "invalid $field declaration"
    continue
  }
  case "$relative" in
    /*|*..*) fail plugin/plugin.json "invalid $field path"; continue ;;
  esac
  if [ "$field" = hooks ]; then
    required_file "plugin/$relative"
    jq -e '.version == 1 and (.hooks | type == "object")' "plugin/$relative" >/dev/null 2>&1 || fail "plugin/$relative" 'invalid hook configuration'
  elif [ ! -d "plugin/$relative" ]; then
    fail "plugin/$relative" 'declared plugin directory is missing'
  fi
done

for platform in azure-devops bamboo bitbucket circleci droneci gitlab jenkins travisci; do
  required_file "plugin/agents/$platform-migrator.agent.md"
  for reference in SKILL.md mapping.md report-template.md secrets.md; do
    required_file "plugin/skills/$platform-migration/$reference"
  done
done
for reference in SKILL.md workflow.md standards.md guardrails.md pinned-actions.json; do
  required_file "plugin/skills/migration-core/$reference"
done
required_file plugin/agents/reusable-workflow-builder.agent.md
required_file plugin/skills/reusable-workflow-patterns/SKILL.md
required_file plugin/skills/actionlint/SKILL.md
required_file plugin/skills/jenkins-migration/pipeline.md
required_file plugin/skills/jenkins-migration/groovy.md

while IFS= read -r file; do
  CHECKED=$((CHECKED + 1))
  if head -1 "$file" | grep -qE '^`{3,}(markdown)?$'; then
    fail "$file" 'file opens with a stray markdown fence'
  elif [ "$(tail -1 "$file")" = '```' ] && [ "$(grep -c '^```' "$file")" -eq 1 ]; then
    fail "$file" 'file ends with an unmatched closing fence'
  fi
done < <(find plugin/skills plugin/agents -type f -name '*.md')

CHECKED=$((CHECKED + 1))
if grep -rnE 'mcp_[a-z_]+|github-mcp-server-[a-z_]+|\{MY_ORGANIZATION\}|knowledge/' plugin/skills/ plugin/agents/; then
  fail plugin/ 'plugin instructions contain undeclared MCP tools, organization placeholders, or retired knowledge paths'
fi

CATALOG=plugin/skills/migration-core/pinned-actions.json
CHECKED=$((CHECKED + 1))
if ! jq -e -s 'length == 1 and (.[0] | type == "object")' "$CATALOG" >/dev/null 2>&1; then
  fail "$CATALOG" 'catalog must contain exactly one valid JSON object'
elif ! jq -e '
  (.resolved_on | type == "string" and test("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")) and
  (.actions | type == "object" and length > 0) and
  ([.actions[].sha | type == "string" and test("^[0-9a-f]{40}$")] | all)
' "$CATALOG" >/dev/null 2>&1; then
  fail "$CATALOG" 'catalog requires a resolution date and full commit SHAs for every action'
fi

CHECKED=$((CHECKED + 1))
APM_VERSION=$(sed -n 's/^version:[[:space:]]*//p' apm.yml | head -1)
PLUGIN_VERSION=$(jq -er '.version | select(type == "string")' plugin/plugin.json)
if [ -z "$PLUGIN_VERSION" ] || [ "$APM_VERSION" != "$PLUGIN_VERSION" ] ||
   ! jq -e --arg version "$PLUGIN_VERSION" '
     .metadata.version == $version and
     (.plugins | length > 0) and
     ([.plugins[].version == $version] | all)
   ' .github/plugin/marketplace.json >/dev/null 2>&1; then
  fail apm.yml 'package version mismatch between APM, plugin, and marketplace'
fi

if [ "$FAILED" -ne 0 ]; then
  printf 'FAILED: %s of %s checks\n' "$FAILED" "$CHECKED"
  exit 1
fi
printf 'PASSED: %s plugin validation checks\n' "$CHECKED"