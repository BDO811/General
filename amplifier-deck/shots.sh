#!/usr/bin/env bash
# Render each slide of a built deck to a 1280x720 PNG.
# usage: ./shots.sh <outdir> [deck.html]
set -euo pipefail
cd "$(dirname "$0")"
CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome
OUT="$(mkdir -p "${1:-/tmp/shots}" && cd "${1:-/tmp/shots}" && pwd)"
DECK="${2:-amplifier-deck.html}"
N=$(python3 - "$OUT" "$DECK" <<'PY'
import re, sys, pathlib
out = pathlib.Path(sys.argv[1])
h = pathlib.Path(sys.argv[2]).read_text()
head, rest = h.split('<div class="deck">', 1)
body = rest.rsplit('</div>\n<script>', 1)[0]
secs = re.findall(r'<section class="slide.*?</section>', body, re.S)
for i, s in enumerate(secs, 1):
    (out / f"slide{i}.html").write_text(head + '<div class="deck">' + s + '</div></body></html>')
print(len(secs))
PY
)
# headless chrome reserves ~87px of the requested window height
for i in $(seq 1 "$N"); do
  "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1280,807 --virtual-time-budget=9000 \
    --screenshot="$OUT/slide$i.png" "file://$OUT/slide$i.html" >/dev/null 2>&1
done
echo "rendered $N slides of $DECK to $OUT"
