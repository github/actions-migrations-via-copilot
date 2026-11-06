# shellcheck shell=bash
# Shared helpers for the surface runners. Source this file; don't run it.

SUITE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC2034  # used by the runners that source this file
TOOL_ROOT=$(git -C "$SUITE_DIR" rev-parse --show-toplevel)
COPILOT_CLI_VERSION=${COPILOT_CLI_VERSION:-latest}

# Scratch git repo holding the conformance hooks, where each surface expects repository hooks.
make_workspace() {
  local ws=$1
  mkdir -p "$ws/.github/hooks" "$ws/hc-out"
  cp "$SUITE_DIR"/kit/* "$ws/.github/hooks/"
  touch "$ws/hc-out/.gitkeep"
  printf 'Scratch repository for actions-migrator surface tests.\n' > "$ws/README.md"
  git -C "$ws" init -q -b main
  git -C "$ws" add -A
  git -C "$ws" -c user.name=surface-tests -c user.email=surface-tests@users.noreply.github.com \
    commit -qm "Surface test workspace"
}

# Prints the prompt for "local" (CLI, VS Code) or "cloud" (cloud agent).
render_prompt() {
  python3 - "$SUITE_DIR/prompt.md" "$1" <<'EOF'
import sys
text = open(sys.argv[1]).read()
# Built at runtime so no file in this repo contains the fake credential line.
fake = "| DEPLOY_TOKEN | " + "Synthetic" + "Probe12345abcdef" + " |"
if sys.argv[2] == "cloud":
    note = ("The repository hooks write `.hook-conformance/probe.jsonl` by themselves. "
            "Don't edit that file yourself, but do include it in your commit.")
    finish = ("Then commit all new files, including the hook-written "
              "`.hook-conformance/probe.jsonl`, and open the pull request.")
else:
    note = "Do not edit anything under `.hook-conformance/`."
    finish = "Do not run any git commands and do not open a pull request."
print(text.replace("{{LOG_NOTE}}", note).replace("{{FINISH}}", finish).replace("{{FAKE_LINE}}", fake))
EOF
}

# Installs the Copilot CLI under $1 and sets COPILOT to its path.
install_copilot_cli() {
  # shellcheck disable=SC2034  # used by the runners
  COPILOT="$1/cli/node_modules/.bin/copilot"
  for _ in 1 2 3; do
    npm install -s --prefix "$1/cli" "@github/copilot@$COPILOT_CLI_VERSION" > "$1/npm-install.log" 2>&1 && [ -x "$COPILOT" ] && return 0
    sleep 10
  done
  echo "Copilot CLI install failed:" >&2
  tail -5 "$1/npm-install.log" >&2
  return 1
}

# Copies the evidence from workspace $2 into $3 and scores it as surface $1.
# Extra args: transcript files, then "--meta key=value" pairs.
collect_and_score() {
  local surface=$1 ws=$2 out=$3; shift 3
  mkdir -p "$out/hc-out"
  cp "$ws/.hook-conformance/probe.jsonl" "$out/probe.jsonl" 2>/dev/null || true
  cp "$ws/hook-results.md" "$out/hook-results.md" 2>/dev/null || true
  cp -R "$ws/hc-out/." "$out/hc-out/" 2>/dev/null || true
  local args=() transcripts=("$out/hook-results.md")
  while [ $# -gt 0 ]; do
    if [ "$1" = --meta ]; then args+=(--meta "$2"); shift 2; else transcripts+=("$1"); shift; fi
  done
  for t in "${transcripts[@]}"; do args+=(--transcript "$t"); done
  python3 "$SUITE_DIR/score.py" --surface "$surface" --log "$out/probe.jsonl" \
    --out-dir "$out/hc-out" --json "$out/score.json" ${args[@]+"${args[@]}"}
}
