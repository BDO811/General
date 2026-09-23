# Amplifier design tokens

Measured from `Amplifier_Flyer_06_Consumer_Wellness.pdf` and
`Amplifier_and_NiceHealthcare_Proposal.pdf`. Do not round these.

## Page

US Letter, 612 x 792.

| | Flyer | Proposal |
|---|---|---|
| Left and right margin | 50 | 54 |
| Text width | 512 | 504 |

## Colour

| Token | Hex | Used for |
|---|---|---|
| `CREAM` | `#F0EAE0` | the ground, every page, edge to edge |
| `BAND` | `#F1DDE1` | pale band behind the flyer hero |
| `BOXFILL` | `#DDDDD3` | proposal callout and stat cell fill |
| `INK` | `#0B0B0A` | proposal headline, rules, mono headers |
| `BLACK` | `#000000` | flyer hero serif, flyer CTA pill |
| `BODY` | `#181716` | flyer body copy |
| `BODY_P` | `#555550` | proposal body copy |
| `ITALIC` | `#32322E` | proposal italic subhead, proposal bullets |
| `ITAL_F` | `#484643` | flyer italic subhead |
| `MUTED` | `#6C6965` | flyer mono labels, disclaimer |
| `MUTED_P` | `#7C7C7B` | proposal mono meta and footer |
| `PINK` | `#FF4AF2` | flyer accent. never in a proposal |
| `GREEN` | `#1E5631` | flyer logo only |
| `HAIR` | `#D8D0C2` | flyer hairline rules |
| `CODEBG` | `#12241A` | flyer sample response block |
| `CODETX` | `#E9E3D5` | code punctuation and values |
| `BTNTX` | `#F0EAE0` | CTA pill label |

## Typefaces

| Role | Face | Notes |
|---|---|---|
| Labels, eyebrows, footers, code, CTA | JetBrains Mono Regular and Bold | always letter spaced |
| Body copy | Inter Regular | flyer 8.8, proposal 9.3 and 9.6 |
| Proposal hero | Inter Bold | auto sized, up to 75.3 |
| Flyer hero and stat numerals | Cormorant Garamond Light | 26 and 14 |
| Proposal serif subhead and numerals | Newsreader Regular | 12.0 and 21.8 |
| Both italic subheads | Newsreader Italic | flyer 19, proposal 18 |

Google's CSS2 endpoint emits the italic face **before** the roman for
Newsreader. `fetch_fonts.py` accounts for it. If serif text comes out
slanted, the two files are swapped.

Descender ratios, needed to convert a measured bbox back to a baseline:

| Face | Descent as em |
|---|---|
| JetBrains Mono | 0.3000 |
| Cormorant Garamond Light | 0.2870 |
| Newsreader | 0.2650 |
| Inter | 0.2412 |

`baseline_rl = 792 - (bbox_bottom_topdown - size * ratio)`

## Letter spacing

Mono labels carry tracking. It is part of the look, not a detail.

| Element | Size | Tracking |
|---|---|---|
| Flyer tagline | 7.5 | 1.0 |
| Flyer eyebrow | 9.5 | 1.1 |
| Flyer section label | 8.3 | 1.0 |
| Flyer block label | 7.8 | 0.9 |
| Flyer stat label | 5.8 | 0.55 |
| Flyer endpoint | 6.8 | 0.5 |
| Flyer CTA label | 8.5 | 1.0 |
| Flyer footer left | 6.8 | 0.8 |
| Flyer footer right | 6.8 | 0.6 |
| Proposal meta and footer | 7.4 to 8.5 | 0.6 to 0.8 |
| Proposal section header | 13.5 | 0.5 |
| Proposal running header | 10.5 | 0.6 |

Character spacing is PDF text state. It persists across text objects.
Always emit `Tc 0` before closing a spaced run or every later line inherits
it. The `Doc.text` helper does this.

## Flyer grid, baselines in ReportLab coordinates

| Element | Value |
|---|---|
| Logo | x 56.6, y 734.6, width 96.6, green |
| Tagline, right aligned at 562 | 742.05 |
| Eyebrow | 706.05 |
| Pink band | y 634.0, height 90.1, full text width |
| Hero line 1 | 675.96, leading 26.0 |
| Subhead line 1 | 616.03, leading 22.8 |
| Stat value | 560.42, columns at 50, 178, 306, 434 |
| Stat label | 543.44, leading 7.2 |
| Pink rule, 1.4pt | 530.2 |
| Section label | 518.19 |
| Lede line 1 | 505.22, leading 10.6 |
| First hairline | 482.0 |
| Block pitch | 52.2. label at rule minus 17.96, body at rule minus 29.98 |
| Code label | 255.39 |
| Code box | y 194.2, height 49.0 |
| Code line 1 | 234.53, leading 8.8, x at 64, 76, 88 |
| CTA pill | y 144.0, 190 x 26, label at x 70 baseline 154.25 |
| Footer rule, 0.75pt | 108.0 |
| Footer line | 94.04 |
| Disclaimer line 1 | 81.99, leading 9.0 |

## Proposal grid

| Element | Value |
|---|---|
| Logo | x 482.3, y 716.9, width 70.8, black |
| Header rule, 0.5pt | 697.0 |
| Cover meta left | 679.52 |
| Cover meta right | 678.82, right aligned at 558 |
| Cover hero line 1 | 559.86, leading 76.8 at full size |
| Cover tagline | 400.27 |
| Cover rule | 384.3 |
| Cover background box | y 266.3, height 102.0 |
| Running header | 706.85 |
| Section header | 679.95, number at x 54, title at x 96 |
| Serif subhead | section minus 16.0, x 69 |
| Bullet marker | x 58, mono 6.6 |
| Bullet text | x 69, Inter 9.3, leading 11.8, gap 4.0 |
| Stat cells | height 54.0, gap 3.0, 2pt black cap rule |
| Footer rule | 52.0 |
| Footer line | 40.05 |

## Required flyer disclaimer

> Amplifier's voice analysis is not FDA approved and is not a diagnostic
> device. Narrative interpretations are provided to qualified care or
> research staff only, never as automated alerts and never directly to the
> person analyzed.

Inter 6.6 in `MUTED`, leading 9.0, under the footer rule.
