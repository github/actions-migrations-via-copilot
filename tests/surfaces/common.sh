# shellcheck shell=bash
# Shared helpers for the surface runners. Source this file; don't run it.

SUITE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC2034  # used by the runners that source this file
TOOL_ROOT=$(git -C "$SUITE_DIR" rev-parse --show-toplevel)
COPILOT_CLI_VERSION=${COPILOT_CLI_VERSION:-latest}
CURRENT_PID=""
HOST_PID=""
INTERRUPTED=0

surface_signal() {
  INTERRUPTED=$1
  [ -z "$CURRENT_PID" ] || kill -TERM "$CURRENT_PID" 2>/dev/null || true
  [ -z "$HOST_PID" ] || kill -TERM "$HOST_PID" 2>/dev/null || true
}

run_captured() {
  local working_dir=""
  if [ "$1" = --cwd ]; then
    working_dir=$2
    shift 2
  fi
  if [ -n "$working_dir" ]; then
    ( cd "$working_dir" && exec "$@" ) &
  else
    "$@" &
  fi
  CURRENT_PID=$!
  wait "$CURRENT_PID"
  local status=$?
  CURRENT_PID=""
  [ "$INTERRUPTED" = 0 ] || status=$INTERRUPTED
  return "$status"
}

cleanup_cloud_resources() {
  local repo=$1 branch=$2 issue=$3 pr=$4 pr_head=$5
  local branch_created=$6 issue_created=$7 remote_started=$8 task_terminal=$9 log=${10}
  local failed=0 pr_cleanup_failed=0 details actual_head actual_base
  if [ "$remote_started" = 1 ] && [ "$task_terminal" != 1 ]; then
    echo "Cleanup deferred: remote task may still be active; issue, pull request, and branch retained." >> "$log"
    return 0
  fi
  if [ -n "$pr" ] && [ "$pr" != null ]; then
    details=$(gh pr view "$pr" --repo "$repo" --json headRefName,baseRefName \
      --jq '[.headRefName, .baseRefName] | @tsv') || details=""
    IFS=$'\t' read -r actual_head actual_base <<< "$details"
    if [ "$actual_head" != "$pr_head" ] || [ "$actual_base" != "$branch" ]; then
      echo "Cleanup refused pull request $pr: ownership could not be confirmed." >> "$log"
      failed=1
      pr_cleanup_failed=1
    elif gh pr close "$pr" --repo "$repo" >/dev/null 2>&1; then
      echo "Cleanup closed pull request $pr owned by base branch $branch." >> "$log"
    else
      echo "Cleanup failed to close owned pull request $pr." >> "$log"
      failed=1
      pr_cleanup_failed=1
    fi
  fi
  if [ "$issue_created" = 1 ] && [ -n "$issue" ] && [ "$issue" != null ]; then
    if gh issue close "$issue" --repo "$repo" >/dev/null 2>&1; then
      echo "Cleanup closed issue $issue after the remote task ended; closing an issue does not cancel a task." >> "$log"
    else
      echo "Cleanup failed to close owned issue $issue." >> "$log"
      failed=1
    fi
  fi
  if [ "$branch_created" = 1 ] && [ "$pr_cleanup_failed" = 0 ]; then
    if gh api -X DELETE "repos/$repo/git/refs/heads/$branch" >/dev/null 2>&1; then
      echo "Cleanup deleted test-run branch $branch." >> "$log"
    else
      echo "Cleanup failed to delete test-run branch $branch." >> "$log"
      failed=1
    fi
  elif [ "$branch_created" = 1 ]; then
    echo "Cleanup retained branch $branch because pull-request ownership or closure was uncertain." >> "$log"
  fi
  return "$failed"
}

# Scratch git repo for one session. $2 = "repo": the conformance hooks as repository hooks.
# $2 = "plugin": no repository hooks; the hooks come from the probe plugins (make_probes.py).
make_workspace() {
  local ws=$1 session=$2
  mkdir -p "$ws/hc-out" || return 1
  if [ "$session" = repo ]; then
    mkdir -p "$ws/.github/hooks" || return 1
    cp "$SUITE_DIR"/kit/* "$ws/.github/hooks/" || return 1
  fi
  touch "$ws/hc-out/.gitkeep" || return 1
  printf 'Scratch repository for actions-migrator surface tests.\n' > "$ws/README.md" || return 1
  git_commit_all "$ws" "Surface test workspace"
}

git_commit_all() {
  git -C "$1" init -q -b main 2>/dev/null || true
  git -C "$1" add -A
  git -C "$1" -c user.name=surface-tests -c user.email=surface-tests@users.noreply.github.com commit -qm "$2"
}

# Local marketplace "hc-probes" with the probe plugins, in $1.
make_probe_marketplace() {
  python3 "$SUITE_DIR/make_probes.py" "$1" || return 1
  git_commit_all "$1" "Probe plugins"
}

# Installs a session's plugins into the Copilot profile at $COPILOT_HOME, logging to $2.
# repo: actions-migrator from this checkout. plugin: the three probe plugins.
install_session_plugins() {
  local session=$1 log=$2
  {
    if [ "$session" = repo ]; then
      "$COPILOT" plugin marketplace add "$TOOL_ROOT" || return 1
      "$COPILOT" plugin install actions-migrator@actions-migrations-via-copilot || return 1
    else
      make_probe_marketplace "$COPILOT_HOME/../probes" || return 1
      "$COPILOT" plugin marketplace add "$COPILOT_HOME/../probes" || return 1
      for p in hc-probe-a hc-probe-b hc-probe-ns; do "$COPILOT" plugin install "$p@hc-probes" || return 1; done
    fi
    "$COPILOT" plugin list || return 1
  } > "$log" 2>&1
}

# Prints the prompt for session $1 (repo or plugin): $2 = "local" (CLI, VS Code) or "cloud" (cloud agent).
render_prompt() {
  local file=prompt.md
  [ "$1" = plugin ] && file=prompt-plugin.md
  python3 "$SUITE_DIR/render_prompt.py" "$SUITE_DIR/$file" "$2"
}

# Installs the Copilot CLI under $1 and sets COPILOT to its path. Set COPILOT_BIN to use an installed CLI instead.
install_copilot_cli() {
  if [ -n "${COPILOT_BIN:-}" ]; then
    COPILOT=$COPILOT_BIN
    return 0
  fi
  # shellcheck disable=SC2034  # used by the runners
  COPILOT="$1/cli/node_modules/.bin/copilot"
  for _ in 1 2 3; do
    npm install -s --prefix "$1/cli" "@github/copilot@$COPILOT_CLI_VERSION" > "$1/npm-install.log" 2>&1 && [ -x "$COPILOT" ] && return 0
    sleep 10
  done
  echo "Copilot CLI install failed:" >&2
  tail -5 "$1/npm-install.log" >&2
  return 1
}

# Copies the evidence from workspace $3 into $4 and scores it as surface $1, session $2.
# Extra args: transcript files, then "--meta key=value" pairs.
collect_and_score() {
  local surface=$1 session=$2 ws=$3 out=$4; shift 4
  mkdir -p "$out/hc-out"
  cp "${HC_FALLBACK_LOG:-/nonexistent}" "$out/probe.jsonl" 2>/dev/null \
    || cp "$ws/.hook-conformance/probe.jsonl" "$out/probe.jsonl" 2>/dev/null || true
  cp "$ws/hook-results.md" "$out/hook-results.md" 2>/dev/null || true
  cp "$ws/.hook-conformance/plugin-guards.jsonl" "$out/plugin-guards.jsonl" 2>/dev/null || true
  cp -R "$ws/hc-out/." "$out/hc-out/" 2>/dev/null || true
  local args=() transcripts=("$out/hook-results.md")
  while [ $# -gt 0 ]; do
    if [ "$1" = --meta ]; then args+=(--meta "$2"); shift 2; else transcripts+=("$1"); shift; fi
  done
  for t in "${transcripts[@]}"; do args+=(--transcript "$t"); done
  python3 "$SUITE_DIR/score.py" --surface "$surface" --session "$session" --log "$out/probe.jsonl" \
    --out-dir "$out/hc-out" --json "$out/score.json" ${args[@]+"${args[@]}"}
}
