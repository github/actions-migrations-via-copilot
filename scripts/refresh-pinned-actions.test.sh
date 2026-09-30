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

cp -R "$ROOT/knowledge" "$ROOT/agents" "$ROOT/plugin" "$ROOT/.github" "$TEST_DIR/"
cp "$ROOT/apm.yml" "$TEST_DIR/"
cp "$ROOT/scripts/check-content-parity.sh" "$TEST_DIR/scripts/"
cp "$ROOT/scripts/check-migration-core-sources.sh" "$TEST_DIR/scripts/"
"$TEST_DIR/scripts/check-content-parity.sh" >"$TEST_DIR/check.log" 2>&1
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
  if "$TEST_DIR/scripts/check-content-parity.sh" >"$TEST_DIR/check.log" 2>&1; then
    printf 'FAIL: content checker accepted %s catalog\n' "$invalid_case" >&2
    exit 1
  fi
  grep -q 'catalog must contain exactly one valid JSON object' "$TEST_DIR/check.log"
  printf 'PASS: content checker rejects %s catalog.\n' "$invalid_case"
done

cp "$ROOT/plugin/skills/migration-core/pinned-actions.json" "$CATALOG"
for source in knowledge/migration-workflow.md knowledge/migration-standards.md knowledge/migration-guardrails.md plugin/skills/migration-core/SKILL.md; do
  printf '\nChanged source\n' >>"$TEST_DIR/$source"
  if "$TEST_DIR/scripts/check-content-parity.sh" >"$TEST_DIR/check.log" 2>&1; then
    printf 'FAIL: content checker accepted an unreviewed change to %s\n' "$source" >&2
    exit 1
  fi
  grep -q 'migration-core source review required' "$TEST_DIR/check.log"
  cp "$ROOT/$source" "$TEST_DIR/$source"
  printf 'PASS: content checker rejects unreviewed %s change.\n' "$source"
done
bash "$TEST_DIR/scripts/check-migration-core-sources.sh" --refresh >/dev/null
"$TEST_DIR/scripts/check-content-parity.sh" >"$TEST_DIR/check.log" 2>&1

for missing in knowledge/migration-standards.md plugin/skills/migration-core/sources.json; do
  mv "$TEST_DIR/$missing" "$TEST_DIR/missing-backup"
  if "$TEST_DIR/scripts/check-content-parity.sh" >"$TEST_DIR/check.log" 2>&1; then
    printf 'FAIL: content checker accepted missing %s\n' "$missing" >&2
    exit 1
  fi
  mv "$TEST_DIR/missing-backup" "$TEST_DIR/$missing"
  printf 'PASS: content checker rejects missing %s.\n' "$missing"
done
sed 's/Never disable secret scanning/Never switch off secret scanning/' \
  "$TEST_DIR/knowledge/migration-guardrails.md" >"$TEST_DIR/changed-guardrails"
mv "$TEST_DIR/changed-guardrails" "$TEST_DIR/knowledge/migration-guardrails.md"
if bash "$TEST_DIR/scripts/check-migration-core-sources.sh" --refresh >"$TEST_DIR/check.log" 2>&1; then
  printf 'FAIL: hash refresh accepted divergent report-safety rules\n' >&2
  exit 1
fi
grep -q 'Safe Migration Reports must match' "$TEST_DIR/check.log"
printf 'PASS: refreshing hashes cannot bypass report-safety section parity.\n'