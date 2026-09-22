#!/usr/bin/env bash
# Render each slide to a 1280x720 PNG using the bundled Chromium.
set -euo pipefail
CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome
OUT="${1:-/tmp/shots}"
mkdir -p "$OUT"
python3 - "$OUT" <<'PY'
import re, sys, pathlib
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
h = pathlib.Path("amplifier-deck.html").read_text()
head, rest = h.split('<div class="deck">', 1)
body = rest.rsplit('</div>\n<script>', 1)[0]
for i, s in enumerate(re.findall(r'<section class="slide.*?</section>', body, re.S), 1):
    (out / f"slide{i}.html").write_text(head + '<div class="deck">' + s + '</div></body></html>')
PY
# headless chrome reserves ~87px of the requested window height for chrome
for i in 1 2 3 4 5; do
  "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1280,807 --virtual-time-budget=9000 \
    --screenshot="$OUT/slide$i.png" "file://$OUT/slide$i.html" >/dev/null 2>&1
done
echo "rendered to $OUT"
