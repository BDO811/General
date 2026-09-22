# PDF Template — ReportLab Boilerplate

The canonical reference script is at:
`/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/MEELA_REFERENCE_TEMPLATE.py`

Always read that file first. Copy it, swap partner content, and run. Do not rebuild from scratch.

Below is the complete boilerplate for reference and reconstruction if the reference script is unavailable.

---

## Page Geometry

```python
PW, PH = 612, 792   # US Letter
ML = MR = 54
MB = 42
TW = 504            # text width = PW - ML - MR
```

## Color System

Two layers. The Amplifier neutrals are fixed and carry all body type. The partner's
brand, extracted in Step 2.5 of SKILL.md, carries the accents.

### Amplifier neutrals (fixed)

```python
from reportlab.lib.colors import HexColor

BK  = HexColor("#050505")
DK  = HexColor("#1A1A1A")
MED = HexColor("#444444")
MU  = HexColor("#888888")
LT  = HexColor("#BBBBBB")
HLT = HexColor("#DDDDDD")
DV  = HexColor("#D0D0D0")
LB  = HexColor("#F5F5F5")
BOX = HexColor("#0A0A0A")
```

### Partner brand (per proposal, never invented)

```python
BRAND = {
    "primary":   HexColor("#CB550B"),   # logo mark fill, strongest signature
    "secondary": HexColor("#B87A5C"),   # highest-frequency CSS accent
    "tertiary":  HexColor("#8FA38F"),   # second accent
    "surface":   HexColor("#F5E6D3"),   # tinted card background
    "ink":       HexColor("#2D3748"),   # brand dark, used for headings
    "logo_png":  "partner-logo.png",    # rendered from their SVG at 512px
}
```

Where each one goes:

| Element | Color |
|---|---|
| Cover hero, H2 headings | `BRAND["ink"]` |
| Thick cover rule, stat-cell top bars, section rules | `BRAND["primary"]` |
| Section label text, bullet glyphs | `BRAND["secondary"]` |
| Stat cell and resource box fills | `BRAND["surface"]` |
| Callout box fill | `BOX` (dark) with `HLT` label and `LT` body |
| All body copy | `DK` |
| Footer and confidential line | `MU` |

Rules that are not negotiable:
- Every hex traces to the partner's live site or logo file. Never invent one.
- A brand color carrying body text clears 4.5:1 against its background. A brand
  color used only on rules, bars and labels clears 3:1. If an accent is too light to
  carry text, demote it to a rule and set the text in `BK`.
- If the partner has no extractable brand, set every BRAND value to the Amplifier
  neutral equivalent so the template degrades cleanly to monochrome.

## Partner Logo

The mark sits top right in the top bar on every page, and larger on the cover above
the hero. Render it from their SVG first:

```python
import cairosvg
cairosvg.svg2png(url="partner-logo.svg", write_to="partner-logo.png",
                 output_width=512, output_height=512)
```

```python
from reportlab.lib.utils import ImageReader

def logo(c, x, y, size, path):
    """Draw the partner mark preserving aspect ratio. Transparent PNG, so mask='auto'."""
    img = ImageReader(path)
    iw, ih = img.getSize()
    w, h = (size, size * ih / iw) if iw >= ih else (size * iw / ih, size)
    c.drawImage(img, x, y, width=w, height=h, mask="auto")
    return w, h
```

Never stretch the mark, never recolor it, and never place it so it reads as a
co-signature on Amplifier's own wordmark. It is the partner's identity on a document
Amplifier is sending them, not a joint logo lockup.

## Font Registration

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("Inter", "/tmp/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Bold", "/tmp/Inter-Bold.ttf"))
```

## Core Helper Functions

```python
def base(top_pt, size_pt, frac=0.758):
    # ALWAYS use frac=0.758 — never 0.82, 0.88, 0.9688
    return PH - top_pt - size_pt * frac

def draw(c, x, y, text, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, text)

def draw_right(c, x, y, text, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawRightString(x, y, text)

def hrule(c, y, color=DV, thickness=0.4):
    c.setStrokeColor(color); c.setLineWidth(thickness); c.line(ML, y, PW - MR, y)

def thick_hrule(c, y, color=BK, thickness=1.5):
    c.setStrokeColor(color); c.setLineWidth(thickness); c.line(ML, y, PW - MR, y)

def filled_rect(c, x, y, w, h, color):
    c.setFillColor(color); c.rect(x, y, w, h, stroke=0, fill=1)

def section_label(c, y, number, name):
    label = f"SECTION {number}  \u00b7  {name}"
    c.setFont("Inter-Bold", 7.4); c.setFillColor(MU); c.drawString(ML, y, label)

def h2(c, y, text):
    c.setFont("Inter-Bold", 15.1); c.setFillColor(BK); c.drawString(ML, y, text)

def h3(c, y, text):
    c.setFont("Inter-Bold", 11.5); c.setFillColor(DK); c.drawString(ML, y, text)

def body_line(c, y, text, indent=0):
    c.setFont("Inter", 10.1); c.setFillColor(DK); c.drawString(ML + indent, y, text)

def bullet(c, y, text, max_w=None, indent=10, leading=12):
    bx = ML + indent; tx = bx + 9; avail = (max_w or TW) - indent - 9
    c.setFont("Inter-Bold", 7.4); c.setFillColor(MED); c.drawString(bx, y + 2, "\u2013")
    c.setFont("Inter", 10.1); c.setFillColor(DK)
    words = text.split(); line = ""
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, "Inter", 10.1) <= avail:
            line = test
        else:
            c.drawString(tx, y, line); y -= leading; line = word
    if line:
        c.drawString(tx, y, line); y -= leading
    return y

def wrap_text(c, text, font, size, max_w):
    """Wrap text into lines that fit within max_w. Returns list of line strings."""
    words = text.split(); lines = []; line = ""
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, font, size) <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def fit_width(c, text, font, max_w, max_size=72, min_size=20):
    """Find the largest font size at which text fits within max_w."""
    size = max_size
    while size >= min_size:
        if c.stringWidth(text, font, size) <= max_w:
            return size
        size -= 0.5
    return min_size

def callout_box(c, y, label, text, pad_v=10, pad_h=12, line_h=12.5):
    """Dark callout box. text is a single string — auto-wraps."""
    lines = wrap_text(c, text, "Inter", 9.6, TW - pad_h * 2)
    box_h = pad_v + 11 + 6 + len(lines) * line_h + pad_v
    filled_rect(c, ML, y - box_h, TW, box_h, BOX)
    ty = y - pad_v - 7.9 * 0.758
    c.setFont("Inter-Bold", 7.9); c.setFillColor(HLT)
    c.drawString(ML + pad_h, ty, label.upper())
    ty -= 11
    c.setFont("Inter", 9.6); c.setFillColor(LT)
    for line in lines:
        c.drawString(ML + pad_h, ty, line); ty -= line_h
    return y - box_h - 8

def stat_block(c, y, stats):
    """stats = [(number_str, label_str, sublabel_str), ...]"""
    n = len(stats); cell_w = TW / n; bh = 52; by = y - bh
    for i, (num, lbl, sub) in enumerate(stats):
        cx = ML + i * cell_w
        filled_rect(c, cx, by, cell_w - 2, bh, LB)
        c.setStrokeColor(BK); c.setLineWidth(2)
        c.line(cx, y, cx + cell_w - 2, y)
        c.setFont("Inter-Bold", 22); c.setFillColor(BK)
        c.drawString(cx + 8, by + bh - 8 - 22 * 0.758, num)
        c.setFont("Inter-Bold", 7.4); c.setFillColor(DK)
        c.drawString(cx + 8, by + 12, lbl)
        c.setFont("Inter", 7.9); c.setFillColor(MU)
        c.drawString(cx + 8, by + 4, sub)
    return by - 10
```

## Top Bar and Footer (every page)

```python
def top_bar(c, partner_upper, brand):
    # Naming: always AND, never x and never the multiplication sign.
    draw(c, ML, base(76.8, 11.04), f"AMPLIFIER HEALTH AND {partner_upper}",
         "Inter-Bold", 11.04, BK)
    lw, _ = logo(c, PW - MR - 13, base(76.8, 11.04) - 2.5, 13, brand["logo_png"])
    draw_right(c, PW - MR - lw - 7, base(76.8, 7.44),
               "CONFIDENTIAL  \u00b7  FOR AUTHORIZED USE ONLY", "Inter-Bold", 7.44, MU)

def footer(c, page_num, partner_display):
    hrule(c, MB + 10)
    draw_right(c, PW - MR, MB - 2,
               f"Amplifier Health and {partner_display}  \u00b7  Confidential  \u00b7  {page_num}",
               "Inter", 7.44, MU)
```

## Cover Page Layout

```python
def cover_page(c, partner_name, callout_text, brand):
    # Top bar
    top_bar(c)
    # Eyebrow
    draw(c, ML, base(106.8, 8.40),
         "PARTNERSHIP PROPOSAL  \u00b7  APRIL 2026", "Inter-Bold", 8.40, MU)
    # Hero — auto-sized to fill TW
    hero_size = fit_width(c, partner_name.upper(), "Inter-Bold", TW, max_size=72, min_size=20)
    hero_y = base(155, hero_size)
    draw(c, ML, hero_y, partner_name.upper(), "Inter-Bold", hero_size, brand["ink"])
    # Subheading
    sub_size = min(hero_size - 4, fit_width(c, "AMPLIFIER HEALTH PROPOSAL", "Inter-Bold", TW))
    sub_y = hero_y - hero_size * 0.92 - 10
    draw(c, ML, sub_y, "AMPLIFIER HEALTH PROPOSAL", "Inter-Bold", sub_size, MED)
    # Thick rule in the partner's primary brand color
    rule_y = sub_y - sub_size * 0.92 - 20
    thick_hrule(c, rule_y, color=brand["primary"], thickness=2.5)
    # WHAT THIS IS callout
    box_y = rule_y - 14
    callout_box(c, box_y, "WHAT THIS IS", callout_text)
    # Footer
    footer(c, 1)
    c.showPage()
```

## Body Page Section Flow

```python
# At the top of each body page:
top_bar(c)
y = base(106.8, 0) - 8   # first content y

# Section rhythm:
y -= 6
hrule(c, y)
y -= 14
section_label(c, y, "01", "WHAT WE KNOW")
y -= 16
h2(c, y, "What We Know About [Partner]")
y -= 22

for b in bullets:
    y = bullet(c, y, b, leading=12)
    y -= 3   # inter-bullet gap

# Stat block:
y -= 10
y = stat_block(c, y, stats)

# Footer at bottom of every page:
footer(c, page_num)
c.showPage()
```

## Section Numbers and Names

| Section | Label | H2 Pattern |
|---------|-------|------------|
| 01 | WHAT WE KNOW | "What We Know About [Partner]" |
| 02 | THE AMPLIFIER FIT | "How Sona-2 Fits [Partner]" |
| 03 | INTEGRATION | "How It Works" |
| 04 | COMMERCIAL | "Partnership Structure" |
| 05 | WHY AMPLIFIER | "Why Amplifier Health" |
| 07 | GET STARTED | "Everything You Need to Build" |

Section 06 does not exist. Do not create it.

## Get Started Page (Section 07)

See `references/proposal-sections.md` Section 07 for the exact resource box content.

```python
def resource_box(c, y, label, title, desc, box_h=48):
    filled_rect(c, ML, y - box_h, TW, box_h, LB)
    ty = y - 10 - 7.9 * 0.758
    c.setFont("Inter-Bold", 7.9); c.setFillColor(MU)
    c.drawString(ML + 10, ty, label.upper())
    ty -= 13
    c.setFont("Inter-Bold", 11.5); c.setFillColor(BK)
    c.drawString(ML + 10, ty, title)
    ty -= 12
    c.setFont("Inter", 9.6); c.setFillColor(MED)
    c.drawString(ML + 10, ty, desc)
    return y - box_h - 6

def resource_box_half(c, y, x, w, label, title, box_h=48):
    filled_rect(c, x, y - box_h, w, box_h, LB)
    ty = y - 10 - 7.9 * 0.758
    c.setFont("Inter-Bold", 7.9); c.setFillColor(MU)
    c.drawString(x + 10, ty, label.upper())
    ty -= 13
    c.setFont("Inter", 9.6); c.setFillColor(DK)
    # wrap title within width
    lines = wrap_text(c, title, "Inter", 9.6, w - 20)
    for line in lines:
        c.drawString(x + 10, ty, line); ty -= 12
    return y - box_h - 6

def day_one_row(c, y, label, desc, row_h=18):
    hrule(c, y, color=DV, thickness=0.4)
    ty = y - row_h * 0.5 - 10 * 0.758
    c.setFont("Inter-Bold", 9.6); c.setFillColor(BK)
    c.drawString(ML + 8, ty, label)
    c.setFont("Inter", 9.6); c.setFillColor(MED)
    c.drawString(ML + 160, ty, desc)
    return y - row_h
```
