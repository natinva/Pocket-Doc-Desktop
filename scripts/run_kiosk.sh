#!/usr/bin/env bash
set -euo pipefail

URL="http://localhost:8765"

if command -v chromium-browser >/dev/null 2>&1; then
  chromium-browser --kiosk --noerrdialogs --disable-infobars "$URL"
elif command -v chromium >/dev/null 2>&1; then
  chromium --kiosk --noerrdialogs --disable-infobars "$URL"
else
  echo "Chromium bulunamadı. Raspberry Pi OS üzerinde chromium-browser kurulu olmalı."
  exit 1
fi
