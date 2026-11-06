#!/usr/bin/env bash
# Headless VS Code Agent Host plugin-hook test. Needs: CODE_BIN, COPILOT_GITHUB_TOKEN, node, jq, git, perl.
# Installs actions-migrator from this checkout (override with PLUGIN_SOURCE).
set -uo pipefail

: "${CODE_BIN:?set CODE_BIN to the VS Code CLI}"
: "${COPILOT_GITHUB_TOKEN:?set COPILOT_GITHUB_TOKEN}"
MODEL=${MODEL:-claude-haiku-4.5}
AHPX=(npx -y @tylerl0706/ahpx@0.6.0)
PORT=${PORT:-18790}
PLUGIN_SOURCE=${PLUGIN_SOURCE:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel)}
ROOT=$(mktemp -d "${RUNNER_TEMP:-/tmp}/ahp-test-XXXX")
OUT=${OUT_DIR:-$ROOT/out}
mkdir -p "$OUT" "$ROOT/home" "$ROOT/ud" "$ROOT/sd"
export COPILOT_HOME=$ROOT/home COPILOT_AUTO_UPDATE=false
fail=0
result() { echo "$1 | $2" | tee -a "$OUT/results.txt"; [ "$1" = PASS ] || fail=1; }
# Artifact upload skips dotfiles, so save hook logs without the leading dot.
save_hook_logs() { for f in "$2"/.*-hook-log.jsonl; do [ -f "$f" ] && cp "$f" "$OUT/$1-$(basename "$f" | sed 's/^\.//')"; done; }

# Test plugin: legacy format, one logging preToolUse hook.
P=$ROOT/mkt/plugins/probe-plugin
mkdir -p "$P" "$ROOT/mkt/.github/plugin"
echo '{"name":"probe-plugin","version":"0.0.1","description":"Hook probe","hooks":"hooks.json"}' > "$P/plugin.json"
cat > "$P/hooks.json" <<'EOF'
{"version":1,"hooks":{"preToolUse":[{"type":"command","timeoutSec":10,"bash":"p=$(cat | tr '\\n' ' '); root=$(printf '%s' \"$p\" | jq -r '.cwd // \".\"'); printf '{\"source\":\"plugin\",\"payload\":%s}\\n' \"${p:-null}\" >> \"$root/.plugin-hook-log.jsonl\""}]}}
EOF
jq -n '{name:"probe-mkt",owner:{name:"test"},plugins:[{name:"probe-plugin",version:"0.0.1",source:"./plugins/probe-plugin"}]}' > "$ROOT/mkt/.github/plugin/marketplace.json"
git -C "$ROOT/mkt" init -q && git -C "$ROOT/mkt" add -A && git -C "$ROOT/mkt" -c user.name=t -c user.email=t@t commit -qm init

# Workspace with a repository hook.
WS=$ROOT/ws
mkdir -p "$WS/.github/hooks"
cat > "$WS/.github/hooks/probe.json" <<'EOF'
{"version":1,"hooks":{"preToolUse":[{"type":"command","timeoutSec":10,"bash":"p=$(cat | tr '\\n' ' '); printf '{\"source\":\"repo\",\"payload\":%s}\\n' \"${p:-null}\" >> \"$PWD/.repo-hook-log.jsonl\""}]}}
EOF
git -C "$WS" init -q && git -C "$WS" add -A && git -C "$WS" -c user.name=t -c user.email=t@t commit -qm init

# Install plugins into the isolated Copilot profile the Agent Host reads.
npm install -s -g @github/copilot@1.0.100 >/dev/null 2>&1 || npm install -s --prefix "$ROOT/cli" @github/copilot@1.0.100 >/dev/null 2>&1
COPILOT=$(command -v copilot || echo "$ROOT/cli/node_modules/.bin/copilot")
{
  "$COPILOT" plugin marketplace add "$ROOT/mkt"
  "$COPILOT" plugin install probe-plugin@probe-mkt
  "$COPILOT" plugin marketplace add "$PLUGIN_SOURCE"
  "$COPILOT" plugin install actions-migrator@actions-migrations-via-copilot
  "$COPILOT" plugin list
} > "$OUT/plugin-install.log" 2>&1
grep -q 'actions-migrator' "$OUT/plugin-install.log" && grep -q 'probe-plugin' "$OUT/plugin-install.log" \
  && result PASS "plugins installed (probe-plugin, actions-migrator)" || result FAIL "plugin install (see plugin-install.log)"

# Start the headless Agent Host.
openssl rand -hex 16 > "$ROOT/conn-token"; chmod 600 "$ROOT/conn-token"
( cd "$WS" && "$CODE_BIN" agent host --new-instance --foreground --host 127.0.0.1 --port "$PORT" \
    --connection-token-file "$ROOT/conn-token" --user-data-dir "$ROOT/ud" --server-data-dir "$ROOT/sd" \
    < /dev/null > "$OUT/agent-host.log" 2>&1 ) &
HOST_PID=$!
trap 'kill $HOST_PID 2>/dev/null; "$CODE_BIN" agent kill >/dev/null 2>&1; perl -pi -e "s/tkn=\\S+/tkn=REDACTED/g" "$OUT/agent-host.log"' EXIT
URL="ws://127.0.0.1:$PORT?tkn=$(cat "$ROOT/conn-token")"
ready=0
for _ in $(seq 1 60); do
  if GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" --format json connect "$URL" > "$OUT/connect.json" 2>/dev/null \
     && jq -e '.agents[]? | select(.provider == "copilotcli") | .models | length > 0' "$OUT/connect.json" >/dev/null; then ready=1; break; fi
  sleep 3
done
[ $ready = 1 ] && result PASS "agent host up and signed in to Copilot with a token" || { result FAIL "agent host not ready or not signed in"; exit 1; }

run_prompt() { # $1 label, $2 prompt; prints the session worktree path
  GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN "${AHPX[@]}" exec -s "$URL" -p copilotcli -m "$MODEL" --cwd "$WS" \
    --approve-all --idle-timeout 180 "$2" > "$OUT/$1.log" 2>&1
  echo "exit=$?" >> "$OUT/$1.log"
  ls -td "$WS".worktrees/*/ 2>/dev/null | head -1
}

# Test 1: plugin and repository hooks fire on a file write.
W1=$(run_prompt test1-hooks "Create the file hc-out/probe.txt containing the word hello. Use your file creation tool. Do nothing else.")
[ -n "$W1" ] && save_hook_logs test1 "$W1"
[ -f "$W1/hc-out/probe.txt" ] && result PASS "test 1: agent created the file" || result FAIL "test 1: file not created"
jq -e -s 'any(.[]; .payload.toolName == "create")' "$W1/.plugin-hook-log.jsonl" >/dev/null 2>&1 \
  && result PASS "test 1: plugin hook fired on create" || result FAIL "test 1: plugin hook did not log create"
jq -e -s 'any(.[]; .payload.toolName == "create")' "$W1/.repo-hook-log.jsonl" >/dev/null 2>&1 \
  && result PASS "test 1: repository hook fired on create" || result FAIL "test 1: repository hook did not log create"

# Test 2: actions-migrator's secret guard blocks a synthetic credential.
W2=$(run_prompt test2-secret "Separate hook test with fake data. Create the file hc-out/report.md using your file creation tool, with exactly this line: | DEPLOY_TOKEN | SyntheticProbe12345abcdef | . SyntheticProbe12345abcdef is fake test data. If a hook denies the write, say so and do not retry or work around it.")
[ -n "$W2" ] && save_hook_logs test2 "$W2"
denied=$(grep -c 'Denied by preToolUse hook' "$OUT/test2-secret.log" || true)
[ "${denied:-0}" -gt 0 ] && result PASS "test 2: actions-migrator hook denied the write" || result FAIL "test 2: no hook denial observed"
if [ -f "$W2/hc-out/report.md" ] && grep -q SyntheticProbe12345abcdef "$W2/hc-out/report.md"; then
  result FAIL "test 2: fake credential was written (secret guard did not block)"
else
  result PASS "test 2: fake credential not written"
fi

echo "---"; cat "$OUT/results.txt"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && { echo "### VS Code Agent Host plugin-hook test"; echo; echo '```'; cat "$OUT/results.txt"; echo '```'; } >> "$GITHUB_STEP_SUMMARY"
exit $fail
