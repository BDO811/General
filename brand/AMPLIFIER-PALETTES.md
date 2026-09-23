# Amplifier Health, named palettes

Two palettes, same key names, so any document can be rendered in either.

**AMPLIFIER-DESIGN-PALETTE is the default for every document.** The dark cut is
used only when it is asked for by name, or for product UI and dashboards.

## AMPLIFIER-DESIGN-PALETTE

The house palette. This is the default for anything that leaves the building:
flyers, proposals, investor documents, printed collateral.

| Role | Hex | Use |
|---|---|---|
| bg | `#f0eae0` | Bone. The page. |
| surface | `#e9e3d5` | Wash. Panels, stat cells, the highlight block behind display type. |
| surface_2 | `#d8d0c2` | Hairlines, rules, table keylines. |
| panel | `#12241a` | Dark green black. Code blocks and inverted panels. |
| ink | `#181716` | Primary text. |
| ink_2 | `#484643` | Secondary text. |
| muted | `#6c6965` | Microtype, labels, captions, footers. |
| accent | `#1e5631` | Forest green. Primary accent, logo, section labels, eyebrows. |
| accent_2 | `#4caf6e` | Bright green. Secondary accent, syntax highlighting, positive deltas. |
| cta | `#000000` | Pill buttons. |

Type
- Display: Cormorant Garamond Light
- Deck and pull quotes: Newsreader 16pt Italic
- Body: Inter
- Microtype, data, labels, code: JetBrains Mono

Signature moves
- Display type set on the open page. Never a wash block behind a headline.
- Topical imagery at 10% behind the text block, feathered to nothing at the
  edges. Sourced from Pixabay through `fetch_imagery.py`.
- Mono eyebrow in forest green, letter spaced, above the headline.
- Four up stat row closed by a forest green rule.
- Section labels in mono forest green, separated by hairlines.
- Dark green black panel for code.
- Black pill for the call to action.
- No grid overlay.

## AMPLIFIER-DARK-PALETTE

The dark variant. Screens, dashboards, product UI, anything shown on a display
rather than printed.

| Role | Hex | Use |
|---|---|---|
| bg | `#050505` | Near black. The page. |
| surface | `#0a0a0a` | Panels, stat cells, table shading. |
| surface_2 | `#18181b` | Raised rows, callouts. |
| panel | `#26262c` | Hairlines and keylines. |
| ink | `#fafafa` | Primary text. |
| ink_2 | `#b4b4bc` | Secondary text. |
| muted | `#8b8b93` | Microtype, labels, captions. |
| accent | `#22d3ee` | Cyan. Primary accent. |
| accent_2 | `#10b981` | Emerald. Secondary accent, positive deltas. |

Type
- Display and pull quotes: Cormorant Garamond SemiBold
- Body: Inter
- Microtype, data, labels: JetBrains Mono

Signature moves
- Subtle white grid overlay at 3.5%.
- Cyan section numbers and keylines, emerald for deltas and secondary series.
