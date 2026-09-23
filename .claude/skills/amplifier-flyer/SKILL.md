---
name: amplifier-flyer
description: Build Amplifier Health flyers, one pagers, partnership proposals and any other Amplifier branded PDF. Use whenever Amit asks for an Amplifier flyer, a one pager, a proposal, a partnership document, a market or use case sheet, or any Amplifier document with design on it. Also use when asked to restyle an existing document into the Amplifier look. This is the only Amplifier design set. Never invent a palette.
---

# Amplifier design set

Two document forms, one system, measured from the shipped originals.

| Form | Pages | Logo | Accent | Hero face |
|---|---|---|---|---|
| **Flyer** | one | green, top left | pink `#FF4AF2` | Cormorant Garamond Light |
| **Proposal** | many | black, top right | none | Inter Bold, very large |

Both sit on the same cream ground `#F0EAE0` and share JetBrains Mono for
every label, Inter for body copy, and Newsreader for serif accents.

## Before you build

1. Fonts. `python3 scripts/fetch_fonts.py` once per machine. It pulls the
   seven faces into `~/.amplifier-fonts`. Override with `AMPLIFIER_FONTS`.
2. Read `references/design-tokens.md`. Every colour, size and coordinate.
3. Copy the matching example, replace the content, keep the call order.
   - `scripts/example_flyer.py` rebuilds Flyer 06 Consumer Wellness exactly.
   - `scripts/example_proposal.py` rebuilds the Nice Healthcare proposal.
4. Render and look at it. `scripts/verify.py out.pdf` writes a PNG per page
   and reports any text crossing the margin.

## The flyer grid is fixed

The flyer is a locked layout, not a flowing one. Positions are absolute
baselines in `FG`. The budget per slot:

| Slot | Budget |
|---|---|
| Hero | two lines of Cormorant 26 across 508pt |
| Subhead | two lines of Newsreader Italic 19 |
| Stats | four cells on a 128pt pitch, value plus a two line label |
| Lede | two lines of Inter 8.8 |
| Blocks | exactly four, each one pink label plus two body lines |
| Code | five lines of JetBrains Mono 7.1 |

Write to the budget. Do not stretch the grid to fit longer copy. Cut the
copy instead. A flyer that runs three lines where the grid says two is the
most common way this goes wrong.

## The proposal flows

Sections are numbered `01 02 03 04 05 07`. **There is no section 06.**
Do not create one.

| Section | Title pattern |
|---|---|
| 01 | What We've Researched On [Partner] |
| 02 | The Opportunity |
| 03 | Integration |
| 04 | Commercial |
| 05 | Why Amplifier Health |
| 07 | Get Started |

A section header is mono, the optional serif subhead sits under it indented
15pt. Bullets take a mono `/` marker, never a dash or a dot.

## Rules that are not negotiable

1. Cream ground on every page, edge to edge. Never white, never dark.
2. Pink appears on flyers only. A proposal with pink in it is wrong.
3. Green appears in the flyer logo only. Never as a text or rule colour.
4. Mono for every label, eyebrow, footer, stat label, code block and CTA.
   Body copy is always Inter. Serif is Cormorant on flyers, Newsreader on
   proposals.
5. Letter spacing on mono labels is real and carries the look. The helper
   handles it, and always resets `Tc` after, because character spacing is
   PDF text state and leaks into everything drawn after it.
6. The logo is a shipped asset in `assets/`, never redrawn or retyped.
7. Every flyer carries the FDA disclaimer in the footer. Check the wording
   against `references/design-tokens.md` before shipping.

## Compliance language

Flyers are marketing. Claim language determines device status, so:

- Say acoustic measurement, vocal biomarker signal, wellness signal,
  observation.
- Never say diagnostic, diagnose, detects disease, screens for, clinical
  grade vital sign, or any disease name paired with a detection verb.
- The footer disclaimer is required, not optional.

## Files

```
SKILL.md
references/design-tokens.md     colours, faces, sizes, the two grids
references/flyer-anatomy.md     slot by slot, with the copy budget
references/proposal-anatomy.md  section order, page furniture, blocks
scripts/fetch_fonts.py          one time font install
scripts/amplifier_design.py     the library. import this, do not fork it
scripts/example_flyer.py        working flyer, matches the original exactly
scripts/example_proposal.py     working proposal
scripts/verify.py               render to PNG and check margins
assets/amplifier_logo_black.png proposal logo
assets/amplifier_logo_green.png flyer logo
```
