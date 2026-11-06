#!/usr/bin/env bash
# Cloud agent surface: assigns the conformance prompt to the Copilot cloud agent in $REPO, waits for its
# PR, and scores the hook log it commits. The cloud agent loads actions-migrator from the org's
# .github-private settings, which resolve the tool repo's main branch, so only run this for main.
# Needs: GH_TOKEN (a user token that can assign Copilot and push to $REPO), REPO, gh, python3, git.
# Writes $OUT_DIR/cloud-agent/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${GH_TOKEN:?set GH_TOKEN}"
: "${REPO:?set REPO to the repo where the cloud agent runs}"
WAIT_MINUTES=${WAIT_MINUTES:-45}

OUT=${OUT_DIR:-$(mktemp -d)}/cloud-agent
mkdir -p "$OUT"
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-cloud-XXXX")
WS=$ROOT/ws
make_workspace "$WS"
BRANCH="surface-run/${GITHUB_RUN_ID:-$(date +%s)}"
git_gh() { git -C "$WS" -c credential.helper= -c 'credential.helper=!gh auth git-credential' "$@"; }

git_gh push -q "https://github.com/$REPO.git" "main:refs/heads/$BRANCH"
issue=$(jq -n --arg t "Surface test: cloud agent (${SHA:-manual})" --arg b "$(render_prompt cloud)" \
  --arg repo "$REPO" --arg base "$BRANCH" \
  '{title: $t, body: $b, assignees: ["copilot-swe-agent[bot]"], agent_assignment: {target_repo: $repo, base_branch: $base}}' \
  | gh api "repos/$REPO/issues" --input - --jq .number)
echo "issue=$issue branch=$BRANCH" | tee "$OUT/run.log"

# The agent's PR title starts with [WIP] until it finishes.
pr="" head="" deadline=$(( $(date +%s) + WAIT_MINUTES * 60 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  read -r pr head title < <(gh pr list --repo "$REPO" --base "$BRANCH" --state all --json number,headRefName,title \
    --jq '.[0] | "\(.number) \(.headRefName) \(.title)"' 2>/dev/null || true)
  if [ -n "$pr" ] && [ "$pr" != null ] && [[ $title != "[WIP]"* ]]; then break; fi
  sleep 30
done
echo "pr=$pr head=$head title=$title" | tee -a "$OUT/run.log"

if [ -n "$pr" ] && [ "$pr" != null ]; then
  git_gh fetch -q "https://github.com/$REPO.git" "$head" && git -C "$WS" checkout -q FETCH_HEAD
  run_id=$(gh run list --repo "$REPO" --branch "$head" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
  [ -n "$run_id" ] && gh run view "$run_id" --repo "$REPO" --log > "$OUT/agent-session.log" 2>/dev/null
else
  echo "No finished pull request within $WAIT_MINUTES minutes" | tee -a "$OUT/run.log"
fi

collect_and_score cloud-agent "$WS" "$OUT" "$OUT/agent-session.log" \
  --meta "issue=$issue" --meta "pr=${pr:-none}"

# Test branches and PRs are disposable.
[ -n "$pr" ] && [ "$pr" != null ] && gh pr close "$pr" --repo "$REPO" --delete-branch >/dev/null 2>&1
gh issue close "$issue" --repo "$REPO" >/dev/null 2>&1
gh api -X DELETE "repos/$REPO/git/refs/heads/$BRANCH" >/dev/null 2>&1
exit 0
