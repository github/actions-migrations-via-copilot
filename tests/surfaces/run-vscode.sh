#!/usr/bin/env bash
# VS Code surface: headless Agent Host (`code agent host`) driven by AHPX, with the same two sessions as
# run-cli.sh (repo and plugin). The test client can't pick a custom agent, so A1/A2 are NOT RUN here.
# Needs: CODE_BIN (VS Code CLI), COPILOT_GITHUB_TOKEN (a Copilot user's token; the workflow token is
# rejected, see microsoft/vscode#346628), node, python3, git, jq, perl. Writes $OUT_DIR/vscode/<session>/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${CODE_BIN:?set CODE_BIN to the VS Code CLI}"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"
MODEL=${MODEL:-auto}
AHPX=(npx -y @tylerl0706/ahpx@0.6.0)
PORT=${PORT:-18790}

OUT_ROOT=${OUT_DIR:-$(mktemp -d)}/vscode
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-vscode-XXXX")
export COPILOT_AUTO_UPDATE=false
version=$("$CODE_BIN" --version 2>/dev/null | head -1)
install_copilot_cli "$ROOT" || exit 1
trap '"$CODE_BIN" agent kill >/dev/null 2>&1' EXIT

run_session() {
  local session=$1 out="$OUT_ROOT/$1" ws="$ROOT/$1/ws" host_pid ready=0
  mkdir -p "$out" "$ROOT/$session/ud" "$ROOT/$session/sd"
  export COPILOT_HOME="$ROOT/$session/home"
  make_workspace "$ws" "$session"
  # The Agent Host reads plugins from the Copilot profile the CLI installs into.
  install_session_plugins "$session" "$out/plugin-install.log"

  openssl rand -hex 16 > "$ROOT/$session/conn-token"
  chmod 600 "$ROOT/$session/conn-token"
  ( cd "$ws" && "$CODE_BIN" agent host --new-instance --foreground --host 127.0.0.1 --port "$PORT" \
      --connection-token-file "$ROOT/$session/conn-token" --user-data-dir "$ROOT/$session/ud" \
      --server-data-dir "$ROOT/$session/sd" < /dev/null > "$out/agent-host.log" 2>&1 ) &
  host_pid=$!
  local url
  url="ws://127.0.0.1:$PORT?tkn=$(cat "$ROOT/$session/conn-token")"

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
    GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" exec -s "$url" -p copilotcli -m "$MODEL" --cwd "$ws" \
      --approve-all --idle-timeout 300 "$(render_prompt "$session" local)" > "$out/session.log" 2>&1
    echo "exit=$?" >> "$out/session.log"
  fi
  kill "$host_pid" 2>/dev/null
  "$CODE_BIN" agent kill >/dev/null 2>&1
  perl -pi -e 's/tkn=\S+/tkn=REDACTED/g' "$out/agent-host.log"

  # Agent Host sessions run in a git worktree next to the workspace.
  local w
  w=$(ls -td "$ws".worktrees/*/ 2>/dev/null | head -1)
  cat "$COPILOT_HOME"/session-state/*/events.jsonl > "$out/events.jsonl" 2>/dev/null || true
  collect_and_score vscode "$session" "${w:-$ws}" "$out" "$out/session.log" "$out/events.jsonl" \
    --meta "vscode=$version" --meta "model=$MODEL" --meta "signed_in=$ready" \
    --meta "agents=the test client can't select a custom agent"
}

run_session repo
run_session plugin
