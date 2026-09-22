#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="$ROOT/.run"

stop_pid_file() {
  local name="$1"
  local file="$PID_DIR/$name.pid"
  if [[ -f "$file" ]]; then
    local pid
    pid="$(cat "$file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" || true
      echo "Stopped $name (pid $pid)"
    fi
    rm -f "$file"
  fi
}

stop_pid_file "tracker"

if pgrep -f "$ROOT/gophish-bin/gophish" >/dev/null 2>&1; then
  pkill -f "$ROOT/gophish-bin/gophish" || true
  echo "Stopped GoPhish"
fi

echo "Done."
