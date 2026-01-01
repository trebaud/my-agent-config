#!/usr/bin/env bash
set -euo pipefail

# ── ANSI colors ──────────────────────────────────────────────────────
readonly RESET='\033[0m'
readonly BOLD_WHITE='\033[1;37m'
readonly BOLD_GREEN='\033[1;32m'
readonly BOLD_RED='\033[1;31m'
readonly BOLD_MAGENTA='\033[1;35m'
readonly CYAN='\033[0;36m'
readonly DIM='\033[0;90m'

# ── state ────────────────────────────────────────────────────────────
VERBOSE=false
SPINNER_PID=""
SPINNER_MSG=""
SPINNER_INDENT=""

# ── helpers ──────────────────────────────────────────────────────────

log() { [[ "$VERBOSE" == true ]] && printf '[DEBUG] %s\n' "$*" >&2 || true; }

die() {
  spinner_stop 1
  printf "\n${BOLD_RED}  ✖ %s${RESET}\n\n" "$*" >&2
  exit 1
}

quiet() {
  if [[ "$VERBOSE" == true ]]; then
    "$@"
  else
    "$@" >/dev/null 2>&1
  fi
}

# ── spinner ──────────────────────────────────────────────────────────

spinner_start() {
  SPINNER_MSG="$1"
  SPINNER_INDENT="${2:-  }"
  printf "${CYAN}%s⠋ %s${RESET}" "$SPINNER_INDENT" "$SPINNER_MSG" >&2
  (
    local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local i=0
    while true; do
      printf "\r${CYAN}%s%s %s${RESET}" "$SPINNER_INDENT" "${frames[$i]}" "$SPINNER_MSG" >&2
      i=$(( (i + 1) % ${#frames[@]} ))
      sleep 0.08
    done
  ) &
  SPINNER_PID=$!
}

spinner_stop() {
  local failed="${1:-0}"
  [[ -z "$SPINNER_PID" ]] && return

  kill "$SPINNER_PID" 2>/dev/null
  wait "$SPINNER_PID" 2>/dev/null || true
  SPINNER_PID=""

  if [[ "$failed" -eq 0 ]]; then
    printf "\r${BOLD_GREEN}%s✔ %s${RESET}\033[K\n" "$SPINNER_INDENT" "$SPINNER_MSG" >&2
  else
    printf "\r${BOLD_RED}%s✖ %s${RESET}\033[K\n" "$SPINNER_INDENT" "$SPINNER_MSG" >&2
  fi
  SPINNER_MSG=""
}

trap 'spinner_stop 1' EXIT

# ── usage / arg parsing ─────────────────────────────────────────────

usage() {
  cat <<'EOF'
Usage: claude-worktree.sh [--no-claude] [-v] [-r repo-dir] [-b branch-name] [-h]

Create a git worktree under <repo>/.claude/worktrees/<branch>, init
submodules, install dependencies, and launch Claude Code.

Options:
  -r repo-dir     Repository root (default: current directory)
  -b branch-name  Branch to create (default: random wt-XXXXX)
  --no-claude     Setup only — skip launching Claude Code
  -v              Verbose output (show debug logs)
  -h, --help      Show this help message
EOF
  exit 0
}

parse_args() {
  CLAUDE=true
  local repo_arg="" branch_arg=""

  # Extract long options before getopts
  local args=()
  for arg in "$@"; do
    case "$arg" in
      --no-claude) CLAUDE=false ;;
      --help)      usage ;;
      *)           args+=("$arg") ;;
    esac
  done
  set -- "${args[@]+"${args[@]}"}"

  while getopts "vr:b:h" opt; do
    case "$opt" in
      v) VERBOSE=true ;;
      r) repo_arg="$OPTARG" ;;
      b) branch_arg="$OPTARG" ;;
      h) usage ;;
      *) usage ;;
    esac
  done

  log "resolving repo dir from '${repo_arg:-.}'"
  REPO="$(cd "${repo_arg:-.}" && pwd)" || die "cannot resolve repo dir '${repo_arg:-.}'"
  log "REPO=$REPO"

  BRANCH="${branch_arg:-wt-$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c5 || :)}"
  log "BRANCH=$BRANCH"
}

# ── worktree setup ───────────────────────────────────────────────────

detect_base_branch() {
  log "detecting main branch"
  if git -C "$REPO" rev-parse --verify --quiet refs/heads/main >/dev/null 2>&1; then
    echo main
  else
    echo master
  fi
}

create_worktree() {
  local base="$1"
  spinner_start "Creating worktree $BRANCH from $base"
  quiet git -C "$REPO" worktree add "$WORKTREE_DIR" -b "$BRANCH" "$base" || die "failed to create worktree"
  spinner_stop
}

setup_worktree() {
  printf "${CYAN}  ◇ Setting up worktree${RESET}\n" >&2

  spinner_start "Syncing submodules" "      "
  log "initializing submodules"
  quiet git -C "$WORKTREE_DIR" submodule update --init --recursive || true
  spinner_stop

  spinner_start "Installing dependencies" "      "
  log "installing dependencies"
  (cd "$WORKTREE_DIR" && quiet pnpm install --frozen-lockfile) || true
  spinner_stop

  printf "${BOLD_GREEN}  ✔ Setting up worktree${RESET}\n" >&2
}

# ── main ─────────────────────────────────────────────────────────────

main() {
  parse_args "$@"

  printf "\n${BOLD_MAGENTA}  ◆ claude-worktree${RESET}\n\n" >&2

  WORKTREE_DIR="$REPO/.claude/worktrees/$BRANCH"
  log "WORKTREE_DIR=$WORKTREE_DIR"

  local base_branch
  base_branch="$(detect_base_branch)"
  log "base_branch=$base_branch"

  create_worktree "$base_branch"
  setup_worktree

  trap - EXIT

  printf "\n${BOLD_GREEN}  Done! 🤖${RESET}\n" >&2
  printf "\n  ${DIM}cd %s${RESET}\n\n" "$WORKTREE_DIR" >&2

  # Print path to stdout so callers can use: cd "$(claude-worktree.sh)"
  [[ ! -t 1 ]] && echo "$WORKTREE_DIR"

  if [[ "$CLAUDE" == true ]]; then
    log "launching claude in worktree '$BRANCH'"
    claude --worktree "$BRANCH"
  fi
}

main "$@"
