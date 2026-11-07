#!/usr/bin/env bash
# Cloud agent surface: assigns the conformance prompt to the Copilot cloud agent in $REPO, waits for its
# PR, and scores the hook log it commits. The cloud agent loads actions-migrator from the org's
# .github-private settings, which resolve the tool repo's main branch, so only run this for main.
# Needs: GH_TOKEN (a user token that can assign Copilot and push to $REPO), REPO, gh, python3, git.
# Requires a published hc-probes marketplace in CLOUD_MARKETPLACE_REPO.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${GH_TOKEN:?set GH_TOKEN}"
: "${REPO:?set REPO to the repo where the cloud agent runs}"
WAIT_MINUTES=${WAIT_MINUTES:-45}
CLOUD_SESSION=${CLOUD_SESSION:-repo}
CLOUD_MARKETPLACE_REPO=${CLOUD_MARKETPLACE_REPO:-$REPO}
case "$CLOUD_SESSION" in repo|plugin) ;; *) echo 'CLOUD_SESSION must be repo or plugin' >&2; exit 1 ;; esac

OUT=${OUT_DIR:-$(mktemp -d)}/cloud-agent/$CLOUD_SESSION
mkdir -p "$OUT"
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-cloud-XXXX")
WS=$ROOT/ws
make_workspace "$WS" "$CLOUD_SESSION"
python3 "$SUITE_DIR/cloud_settings.py" "$WS" "$CLOUD_SESSION" "$CLOUD_MARKETPLACE_REPO"
git_commit_all "$WS" "Configure isolated cloud test plugins"
BRANCH="surface-run/${GITHUB_RUN_ID:-$(date +%s)}-$CLOUD_SESSION"
git_gh() { git -C "$WS" -c credential.helper= -c 'credential.helper=!gh auth git-credential' "$@"; }
issue="" pr="" head="" title="" created=0 completed=0

cleanup() {
  if [ -n "$pr" ] && [ "$pr" != null ]; then
    gh pr close "$pr" --repo "$REPO" --delete-branch >/dev/null 2>&1 || true
  fi
  [ -z "$issue" ] || gh issue close "$issue" --repo "$REPO" >/dev/null 2>&1 || true
  [ "$created" = 0 ] || gh api -X DELETE "repos/$REPO/git/refs/heads/$BRANCH" >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

git_gh push -q "https://github.com/$REPO.git" "main:refs/heads/$BRANCH" || exit 1
created=1
issue=$(jq -n --arg t "Surface test: cloud agent $CLOUD_SESSION (${SHA:-manual})" --arg b "$(render_prompt "$CLOUD_SESSION" cloud)" \
  --arg repo "$REPO" --arg base "$BRANCH" \
  '{title: $t, body: $b, assignees: ["copilot-swe-agent[bot]"], agent_assignment: {target_repo: $repo, base_branch: $base}}' \
  | gh api "repos/$REPO/issues" --input - --jq .number) || exit 1
echo "issue=$issue branch=$BRANCH" | tee "$OUT/run.log"

# The agent's PR title starts with [WIP] until it finishes.
deadline=$(( $(date +%s) + WAIT_MINUTES * 60 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  read -r pr head title < <(gh pr list --repo "$REPO" --base "$BRANCH" --state all --json number,headRefName,title \
    --jq '.[0] | "\(.number) \(.headRefName) \(.title)"' 2>/dev/null || true)
  if [ -n "$pr" ] && [ "$pr" != null ] && [[ $title != "[WIP]"* ]]; then
    completed=1
    break
  fi
  sleep 30
done
echo "pr=$pr head=$head title=$title" | tee -a "$OUT/run.log"

if [ "$completed" = 1 ]; then
  git_gh fetch -q "https://github.com/$REPO.git" "$head" && git -C "$WS" checkout -q FETCH_HEAD
  run_id=$(gh run list --repo "$REPO" --branch "$head" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
  [ -n "$run_id" ] && gh run view "$run_id" --repo "$REPO" --log > "$OUT/agent-session.log" 2>/dev/null
else
  echo "No finished pull request within $WAIT_MINUTES minutes" | tee -a "$OUT/run.log"
fi

collect_and_score cloud-agent "$CLOUD_SESSION" "$WS" "$OUT" "$OUT/agent-session.log" \
  --meta "issue=$issue" --meta "pr=${pr:-none}" --meta "marketplace=$CLOUD_MARKETPLACE_REPO"

[ "$completed" = 1 ]
