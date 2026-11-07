#!/usr/bin/env bash
# VS Code surface: headless Agent Host (`code agent host`), with the same two sessions as run-cli.sh.
# Plugins are sent to the Agent Host the way the VS Code editor sends them (patch_ahpx.py), so VS Code's
# own plugin loader runs them. The client adapter also selects discovered plugin agents for A1/A2.
# Needs: CODE_BIN (VS Code CLI), COPILOT_GITHUB_TOKEN (a Copilot user's token; the workflow token is
# rejected, see microsoft/vscode#346628), node, npm, python3, git, jq, perl.
# Optional: AHPX_NODE_MODULES, a node_modules folder that already has @tylerl0706/ahpx@0.6.0.
# Writes $OUT_DIR/vscode/<session>/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${CODE_BIN:?set CODE_BIN to the VS Code CLI}"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"
MODEL=${MODEL:-claude-haiku-4.5}
PORT=${PORT:-18790}

OUT_ROOT=${OUT_DIR:-$(mktemp -d)}/vscode
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-vscode-XXXX")
version=$("$CODE_BIN" --version 2>/dev/null | head -1)
# The CLI otherwise starts the newest server it can find, not its own version.
commit=$(sed -nE 's/.*\(commit ([0-9a-f]{40})\).*/\1/p' <<< "$version")
[ -n "$commit" ] && export VSCODE_CLI_INITIAL_AH_VERSION=$commit
trap '"$CODE_BIN" agent kill >/dev/null 2>&1' EXIT

prepare_ahpx() {
  local nm="$ROOT/ahpx/node_modules"
  mkdir -p "$ROOT/ahpx"
  if [ -n "${AHPX_NODE_MODULES:-}" ]; then
    cp -R "$AHPX_NODE_MODULES" "$nm"
  else
    for _ in 1 2 3; do
      npm install -s --prefix "$ROOT/ahpx" @tylerl0706/ahpx@0.6.0 > "$ROOT/ahpx/npm-install.log" 2>&1 && break
      sleep 10
    done
  fi
  python3 "$SUITE_DIR/patch_ahpx.py" "$nm/@tylerl0706/ahpx/dist/bin.js" || return 1
  AHPX=(node "$nm/@tylerl0706/ahpx/dist/bin.js")
}
prepare_ahpx || { echo "Could not prepare the AHPX test client" >&2; exit 1; }

run_session() {
  local session=$1 out="$OUT_ROOT/$1" ws="$ROOT/$1/ws" host_pid ready=0 port=$PORT plugins server agents=not-tested
  [ "$session" = plugin ] && port=$((PORT + 1))
  mkdir -p "$out" "$ROOT/$session/ud" "$ROOT/$session/sd"
  # An empty Copilot profile, so no Copilot CLI-installed plugins load.
  export COPILOT_HOME="$ROOT/$session/home"
  export HC_FALLBACK_LOG="$ROOT/$session/fallback-probe.jsonl"
  make_workspace "$ws" "$session"
  if [ "$session" = repo ]; then
    plugins="$TOOL_ROOT/plugin"
  else
    make_probe_marketplace "$ROOT/$session/probes"
    plugins="$ROOT/$session/probes/plugins/hc-probe-a:$ROOT/$session/probes/plugins/hc-probe-b:$ROOT/$session/probes/plugins/hc-probe-ns"
  fi
  echo "Plugins sent the way the VS Code editor sends them: $plugins" > "$out/plugin-install.log"

  openssl rand -hex 16 > "$ROOT/$session/conn-token"
  chmod 600 "$ROOT/$session/conn-token"
  ( cd "$ws" && exec "$CODE_BIN" agent host --new-instance --foreground --host 127.0.0.1 --port "$port" \
      --connection-token-file "$ROOT/$session/conn-token" --user-data-dir "$ROOT/$session/ud" \
      --server-data-dir "$ROOT/$session/sd" < /dev/null > "$out/agent-host.log" 2>&1 ) &
  host_pid=$!
  local url
  url="ws://127.0.0.1:$port?tkn=$(cat "$ROOT/$session/conn-token")"

  for _ in $(seq 1 60); do
    if GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" --format json connect "$url" > "$out/connect.json" 2>/dev/null \
       && jq -e '.agents[]? | select(.provider == "copilotcli") | .models | length > 0' "$out/connect.json" >/dev/null; then
      ready=1; break
    fi
    sleep 3
  done
  if [ $ready = 0 ]; then
    echo "Agent Host not ready or not signed in to Copilot" | tee "$out/session.log"
  else
    HC_EVIDENCE_DIR="$ROOT/$session/evidence" HC_PLUGIN_DIRS=$plugins GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" exec -s "$url" -p copilotcli -m "$MODEL" \
      --cwd "$ws" --approve-all --idle-timeout 300 "$(render_prompt "$session" local)" > "$out/session.log" 2>&1
    echo "exit=$?" >> "$out/session.log"
    if [ "$session" = plugin ]; then
      agents=tested
      local agent agent_ws agent_evidence agent_file
      for agent in hc-probe-agent hc-probe-ns-agent; do
        agent_ws="$ROOT/$session/$agent/ws"
        agent_evidence="$ROOT/$session/$agent/evidence"
        make_workspace "$agent_ws" plugin
        HC_AGENT_NAME="$agent" HC_EVIDENCE_DIR="$agent_evidence" HC_PLUGIN_DIRS=$plugins \
          GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" exec -s "$url" -p copilotcli -m "$MODEL" \
          --cwd "$agent_ws" --approve-all --idle-timeout 180 'Do your task.' > "$out/$agent.log" 2>&1
        echo "exit=$?" >> "$out/$agent.log"
        agent_file="agent-legacy.txt"
        [ "$agent" = hc-probe-ns-agent ] && agent_file="agent-ns.txt"
        cp "$agent_evidence/hc-out/$agent_file" "$ROOT/$session/evidence/hc-out/" 2>/dev/null || true
      done
    fi
  fi
  kill "$host_pid" 2>/dev/null
  wait "$host_pid" 2>/dev/null
  "$CODE_BIN" agent kill >/dev/null 2>&1
  perl -pi -e 's/tkn=\S+/tkn=REDACTED/g' "$out/agent-host.log"
  server=$(sed -nE 's/.*\[([0-9a-f]{7})\]: Server ready.*/\1/p' "$out/agent-host.log" | head -1)
  grep -h 'AgentPluginManager' "$ROOT/$session/sd"/data/logs/*/*.log >> "$out/plugin-install.log" 2>/dev/null || true

  # Agent Host sessions run in a git worktree next to the workspace.
  local w
  w=$(ls -td "$ws".worktrees/*/ 2>/dev/null | head -1)
  [ -d "$ROOT/$session/evidence" ] && w="$ROOT/$session/evidence"
  cat "$COPILOT_HOME"/session-state/*/events.jsonl > "$out/events.jsonl" 2>/dev/null || true
  collect_and_score vscode "$session" "${w:-$ws}" "$out" "$out/session.log" "$out/events.jsonl" \
    --meta "vscode=$version" --meta "server=${server:-unknown}" --meta "model=$MODEL" --meta "signed_in=$ready" \
    --meta "agents=$agents"
}

# SESSIONS=plugin (or repo) runs just one session, e.g. while debugging.
for session in ${SESSIONS:-repo plugin}; do run_session "$session"; done
