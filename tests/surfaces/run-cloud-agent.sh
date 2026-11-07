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
CLOUD_AGENT=${CLOUD_AGENT:-}
case "$CLOUD_SESSION" in repo|plugin) ;; *) echo 'CLOUD_SESSION must be repo or plugin' >&2; exit 1 ;; esac

export OUT_DIR=${OUT_DIR:-$(mktemp -d)}
OUT=$OUT_DIR/cloud-agent/$CLOUD_SESSION
case "$CLOUD_AGENT" in
  '') ;;
  hc-probe-agent) OUT="$OUT/agents/control" ;;
  hc-probe-a:hc-probe-agent) OUT="$OUT/agents/A1" ;;
  hc-probe-ns:hc-probe-ns-agent) OUT="$OUT/agents/A2" ;;
  *) echo 'Unknown cloud probe agent' >&2; exit 1 ;;
esac
mkdir -p "$OUT"
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-cloud-XXXX")
WS=$ROOT/ws
default_branch=$(gh api "repos/$REPO" --jq .default_branch) || exit 1
gh api "repos/$REPO/contents/.github/copilot/settings.json?ref=$default_branch" --jq .content \
  | base64 -d > "$ROOT/default-settings.json" || exit 1
python3 "$SUITE_DIR/cloud_settings.py" --check "$ROOT/default-settings.json" "$CLOUD_SESSION" "$CLOUD_MARKETPLACE_REPO" || exit 1
gh api "repos/$CLOUD_MARKETPLACE_REPO/contents/fixture-source.json" --jq .content \
  | base64 -d > "$OUT/fixture-source.json" || exit 1
source_sha=$(jq -er .source_sha "$OUT/fixture-source.json") || exit 1
if [ -n "${SHA:-}" ] && [ "$SHA" != "$source_sha" ]; then
  echo 'Requested source SHA does not match the published cloud fixture' >&2
  exit 1
fi
SHA=$source_sha
make_workspace "$WS" "$CLOUD_SESSION"
python3 "$SUITE_DIR/cloud_settings.py" "$WS" "$CLOUD_SESSION" "$CLOUD_MARKETPLACE_REPO"
if [ "$CLOUD_AGENT" = hc-probe-agent ]; then
  mkdir -p "$WS/.github/agents"
  gh api "repos/$CLOUD_MARKETPLACE_REPO/contents/plugins/hc-probe-a/agents/hc-probe-agent.agent.md" --jq .content \
    | base64 -d > "$WS/.github/agents/hc-probe-agent.agent.md" || exit 1
fi
git_commit_all "$WS" "Configure isolated cloud test plugins"
BRANCH="surface-run/${GITHUB_RUN_ID:-$(date +%s)}-$CLOUD_SESSION${CLOUD_AGENT:+-${CLOUD_AGENT##*:}}"
git_gh() { git -C "$WS" -c credential.helper= -c 'credential.helper=!gh auth git-credential' "$@"; }
issue="" pr="" head="" title="" created=0 completed=0 run_id="" run_status="" run_conclusion="" rejected=0

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
prompt=$(render_prompt "$CLOUD_SESSION" cloud)
[ -z "$CLOUD_AGENT" ] || prompt='Do your assigned agent task. Commit the resulting evidence and open a pull request.'
issue=$(jq -n --arg t "Surface test: cloud agent $CLOUD_SESSION $CLOUD_AGENT (${SHA:-manual})" --arg b "$prompt" \
  --arg repo "$REPO" --arg base "$BRANCH" --arg agent "$CLOUD_AGENT" \
  '{title: $t, body: $b, assignees: ["copilot-swe-agent[bot]"], agent_assignment: ({target_repo: $repo, base_branch: $base} + if $agent == "" then {} else {custom_agent:$agent} end)}' \
  | gh api "repos/$REPO/issues" --input - --jq .number) || exit 1
echo "issue=$issue branch=$BRANCH" | tee "$OUT/run.log"

deadline=$(( $(date +%s) + WAIT_MINUTES * 60 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  read -r pr head title < <(gh pr list --repo "$REPO" --base "$BRANCH" --state all --json number,headRefName,title \
    --jq '.[0] | "\(.number) \(.headRefName) \(.title)"' 2>/dev/null || true)
  if [ -n "$pr" ] && [ "$pr" != null ]; then
    read -r run_id run_status run_conclusion < <(gh run list --repo "$REPO" --branch "$head" --limit 20 \
      --json databaseId,status,conclusion,workflowName \
      --jq '[.[] | select(.workflowName == "Copilot cloud agent")][0] | select(. != null) | "\(.databaseId) \(.status) \(.conclusion)"')
    if [ "$run_status" = completed ]; then
      [ "$run_conclusion" = success ] && completed=1
      break
    fi
  fi
  if [ -n "$CLOUD_AGENT" ]; then
    gh api "repos/$REPO/issues/$issue/comments" --jq '[.[] | select(.user.type == "Bot") | {login:.user.login,body}]' > "$OUT/agent-start.json"
    if jq -e 'any(.[]; .body | test("unable to start working on this issue"; "i"))' "$OUT/agent-start.json" >/dev/null; then
      rejected=1
      break
    fi
  fi
  sleep 30
done
echo "pr=$pr head=$head title=$title" | tee -a "$OUT/run.log"

if [ "$completed" = 1 ]; then
  git_gh fetch -q "https://github.com/$REPO.git" "$head" && git -C "$WS" checkout -q FETCH_HEAD
else
  if [ "$rejected" = 1 ]; then
    echo "Cloud agent rejected the selected agent before startup" | tee -a "$OUT/run.log"
  else
    echo "No successful cloud task within $WAIT_MINUTES minutes (conclusion=${run_conclusion:-unknown})" | tee -a "$OUT/run.log"
  fi
fi
[ -z "$run_id" ] || gh run view "$run_id" --repo "$REPO" --log > "$OUT/agent-session.log" 2>/dev/null

if [ -n "$CLOUD_AGENT" ]; then
  cp -R "$WS/hc-out" "$OUT/" 2>/dev/null || true
  jq -n --arg agent "$CLOUD_AGENT" --arg issue "$issue" --arg pr "$pr" --arg run "$run_id" \
    --argjson completed "$completed" --argjson rejected "$rejected" \
    '{agent:$agent,issue:$issue,pr:$pr,run:$run,completed:($completed==1),rejected:($rejected==1)}' > "$OUT/agent-selection.json"
else
  if [ "$CLOUD_SESSION" = plugin ] && [ "$completed" = 1 ]; then
    for selected_agent in hc-probe-agent hc-probe-a:hc-probe-agent hc-probe-ns:hc-probe-ns-agent; do
      CLOUD_AGENT="$selected_agent" bash "$SUITE_DIR/run-cloud-agent.sh" || true
    done
  fi
  collect_and_score cloud-agent "$CLOUD_SESSION" "$WS" "$OUT" "$OUT/agent-session.log" \
    --meta "issue=$issue" --meta "pr=${pr:-none}" --meta "marketplace=$CLOUD_MARKETPLACE_REPO" \
    --meta "run=${run_id:-none}" --meta "run_conclusion=${run_conclusion:-unknown}" --meta "source_sha=$source_sha"
fi

[ "$completed" = 1 ] || [ "$rejected" = 1 ]
