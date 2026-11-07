# shellcheck shell=bash
# Shared helpers for the surface runners. Source this file; don't run it.

SUITE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC2034  # used by the runners that source this file
TOOL_ROOT=$(git -C "$SUITE_DIR" rev-parse --show-toplevel)
COPILOT_CLI_VERSION=${COPILOT_CLI_VERSION:-latest}

# Scratch git repo for one session. $2 = "repo": the conformance hooks as repository hooks.
# $2 = "plugin": no repository hooks; the hooks come from the probe plugins (make_probes.py).
make_workspace() {
  local ws=$1 session=$2
  mkdir -p "$ws/hc-out"
  if [ "$session" = repo ]; then
    mkdir -p "$ws/.github/hooks"
    cp "$SUITE_DIR"/kit/* "$ws/.github/hooks/"
  fi
  touch "$ws/hc-out/.gitkeep"
  printf 'Scratch repository for actions-migrator surface tests.\n' > "$ws/README.md"
  git_commit_all "$ws" "Surface test workspace"
}

git_commit_all() {
  git -C "$1" init -q -b main 2>/dev/null || true
  git -C "$1" add -A
  git -C "$1" -c user.name=surface-tests -c user.email=surface-tests@users.noreply.github.com commit -qm "$2"
}

# Local marketplace "hc-probes" with the probe plugins, in $1.
make_probe_marketplace() {
  python3 "$SUITE_DIR/make_probes.py" "$1"
  git_commit_all "$1" "Probe plugins"
}

# Installs a session's plugins into the Copilot profile at $COPILOT_HOME, logging to $2.
# repo: actions-migrator from this checkout. plugin: the three probe plugins.
install_session_plugins() {
  local session=$1 log=$2
  {
    if [ "$session" = repo ]; then
      "$COPILOT" plugin marketplace add "$TOOL_ROOT"
      "$COPILOT" plugin install actions-migrator@actions-migrations-via-copilot
    else
      make_probe_marketplace "$COPILOT_HOME/../probes"
      "$COPILOT" plugin marketplace add "$COPILOT_HOME/../probes"
      for p in hc-probe-a hc-probe-b hc-probe-ns; do "$COPILOT" plugin install "$p@hc-probes"; done
    fi
    "$COPILOT" plugin list
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
