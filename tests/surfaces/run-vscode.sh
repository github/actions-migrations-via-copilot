#!/usr/bin/env bash
# VS Code surface: headless Agent Host (`code agent host`), with the same two sessions as run-cli.sh.
# Plugins are sent to the Agent Host the way the VS Code editor sends them (patch_ahpx.py), so VS Code's
# own plugin loader runs them. The client adapter also selects discovered plugin agents for A1/A2.
# Needs: CODE_BIN (VS Code CLI), COPILOT_GITHUB_TOKEN (a Copilot user's token; the workflow token is
# rejected, see microsoft/vscode#346628), node, npm, python3, git, jq, perl.
# Writes $OUT_DIR/vscode/<session>/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
trap 'surface_signal 130' INT
trap 'surface_signal 143' TERM
: "${CODE_BIN:?set CODE_BIN to the VS Code CLI}"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"
MODEL=${MODEL:-claude-haiku-4.5}
PORT=${PORT:-18790}

OUT_ROOT=${OUT_DIR:-$(mktemp -d)}/vscode
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-vscode-XXXX")
mkdir -p "$OUT_ROOT"
if version=$("$CODE_BIN" --version 2>/dev/null); then
  version=$(head -1 <<< "$version")
else
  status=$?
  echo "VS Code CLI version check failed (exit=$status)" > "$OUT_ROOT/setup.log"
  exit "$status"
fi
# The CLI otherwise starts the newest server it can find, not its own version.
commit=$(sed -nE 's/.*\(commit ([0-9a-f]{40})\).*/\1/p' <<< "$version")
[ -n "$commit" ] && export VSCODE_CLI_INITIAL_AH_VERSION=$commit

if ! ahpx_bin=$(prepare_ahpx "$ROOT"); then
  echo "Could not prepare the AHPX test client" | tee "$OUT_ROOT/setup.log" >&2
  [ -f "$ROOT/ahpx/npm-install.log" ] && cp "$ROOT/ahpx/npm-install.log" "$OUT_ROOT/setup.log"
  exit 1
fi
AHPX=(node "$ahpx_bin")

stop_host() {
  local failed=0
  if [ -n "$HOST_PID" ]; then
    if kill -TERM "$HOST_PID" 2>/dev/null; then
      wait "$HOST_PID" 2>/dev/null || true
    else
      wait "$HOST_PID" 2>/dev/null || failed=1
    fi
    HOST_PID=""
  fi
  return "$failed"
}
trap 'stop_host' EXIT
overall=0

run_session() {
  local session=$1 out="$OUT_ROOT/$1" ws="$ROOT/$1/ws" host_pid ready=0 port=$PORT plugins server agents=not-tested
  local setup_exit=0 session_exit=0 agent_legacy_exit=0 agent_ns_exit=0 host_cleanup_exit=0 score_exit=0 connect_exit=0
  [ "$session" = plugin ] && port=$((PORT + 1))
  mkdir -p "$out" "$ROOT/$session/ud" "$ROOT/$session/sd" || return 1
  for evidence_file in events.jsonl session.log hc-probe-agent.log hc-probe-ns-agent.log; do
    : > "$out/$evidence_file" || return 1
  done
  HOST_PID=""
  # An empty Copilot profile, so no Copilot CLI-installed plugins load.
  export COPILOT_HOME="$ROOT/$session/home"
  export HC_FALLBACK_LOG="$ROOT/$session/fallback-probe.jsonl"
  plugins=""
  make_workspace "$ws" "$session" || setup_exit=$?
  if [ "$setup_exit" = 0 ] && [ "$session" = repo ]; then
    make_observed_marketplace "$ROOT/$session/observed-plugin" || setup_exit=$?
    plugins="$ROOT/$session/observed-plugin/plugins/actions-migrator"
  elif [ "$setup_exit" = 0 ]; then
    make_probe_marketplace "$ROOT/$session/probes" || setup_exit=$?
    plugins="$ROOT/$session/probes/plugins/hc-probe-a:$ROOT/$session/probes/plugins/hc-probe-b:$ROOT/$session/probes/plugins/hc-probe-ns"
  fi
  echo "Plugins sent the way the VS Code editor sends them: $plugins" > "$out/plugin-install.log"

  if [ "$setup_exit" = 0 ]; then
    openssl rand -hex 16 > "$ROOT/$session/conn-token" || setup_exit=$?
    chmod 600 "$ROOT/$session/conn-token" || setup_exit=$?
  fi
  if [ "$setup_exit" = 0 ]; then
    ( cd "$ws" && exec "$CODE_BIN" agent host --new-instance --foreground --host 127.0.0.1 --port "$port" \
        --connection-token-file "$ROOT/$session/conn-token" --user-data-dir "$ROOT/$session/ud" \
        --server-data-dir "$ROOT/$session/sd" < /dev/null > "$out/agent-host.log" 2>&1 ) &
    host_pid=$!
    HOST_PID=$host_pid
    local url
    url="ws://127.0.0.1:$port?tkn=$(cat "$ROOT/$session/conn-token")"

    for _ in $(seq 1 "${HOST_READY_ATTEMPTS:-60}"); do
      connect_exit=0
      run_captured timeout "${AHPX_CONNECT_TIMEOUT:-30}" env GITHUB_TOKEN="$COPILOT_GITHUB_TOKEN" \
        "${AHPX[@]}" --format json connect "$url" \
        > "$out/connect.json" 2>/dev/null || connect_exit=$?
      if [ "$connect_exit" = 0 ] \
         && jq -e '.agents[]? | select(.provider == "copilotcli") | .models | length > 0' "$out/connect.json" >/dev/null; then
        ready=1; break
      fi
      [ "$INTERRUPTED" = 0 ] || break
      sleep "${HOST_RETRY_DELAY:-3}"
    done
  else
    echo "Agent Host setup failed (exit=$setup_exit)" > "$out/session.log"
  fi
  if [ "$ready" = 0 ] && [ "$setup_exit" = 0 ]; then
    echo "Agent Host not ready or not signed in to Copilot" | tee "$out/session.log"
    setup_exit=${connect_exit:-1}
    [ "$setup_exit" = 0 ] && setup_exit=1
  fi
  if [ "$ready" = 1 ]; then
    run_captured timeout "${AHPX_TIMEOUT:-1200}" env HC_EVIDENCE_DIR="$ROOT/$session/evidence" HC_PLUGIN_DIRS="$plugins" \
      HC_FIXTURE_WORKSPACE="$ws" \
      GITHUB_TOKEN="$COPILOT_GITHUB_TOKEN" "${AHPX[@]}" exec -s "$url" -p copilotcli -m "$MODEL" \
      --cwd "$ws" --deny-all --idle-timeout "${SESSION_IDLE_TIMEOUT:-300}" \
      "$(render_prompt "$session" local)" > "$out/session.log" 2>&1 || session_exit=$?
    echo "exit=$session_exit" >> "$out/session.log"
    if [ "$session" = plugin ] && [ "$INTERRUPTED" = 0 ]; then
      agents=tested
      local agent agent_ws agent_evidence agent_file agent_status
      for agent in hc-probe-agent hc-probe-ns-agent; do
        agent_ws="$ROOT/$session/$agent/ws"
        agent_evidence="$ROOT/$session/$agent/evidence"
        make_workspace "$agent_ws" plugin || agent_status=$?
        if [ -z "${agent_status:-}" ]; then
          run_captured timeout "${AGENT_TIMEOUT:-300}" env HC_AGENT_NAME="$agent" HC_EVIDENCE_DIR="$agent_evidence" HC_PLUGIN_DIRS="$plugins" \
            HC_FIXTURE_WORKSPACE="$agent_ws" \
            GITHUB_TOKEN="$COPILOT_GITHUB_TOKEN" "${AHPX[@]}" exec -s "$url" -p copilotcli -m "$MODEL" \
            --cwd "$agent_ws" --deny-all --idle-timeout "${AGENT_IDLE_TIMEOUT:-180}" \
            'Do your task.' > "$out/$agent.log" 2>&1 || agent_status=$?
        fi
        agent_status=${agent_status:-0}
        echo "exit=$agent_status" >> "$out/$agent.log"
        if [ "$agent" = hc-probe-agent ]; then
          agent_legacy_exit=$agent_status
        else
          agent_ns_exit=$agent_status
        fi
        unset agent_status
        agent_file="agent-legacy.txt"
        [ "$agent" = hc-probe-ns-agent ] && agent_file="agent-ns.txt"
        cp "$agent_evidence/hc-out/$agent_file" "$ROOT/$session/evidence/hc-out/" 2>/dev/null || true
        [ "$INTERRUPTED" = 0 ] || break
      done
    fi
  fi
  stop_host || host_cleanup_exit=$?
  perl -pi -e 's/tkn=\S+/tkn=REDACTED/g' "$out/agent-host.log"
  server=$(sed -nE 's/.*\[([0-9a-f]{7})\]: Server ready.*/\1/p' "$out/agent-host.log" | head -1)
  grep -h 'AgentPluginManager' "$ROOT/$session/sd"/data/logs/*/*.log >> "$out/plugin-install.log" 2>/dev/null || true

  # Agent Host sessions run in a git worktree next to the workspace.
  local workspace_source
  workspace_source=$(find "$ws.worktrees" -mindepth 1 -maxdepth 1 -type d -print -quit 2>/dev/null)
  [ -d "$ROOT/$session/evidence" ] && workspace_source="$ROOT/$session/evidence"
  cat "$COPILOT_HOME"/session-state/*/events.jsonl > "$out/events.jsonl" 2>/dev/null || true
  collect_and_score vscode "$session" "${workspace_source:-$ws}" "$out" "$out/session.log" "$out/events.jsonl" \
    --meta "vscode=$version" --meta "server=${server:-unknown}" --meta "model=$MODEL" --meta "signed_in=$ready" \
    --meta "agents=$agents" --meta "setup_exit=$setup_exit" --meta "ahpx_exit=$session_exit" \
    --meta "agent_legacy_exit=$agent_legacy_exit" --meta "agent_ns_exit=$agent_ns_exit" \
    --meta "host_cleanup_exit=$host_cleanup_exit" --meta "interrupt_exit=$INTERRUPTED" || score_exit=$?
  if [ "$setup_exit" != 0 ] || [ "$session_exit" != 0 ] || [ "$agent_legacy_exit" != 0 ] \
      || [ "$agent_ns_exit" != 0 ] || [ "$host_cleanup_exit" != 0 ] || [ "$score_exit" != 0 ] \
      || [ "$INTERRUPTED" != 0 ]; then
    return 1
  fi
}

# SESSIONS=plugin (or repo) runs just one session, e.g. while debugging.
for session in ${SESSIONS:-repo plugin}; do
  run_session "$session" || overall=1
  [ "$INTERRUPTED" = 0 ] || break
done
exit "$overall"
