#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ARGS=()
[[ "${1:-}" == "--console" ]] && ARGS+=("--console")
python3 build.py "${ARGS[@]}"