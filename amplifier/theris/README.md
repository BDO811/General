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

## What Theris actually is, read off their own site

Source: the lazy-loaded route chunks behind `theris.ai` (`/js/Home-*.js`,
`Technology-*.js`, `ClinicalServices-*.js`, `About-*.js`, `Team-*.js`). The site is a
React SPA, so a plain fetch returns only the page title. The copy lives in the chunks.

- Geriatric behavioral health delivered into congregate living facilities. Founded as
  Empower Nation, rebranded to Theris. A senior living company, not a general
  behavioral health company.
- Hybrid delivery: a dedicated Care Coordinator on site sets up and facilitates the
  session and handles documentation; the clinician joins by telehealth. Psychiatrists,
  psychologists, nurse practitioners, LCSWs and LPCs.
- Seven active states plus three launching Q1 2026. Oklahoma City, New Jersey,
  Colorado, Ohio, Texas, Pennsylvania, Virginia. In network with all major plans.
- Clinical scope: depression in high acuity patients with PHQ-9 monitoring, anxiety
  and PTSD with GAD-7, dementia related behaviors, mood disorders, substance use,
  adjustment and loss.
- Stated value pillars, which the proposal is organized around: Better Outcomes,
  Maximized Reimbursement, Increased Utilization, Reduced Liability.
- EHR integrations: Athena Health and Point Click Care.
- Positioning: "From Treatment to Outcome", zero staff burden for the operator.

**Scope discrepancy worth resolving.** Launch press described VA community residences,
sober living homes and K-12 schools, and named the VA as a major client. None of that
appears on theris.ai. The proposal is built on the site and flags the gap as an open
item.

## United States only

Theris operates in US states and nowhere else. There is no international section and
there should not be one.

## Numbers that still have to come from Theris

1. Real facility count, by state and by facility type.
2. Missed enrollment rate: residents per facility eligible for CPT 99484 or the
   collaborative care codes today and not enrolled.
3. Average clinician caseload and how visit frequency is allocated across risk levels.
