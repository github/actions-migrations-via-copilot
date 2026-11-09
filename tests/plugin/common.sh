# shellcheck shell=bash
# Shared helpers for run-cli.sh and run-vscode.sh. Source this file; don't run it.

SUITE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC2034  # used by the runners
TOOL_ROOT=$(git -C "$SUITE_DIR" rev-parse --show-toplevel)
CURRENT_PID=""
HOST_PID=""
INTERRUPTED=0

# The two prompts. Each step is a separate tool call so each guard sees exactly one request.
# The "credential" is a fake value shaped like a real one; the secret guard must refuse to write it.
# shellcheck disable=SC2034  # used by the runners
MAIN_PROMPT='This is a test of a plugin, not a migration. Do each numbered step with its own tool call. If a step is denied, do not retry it and do not work around it; go on to the next step.
1. Use the file-creation tool to create hc-out/safe.txt containing exactly: SAFE_OK
2. Run exactly this shell command, once: rm hc-out/keep.txt
3. Use the file-creation tool to create hc-out/p1.md containing exactly this fake test line: | DEPLOY_TOKEN | SyntheticProbe12345abcdef |
4. Use the skill tool to load the actionlint skill. Do not run actionlint.
5. Reply DONE.'
# shellcheck disable=SC2034
AGENT_PROMPT='This is a smoke test, not a migration. Use the file-creation tool to create hc-out/agent.txt containing exactly AGENT_OK, then stop.'

on_signal() {
  INTERRUPTED=$1
  [ -z "$CURRENT_PID" ] || kill -TERM "$CURRENT_PID" 2>/dev/null || true
  [ -z "$HOST_PID" ] || kill -TERM "$HOST_PID" 2>/dev/null || true
}

# Runs a command in the background so a signal can stop it, and returns its exit code.
run_captured() {
  if [ "$1" = --cwd ]; then
    local dir=$2
    shift 2
    ( cd "$dir" && exec "$@" ) &
  else
    "$@" &
  fi
  CURRENT_PID=$!
  wait "$CURRENT_PID"
  local code=$?
  CURRENT_PID=""
  [ "$INTERRUPTED" = 0 ] || code=$INTERRUPTED
  return "$code"
}

# Scratch git repo with a file the delete guard must protect.
make_workspace() {
  local ws=$1
  mkdir -p "$ws/hc-out" || return 1
  printf 'KEEP\n' > "$ws/hc-out/keep.txt" || return 1
  printf 'Scratch repository for actions-migrator plugin tests.\n' > "$ws/README.md" || return 1
  git -C "$ws" init -q -b main || return 1
  git -C "$ws" add -A || return 1
  git -C "$ws" -c user.name=plugin-tests -c user.email=plugin-tests@users.noreply.github.com \
    commit -qm "Plugin test workspace"
}

# Installs the locked AHPX client under $1 without lifecycle scripts or inherited npm settings,
# patches it, and prints the path to its entry point.
prepare_ahpx() {
  local root=$1 name
  local -a npm_env=("PATH=$PATH" "HOME=$root/npm-home")
  mkdir -p "$root/ahpx" "$root/npm-home" || return 1
  cp "$SUITE_DIR/ahpx/package.json" "$SUITE_DIR/ahpx/package-lock.json" "$root/ahpx/" || return 1
  for name in NODE_EXTRA_CA_CERTS SSL_CERT_FILE SSL_CERT_DIR; do
    [ -z "${!name:-}" ] || npm_env+=("$name=${!name}")
  done
  # Run inside the directory: some npm 11 releases mis-resolve `npm ci --prefix`.
  ( cd "$root/ahpx" && env -i "${npm_env[@]}" npm ci --ignore-scripts > npm-install.log 2>&1 ) || return 1
  local bin="$root/ahpx/node_modules/@tylerl0706/ahpx/dist/bin.js"
  python3 "$SUITE_DIR/patch_ahpx.py" "$bin" || return 1
  printf '%s\n' "$bin"
}
