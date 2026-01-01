#!/usr/bin/env bash
# Usage: scan.sh [TARGET_DIR]
set -euo pipefail

TARGET="${1:-.}"

if [[ -f "$TARGET/semgrep.yaml" ]]; then
  semgrep scan --config p/owasp-top-ten --config "$TARGET/semgrep.yaml" --metrics=off --verbose "$TARGET"
else
  semgrep scan --config p/owasp-top-ten --metrics=off --verbose "$TARGET"
fi
