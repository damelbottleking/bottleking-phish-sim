#!/usr/bin/env bash
# Run inside Terminal.app — keeps cloudflared alive and logs the public URL.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:?port required}"
NAME="${2:?name required}"
LOG="$ROOT/.run/${NAME}.log"
mkdir -p "$ROOT/.run"
: >"$LOG"
echo "Starting cloudflared for port ${PORT} (${NAME})..."
echo "Mac will stay awake (caffeinate -i) while this window is open."
echo "Logging to ${LOG}"
exec caffeinate -i cloudflared tunnel --url "http://127.0.0.1:${PORT}" 2>&1 | tee -a "$LOG"
