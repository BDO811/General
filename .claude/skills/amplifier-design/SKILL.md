---
name: amplifier-design
description: The Amplifier Health design system and its two named palettes. AMPLIFIER-DESIGN-PALETTE is the DEFAULT for every document Amit creates, always, unless he names the other one. Use this skill whenever creating, restyling or reviewing any Amplifier Health visual artifact: a PDF, flyer, one pager, proposal, investor document, deck, report, memo, chart, dashboard or HTML page. Also use it when Amit says "the usual palette", "our palette", "the design palette", "the dark palette", "make it on brand", "use the amplifier design set", or asks what the brand colors or fonts are.
---

# Amplifier Health design system

## The default is not a choice

Every document starts in **AMPLIFIER-DESIGN-PALETTE**. Do not ask which palette
to use. Do not invent a palette. Do not carry over the colors of a document you
were handed, even when restyling it.

Use **AMPLIFIER-DARK-PALETTE** only when Amit names it, or when the artifact is
a screen surface (product UI, dashboard, terminal) rather than a document.

## AMPLIFIER-DESIGN-PALETTE

The house palette. Bone ground, forest green accent, warm black ink.

| Role | Hex | Use |
|---|---|---|
| bg | `#f0eae0` | Bone. The page. |
| surface | `#e9e3d5` | Wash. Panels, stat cells, the block behind display type. |
| surface_2 | `#d8d0c2` | Hairlines, rules, table keylines. |
| panel | `#12241a` | Dark green black. Code blocks and inverted panels. |
| ink | `#181716` | Primary text. |
| ink_2 | `#484643` | Secondary text. |
| muted | `#6c6965` | Microtype, labels, captions, footers. |
| accent | `#1e5631` | Forest green. Logo, section labels, eyebrows, keylines. |
| accent_2 | `#4caf6e` | Bright green. Syntax, secondary series, positive deltas. |
| cta | `#000000` | Pill buttons. |

Type
- Display: **Cormorant Garamond Light**
- Deck and pull quotes: **Newsreader 16pt Italic**
- Body: **Inter**
- Microtype, data, labels, code: **JetBrains Mono**

Signature moves
- Every document opens on the brand cover. See **Cover** below.
- Display type sits on the **open page**. Never put a wash block, a highlight
  or any panel behind a headline. The hero line is set on bare paper.
- Every document carries **topical imagery at 10% behind the text block**,
  feathered to nothing at every edge so it dissolves into the sheet rather
  than sitting in a visible box. See **Imagery** below.
- Mono eyebrow in forest green, letter spaced, above the headline.
- Four up stat row, each cell closed by a forest green rule on top.
- Section labels in mono forest green between hairlines: `01  ·  THE SLOPE`.
- Dark green black panel for code.
- Black pill for the call to action.
- Serif italic pull quote anchored above the footer to land the page.
- No grid overlay. That belongs to the dark cut.

## AMPLIFIER-DARK-PALETTE

Screens only. `#050505` ground, `#0a0a0a` surface, `#18181b` raised, `#26262c`
keylines, `#fafafa` / `#b4b4bc` / `#8b8b93` ink, `#22d3ee` cyan accent,
`#10b981` emerald secondary. Cormorant Garamond SemiBold for display, Inter for
body, JetBrains Mono for data. Subtle white grid overlay at 3.5%.



## Cover

Every document opens on the brand cover. It is unnumbered and carries no page
chrome: centred logo, the company name in display type, the document's topic
under it in forest green, the try link at the foot.

```python
d.cover(topic="Regulatory Approach", date="September 2026")
d.end_page()
```

The topic is the document's subject in title case, set under `Amplifier Health`
so the cover reads as one title: Amplifier Health, Regulatory Approach. The
`confidential` string the document was built with prints at the very bottom, so
an internal document says INTERNAL USE ONLY there without any extra argument.
The try link is `try.amplifierhealth.com`, set with the host in the accent, the
way the deck sets it. Do not change it per document.

## Imagery

Every document gets a backdrop image chosen for its subject, laid in at 10%
behind the text block. This is a house signature, not a decoration to skip.

Source it from **Pixabay** (free licence, no attribution required):

```bash
export PIXABAY_API_KEY=...        # free key at pixabay.com/api/docs
python3 brand/fetch_imagery.py <slug> "<query>"
```

Then in the document:

```python
d.set_backdrop("brand/assets/imagery/<slug>.jpg", alpha=0.10)
```

`set_backdrop` composites the image against the page colour in advance, so the
PDF carries no transparency group and the backdrop prints exactly as it screens.
It feathers to the page colour on all four edges.

Choosing the image
- Abstract and textural wins. At 10% behind body copy, anything with faces,
  hard edges, small detail or text in it turns to grey noise.
- It must read as subject matter, not stock. Voice work gets waveforms and
  spectra. Regulatory work gets architecture and columns. Growth work gets
  abstract line and field.
- Landscape orientation, 1920px wide minimum.
- Check legibility on the finished page before shipping. Body copy over the
  backdrop must be as readable as body copy over bare paper. If it is not,
  the image is too busy, not the opacity too high.

## Never

- A highlight or wash block behind display type.
- Em dashes, double dashes or ellipses, anywhere, in any document.
- A dash as a list marker. The bullet is a small square in the accent.

## How to build

The palettes and the document kit live in `brand/` at the repo root.

```bash
python3 brand/fetch_fonts.py          # once, if brand/fonts is empty
```

```python
import sys; sys.path.insert(0, "brand")
from amplifier_doc_kit import AmplifierDoc

d = AmplifierDoc("out.pdf", title="Whatever it is")   # design palette by default
d.new_page(1, 3)
d.eyebrow("SECTION LABEL  ·  SEPTEMBER 2026")
d.hero("The one line that matters.")
y = d.para(d.ML, 604, [("Body copy with ", "r"), ("emphasis", "b"),
                       (" and an ", "r"), ("accent", "c"), (".", "r")])
y = d.stat_cells(y - 14, [("27.0", "%", "LABEL LINE ONE", "LABEL LINE TWO")])
d.pullquote("Read it this way", "The sentence you want them to remember.")
d.end_page()
d.save()
```

Components: `eyebrow`, `hero`, `para`, `section_head`, `stat_cells`,
`pullquote`, `table_header`, `table_row`, `image_panel`, `strip`, `rule`,
`rect`, `draw`, `draw_right`, `tracked`, `wrap_plain`.

Paragraph styles: `r` body, `b` emphasis, `c` accent, `e` secondary accent.

For charts, read the palette rather than hard coding colors:

```python
from amplifier_palettes import get
P = get()                    # AMPLIFIER-DESIGN-PALETTE
```

Chart rules: panel on `surface`, gridlines on `surface_2`, primary series on
`accent`, secondary on `accent_2`, the de-emphasised series on `muted`, line
overlays on `ink`. Tick labels and legends in JetBrains Mono at 6pt in `muted`.

## Worked example

`brand/examples/token_run_rate.py` builds a five page document end to end and
renders in either palette from the same source:

```bash
cd brand/examples
python3 token_run_rate_charts.py && python3 token_run_rate.py
python3 token_run_rate_charts.py AMPLIFIER-DARK-PALETTE && python3 token_run_rate.py AMPLIFIER-DARK-PALETTE
```

## House writing rules that travel with the design

No em dashes, no double dashes, no ellipses, anywhere. Restructure the sentence
instead, and do not substitute a comma for the dash you removed.

## Vertical rhythm

Spacing is checked line by line, not eyeballed once. `def_row` fixes the
rhythm so every row in every document measures the same: the keyline sits
18pt above the title baseline and 14pt below the previous row's last line,
so it reads as a separator between rows rather than a hat on the next title.
Use `d.rows_start(y, "para" | "label" | "head")` to place the first row of a
run, rather than guessing an offset. After building, render every page and
look at it. Overlaps and cramped blocks are defects, not taste.
