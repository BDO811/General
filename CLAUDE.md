# General

## Amplifier Health documents: palette default

**Every document, deck, flyer, report, chart or page created for Amplifier
Health uses AMPLIFIER-DESIGN-PALETTE by default.** Do not ask which palette.
Do not invent colors. Do not inherit the colors of a source document you were
handed, even when the task is to restyle that document.

- `bg #f0eae0` · `surface #e9e3d5` · `rules #d8d0c2` · `panel #12241a`
- `ink #181716` · `ink_2 #484643` · `muted #6c6965`
- `accent #1e5631` forest · `accent_2 #4caf6e` bright green · `cta #000000`
- Cormorant Garamond Light display, Newsreader 16pt Italic deck and pull quotes,
  Inter body, JetBrains Mono microtype and data

**AMPLIFIER-DARK-PALETTE** (`#050505` ground, `#22d3ee` cyan, `#10b981` emerald)
is the screen variant. Use it only when asked for by name, or for product UI and
dashboards.

Two rules that are not optional: display type is set on the open page, never
on a wash block, and every document carries topical imagery at 10% behind the
text block, sourced from Pixabay via `brand/fetch_imagery.py`.

Definitions, the document kit and worked examples live in `brand/`. The full
system is in `.claude/skills/amplifier-design/SKILL.md`, which loads
automatically for design work.

## Writing

No em dashes, no double dashes, no ellipses in any output. Restructure the
sentence rather than swapping in a comma.

## Repositories in this working directory

- `fidelity-quick-order-overlay` Chrome extension, unrelated to the brand kit.
