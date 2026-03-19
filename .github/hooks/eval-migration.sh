#!/usr/bin/env bash
# =============================================================================
# eval-migration.sh — Post-session evaluation hook for CI/CD migration agents
#
# Runs automatically via Copilot coding agent hooks (sessionEnd) after a
# migration agent completes its work. Validates that the migration output
# meets the standards defined in knowledge/migration-standards.md and
# knowledge/migration-guardrails.md.
#
# Can also be run manually:
#   .github/hooks/eval-migration.sh [--ci-type jenkins|gitlab|circleci|...]
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ARCHIVE_DIR=".github/ci-archive"
WORKFLOWS_DIR=".github/workflows"
MIGRATION_README="$ARCHIVE_DIR/MIGRATION-README.md"

# Source CI file patterns — if ANY of these exist outside the archive, the
# agent failed to clean up.
CI_FILE_PATTERNS=(
  "Jenkinsfile"
  "*.jenkinsfile"
  ".gitlab-ci.yml"
  ".circleci/config.yml"
  ".travis.yml"
  "azure-pipelines.yml"
  "azure-pipelines/*.yml"
  ".drone.yml"
  "bitbucket-pipelines.yml"
  "bamboo-specs/*.yaml"
  "bamboo-specs/*.yml"
)

# Known verified action creator orgs on GitHub Marketplace.
# Actions from these orgs are considered safe.
VERIFIED_CREATORS=(
  "actions"
  "docker"
  "github"
  "SonarSource"
  "slackapi"
  "azure"
  "aws-actions"
  "google-github-actions"
  "hashicorp"
  "gradle"
  "ruby"
  "swift-actions"
  "cachix"
  "peaceiris"
  "JamesIves"
  "peter-evans"
  "softprops"
  "svenstaro"
  "ncipollo"
  "mikepenz"
  "dorny"
  "codecov"
  "sonarsource"
)

# Placeholder strings that should never appear in a completed migration report.
PLACEHOLDER_PATTERNS=(
  "TODO"
  "TBD"
  "PLACEHOLDER"
  "FIXME"
  "XXX"
  "CHANGEME"
  "INSERT"
  "REPLACE_ME"
  "your-.*-here"
  "<your"
  "example\.com"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS=0
FAIL=0
WARN=0
RESULTS=""

check_pass() {
  PASS=$((PASS + 1))
  RESULTS+="| $1 | ✅ Pass | $2 |\n"
}

check_fail() {
  FAIL=$((FAIL + 1))
  RESULTS+="| $1 | ❌ Fail | $2 |\n"
}

check_warn() {
  WARN=$((WARN + 1))
  RESULTS+="| $1 | ⚠️ Warn | $2 |\n"
}

# ---------------------------------------------------------------------------
# 1. Workflow files exist
# ---------------------------------------------------------------------------
check_workflows_exist() {
  local count
  count=$(find "$WORKFLOWS_DIR" -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')

  if [[ "$count" -gt 0 ]]; then
    check_pass "Workflows created" "$count workflow file(s) in $WORKFLOWS_DIR"
  else
    check_fail "Workflows created" "No workflow files found in $WORKFLOWS_DIR"
  fi
}

# ---------------------------------------------------------------------------
# 2. actionlint validation
# ---------------------------------------------------------------------------
check_actionlint() {
  if ! command -v actionlint &>/dev/null; then
    check_warn "actionlint" "actionlint not installed — skipping syntax validation"
    return
  fi

  local output
  output=$(actionlint "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml 2>&1 || true)
  local errors
  errors=$(echo "$output" | grep -c "error" 2>/dev/null || echo "0")

  if [[ "$errors" -eq 0 ]]; then
    check_pass "actionlint" "0 errors across all workflow files"
  else
    check_fail "actionlint" "$errors error(s) found — run \`actionlint\` for details"
  fi
}

# ---------------------------------------------------------------------------
# 3. Archive directory exists with files
# ---------------------------------------------------------------------------
check_archive_exists() {
  if [[ -d "$ARCHIVE_DIR" ]]; then
    local count
    count=$(find "$ARCHIVE_DIR" -type f ! -name "MIGRATION-README.md" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$count" -gt 0 ]]; then
      check_pass "Originals archived" "$count file(s) archived in $ARCHIVE_DIR"
    else
      check_fail "Originals archived" "$ARCHIVE_DIR exists but contains no archived source files"
    fi
  else
    check_fail "Originals archived" "$ARCHIVE_DIR directory not found"
  fi
}

# ---------------------------------------------------------------------------
# 4. No CI source files left outside the archive
# ---------------------------------------------------------------------------
check_no_originals_remain() {
  local found=()

  for pattern in "${CI_FILE_PATTERNS[@]}"; do
    # Search everywhere except .github/ci-archive/ and .git/
    while IFS= read -r f; do
      # Skip files inside the archive or .git
      if [[ "$f" != *"$ARCHIVE_DIR"* && "$f" != *".git/"* ]]; then
        found+=("$f")
      fi
    done < <(find . -path "./$ARCHIVE_DIR" -prune -o -path "./.git" -prune -o -name "$pattern" -print 2>/dev/null)
  done

  if [[ ${#found[@]} -eq 0 ]]; then
    check_pass "No originals remain" "No CI source files found outside $ARCHIVE_DIR"
  else
    check_fail "No originals remain" "Found ${#found[@]} file(s) outside archive: ${found[*]}"
  fi
}

# ---------------------------------------------------------------------------
# 5. MIGRATION-README.md exists
# ---------------------------------------------------------------------------
check_readme_exists() {
  if [[ -f "$MIGRATION_README" ]]; then
    local lines
    lines=$(wc -l < "$MIGRATION_README" | tr -d ' ')
    if [[ "$lines" -gt 20 ]]; then
      check_pass "MIGRATION-README.md" "Exists with $lines lines"
    else
      check_warn "MIGRATION-README.md" "Exists but only $lines lines — may be incomplete"
    fi
  else
    check_fail "MIGRATION-README.md" "Not found at $MIGRATION_README"
  fi
}

# ---------------------------------------------------------------------------
# 6. No placeholder text in README
# ---------------------------------------------------------------------------
check_no_placeholders() {
  if [[ ! -f "$MIGRATION_README" ]]; then
    return  # Already flagged by check_readme_exists
  fi

  local found_placeholders=()
  for pattern in "${PLACEHOLDER_PATTERNS[@]}"; do
    if grep -qiE "$pattern" "$MIGRATION_README" 2>/dev/null; then
      found_placeholders+=("$pattern")
    fi
  done

  if [[ ${#found_placeholders[@]} -eq 0 ]]; then
    check_pass "No placeholders" "No placeholder text found in migration report"
  else
    check_fail "No placeholders" "Found placeholder patterns: ${found_placeholders[*]}"
  fi
}

# ---------------------------------------------------------------------------
# 7. Actions are SHA-pinned
# ---------------------------------------------------------------------------
check_sha_pinning() {
  local total=0
  local pinned=0
  local unpinned=()

  while IFS= read -r line; do
    total=$((total + 1))
    # Extract the ref after @
    local ref
    ref=$(echo "$line" | sed 's/.*@//')
    # Check if it's a 40-char hex string (SHA)
    if echo "$ref" | grep -qE '^[a-f0-9]{40}$'; then
      pinned=$((pinned + 1))
    else
      unpinned+=("$(echo "$line" | sed 's/.*uses: *//')")
    fi
  done < <(grep -rh '^\s*-\?\s*uses:' "$WORKFLOWS_DIR"/ 2>/dev/null | grep -v '#')

  if [[ "$total" -eq 0 ]]; then
    check_warn "SHA pinning" "No \`uses:\` statements found"
  elif [[ ${#unpinned[@]} -eq 0 ]]; then
    check_pass "SHA pinning" "$pinned/$total actions pinned to commit SHAs"
  else
    check_fail "SHA pinning" "${#unpinned[@]}/$total not SHA-pinned: ${unpinned[*]}"
  fi
}

# ---------------------------------------------------------------------------
# 8. Actions from verified creators only
# ---------------------------------------------------------------------------
check_verified_creators() {
  local unverified=()

  while IFS= read -r action; do
    # Extract org from actions/checkout@sha → actions
    local org
    org=$(echo "$action" | cut -d'/' -f1)
    local is_verified=false
    for vc in "${VERIFIED_CREATORS[@]}"; do
      if echo "$org" | grep -qiE "^${vc}$"; then
        is_verified=true
        break
      fi
    done
    if [[ "$is_verified" == "false" ]]; then
      unverified+=("$action")
    fi
  done < <(grep -rh '^\s*-\?\s*uses:' "$WORKFLOWS_DIR"/ 2>/dev/null | sed 's/.*uses: *//; s/@.*//' | sort -u)

  if [[ ${#unverified[@]} -eq 0 ]]; then
    check_pass "Verified creators" "All actions from verified creators"
  else
    check_warn "Verified creators" "Unverified: ${unverified[*]} — review manually"
  fi
}

# ---------------------------------------------------------------------------
# 9. Permissions declared
# ---------------------------------------------------------------------------
check_permissions() {
  local total=0
  local with_perms=0
  local missing=()

  for wf in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
    [[ -f "$wf" ]] || continue
    total=$((total + 1))
    if grep -q '^permissions:' "$wf" 2>/dev/null; then
      with_perms=$((with_perms + 1))
    else
      missing+=("$(basename "$wf")")
    fi
  done

  if [[ "$total" -eq 0 ]]; then
    check_warn "Permissions" "No workflow files to check"
  elif [[ ${#missing[@]} -eq 0 ]]; then
    check_pass "Permissions" "$with_perms/$total workflows declare top-level permissions"
  else
    check_fail "Permissions" "Missing permissions block: ${missing[*]}"
  fi
}

# ---------------------------------------------------------------------------
# 10. Secrets documented in README
# ---------------------------------------------------------------------------
check_secrets_documented() {
  if [[ ! -f "$MIGRATION_README" ]]; then
    return
  fi

  local undocumented=()

  # Extract all secrets.* references from workflows
  while IFS= read -r secret; do
    if ! grep -qi "$secret" "$MIGRATION_README" 2>/dev/null; then
      undocumented+=("$secret")
    fi
  done < <(grep -roh 'secrets\.[A-Z_]*' "$WORKFLOWS_DIR"/ 2>/dev/null | sed 's/secrets\.//' | sort -u)

  if [[ ${#undocumented[@]} -eq 0 ]]; then
    local total
    total=$(grep -roh 'secrets\.[A-Z_]*' "$WORKFLOWS_DIR"/ 2>/dev/null | sed 's/secrets\.//' | sort -u | wc -l | tr -d ' ')
    check_pass "Secrets documented" "$total secret(s) all documented in README"
  else
    check_fail "Secrets documented" "Undocumented: ${undocumented[*]}"
  fi
}

# ---------------------------------------------------------------------------
# 11. Version comments present (SHA → version mapping)
# ---------------------------------------------------------------------------
check_version_comments() {
  local total=0
  local commented=0

  while IFS= read -r line_num; do
    total=$((total + 1))
  done < <(grep -rn '^\s*-\?\s*uses:.*@[a-f0-9]\{40\}' "$WORKFLOWS_DIR"/ 2>/dev/null)

  # Check if there's a version comment on the same line or the line above
  for wf in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
    [[ -f "$wf" ]] || continue
    local prev_line=""
    while IFS= read -r line; do
      if echo "$line" | grep -qE '@[a-f0-9]{40}'; then
        if echo "$line" | grep -qiE '#.*v[0-9]' || echo "$prev_line" | grep -qiE '#.*v[0-9]'; then
          commented=$((commented + 1))
        fi
      fi
      prev_line="$line"
    done < "$wf"
  done

  if [[ "$total" -eq 0 ]]; then
    check_warn "Version comments" "No SHA-pinned actions to check"
  elif [[ "$commented" -eq "$total" ]]; then
    check_pass "Version comments" "$commented/$total SHA-pinned actions have version comments"
  else
    check_warn "Version comments" "$commented/$total have version comments — consider adding to all"
  fi
}

# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------
main() {
  check_workflows_exist
  check_actionlint
  check_archive_exists
  check_no_originals_remain
  check_readme_exists
  check_no_placeholders
  check_sha_pinning
  check_verified_creators
  check_permissions
  check_secrets_documented
  check_version_comments

  # Output report
  local total=$((PASS + FAIL + WARN))
  echo ""
  echo "## Migration Eval Report"
  echo ""
  echo "| Check | Result | Details |"
  echo "|-------|--------|---------|"
  echo -e "$RESULTS"
  echo ""
  echo "**Score: $PASS passed, $FAIL failed, $WARN warnings out of $total checks**"
  echo ""

  if [[ "$FAIL" -gt 0 ]]; then
    echo "❌ Migration does not meet standards. Review failed checks above."
    exit 1
  else
    echo "✅ Migration meets all required standards."
    exit 0
  fi
}

main "$@"
