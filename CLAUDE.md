# Standing rules for anything produced in this repo

These are Amit's standing rules. They are not suggestions and they are not per task.
They apply to every proposal, business case, deck, one pager and document produced
here or by any of the proposal skills, whichever machine it runs on.

## 1. Attribution: a proposal is from the company, never from Amit

**Never put Amit's name on a proposal.** Not a byline, not a signature, not a contact
card, not a callout label, not a footer. It is always from the company.

Banned on any page of any proposal:

- "Prepared by Amit Mehta", "Prepared by", or any "prepared by" line at all
- "From Amit Mehta", "FROM AMIT MEHTA", "Dr. Amit Mehta"
- "Amit Mehta, MD, FRCP", "Amit Mehta, CEO", "Amit Mehta, CMO"
- Any author credit, byline or named contact block

Write the company instead:

| Instead of | Write |
|---|---|
| `Prepared by Amit Mehta, MD, FRCP · CEO, Amplifier Health` | `Amplifier Health · amplifierhealth.com · partnerships@amplifierhealth.com` |
| `FROM AMIT MEHTA · CEO, AMPLIFIER HEALTH` | `FROM AMPLIFIER HEALTH` |
| `Amit Mehta, CMO` on an Intrinsic contact card | `Intrinsic Imaging` plus its contact routes |

**Enforce it in code.** Any script that renders a proposal must scan its own rendered
output for `Amit`, `Mehta`, `FRCP`, `Prepared by` and `CEO,` and fail loudly if any
appear. Do not rely on remembering. `amplifier/theris/build_theris.py` has the pattern:
extract the text from the finished PDF and assert the tokens are absent before calling
the file done.

**The only carve-out is email.** An outreach email is from a person and keeps its normal
sign-off: "Thanks" / "a" and the real signature block. This rule governs the attached
document, not the message it rides on. Stripping the email signature is a different
mistake and just as wrong.

## 2. Naming: "and", never "x"

A partnership is always named with the word "and". Never "Amplifier x Company",
never "Intrinsic x Company", and never the multiplication sign as a substitute.

Applies to filenames (`Amplifier_and_Theris_Proposal.pdf`), cover top bars, page
footers, email subjects, document titles, folder names and trackers.

## 3. Punctuation: no em dash, ever

No em dash, no en dash in prose, no double dash. Amit does not use them. Restructure
the sentence instead, and do not swap in a comma to fake one. An en dash is acceptable
only as a list bullet glyph, never as punctuation inside a sentence.

Grep the finished text for these characters before calling anything done.

## 4. Line spacing and alignment are checked before anything is delivered

**Never hand over a document whose line spacing has not been checked programmatically.**
Glancing at a thumbnail is not checking. The failure this rule exists to prevent was a
tinted card whose text sat 2.1pt above its own top edge with 12.9pt of dead space below
it: invisible small, glaring at full size, and shipped twice.

Build every vertical measurement from `pdfmetrics.getAscentDescent(font, size)`, never
from a constant that looked right once. A padded box is
`pad + ascent + (n-1)*leading + descent + pad`, with padding measured to the glyph edges
rather than to the baseline. Measuring to the baseline is exactly what produces boxes
crowded at the top and hollow at the bottom. One leading ratio for a whole document,
1.40, because Inter's own minimum line box is about 1.21x and anything under 1.3x pushes
ascenders into the descenders above.

Then check the rendered file. `layout_check()` in `amplifier/theris/build_theris.py` is
the working implementation. On every line it verifies:

1. the line's bounding box does not cross either margin
2. every gap between consecutive baselines in a column is at least 1.30x the type size,
   and all gaps in that column match to within 0.75pt
3. every filled card has positive top padding, within 4pt of its bottom padding

The build exits non-zero on any finding, so a broken layout cannot ship by accident.
Validate changes to the checker by running it against a known-bad file and confirming it
reports the problem. Visual review is in addition to this, never instead of it.

## 5. Customer branding on proposals

Every proposal is rendered in the recipient's own visual identity, pulled from their
live site rather than guessed. Curl the HTML and the stylesheet (a plain fetch strips
CSS, and a React SPA returns only the page title, so check for lazy-loaded route chunks
under `/js/`), rank hex values by frequency, discard Bootstrap and Tailwind stock values
as framework noise, and render their logo from SVG to PNG.

Their brand carries the accents. Amplifier's neutrals carry the body type. Any accent
carrying text clears 4.5:1 contrast. Never invent a hex.

## 6. Where the skills live

The proposal skills are normally loaded from the synced skill store. Cloud sessions only
have a read cache of it, so the copies under `.claude/skills/` here are the durable ones.
When a rule above changes, change it in **both** places: the skill files in this repo and
the canonical synced copies.
