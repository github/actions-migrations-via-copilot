#!/usr/bin/env bash
# VS Code surface: the headless VS Code Agent Host (`code agent host`) with the real plugin offered the
# way the VS Code editor offers it, so VS Code's own plugin and hook loader runs it.
# Needs: CODE_BIN (VS Code CLI), COPILOT_GITHUB_TOKEN (a Copilot user's token; the workflow token is
# rejected, see microsoft/vscode#346628), node, npm, python3, git, jq, openssl.
# Writes $OUT_DIR/vscode/result.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
trap 'on_signal 130' INT
trap 'on_signal 143' TERM
: "${CODE_BIN:?set CODE_BIN to the VS Code CLI}"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"
PORT=${PORT:-18790}
MODEL=${MODEL:-claude-haiku-4.5}

OUT=${OUT_DIR:-$(mktemp -d)}/vscode
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/plugin-vscode-XXXX")
mkdir -p "$OUT"
stop_host() {
  [ -n "$HOST_PID" ] || return 0
  kill -TERM "$HOST_PID" 2>/dev/null || true
  wait "$HOST_PID" 2>/dev/null || true
  HOST_PID=""
}
trap 'stop_host' EXIT

setup_exit=0 main_exit=0 agent_exit=0 ready=0
version=$("$CODE_BIN" --version 2>/dev/null | head -1) || setup_exit=1
# The CLI otherwise starts the newest Agent Host it finds, not its own version.
commit=$(sed -nE 's/.*\(commit ([0-9a-f]{40})\).*/\1/p' <<< "$version")
[ -n "$commit" ] && export VSCODE_CLI_INITIAL_AH_VERSION=$commit
[ "$setup_exit" = 0 ] && { ahpx_bin=$(prepare_ahpx "$ROOT") || setup_exit=$?; }
export COPILOT_HOME="$ROOT/home"   # empty profile: no CLI-installed plugins
ws="$ROOT/ws" agent_ws="$ROOT/agent-ws"
[ "$setup_exit" = 0 ] && { make_workspace "$ws" && make_workspace "$agent_ws" || setup_exit=$?; }
if [ "$setup_exit" = 0 ]; then
  openssl rand -hex 16 > "$ROOT/conn-token" && chmod 600 "$ROOT/conn-token" || setup_exit=$?
fi

if [ "$setup_exit" = 0 ]; then
  ( cd "$ws" && exec "$CODE_BIN" agent host --new-instance --foreground --host 127.0.0.1 --port "$PORT" \
      --connection-token-file "$ROOT/conn-token" --user-data-dir "$ROOT/ud" --server-data-dir "$ROOT/sd" \
      < /dev/null > "$ROOT/agent-host.log" 2>&1 ) &
  HOST_PID=$!
  url="ws://127.0.0.1:$PORT?tkn=$(cat "$ROOT/conn-token")"
  for _ in $(seq 1 "${HOST_READY_ATTEMPTS:-60}"); do
    if run_captured timeout 30 env GITHUB_TOKEN="$COPILOT_GITHUB_TOKEN" node "$ahpx_bin" --format json connect "$url" \
         > "$ROOT/connect.json" 2>/dev/null \
       && jq -e '.agents[]? | select(.provider == "copilotcli") | .models | length > 0' "$ROOT/connect.json" >/dev/null; then
      ready=1; break
    fi
    [ "$INTERRUPTED" = 0 ] || break
    sleep 3
  done
  [ "$ready" = 1 ] || { echo "Agent Host not ready or not signed in to Copilot" >&2; setup_exit=1; }
fi

# One session per prompt. Tool calls are denied unless approve_tool.mjs allows them.
run_session() {
  local name=$1 cwd=$2 prompt=$3 agent=${4:-}
  mkdir -p "$ROOT/$name" || return 1
  run_captured timeout "${SESSION_TIMEOUT:-600}" env HC_EVIDENCE_DIR="$ROOT/$name" HC_PLUGIN_DIRS="$TOOL_ROOT/plugin" \
    HC_WORKSPACE="$cwd" HC_AGENT_NAME="$agent" GITHUB_TOKEN="$COPILOT_GITHUB_TOKEN" \
    node "$ahpx_bin" exec -s "$url" -p copilotcli -m "$MODEL" --cwd "$cwd" --deny-all \
    --idle-timeout "${IDLE_TIMEOUT:-300}" "$prompt" > "$OUT/$name.log" 2>&1
}
if [ "$ready" = 1 ]; then
  run_session main "$ws" "$MAIN_PROMPT" || main_exit=$?
  if [ "$INTERRUPTED" = 0 ]; then
    run_session agent "$agent_ws" "$AGENT_PROMPT" jenkins-migrator || agent_exit=$?
  fi
fi
stop_host

mkdir -p "$OUT/main" "$OUT/agent"
for name in main agent; do
  cp "$ROOT/$name/plugin-ready.json" "$ROOT/$name/agent-selected.json" "$OUT/$name/" 2>/dev/null || true
  cp -R "$ROOT/$name/hc-out" "$OUT/$name/" 2>/dev/null || true
  cp "$ROOT/$name/.github/MIGRATION-SCORECARD.md" "$OUT/$name/" 2>/dev/null || true
done
python3 "$SUITE_DIR/score.py" vscode "$OUT" --runtime "$version" --model "$MODEL" \
  --setup-exit "$setup_exit" --main-exit "$main_exit" --agent-exit "$agent_exit" --interrupted "$INTERRUPTED"
