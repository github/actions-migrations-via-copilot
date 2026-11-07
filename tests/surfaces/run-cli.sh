#!/usr/bin/env bash
# Copilot CLI surface, two sessions:
#   repo:   the conformance hooks as repository hooks, plus actions-migrator from this checkout.
#   plugin: the same hooks inside probe plugins, plus format, skill, rule and agent probes.
# Needs: COPILOT_GITHUB_TOKEN (a Copilot user's token, or the workflow token with copilot-requests: write),
# node, python3, git. Writes $OUT_DIR/cli/<session>/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
trap 'surface_signal 130' INT
trap 'surface_signal 143' TERM
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"

OUT_ROOT=${OUT_DIR:-$(mktemp -d)}/cli
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-cli-XXXX")
export COPILOT_AUTO_UPDATE=false
mkdir -p "$OUT_ROOT"
if ! install_copilot_cli "$ROOT"; then
  echo "Copilot CLI setup failed" > "$OUT_ROOT/setup.log"
  [ -f "$ROOT/npm-install.log" ] && cat "$ROOT/npm-install.log" >> "$OUT_ROOT/setup.log"
  exit 1
fi
if version=$("$COPILOT" --version 2>/dev/null); then
  version=$(head -1 <<< "$version")
else
  status=$?
  echo "Copilot CLI version check failed (exit=$status)" > "$OUT_ROOT/setup.log"
  exit "$status"
fi
model_args=()
[ -n "${MODEL:-}" ] && model_args=(--model "$MODEL")
overall=0

run_session() {
  local session=$1 out="$OUT_ROOT/$1" ws="$ROOT/$1/ws" agents=not-tested
  local workspace_exit=0 install_exit=0 main_exit=0 agent_a_exit=0 agent_ns_exit=0 score_exit=0
  mkdir -p "$out"
  export COPILOT_HOME="$ROOT/$session/home"
  export HC_FALLBACK_LOG="$ROOT/$session/fallback-probe.jsonl"
  make_workspace "$ws" "$session" || workspace_exit=$?
  if [ "$workspace_exit" = 0 ]; then
    install_session_plugins "$session" "$out/plugin-install.log" || install_exit=$?
  else
    install_exit=$workspace_exit
  fi

  # --add-dir /tmp lets the rm step reach the hooks instead of failing the CLI's own path check.
  if [ "$install_exit" = 0 ]; then
    run_captured --cwd "$ws" timeout "${CLI_TIMEOUT:-1200}" "$COPILOT" \
        --trust-folder --allow-all-tools --add-dir /tmp \
        ${model_args[@]+"${model_args[@]}"} --output-format json --share "$out/transcript.md" \
        -p "$(render_prompt "$session" local)" > "$out/events.jsonl" 2> "$out/stderr.log" || main_exit=$?
  else
    main_exit=$install_exit
    echo "Plugin setup failed (exit=$install_exit)" > "$out/stderr.log"
  fi
  echo "exit=$main_exit" >> "$out/stderr.log"

  if [ "$session" = plugin ] && [ "$INTERRUPTED" = 0 ] && [ "$install_exit" = 0 ]; then
    agents=tested
    run_captured --cwd "$ws" timeout "${AGENT_TIMEOUT:-300}" "$COPILOT" \
        --agent hc-probe-a:hc-probe-agent --trust-folder --allow-all-tools \
        ${model_args[@]+"${model_args[@]}"} -p "Do your task." >> "$out/agents.log" 2>&1 || agent_a_exit=$?
    echo "agent=hc-probe-a:hc-probe-agent exit=$agent_a_exit" >> "$out/agents.log"
    if [ "$INTERRUPTED" = 0 ]; then
      run_captured --cwd "$ws" timeout "${AGENT_TIMEOUT:-300}" "$COPILOT" \
          --agent hc-probe-ns:hc-probe-ns-agent --trust-folder --allow-all-tools \
          ${model_args[@]+"${model_args[@]}"} -p "Do your task." >> "$out/agents.log" 2>&1 || agent_ns_exit=$?
      echo "agent=hc-probe-ns:hc-probe-ns-agent exit=$agent_ns_exit" >> "$out/agents.log"
    fi
  fi

  collect_and_score cli "$session" "$ws" "$out" "$out/events.jsonl" "$out/transcript.md" "$out/agents.log" \
    --meta "copilot_cli=$version" --meta "model=${MODEL:-default}" --meta "agents=$agents" \
    --meta "setup_exit=$install_exit" --meta "cli_exit=$main_exit" \
    --meta "agent_hc-probe-a_exit=$agent_a_exit" --meta "agent_hc-probe-ns_exit=$agent_ns_exit" \
    --meta "workspace_exit=$workspace_exit" --meta "interrupt_exit=$INTERRUPTED" || score_exit=$?
  if [ "$install_exit" != 0 ] || [ "$main_exit" != 0 ] || [ "$agent_a_exit" != 0 ] \
      || [ "$agent_ns_exit" != 0 ] || [ "$score_exit" != 0 ] || [ "$INTERRUPTED" != 0 ]; then
    return 1
  fi
}

# SESSIONS=plugin (or repo) runs just one session, e.g. while debugging.
for session in ${SESSIONS:-repo plugin}; do
  run_session "$session" || overall=1
  [ "$INTERRUPTED" = 0 ] || break
done
exit "$overall"
