#!/usr/bin/env bash
# Opens two Terminal.app tabs for cloudflared and waits for public URLs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
chmod +x "$ROOT/scripts/run-tunnel-terminal.sh"
: >"$ROOT/.run/cf-gophish.log"
: >"$ROOT/.run/cf-tracker.log"

osascript <<APPLESCRIPT
tell application "Terminal"
  activate
  do script "bash '$ROOT/scripts/run-tunnel-terminal.sh' 8090 cf-gophish"
  delay 1
  do script "bash '$ROOT/scripts/run-tunnel-terminal.sh' 9090 cf-tracker"
end tell
APPLESCRIPT

echo "Waiting for tunnel URLs in $ROOT/.run/ ..."
GOPHISH_URL=""
TRACKER_URL=""
for _ in $(seq 1 60); do
  if [[ -z "$GOPHISH_URL" ]]; then
    GOPHISH_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$ROOT/.run/cf-gophish.log" 2>/dev/null | head -1 || true)
  fi
  if [[ -z "$TRACKER_URL" ]]; then
    TRACKER_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$ROOT/.run/cf-tracker.log" 2>/dev/null | head -1 || true)
  fi
  if [[ -n "$GOPHISH_URL" && -n "$TRACKER_URL" ]]; then
    break
  fi
  sleep 2
done

if [[ -z "$GOPHISH_URL" || -z "$TRACKER_URL" ]]; then
  echo "Timeout waiting for URLs. Check Terminal windows and .run/cf-*.log" >&2
  exit 1
fi

python3 - <<PY
import json, re
from pathlib import Path
root = Path("${ROOT}")
cfg = {"gophish_url": "${GOPHISH_URL}", "tracker_url": "${TRACKER_URL}"}
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
print("gophish_url:", cfg["gophish_url"])
print("tracker_url:", cfg["tracker_url"])
PY
