#!/usr/bin/env bash
# Copilot CLI surface: the conformance kit as repository hooks, plus actions-migrator from this checkout.
# Needs: COPILOT_GITHUB_TOKEN (a Copilot user's token, or the workflow token with copilot-requests: write),
# node, python3, git. Writes $OUT_DIR/cli/score.json.
set -uo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"

OUT=${OUT_DIR:-$(mktemp -d)}/cli
mkdir -p "$OUT"
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-cli-XXXX")
export COPILOT_HOME=$ROOT/home COPILOT_AUTO_UPDATE=false
WS=$ROOT/ws
make_workspace "$WS"
install_copilot_cli "$ROOT" || exit 1
version=$("$COPILOT" --version 2>/dev/null | head -1)
model_args=()
[ -n "${MODEL:-}" ] && model_args=(--model "$MODEL")

# --add-dir /tmp lets the rm step reach the hooks instead of failing the CLI's own path check.
( cd "$WS" && timeout 1200 "$COPILOT" --plugin-dir "$TOOL_ROOT/plugin" --trust-folder --allow-all-tools \
    --add-dir /tmp ${model_args[@]+"${model_args[@]}"} --output-format json --share "$OUT/transcript.md" \
    -p "$(render_prompt local)" > "$OUT/events.jsonl" 2> "$OUT/stderr.log" )
echo "exit=$?" >> "$OUT/stderr.log"

collect_and_score cli "$WS" "$OUT" "$OUT/events.jsonl" "$OUT/transcript.md" \
  --meta "copilot_cli=$version" --meta "model=${MODEL:-default}"
