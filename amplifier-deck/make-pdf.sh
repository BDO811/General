#!/usr/bin/env bash
# Export both themed decks to 16:9 (13.333in x 7.5in) PDFs.
set -euo pipefail
cd "$(dirname "$0")"
CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome
export_one () {
  "$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
    --virtual-time-budget=15000 --print-to-pdf="$2" "file://$PWD/$1"
}
export_one amplifier-deck.html       Amplifier-Health-Deck.pdf
export_one amplifier-deck-brand.html Amplifier-Health-Deck-Brand.pdf
