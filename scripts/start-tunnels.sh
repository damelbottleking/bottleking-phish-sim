#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="$ROOT/.run"
mkdir -p "$PID_DIR"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx required for localtunnel"
  exit 1
fi

stop_tunnel() {
  local name="$1"
  local file="$PID_DIR/${name}.pid"
  if [[ -f "$file" ]]; then
    local pid
    pid="$(cat "$file")"
    kill "$pid" 2>/dev/null || true
    rm -f "$file"
  fi
}

start_tunnel() {
  local name="$1"
  local port="$2"
  local log="$PID_DIR/${name}.log"
  stop_tunnel "$name"
  nohup npx --yes localtunnel --port "$port" >"$log" 2>&1 &
  echo $! >"$PID_DIR/${name}.pid"
  local url=""
  for _ in $(seq 1 30); do
    url="$(grep -Eo 'https://[a-z0-9-]+\.loca\.lt' "$log" | head -1 || true)"
    if [[ -n "$url" ]]; then
      echo "$url"
      return 0
    fi
    sleep 1
  done
  echo "Failed to start $name tunnel. See $log" >&2
  return 1
}

GOPHISH_URL="$(start_tunnel gophish-tunnel 8090)"
TRACKER_URL="$(start_tunnel tracker-tunnel 9090)"

python3 - <<PY
import json
import re
from pathlib import Path

root = Path("${ROOT}")
cfg = {
    "gophish_url": "${GOPHISH_URL}",
    "tracker_url": "${TRACKER_URL}",
}
(root / "docs/config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

env_path = root / ".env"
if env_path.exists():
    text = env_path.read_text(encoding="utf-8")
    for key, val in [("GOPHISH_PUBLIC_URL", cfg["gophish_url"]), ("TRACKER_PUBLIC_URL", cfg["tracker_url"])]:
        line = f"{key}={val}"
        if re.search(rf"^{re.escape(key)}=", text, flags=re.M):
            text = re.sub(rf"^{re.escape(key)}=.*$", line, text, flags=re.M)
        else:
            text = text.rstrip() + "\n" + line + "\n"
    env_path.write_text(text, encoding="utf-8")

print("Updated docs/config.json and .env")
print("  gophish_url:", cfg["gophish_url"])
print("  tracker_url:", cfg["tracker_url"])
PY

echo
echo "Push docs/config.json to GitHub Pages after tunnels start."
echo "Keep this terminal session running or leave tunnel PIDs alive."
