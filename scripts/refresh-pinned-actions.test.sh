#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT
mkdir -p "$TEST_DIR/scripts" "$TEST_DIR/plugin/skills/migration-core"
cp "$ROOT/scripts/refresh-pinned-actions.sh" "$TEST_DIR/scripts/"

export TEST_SHA=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
export TEST_TAG='v1", "sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" }, "actions/checkout": { "tag": "injected\tag'

gh() {
  if [ "$1" = auth ]; then
    return 0
  fi
  if [ "${TEST_ALL_UNRESOLVED:-0}" = 1 ]; then
    return 1
  fi
  case "$2" in
    repos/codecov/codecov-action/*) printf 'invalid-sha\n' ;;
    repos/ruby/setup-ruby/releases/latest) return 1 ;;
    repos/actions/setup-node/releases/latest) printf '%s\n' "$TEST_TAG" ;;
    */releases/latest) printf 'v1.2.3\n' ;;
    */commits*) printf '%s\n' "$TEST_SHA" ;;
    *) return 1 ;;
  esac
}
export -f gh

bash "$TEST_DIR/scripts/refresh-pinned-actions.sh" 2>"$TEST_DIR/run.log"
jq -e --arg tag "$TEST_TAG" --arg sha "$TEST_SHA" '
  (keys | sort) == ["_comment", "actions", "resolved_on"] and
  (.resolved_on | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")) and
  (.actions | length) == 21 and
  .actions["actions/setup-node"].tag == $tag and
  .actions["actions/checkout"] == {tag: "v1.2.3", sha: $sha} and
  .actions["ruby/setup-ruby"] == {tag: "", sha: $sha} and
  (.actions | has("codecov/codecov-action") | not) and
  ([.actions[].sha] | all(. == $sha))
' "$TEST_DIR/plugin/skills/migration-core/pinned-actions.json" >/dev/null
printf 'PASS: JSON injection stays literal; catalog entries, fallback and skipped actions are correct.\n'

TEST_ALL_UNRESOLVED=1 bash "$TEST_DIR/scripts/refresh-pinned-actions.sh" 2>"$TEST_DIR/run.log"
jq -e '.actions == {}' "$TEST_DIR/plugin/skills/migration-core/pinned-actions.json" >/dev/null
printf 'PASS: unresolved actions produce an empty object, not invalid JSON.\n'

cp -R "$ROOT/plugin" "$ROOT/.github" "$TEST_DIR/"
cp "$ROOT/apm.yml" "$TEST_DIR/"
cp "$ROOT/scripts/check-plugin-content.sh" "$TEST_DIR/scripts/"
bash "$TEST_DIR/scripts/check-plugin-content.sh" >"$TEST_DIR/check.log" 2>&1
printf 'PASS: committed catalog passes the content checker.\n'

CATALOG="$TEST_DIR/plugin/skills/migration-core/pinned-actions.json"
for invalid_case in trailing-text empty multiple-objects array; do
  cp "$ROOT/plugin/skills/migration-core/pinned-actions.json" "$CATALOG"
  case "$invalid_case" in
    trailing-text) printf '\nnot JSON\n' >>"$CATALOG" ;;
    empty) : >"$CATALOG" ;;
    multiple-objects) printf '\n{}\n' >>"$CATALOG" ;;
    array) printf '[]\n' >"$CATALOG" ;;
  esac
  if bash "$TEST_DIR/scripts/check-plugin-content.sh" >"$TEST_DIR/check.log" 2>&1; then
    printf 'FAIL: content checker accepted %s catalog\n' "$invalid_case" >&2
    exit 1
  fi
  grep -q 'catalog must contain exactly one valid JSON object' "$TEST_DIR/check.log"
  printf 'PASS: content checker rejects %s catalog.\n' "$invalid_case"
done

cp "$ROOT/plugin/skills/migration-core/pinned-actions.json" "$CATALOG"
expect_invalid() {
  local label="$1" reason="$2"
  if bash "$TEST_DIR/scripts/check-plugin-content.sh" >"$TEST_DIR/check.log" 2>&1; then
    printf 'FAIL: plugin validator accepted %s\n' "$label" >&2
    exit 1
  fi
  grep -q "$reason" "$TEST_DIR/check.log"
  printf 'PASS: plugin validator rejects %s.\n' "$label"
}

for missing in plugin/skills/migration-core/standards.md plugin/skills/jenkins-migration/SKILL.md plugin/skills/jenkins-migration/mapping.md plugin/skills/jenkins-migration/report-template.md plugin/skills/jenkins-migration/secrets.md plugin/agents/jenkins-migrator.agent.md plugin/hooks.json; do
  mv "$TEST_DIR/$missing" "$TEST_DIR/missing-backup"
  expect_invalid "missing $missing" 'required plugin file is missing'
  mv "$TEST_DIR/missing-backup" "$TEST_DIR/$missing"
done

for invalid_text in 'mcp_github_get_tag' 'github-mcp-server-get_tag' '{MY_ORGANIZATION}' 'knowledge/migration-workflow.md'; do
  printf '\n%s\n' "$invalid_text" >>"$TEST_DIR/plugin/skills/migration-core/SKILL.md"
  expect_invalid "$invalid_text instruction" 'undeclared MCP tools'
  cp "$ROOT/plugin/skills/migration-core/SKILL.md" "$TEST_DIR/plugin/skills/migration-core/SKILL.md"
done

for version_file in apm.yml plugin/plugin.json .github/plugin/marketplace.json; do
  if [ "$version_file" = apm.yml ]; then
    sed 's/^version:.*/version: 0.0.0/' "$ROOT/$version_file" >"$TEST_DIR/$version_file"
  elif [ "$version_file" = plugin/plugin.json ]; then
    jq '.version = "0.0.0"' "$ROOT/$version_file" >"$TEST_DIR/$version_file"
  else
    jq '.plugins[0].version = "0.0.0"' "$ROOT/$version_file" >"$TEST_DIR/$version_file"
  fi
  expect_invalid "version mismatch in $version_file" 'package version mismatch'
  cp "$ROOT/$version_file" "$TEST_DIR/$version_file"
done

MARKETPLACE="$TEST_DIR/.github/plugin/marketplace.json"
for invalid_case in trailing-text empty multiple-valid-objects conflicting-then-valid array; do
  cp "$ROOT/.github/plugin/marketplace.json" "$MARKETPLACE"
  case "$invalid_case" in
    trailing-text) printf '\nnot JSON\n' >>"$MARKETPLACE" ;;
    empty) : >"$MARKETPLACE" ;;
    multiple-valid-objects) cat "$ROOT/.github/plugin/marketplace.json" >>"$MARKETPLACE" ;;
    conflicting-then-valid)
      jq '.metadata.version = "0.0.0" | .plugins[].version = "0.0.0"' \
        "$ROOT/.github/plugin/marketplace.json" >"$MARKETPLACE"
      cat "$ROOT/.github/plugin/marketplace.json" >>"$MARKETPLACE"
      ;;
    array) jq -s '.' "$ROOT/.github/plugin/marketplace.json" >"$MARKETPLACE" ;;
  esac
  expect_invalid "$invalid_case marketplace" 'package version mismatch'
done
cp "$ROOT/.github/plugin/marketplace.json" "$MARKETPLACE"

find() { return 2; }
export -f find
expect_invalid 'failed Markdown enumeration' 'unable to enumerate plugin Markdown files'
find() {
  printf '%s\n' 'plugin/skills/jenkins-migration/SKILL.md'
  return 2
}
export -f find
expect_invalid 'partial Markdown enumeration' 'unable to enumerate plugin Markdown files'
unset -f find

jq '.hooks = "../outside.json"' "$ROOT/plugin/plugin.json" >"$TEST_DIR/plugin/plugin.json"
expect_invalid 'hook path outside package' 'invalid hooks path'
cp "$ROOT/plugin/plugin.json" "$TEST_DIR/plugin/plugin.json"

for catalog_case in short-sha empty-actions missing-date; do
  case "$catalog_case" in
    short-sha) jq '.actions["actions/checkout"].sha = "abc"' "$ROOT/plugin/skills/migration-core/pinned-actions.json" >"$CATALOG" ;;
    empty-actions) jq '.actions = {}' "$ROOT/plugin/skills/migration-core/pinned-actions.json" >"$CATALOG" ;;
    missing-date) jq 'del(.resolved_on)' "$ROOT/plugin/skills/migration-core/pinned-actions.json" >"$CATALOG" ;;
  esac
  expect_invalid "$catalog_case catalog" 'resolution date and full commit SHAs'
done
cp "$ROOT/plugin/skills/migration-core/pinned-actions.json" "$CATALOG"

printf '````markdown\nwrapped content\n````\n' >"$TEST_DIR/plugin/skills/jenkins-migration/secrets.md"
expect_invalid 'whole-file markdown wrapper' 'stray markdown fence'
printf 'unmatched closing fence\n```\n' >"$TEST_DIR/plugin/skills/jenkins-migration/secrets.md"
expect_invalid 'unmatched closing fence' 'unmatched closing fence'
cp "$ROOT/plugin/skills/jenkins-migration/secrets.md" "$TEST_DIR/plugin/skills/jenkins-migration/secrets.md"
bash "$TEST_DIR/scripts/check-plugin-content.sh" >"$TEST_DIR/check.log" 2>&1