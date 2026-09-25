#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
MANIFEST="plugin/skills/migration-core/sources.json"
SKILL="plugin/skills/migration-core/SKILL.md"
SOURCES=(knowledge/migration-workflow.md knowledge/migration-standards.md knowledge/migration-guardrails.md)
MODE="${1:-check}"
case "$MODE" in
  check|--refresh) ;;
  *) printf 'Usage: %s [--refresh]\n' "$0" >&2; exit 1 ;;
esac
for command in jq awk; do
  command -v "$command" >/dev/null || { printf 'Missing command: %s\n' "$command" >&2; exit 1; }
done
if command -v sha256sum >/dev/null; then
  HASH=(sha256sum)
elif command -v shasum >/dev/null; then
  HASH=(shasum -a 256)
else
  printf 'Missing sha256sum or shasum\n' >&2
  exit 1
fi

report_rules() {
  awk '/^### Safe Migration Reports$/ {active=1; next}
       active && (/^#/ || /^---$/) {exit}
       active && NF {print}' "$1"
}
RULES=$(report_rules knowledge/migration-guardrails.md)
if [ -z "$RULES" ] || [ "$RULES" != "$(report_rules "$SKILL")" ]; then
  printf 'Safe Migration Reports must match in the shared guardrails and migration-core skill.\n' >&2
  exit 1
fi

CURRENT='{"schema":1,"files":{}}'
for source in "${SOURCES[@]}" "$SKILL"; do
  [ -f "$source" ] || { printf 'Missing migration-core source: %s\n' "$source" >&2; exit 1; }
  digest=$("${HASH[@]}" "$source")
  CURRENT=$(jq --arg path "$source" --arg sha "${digest%% *}" '.files[$path]=$sha' <<<"$CURRENT")
done

if [ "$MODE" = --refresh ]; then
  printf '%s\n' "$CURRENT" >"$MANIFEST"
  printf 'Updated %s; commit only after reviewing source/skill consistency.\n' "$MANIFEST"
elif ! jq -e -s --argjson expected "$CURRENT" 'length == 1 and .[0] == $expected' "$MANIFEST" >/dev/null; then
  printf 'Migration-core sources changed or the review record is missing. Review the source/skill changes, then run bash scripts/check-migration-core-sources.sh --refresh.\n' >&2
  exit 1
else
  printf 'Migration-core source review hashes and report-safety rules match.\n'
fi