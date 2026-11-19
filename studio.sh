#!/usr/bin/env bash
# Start Harness Studio (harness/studio) and open it in the browser. macOS and Linux.
# Usage: ./studio.sh       (from the repo root)
#        ./studio.sh 8780  (another port)
# Windows uses studio.cmd instead.
set -euo pipefail
cd "$(dirname "$0")"

export AEW_AUTO_APPROVE=1
export STUDIO_PORT="${1:-${STUDIO_PORT:-8765}}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed: https://docs.astral.sh/uv/ (macOS: brew install uv)" >&2
  exit 1
fi

if [ -z "${STUDIO_NO_BROWSER:-}" ]; then
  url="http://127.0.0.1:${STUDIO_PORT}"
  if command -v open >/dev/null 2>&1; then opener=open
  elif command -v xdg-open >/dev/null 2>&1; then opener=xdg-open
  else opener=""
  fi
  [ -n "$opener" ] && (sleep 4 && "$opener" "$url" >/dev/null 2>&1) &
fi

exec uv run --with-requirements harness/studio/requirements.txt python harness/studio/server.py
