# Amplifier Health Deck

A self contained 4 slide 16:9 deck, built in two themes from one template.
Every font and image is base64 embedded, so each build renders identically in a
browser, offline, and in PDF.

## Themes

| Theme | File | Look |
| --- | --- | --- |
| `midnight` | `amplifier-deck.html` | Near black presentation palette, cyan and emerald accents. |
| `paper` | `amplifier-deck-brand.html` | Amplifier's own brand palette: ink `#231200` on paper `#dbccb1`, with green `#8eff84`, tan and brown. The closing slide inverts to ink. |

The `paper` tokens are the real ones, read from the design tokens published at
`amplifierhealth.com/assets/styles-*.css`, not approximated by eye.

## Files

| File | What it is |
| --- | --- |
| `amplifier-deck.html` | Midnight build. Arrow keys or space to advance. |
| `amplifier-deck-brand.html` | Brand build. |
| `Amplifier-Health-Deck.pdf` | 4 pages, 13.333in x 7.5in. |
| `Amplifier-Health-Deck-Brand.pdf` | Same, brand theme. |
| `deck.template.html` | Source template. Edit this, not the built files. |
| `build.py` | Themes, content data, and asset inlining. |
| `make-pdf.sh` | Re-exports both PDFs. |
| `desaturate.py` | One time asset step, bakes the 8% desaturation into the plates. |
| `shots.sh` | Renders a build's slides to PNG for review. |

## Slides

1. Imagine a technology that could touch every human on the planet.
2. Introducing Amplifier Health, the registered brandmark, and amplifierhealth.com.
3. Sona-2, a Large Acoustic Model, and what 15 seconds of speech returns.
4. try.amplifierhealth.com

## Rebuilding

```bash
python3 build.py                              # template + assets -> both HTML builds
./make-pdf.sh                                 # both PDFs
./shots.sh /tmp/out amplifier-deck-brand.html # per slide PNGs
```

## Notes on content

Slide 3 is not illustrative. The 17 biomarker signals, the 10 established
conditions, and the 8 model pipelines were read from the Amplifier v2 production
API, so the slide matches what the platform actually returns today. Only the
established tier (broadest validation evidence) is shown; the emerging and
investigational tiers are deliberately left off.

## Assets

Backgrounds are Pixabay stock at 10 to 12 percent opacity under a vignette and
grid, multiplied into the paper stock on the brand theme. An 8 percent
desaturation is baked into the plates rather than applied as a CSS filter: a
filter on that layer makes Chrome rasterize the whole background on print, which
tripled the exported PDF.

Both URLs are live anchors, so they stay clickable in the exported PDFs. Typography is Cormorant
Garamond with JetBrains Mono accents, latin subsets only. The logo is the official
`Amplifier_Brandmark_White_RGB.svg` from amplifierhealth.com, recolored to ink for
the brand theme.
