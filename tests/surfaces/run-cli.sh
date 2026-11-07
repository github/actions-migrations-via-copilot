#!/usr/bin/env bash
# Copilot CLI surface, two sessions:
#   repo:   the conformance hooks as repository hooks, plus actions-migrator from this checkout.
#   plugin: the same hooks inside probe plugins, plus format, skill, rule and agent probes.
# Needs: COPILOT_GITHUB_TOKEN (a Copilot user's token, or the workflow token with copilot-requests: write),
# node, python3, git. Writes $OUT_DIR/cli/<session>/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"

OUT_ROOT=${OUT_DIR:-$(mktemp -d)}/cli
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-cli-XXXX")
export COPILOT_AUTO_UPDATE=false
install_copilot_cli "$ROOT" || exit 1
version=$("$COPILOT" --version 2>/dev/null | head -1)
model_args=()
[ -n "${MODEL:-}" ] && model_args=(--model "$MODEL")

run_session() {
  local session=$1 out="$OUT_ROOT/$1" ws="$ROOT/$1/ws" agents=not-tested
  mkdir -p "$out"
  export COPILOT_HOME="$ROOT/$session/home"
  export HC_FALLBACK_LOG="$ROOT/$session/fallback-probe.jsonl"
  make_workspace "$ws" "$session"
  install_session_plugins "$session" "$out/plugin-install.log"

  # --add-dir /tmp lets the rm step reach the hooks instead of failing the CLI's own path check.
  ( cd "$ws" && timeout 1200 "$COPILOT" --trust-folder --allow-all-tools --add-dir /tmp \
      ${model_args[@]+"${model_args[@]}"} --output-format json --share "$out/transcript.md" \
      -p "$(render_prompt "$session" local)" > "$out/events.jsonl" 2> "$out/stderr.log" )
  echo "exit=$?" >> "$out/stderr.log"

  if [ "$session" = plugin ]; then
    agents=tested
    for agent in hc-probe-a:hc-probe-agent hc-probe-ns:hc-probe-ns-agent; do
      ( cd "$ws" && timeout 300 "$COPILOT" --agent "$agent" --trust-folder --allow-all-tools \
          ${model_args[@]+"${model_args[@]}"} -p "Do your task." ) >> "$out/agents.log" 2>&1
      echo "agent=$agent exit=$?" >> "$out/agents.log"
    done
  fi

  collect_and_score cli "$session" "$ws" "$out" "$out/events.jsonl" "$out/transcript.md" "$out/agents.log" \
    --meta "copilot_cli=$version" --meta "model=${MODEL:-default}" --meta "agents=$agents"
}

# SESSIONS=plugin (or repo) runs just one session, e.g. while debugging.
for session in ${SESSIONS:-repo plugin}; do run_session "$session"; done
