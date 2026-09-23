# -*- coding: utf-8 -*-
"""Pull the four Amplifier brand faces from Google Fonts into brand/fonts/.

    python3 fetch_fonts.py

Cormorant Garamond (display), Newsreader Italic (deck and pull quotes),
Inter (body), JetBrains Mono (microtype, data, code).
"""
import os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fonts")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

FAMILIES = [
    ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600"
     "&family=Inter:wght@400;500;600;700"
     "&family=JetBrains+Mono:wght@400;500;700&display=swap",
     r"font-family: '([^']+)';.*?font-weight: (\d+);.*?src: url\(([^)]+)\)",
     lambda m: "%s-%s.ttf" % (m[0].replace(" ", ""), m[1])),
    ("https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@1,16,400;1,16,500"
     "&display=swap",
     r"font-family: '([^']+)';\s*font-style: (\w+);.*?font-weight: (\d+);.*?src: url\(([^)]+)\)",
     lambda m: "%s-%s-%s.ttf" % (m[0].replace(" ", ""), m[1], m[2])),
]

def main():
    os.makedirs(OUT, exist_ok=True)
    for url, pattern, namer in FAMILIES:
        css = subprocess.run(["curl", "-sS", url, "-H", "User-Agent: " + UA],
                             capture_output=True, text=True).stdout
        seen = set()
        for m in re.findall(pattern, css, re.S):
            name = namer(m)
            if name in seen:
                continue
            seen.add(name)
            subprocess.run(["curl", "-sSL", "-o", os.path.join(OUT, name), m[-1]], check=True)
            print("fetched", name)

if __name__ == "__main__":
    main()
