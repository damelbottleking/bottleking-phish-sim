#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GOPHISH_DIR="$ROOT/gophish-bin"
TRACKER_DIR="$ROOT/tracker"
PID_DIR="$ROOT/.run"
mkdir -p "$PID_DIR"

if [[ ! -x "$GOPHISH_DIR/gophish" ]]; then
  echo "GoPhish binary not found. Run: bash scripts/download-gophish.sh"
  exit 1
fi

echo "Starting form-interaction tracker on http://127.0.0.1:9090 ..."
if [[ ! -d "$TRACKER_DIR/.venv" ]]; then
  python3 -m venv "$TRACKER_DIR/.venv"
  "$TRACKER_DIR/.venv/bin/pip" install -q -r "$TRACKER_DIR/requirements.txt"
fi

nohup "$TRACKER_DIR/.venv/bin/python" "$TRACKER_DIR/server.py" \
  > "$PID_DIR/tracker.log" 2>&1 &
echo $! > "$PID_DIR/tracker.pid"

cp "$ROOT/gophish/config.json" "$GOPHISH_DIR/config.json"

echo "Starting GoPhish admin UI on https://127.0.0.1:3333 ..."
echo "Starting GoPhish landing pages on http://0.0.0.0:8080 ..."
echo
echo "IMPORTANT: On first run, GoPhish prints a one-time admin password below."
echo "Save it immediately."
echo

cd "$GOPHISH_DIR"
exec ./gophish
