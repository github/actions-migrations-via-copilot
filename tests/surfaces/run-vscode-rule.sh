#!/usr/bin/env bash
# Isolated VS Code Agent Host rule probe: exactly one plugin rule, no skills or agents.
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
: "${CODE_BIN:?set CODE_BIN to the VS Code CLI}"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"
: "${RULE_FORMAT:?set RULE_FORMAT to current or namespace}"
case "$RULE_FORMAT" in
  current|namespace) ;;
  *) echo "RULE_FORMAT must be current or namespace" >&2; exit 2 ;;
esac
[ -z "$(git -C "$TOOL_ROOT" status --porcelain)" ] || {
  echo "Commit the suite changes before running the probe so its source SHA is exact" >&2
  exit 2
}

MODEL=${MODEL:-claude-haiku-4.5}
PORT=${PORT:-18792}
prompt_file=${RULE_PROMPT_FILE:-$SUITE_DIR/prompt-rule.md}
prompt_sha=$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$prompt_file")
OUT_ROOT=${OUT_DIR:-$(mktemp -d)}/vscode-rule
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/surface-vscode-rule-XXXX")
mkdir -p "$OUT_ROOT"
host_pid=
cleanup() {
  if [ -n "$host_pid" ]; then
    kill "$host_pid" 2>/dev/null || true
    wait "$host_pid" 2>/dev/null || true
  fi
  rm -rf "$ROOT"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

version=$("$CODE_BIN" --version 2>/dev/null | head -1)
commit=$(sed -nE 's/.*\(commit ([0-9a-f]{40})\).*/\1/p' <<< "$version")
[ -n "$commit" ] || { echo "Could not identify the VS Code Agent Host commit" >&2; exit 1; }
export VSCODE_CLI_INITIAL_AH_VERSION=$commit

nm="$ROOT/ahpx/node_modules"
ahpx_bin=$(prepare_ahpx "$ROOT")
ahpx_version=$(node -p "require('$nm/@tylerl0706/ahpx/package.json').version")
[ "$ahpx_version" = 0.6.0 ] || { echo "Expected AHPX 0.6.0, found $ahpx_version" >&2; exit 1; }
AHPX=(node "$ahpx_bin")

plugin_root="$ROOT/probe"
python3 "$SUITE_DIR/make_probes.py" "$plugin_root" --rule-only "$RULE_FORMAT"
rule_file=$(cat "$plugin_root/rule-resource-path")
rule_sha=$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$rule_file")
plugin_dir="$plugin_root/plugins/hc-rule-probe"
ws="$ROOT/ws"
evidence="$ROOT/evidence"
mkdir -p "$ROOT/ud" "$ROOT/sd" "$evidence"
make_workspace "$ws" plugin
export COPILOT_HOME="$ROOT/copilot-home"

openssl rand -hex 16 > "$ROOT/conn-token"
chmod 600 "$ROOT/conn-token"
( cd "$ws" && exec "$CODE_BIN" agent host --new-instance --foreground --host 127.0.0.1 --port "$PORT" \
    --connection-token-file "$ROOT/conn-token" --user-data-dir "$ROOT/ud" \
  --server-data-dir "$ROOT/sd" < /dev/null > "$ROOT/host.log" 2>&1 ) &
host_pid=$!
url="ws://127.0.0.1:$PORT?tkn=$(cat "$ROOT/conn-token")"
ready=0
for _ in $(seq 1 60); do
  if GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" --format json connect "$url" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 3
done
if [ "$ready" != 1 ]; then
  echo "Agent Host connection failed; no rule result was established" >&2
  exit 1
fi

suite_sha=$(git -C "$TOOL_ROOT" rev-parse HEAD)
set +e
HC_EVIDENCE_DIR="$evidence" HC_PLUGIN_DIRS="$plugin_dir" \
HC_FIXTURE_WORKSPACE="$ws" \
HC_RULE_RESOURCE_PATH="$rule_file" \
HC_RULE_RESOURCE_SHA256="$rule_sha" GITHUB_TOKEN="$COPILOT_GITHUB_TOKEN" \
  "${AHPX[@]}" --format json exec -s "$url" -p copilotcli -m "$MODEL" --cwd "$ws" --deny-all \
  --idle-timeout 180 "$(cat "$prompt_file")" 2>&1 \
  | python3 "$SUITE_DIR/rule_evidence.py" capture "$evidence/rule-events.jsonl" > "$ROOT/plugin-discovered"
statuses=("${PIPESTATUS[@]}")
session_exit=${statuses[0]}
set -e
[ "${statuses[1]}" = 0 ] || { echo "Rule evidence capture failed" >&2; exit 1; }

server=$(sed -nE 's/.*\[([0-9a-f]{7})\]: Server ready.*/\1/p' "$ROOT/host.log" | head -1)
plugin_discovered=$(cat "$ROOT/plugin-discovered")
server_matches_pin=false
[ "$server" = "${commit:0:7}" ] && server_matches_pin=true
case_id=R1
[ "$RULE_FORMAT" = namespace ] && case_id=R2

python3 "$SUITE_DIR/rule_evidence.py" --format "$RULE_FORMAT" \
  --delivery-log "$evidence/rule-resource.jsonl" --events "$evidence/rule-events.jsonl" --workspace "$evidence" \
  --rule-file "$rule_file" --out "$OUT_ROOT/$RULE_FORMAT.json" \
  --meta "session=vscode-agent-host-rule" --meta "case=$case_id" \
  --meta "suite_sha=$suite_sha" --meta "plugin=hc-rule-probe@0.0.1" \
  --meta "vscode_cli=$version" --meta "agent_host_commit=$commit" \
  --meta "server_ready_commit=${server:-unknown}" --meta "ahpx=$ahpx_version" \
  --meta "model_selector=$MODEL" --meta "session_exit=$session_exit" \
  --meta "prompt_sha256=$prompt_sha" \
  --meta "tool_event_source=agent-host-client" \
  --meta "plugin_discovered=$plugin_discovered" \
  --meta "server_commit_matches_pin=$server_matches_pin"
echo "evidence=$OUT_ROOT/$RULE_FORMAT.json"
