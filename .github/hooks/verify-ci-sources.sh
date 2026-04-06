#!/usr/bin/env bash
# =============================================================================
# verify-ci-sources.sh — sessionStart hook
#
# Runs when a migration agent session begins. Validates that the repository
# contains at least one CI/CD source file that can be migrated.
#
# Enforces guardrail: "DO NOT create GitHub Actions workflows without a source
# CI/CD configuration file"
#
# This hook does NOT block the agent (sessionStart output is ignored), but it
# logs a clear warning so the agent sees it in its environment.
# =============================================================================

set -euo pipefail

INPUT=$(cat)

# CI source file patterns — at least one must exist for migration to proceed
CI_PATTERNS=(
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

FOUND_FILES=()

for pattern in "${CI_PATTERNS[@]}"; do
  while IFS= read -r f; do
    [[ -n "$f" ]] && FOUND_FILES+=("$f")
  done < <(find . -maxdepth 3 -name "$pattern" -not -path "./.git/*" -not -path "./.github/ci-archive/*" 2>/dev/null)
done

if [[ ${#FOUND_FILES[@]} -eq 0 ]]; then
  echo "================================================================" >&2
  echo "WARNING: No CI/CD source files found in this repository."        >&2
  echo ""                                                                 >&2
  echo "Migration agents require existing CI/CD configuration files"     >&2
  echo "(e.g., Jenkinsfile, .gitlab-ci.yml, .travis.yml, etc.)"         >&2
  echo ""                                                                 >&2
  echo "Per migration guardrails: DO NOT create GitHub Actions"          >&2
  echo "workflows without a source CI/CD configuration file."            >&2
  echo "================================================================" >&2
  exit 1
else
  echo "Found ${#FOUND_FILES[@]} CI/CD source file(s):" >&2
  for f in "${FOUND_FILES[@]}"; do
    echo "  - $f" >&2
  done
fi
