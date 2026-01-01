#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO_DIR/skills"
AGENTS_DIR="$HOME/.agents/skills"
TARGETS=(
  "$HOME/.claude/skills"
  "$HOME/.opencode/skills"
)

usage() {
  echo "usage: $(basename "$0") <skill-name>" >&2
  echo >&2
  echo "available skills:" >&2
  for skill in "$SKILLS_DIR"/*/; do
    [[ -d "$skill" ]] || continue
    echo "  $(basename "${skill%/}")" >&2
  done
}

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

name="$1"
source_skill="$SKILLS_DIR/$name"

if [[ ! -d "$source_skill" ]]; then
  echo "Error: skill '$name' not found in $SKILLS_DIR" >&2
  echo >&2
  usage
  exit 1
fi

# Copy the skill into ~/.agents/skills, replacing any previous install
mkdir -p "$AGENTS_DIR"
installed="$AGENTS_DIR/$name"

if [[ -L "$installed" ]]; then
  echo "warning: $installed is a symlink, replacing it with a copy" >&2
  rm "$installed"
elif [[ -e "$installed" && ! -d "$installed" ]]; then
  echo "Error: $installed exists and is not a directory" >&2
  exit 1
fi

rm -rf "$installed"
cp -R "$source_skill" "$installed"
echo "installed: $installed (from $source_skill)"

# Link the installed skill into each agent's skills directory
for target_dir in "${TARGETS[@]}"; do
  mkdir -p "$target_dir"
  link="$target_dir/$name"

  if [[ -L "$link" ]]; then
    current="$(readlink "$link")"
    if [[ "$current" == "$installed" ]]; then
      echo "up to date: $link -> $installed"
      continue
    fi
    echo "updating symlink: $link"
    rm "$link"
  elif [[ -e "$link" ]]; then
    echo "warning: $link exists and is not a symlink, skipping" >&2
    continue
  fi

  ln -s "$installed" "$link"
  echo "linked: $link -> $installed"
done
