#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="$(uname -m)"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"

case "$OS-$ARCH" in
  darwin-arm64|darwin-x86_64)
    ASSET="gophish-v0.12.1-osx-64bit.zip"
    ;;
  linux-x86_64|linux-amd64)
    ASSET="gophish-v0.12.1-linux-64bit.zip"
    ;;
  *)
    echo "Unsupported platform: $OS $ARCH"
    echo "Use Linux x86_64 or macOS for local testing."
    exit 1
    ;;
esac

URL="https://github.com/gophish/gophish/releases/download/v0.12.1/$ASSET"
TMP="$ROOT/gophish.zip"

echo "Downloading $ASSET ..."
curl -sL -o "$TMP" "$URL"
rm -rf "$ROOT/gophish-bin"
unzip -q -o "$TMP" -d "$ROOT/gophish-bin"
chmod +x "$ROOT/gophish-bin/gophish"
rm -f "$TMP"

echo "Installed GoPhish to $ROOT/gophish-bin"
