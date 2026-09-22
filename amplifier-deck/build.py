#!/usr/bin/env python3
"""Build a single self-contained HTML deck: inlines Pixabay backgrounds as
base64 and the official Amplifier brandmark as inline SVG."""
import base64, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
A = ROOT / "assets"

IMAGES = {
    "__IMG1__": "s1_earth.jpg",
    "__IMG2__": "s2_wave.jpg",
    "__IMG3__": "s3_ai.jpg",
    "__IMG4__": "s4_freq.jpg",
    "__IMG5__": "s5_wave.jpg",
}

# 17 biomarker signals, pulled live from the Amplifier v2 production API.
SIGNS = [
    "Stress", "Anxiety", "Mood Disruption", "Fatigue", "Cognitive Impairment",
    "Elevated Blood Pressure", "Metabolic Load", "Dehydration", "Iron Deficiency",
    "Elevated Androgens", "Airway Obstruction Pattern", "Allergy", "Head Impact",
    "Hypervigilance", "Attention Dysregulation", "Alcohol Use Pattern",
    "Substance Use Pattern",
]


FONTS = [
    # (family, style, woff2 file) - all three are variable fonts covering 300-700
    ("Cormorant Garamond", "normal", "CormorantGaramond-normal-400.woff2"),
    ("Cormorant Garamond", "italic", "CormorantGaramond-italic-300.woff2"),
    ("JetBrains Mono", "normal", "JetBrainsMono-normal-400.woff2"),
]


def font_faces() -> str:
    """Inline the latin subsets so the deck renders identically offline and in PDF."""
    out = []
    for family, style, fname in FONTS:
        raw = (A / "fonts" / fname).read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        out.append(
            "@font-face{font-family:'%s';font-style:%s;font-weight:300 700;"
            "font-display:block;src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (family, style, b64)
        )
    return "\n".join(out)


def data_uri(path: pathlib.Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def inline_svg(path: pathlib.Path) -> str:
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)          # drop XML prolog
    svg = re.sub(r'\sid="Layer_1"', "", svg)          # avoid id collisions
    return svg.strip()


def main() -> int:
    html = (ROOT / "deck.template.html").read_text(encoding="utf-8")

    for token, name in IMAGES.items():
        src = A / name
        if not src.exists():
            print(f"missing asset: {src}", file=sys.stderr)
            return 1
        html = html.replace(token, data_uri(src))

    html = html.replace("__FONTS__", font_faces())
    html = html.replace("__LOGO__", inline_svg(A / "Amplifier_Brandmark_White_RGB.svg"))
    html = html.replace(
        "__CHIPS__",
        "".join(f'<span class="chip">{s}</span>' for s in SIGNS),
    )

    leftover = re.findall(r"__[A-Z0-9_]+__", html)
    if leftover:
        print(f"unsubstituted tokens: {sorted(set(leftover))}", file=sys.stderr)
        return 1

    out = ROOT / "amplifier-deck.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
