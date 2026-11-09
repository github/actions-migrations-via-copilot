#!/usr/bin/env bash
# Copilot CLI surface: installs the real plugin from this checkout into an empty Copilot profile.
# Needs: COPILOT_GITHUB_TOKEN (a Copilot user's token, or the workflow token with copilot-requests: write),
# npm, python3, git. Set COPILOT_BIN to use an installed CLI. Writes $OUT_DIR/cli/result.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
trap 'on_signal 130' INT
trap 'on_signal 143' TERM
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"

OUT=${OUT_DIR:-$(mktemp -d)}/cli
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/plugin-cli-XXXX")
export COPILOT_AUTO_UPDATE=false COPILOT_HOME="$ROOT/home"
mkdir -p "$OUT/main" "$OUT/agent"

setup_exit=0 main_exit=0 agent_exit=0 version=""
model_args=()
[ -n "${MODEL:-}" ] && model_args=(--model "$MODEL")
COPILOT=${COPILOT_BIN:-$ROOT/cli/node_modules/.bin/copilot}
if [ -z "${COPILOT_BIN:-}" ]; then
  npm install -s --prefix "$ROOT/cli" "@github/copilot@${COPILOT_CLI_VERSION:-latest}" > "$ROOT/npm-install.log" 2>&1 \
    || setup_exit=$?
fi
[ "$setup_exit" = 0 ] && { version=$("$COPILOT" --version 2>/dev/null | head -1) || setup_exit=1; }
ws="$ROOT/ws" agent_ws="$ROOT/agent-ws"
[ "$setup_exit" = 0 ] && { make_workspace "$ws" && make_workspace "$agent_ws" || setup_exit=$?; }
if [ "$setup_exit" = 0 ]; then
  { "$COPILOT" plugin marketplace add "$TOOL_ROOT" && "$COPILOT" plugin install actions-migrator@actions-migrations-via-copilot \
      && "$COPILOT" plugin list; } > "$OUT/plugin-list.txt" 2>&1 || setup_exit=$?
fi

# Tool permissions are granted only for the exact calls the prompts ask for, so a refusal can only
# come from the plugin's hooks.
if [ "$setup_exit" = 0 ]; then
  scope=$(cd "$ws" && pwd -P)
  run_captured --cwd "$ws" timeout "${SESSION_TIMEOUT:-600}" "$COPILOT" --trust-folder --disallow-temp-dir \
    ${model_args[@]+"${model_args[@]}"} --available-tools 'bash,create,view,skill' --allow-tool 'shell(rm hc-out/keep.txt)' \
    --allow-tool "write($scope/hc-out/safe.txt)" --allow-tool "write($scope/hc-out/p1.md)" \
    --output-format json -p "$MAIN_PROMPT" > "$OUT/main-events.jsonl" 2> "$ROOT/main-stderr.log" || main_exit=$?
fi
if [ "$setup_exit" = 0 ] && [ "$INTERRUPTED" = 0 ]; then
  scope=$(cd "$agent_ws" && pwd -P)
  run_captured --cwd "$agent_ws" timeout "${SESSION_TIMEOUT:-600}" "$COPILOT" \
    --agent actions-migrator:jenkins-migrator --trust-folder --disallow-temp-dir ${model_args[@]+"${model_args[@]}"} \
    --available-tools 'create,view' --allow-tool "write($scope/hc-out/agent.txt)" \
    --output-format json -p "$AGENT_PROMPT" > "$OUT/agent-events.jsonl" 2> "$ROOT/agent-stderr.log" || agent_exit=$?
fi

cp -R "$ws/hc-out" "$OUT/main/" 2>/dev/null || true
cp "$ws/.github/MIGRATION-SCORECARD.md" "$OUT/main/" 2>/dev/null || true
cp -R "$agent_ws/hc-out" "$OUT/agent/" 2>/dev/null || true
python3 "$SUITE_DIR/score.py" cli "$OUT" --runtime "${version:-unknown}" --model "${MODEL:-default}" \
  --setup-exit "$setup_exit" --main-exit "$main_exit" --agent-exit "$agent_exit" --interrupted "$INTERRUPTED"
