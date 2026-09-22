#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
OUT_DIR="$ROOT/templates/prepared"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env file. Copy .env.example to .env and fill it in first."
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

mkdir -p "$OUT_DIR"

TRACKER_URL="${TRACKER_PUBLIC_URL:-http://127.0.0.1:9090}"

sed "s|__TRACKER_BASE__|${TRACKER_URL}|g" \
  "$ROOT/templates/landing-page.html" \
  > "$OUT_DIR/landing-page-ready.html"

cp "$ROOT/templates/email-template-placeholder.html" "$OUT_DIR/email-template-ready.html"

echo "Prepared templates in $OUT_DIR"
echo "  - email-template-ready.html  -> paste into GoPhish Email Template"
echo "  - landing-page-ready.html    -> paste into GoPhish Landing Page"
