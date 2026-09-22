# Amplifier Health and Theris

## What is here

- `Amplifier_and_Theris_BusinessCase.pdf` — 7 page business case, rendered in the Theris brand.
- `build_theris.py` — the ReportLab generator. Edit the content in `build()` and re-run.
- `theris-favicon.svg` / `theris-logo.png` — the Theris mark, pulled from theris.ai and
  rendered to PNG for embedding.

## Rebuild

```bash
pip install reportlab pymupdf cairosvg
curl -sL -A "Mozilla/5.0" -o /tmp/Inter-Regular.ttf \
  "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuFuYMZg.ttf"
curl -sL -A "Mozilla/5.0" -o /tmp/Inter-Bold.ttf \
  "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf"
python3 build_theris.py Amplifier_and_Theris_BusinessCase.pdf
```

The script self-checks the rendered text on every run and prints `guard: CLEAN` only when
there is no em dash, no double dash, no multiplication sign, no `_x_` naming and no blank
page. A failure prints what it found.

## Theris brand, as extracted

Source: `https://www.theris.ai/favicon.svg` and `https://www.theris.ai/css/index-x07e0SnK.css`.

| Token | Hex | Where it came from |
|---|---|---|
| primary | `#CB550B` | fill of the logo mark |
| secondary | `#B87A5C` | highest frequency CSS accent, 27 uses |
| tertiary | `#8FA38F` | second accent, sage, 27 uses |
| surface | `#F5E6D3` | cream card fill |
| ink | `#2D3748` | brand dark, used for headings |

Theris's own web fonts are Public Sans and Space Mono. The proposal stays on Inter for
body type so it reads as an Amplifier document carrying Theris's color, not as a forged
Theris document.

## Numbers that still have to come from Theris

1. Real facility count, by setting type.
2. Missed enrollment rate: patients per facility eligible for CPT 99484 or the
   collaborative care codes today and not enrolled.
3. Average clinician caseload and how visit frequency is allocated across risk levels.
