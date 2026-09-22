#!/usr/bin/env python3
"""Build the Amplifier Health deck as self-contained HTML.

Produces two themed builds from one template:
  midnight - the near-black presentation palette
  paper    - Amplifier's own brand palette (ink / paper / green), taken from
             the design tokens published on amplifierhealth.com
"""
import base64, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
A = ROOT / "assets"

IMAGES = {
    "__IMG1__": "s1_earth.jpg",   # 01  earth from space
    "__IMG2__": "s2_wave.jpg",    # 02  sound waves
    "__IMG3__": "s3_ai.jpg",      # 03  acoustic / neural
    "__IMG5__": "s5_wave.jpg",    # 04  waveform landscape
}

FONTS = [
    ("Cormorant Garamond", "normal", "CormorantGaramond-normal-400.woff2"),
    ("Cormorant Garamond", "italic", "CormorantGaramond-italic-300.woff2"),
    ("JetBrains Mono", "normal", "JetBrainsMono-normal-400.woff2"),
]

# 17 biomarker signals, from the Amplifier v2 production API.
SIGNS = [
    "Stress", "Anxiety", "Mood Disruption", "Fatigue", "Cognitive Impairment",
    "Elevated Blood Pressure", "Metabolic Load", "Dehydration", "Iron Deficiency",
    "Elevated Androgens", "Airway Obstruction Pattern", "Allergy", "Head Impact",
    "Hypervigilance", "Attention Dysregulation", "Alcohol Use Pattern",
    "Substance Use Pattern",
]

# The 10 "established" conditions (broadest validation evidence). The emerging
# and investigational tiers are deliberately left off the slide.
CONDITIONS = [
    ("Depression", ""), ("Acute Stress", ""),
    ("Depression", "Female"), ("Fatigue", ""),
    ("Anxiety", ""), ("Elevated Blood Pressure", ""),
    ("Anxiety", "Female"), ("COPD", ""),
    ("Cognitive Impairment", ""), ("Traumatic Brain Injury", ""),
]

THEMES = {
    "midnight": dict(
        out="amplifier-deck.html", logo_fill="#ffffff", extra="", tokens="""
  --bg:#050505;
  --surface:rgba(24,24,27,.72);
  --text:#fafafa;
  --muted:rgba(255,255,255,.70);
  --faint:rgba(255,255,255,.42);
  --hair:rgba(255,255,255,.12);
  --hair-strong:rgba(255,255,255,.18);
  --accent:#22d3ee;
  --accent-2:#10b981;
  --bar:linear-gradient(180deg,#22d3ee,#10b981);
  --line:rgba(255,255,255,.055);
  --shade-soft:rgba(5,5,5,.55);
  --shade-strong:rgba(5,5,5,.75);
  --glow-a:rgba(34,211,238,.20);
  --glow-b:rgba(16,185,129,.17);
  --bg-opacity:.10;
  --bg-blend:normal;
  --bg-filter:none;  /* the 8% desaturation is baked into the plates */
  --card:rgba(24,24,27,.55);
  --card-line:rgba(255,255,255,.12);
  --card-text:rgba(255,255,255,.88);
  --card-faint:rgba(255,255,255,.42);
  --card-accent:#10b981;
  --chip-line:rgba(34,211,238,.26);
  --chip-bg:rgba(34,211,238,.055);
  --url-gradient:linear-gradient(95deg,#fafafa 18%,#22d3ee 58%,#10b981 96%);"""),

    # Brand tokens: ink #231200, paper #dbccb1, paper-2 #e6dac4, green #8eff84,
    # tan #b79862, brown #4b2700.
    "paper": dict(
        out="amplifier-deck-brand.html", logo_fill="#231200", tokens="""
  --bg:#dbccb1;
  --surface:#e6dac4;
  --text:#231200;
  --muted:rgba(35,18,0,.72);
  --faint:rgba(35,18,0,.50);
  --hair:rgba(35,18,0,.16);
  --hair-strong:rgba(35,18,0,.26);
  --accent:#4b2700;
  --accent-2:#4b2700;
  --bar:linear-gradient(180deg,#4b2700,#b79862);
  --line:rgba(35,18,0,.07);
  --shade-soft:rgba(219,204,177,.55);
  --shade-strong:rgba(219,204,177,.80);
  --glow-a:rgba(183,152,98,.34);
  --glow-b:rgba(183,152,98,.22);
  --bg-opacity:.12;
  --bg-blend:multiply;
  --bg-filter:grayscale(.92) contrast(1.05);
  --card:#231200;
  --card-line:rgba(219,204,177,.18);
  --card-text:rgba(219,204,177,.92);
  --card-faint:rgba(219,204,177,.54);
  --card-accent:#8eff84;
  --chip-line:rgba(142,255,132,.30);
  --chip-bg:rgba(142,255,132,.07);
  --url-gradient:linear-gradient(95deg,#231200 25%,#4b2700 100%);""",
        # The closer inverts to ink so the deck lands on the brand's dark side,
        # where the green accent actually carries.
        extra="""
.s4{background:#231200}
.s4 .bg{opacity:.18;mix-blend-mode:screen;filter:grayscale(.7) contrast(1.1)}
.s4 .vign{background:
  radial-gradient(120% 90% at 50% 45%,transparent 30%,rgba(8,4,0,.72) 100%),
  linear-gradient(180deg,rgba(8,4,0,.5) 0%,transparent 22%,transparent 74%,rgba(8,4,0,.75) 100%)}
.s4 .gridlines{background-image:
  linear-gradient(to right,rgba(219,204,177,.06) 1px,transparent 1px),
  linear-gradient(to bottom,rgba(219,204,177,.06) 1px,transparent 1px)}
.s4 .glow.g-a{background:radial-gradient(circle,rgba(142,255,132,.15),transparent 68%)}
.s4 .eyebrow{color:#8eff84}
.s4 .eyebrow::before{background:linear-gradient(90deg,#8eff84,transparent)}
.s4 .url{background:linear-gradient(95deg,#dbccb1 16%,#8eff84 60%,#c8f579 96%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.s4 .say{color:#dbccb1}
.s4 .say em{color:#8eff84}
.s4 .note,.s4 .steps{color:rgba(219,204,177,.74)}
.s4 .steps b{color:#8eff84}
.s4 .sig{color:rgba(219,204,177,.56);border-top-color:rgba(219,204,177,.22)}
.s4 .sig b{color:rgba(219,204,177,.92)}
.s4 .sfoot{color:rgba(219,204,177,.5)}
"""),
}


def font_faces() -> str:
    """Inline the latin subsets so the deck renders identically offline and in PDF."""
    out = []
    for family, style, fname in FONTS:
        b64 = base64.b64encode((A / "fonts" / fname).read_bytes()).decode("ascii")
        out.append(
            "@font-face{font-family:'%s';font-style:%s;font-weight:300 700;"
            "font-display:block;src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (family, style, b64)
        )
    return "\n".join(out)


def data_uri(path: pathlib.Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def inline_svg(path: pathlib.Path, fill: str) -> str:
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r'\sid="Layer_1"', "", svg)
    svg = svg.replace('fill="#ffffff"', f'fill="{fill}"')
    return svg.strip()


def build(theme_name: str, theme: dict, template: str, fonts: str) -> pathlib.Path:
    html = (template
            .replace("__THEME__", theme["tokens"])
            .replace("__THEME_EXTRA__", theme["extra"])
            .replace("__FONTS__", fonts))

    for token, name in IMAGES.items():
        src = A / name
        if not src.exists():
            sys.exit(f"missing asset: {src}")
        html = html.replace(token, data_uri(src))

    html = html.replace("__LOGO__", inline_svg(A / "Amplifier_Brandmark_White_RGB.svg",
                                               theme["logo_fill"]))
    html = html.replace("__CHIPS__",
                        "".join(f'<span class="chip">{s}</span>' for s in SIGNS))
    html = html.replace("__CONDITIONS__", "".join(
        '<li><span class="dot"></span>{}{}</li>'.format(
            name, f' <span class="sx">({qual})</span>' if qual else "")
        for name, qual in CONDITIONS))

    leftover = sorted(set(re.findall(r"__[A-Z0-9_]+__", html)))
    if leftover:
        sys.exit(f"[{theme_name}] unsubstituted tokens: {leftover}")

    out = ROOT / theme["out"]
    out.write_text(html, encoding="utf-8")
    print(f"  {theme_name:9s} -> {out.name}  ({out.stat().st_size/1024:.0f} KB)")
    return out


def main() -> int:
    template = (ROOT / "deck.template.html").read_text(encoding="utf-8")
    fonts = font_faces()
    print("building:")
    for name, theme in THEMES.items():
        build(name, theme, template, fonts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
