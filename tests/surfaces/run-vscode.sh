#!/usr/bin/env bash
# VS Code surface: headless Agent Host (`code agent host`) driven by AHPX, same kit and plugin as the CLI.
# Needs: CODE_BIN (VS Code CLI), COPILOT_GITHUB_TOKEN (a Copilot user's token; the workflow token is
# rejected, see microsoft/vscode#346628), node, python3, git, jq, perl. Writes $OUT_DIR/vscode/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${CODE_BIN:?set CODE_BIN to the VS Code CLI}"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"
MODEL=${MODEL:-auto}
AHPX=(npx -y @tylerl0706/ahpx@0.6.0)
PORT=${PORT:-18790}

OUT=${OUT_DIR:-$(mktemp -d)}/vscode
mkdir -p "$OUT"
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-vscode-XXXX")
mkdir -p "$ROOT/ud" "$ROOT/sd"
export COPILOT_HOME=$ROOT/home COPILOT_AUTO_UPDATE=false
WS=$ROOT/ws
make_workspace "$WS"
version=$("$CODE_BIN" --version 2>/dev/null | head -1)

# The Agent Host reads plugins from the Copilot profile the CLI installs into.
install_copilot_cli "$ROOT" || exit 1
{
  "$COPILOT" plugin marketplace add "$TOOL_ROOT"
  "$COPILOT" plugin install actions-migrator@actions-migrations-via-copilot
  "$COPILOT" plugin list
} > "$OUT/plugin-install.log" 2>&1

openssl rand -hex 16 > "$ROOT/conn-token"
chmod 600 "$ROOT/conn-token"
( cd "$WS" && "$CODE_BIN" agent host --new-instance --foreground --host 127.0.0.1 --port "$PORT" \
    --connection-token-file "$ROOT/conn-token" --user-data-dir "$ROOT/ud" --server-data-dir "$ROOT/sd" \
    < /dev/null > "$OUT/agent-host.log" 2>&1 ) &
HOST_PID=$!
trap 'kill $HOST_PID 2>/dev/null; "$CODE_BIN" agent kill >/dev/null 2>&1; perl -pi -e "s/tkn=\\S+/tkn=REDACTED/g" "$OUT/agent-host.log"' EXIT
URL="ws://127.0.0.1:$PORT?tkn=$(cat "$ROOT/conn-token")"

ready=0
for _ in $(seq 1 60); do
  if GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" --format json connect "$URL" > "$OUT/connect.json" 2>/dev/null \
     && jq -e '.agents[]? | select(.provider == "copilotcli") | .models | length > 0' "$OUT/connect.json" >/dev/null; then
    ready=1; break
  fi
  sleep 3
done
if [ $ready = 0 ]; then
  echo "Agent Host not ready or not signed in to Copilot" | tee "$OUT/session.log"
else
  GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" exec -s "$URL" -p copilotcli -m "$MODEL" --cwd "$WS" \
    --approve-all --idle-timeout 300 "$(render_prompt local)" > "$OUT/session.log" 2>&1
  echo "exit=$?" >> "$OUT/session.log"
fi

# Agent Host sessions run in a git worktree next to the workspace.
W=$(ls -td "$WS".worktrees/*/ 2>/dev/null | head -1)
cat "$COPILOT_HOME"/session-state/*/events.jsonl > "$OUT/events.jsonl" 2>/dev/null || true
collect_and_score vscode "${W:-$WS}" "$OUT" "$OUT/session.log" "$OUT/events.jsonl" \
  --meta "vscode=$version" --meta "model=$MODEL" --meta "signed_in=$ready"
