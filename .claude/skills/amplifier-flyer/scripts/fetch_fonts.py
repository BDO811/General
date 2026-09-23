#!/usr/bin/env python3
"""Fetch the five Amplifier typefaces into a local font directory.

Amplifier documents use exactly these:
    JetBrainsMono-Regular, JetBrainsMono-Bold   labels, eyebrows, footers, code
    CormorantGaramond-Light                     flyer hero, flyer stat numerals
    Newsreader-Regular, Newsreader-Italic       proposal subheads and numerals
    Inter-Regular, Inter-Bold                   body copy, proposal hero

Run once per machine:  python3 fetch_fonts.py [outdir]
Default outdir is ~/.amplifier-fonts
"""
import os, re, sys, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.amplifier-fonts")
UA = {"User-Agent": "Mozilla/5.0"}

# family query -> [(css order index, saved filename), ...]
WANT = [
    ("JetBrains+Mono:wght@400;700", ["JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"]),
    ("Cormorant+Garamond:wght@300", ["CormorantGaramond-Light.ttf"]),
    ("Newsreader:ital,wght@0,400;1,400", ["Newsreader-Italic.ttf", "Newsreader-Regular.ttf"]),  # css2 emits italic first
    ("Inter:wght@400;700", ["Inter-Regular.ttf", "Inter-Bold.ttf"]),
]

def get(url, headers=UA):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45).read()

def main():
    os.makedirs(OUT, exist_ok=True)
    for query, names in WANT:
        css = get("https://fonts.googleapis.com/css2?family=%s&display=swap" % query).decode()
        urls = re.findall(r"https://fonts\.gstatic\.com[^)]+\.ttf", css)
        seen, ordered = set(), []
        for u in urls:
            if u not in seen:
                seen.add(u); ordered.append(u)
        if len(ordered) < len(names):
            raise SystemExit("expected %d faces for %s, got %d" % (len(names), query, len(ordered)))
        for name, url in zip(names, ordered):
            path = os.path.join(OUT, name)
            if os.path.exists(path) and os.path.getsize(path) > 20000:
                print("have %s" % name); continue
            data = get(url)
            with open(path, "wb") as f:
                f.write(data)
            print("got  %s  %d bytes" % (name, len(data)))
    print("\nfonts in %s" % OUT)

if __name__ == "__main__":
    main()
