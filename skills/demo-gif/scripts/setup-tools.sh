#!/usr/bin/env bash
# Install the VHS recording toolchain into a local dir — no sudo required.
# Produces: vhs (go install) + static ttyd + static ffmpeg/ffprobe binaries.
# Print the line to add to PATH on success.
set -euo pipefail

BIN="${1:-$HOME/.local/vhs-tools/bin}"
mkdir -p "$BIN"

have() { command -v "$1" >/dev/null 2>&1; }

# ffmpeg + ttyd: prefer system copies if already present and on PATH.
if ! have vhs && ! [ -x "$BIN/vhs" ]; then
  echo ">> go install vhs ..."
  GOBIN="$BIN" go install github.com/charmbracelet/vhs@latest
fi

if ! have ttyd && ! [ -x "$BIN/ttyd" ]; then
  echo ">> fetching static ttyd ..."
  curl -fsSL -o "$BIN/ttyd" \
    https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64
  chmod +x "$BIN/ttyd"
fi

if ! have ffmpeg && ! [ -x "$BIN/ffmpeg" ]; then
  echo ">> fetching static ffmpeg ..."
  tmp="$(mktemp -d)"
  curl -fsSL -o "$tmp/ff.tar.xz" \
    https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  tar -xf "$tmp/ff.tar.xz" -C "$tmp"
  cp "$tmp"/ffmpeg-*-amd64-static/ffmpeg "$tmp"/ffmpeg-*-amd64-static/ffprobe "$BIN/"
  rm -rf "$tmp"
fi

echo
echo "Toolchain ready in $BIN"
PATH="$BIN:$PATH" vhs --version
PATH="$BIN:$PATH" ttyd --version 2>&1 | head -1
PATH="$BIN:$PATH" ffmpeg -version 2>&1 | head -1 | cut -c1-30
echo
echo "Add to PATH:  export PATH=\"$BIN:\$PATH\""
