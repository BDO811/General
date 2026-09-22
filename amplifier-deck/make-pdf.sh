#!/usr/bin/env bash
# Export the deck to a 16:9 (13.333in x 7.5in) PDF.
set -euo pipefail
cd "$(dirname "$0")"
/opt/pw-browsers/chromium-1194/chrome-linux/chrome --headless --disable-gpu --no-sandbox \
  --no-pdf-header-footer --virtual-time-budget=15000 \
  --print-to-pdf="Amplifier-Health-5-Slide.pdf" "file://$PWD/amplifier-deck.html"
