---
name: amplifier-proposal
description: Runs the full Amplifier Health partnership proposal pipeline end-to-end. Use this skill whenever Amit says 'run the proposal pipeline', 'generate proposals', 'generate more proposals', 'run the skill', 'do the next batch', or any variation of generating Amplifier Health partnership proposals, outreach emails, or CRO outreach. This skill handles everything: company research, active-status verification, 3-source email confirmation, PDF generation, visual verification, Gmail draft creation with PDF attachment, and Obsidian tracker update. Always invoke this skill for any Amplifier proposal or outreach generation task.
---

# Amplifier Health Partnership Proposal Pipeline

## What This Skill Does

End-to-end pipeline for generating Amplifier Health partnership proposals:
1. Identify and verify target companies
2. Research each company for proposal content
3. Confirm CEO/founder email from 3 independent sources
4. Generate a 5-page PDF proposal (ReportLab, TEMPLATE 1 / BLACK AND WHITE TEMPLATE)
5. Run visual verification on each cover
6. Copy PDF to the CRO folder
7. Create a Gmail draft with PDF attachment
8. Update the Obsidian contacted_companies.md tracker
9. Surface any flags before sending

---

## Naming — Hard Rule (No Exceptions, Every Artifact)

**Never write "Amplifier x [Company]". The word is always "and".**

This applies to every artifact the pipeline touches, with no exceptions:

| Artifact | Correct | Never |
|---|---|---|
| PDF filename | `Amplifier_and_[Company]_Proposal.pdf` | `Amplifier_x_[Company]_Proposal.pdf` |
| Cover top bar | `AMPLIFIER HEALTH AND [COMPANY]` | `AMPLIFIER x [COMPANY]` |
| Page footer | `Amplifier Health and [Company]` | `Amplifier Health x [Company]` |
| Email subject | `Amplifier Health and [Company]` | `Amplifier Health x [Company]` |
| Google Doc / business case title | `Amplifier and [Company] Business Case` | `Amplifier x [Company]` |
| Tracker and folder names | `... and ...` | `... x ...` |

Also never use the multiplication sign as a substitute. Before any PDF is
written or any draft is created, grep the generated script and the output filename
for ` x ` and `_x_` and the multiplication sign and fix every hit. Legacy files already on disk that
carry the old `_x_` name are renamed on next touch.

---

## Step 0 — Environment Setup

**Fonts:** The PDF generator requires Inter fonts at `/tmp/`. Check and download if missing:
```bash
ls /tmp/Inter-Regular.ttf 2>/dev/null || curl -L -o /tmp/Inter-Regular.ttf \
  "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.ttf"
ls /tmp/Inter-Bold.ttf 2>/dev/null || curl -L -o /tmp/Inter-Bold.ttf \
  "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.ttf"
```

**Mac path discovery:** The sandbox `/sessions/.../mnt/outputs/` maps to a Mac path needed to execute Python scripts via osascript. Discover it at the start of every new session by writing a unique test file to mnt/outputs and then finding it on the Mac:

```python
# Write a test file to sandbox
with open('/sessions/.../mnt/outputs/findme_UNIQUE.txt', 'w') as f:
    f.write('x')
```
Then osascript:
```applescript
do shell script "find '/Users/amitmehta/Library/Application Support/Claude/local-agent-mode-sessions' -name 'findme_UNIQUE.txt' 2>/dev/null | head -1"
```
Strip the filename to get OUTPUT_DIR.

**Key paths (hardcoded — never change):**
- CRO folder: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/`
- Target list: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/amplifier_target_companies.txt`
- Tracker: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/contacted_companies.md`
- Gmail token: `~/.gmail_mcp_token.json`
- Reference template: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/MEELA_REFERENCE_TEMPLATE.py` (canonical proposal script — copy and adapt for each batch)

---

## Step 1 — Select Target Companies

Read the target list:
```
cat '/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/amplifier_target_companies.txt'
```

If Amit specifies companies, use those. Otherwise select the next uncontacted batch (default 5, ask if he wants more).

**Rule 10 — Active verification (MANDATORY before any proposal):**
Web search each company: `"[Company] acquired closed shutdown 2024 2025 2026"`
Fail conditions: acquired, shut down, merged, bankruptcy, WARN Act layoffs >50%.
If a company fails: remove from target list, note INACTIVE in tracker, select replacement.
Also flag (do not block, but surface at end): pending acquisitions not yet closed, public companies (NYSE/NASDAQ), no funding in 3+ years.

---

## Step 2 — Research Each Company

For each company, gather content for all 5 proposal sections. Read `references/proposal-sections.md` for exact content rules per section.

Key research targets:
- Product description and delivery mechanism (video sessions? coaching calls? app-based?)
- Member/patient volume, employer/payer distribution
- Funding, valuation, current CEO name and title
- Clinical evidence or outcomes data they publish
- The specific audio touchpoint where Sona-2 would operate
- The comorbidity or clinical gap Sona-2 fills for this company
- Any AI or data infrastructure already in place

---

## Step 2.5 — Extract the Partner's Brand (MANDATORY)

Every proposal is rendered in the partner's own visual identity. A monochrome
proposal is no longer acceptable output. Pull the real assets from their live site
rather than guessing at colors.

**1. Fetch the site and its stylesheet.** A plain `WebFetch` strips CSS, so curl the
HTML, find the stylesheet and the icon, and curl those too:

```bash
curl -sL https://[partner-domain] -o site.html
grep -oE '(href|src)="[^"]*\.(css|svg|png|webp)[^"]*"' site.html | sort -u
curl -sL https://[partner-domain]/[stylesheet].css -o site.css
```

**2. Rank the palette by frequency, then discard framework defaults.**

```bash
grep -oE '#[0-9a-fA-F]{6}\b|oklch\([^)]*\)' site.css | sort | uniq -c | sort -rn | head -40
grep -oE '\-\-[a-z0-9-]+:\s*#[0-9a-fA-F]{3,8}' site.css | head -40
```

Throw out Bootstrap and Tailwind stock values (`#0066cc`, `#28a745`, `#dc3545`,
`#6c757d`, `#f8f9fa`, `#e9ecef`, `#adb5bd`, `#495057`) — they are framework noise, not
brand. What survives at high frequency, especially inside `--color-*` custom
properties or Tailwind arbitrary classes like `.bg-\[\#B87A5C\]`, is the real palette.

**3. Take the logo color from the logo, not the CSS.** The mark's own fill is usually
the truest primary. Fetch and render it:

```bash
curl -sL https://[partner-domain]/favicon.svg -o partner-logo.svg
python3 -c "import cairosvg; cairosvg.svg2png(url='partner-logo.svg', write_to='partner-logo.png', output_width=512, output_height=512)"
```

Read the rendered PNG with the Read tool and confirm it is the real mark, not a
placeholder. Sample the dominant fill with PIL if the SVG is complex.

**4. Record the brand block** and carry it into the build script:

```python
BRAND = {
    "primary":   HexColor("#CB550B"),   # logo mark fill — strongest signature
    "secondary": HexColor("#B87A5C"),   # highest-frequency CSS accent
    "tertiary":  HexColor("#8FA38F"),   # second accent
    "surface":   HexColor("#F5E6D3"),   # tinted card background
    "ink":       HexColor("#2D3748"),   # brand dark, used for headings
    "logo_png":  "partner-logo.png",
}
```

**Contrast check before you build.** Any brand color carrying body text must clear
4.5:1 against its background, and a color used only for rules, bars and labels must
clear 3:1. If a brand accent is too light to carry text, use it for rules and accent
bars only and set the text in `BK`. Never ship an unreadable page to defend a hex code.

**If the site yields nothing usable** (image-only site, no stylesheet, palette is all
framework defaults), say so and fall back to the monochrome template rather than
inventing a palette.

---

## Step 3 — Verify Email Address (MANDATORY — 3 sources)

Never use an email without confirmation from at least 3 independent sources.

Acceptable sources: ZoomInfo, RocketReach, ContactOut, EasyLeadz, LeadIQ, Wiza, Adapt.io, Growjo, SignalHire, confirmed company email domain pattern.

Process:
1. Confirm the company's active email domain
2. Confirm the email format pattern (first@, flast@, first.last@)
3. Cross-reference the specific executive's email across 3+ sources
4. If all 3 agree: mark CONFIRMED. If sources conflict: use most authoritative (ZoomInfo > RocketReach) and note the conflict as a flag.

---

## Step 4 — Generate PDF Proposals

Read `references/pdf-template.md` for the full ReportLab code: all helper functions, section structure, cover layout, and the Get Started page spec.

The fastest path: read the MEELA_REFERENCE_TEMPLATE.py from the CRO folder, copy it, and swap in partner-specific content (hero name, callout text, section bullets, stats, email address).

**Hard rules (every proposal, no exceptions):**
- Fonts: Inter-Bold (headings) + Inter-Regular (body) from /tmp/
- The partner's brand is applied throughout, per the BRAND block from Step 2.5: their
  logo mark on the cover and in the top bar, `primary` on the thick cover rule and
  stat-block accent bars, `ink` on the hero and H2 headings, `surface` as the tint
  behind stat cells and resource boxes. Amplifier's own identity stays in the
  wordmark and the body type; the partner's identity carries the color.
- Never invent a partner color. Every hex in the BRAND block traces to their live
  site or their logo file, and any accent carrying body text clears 4.5:1 contrast.
- `base()` always uses `frac=0.758`
- Cover hero: partner name ALL CAPS, auto-sized via `fit_width()` to fill TW=504
- Callout label: always "WHAT THIS IS"
- Section 01 heading: always "What We Know About [Partner]"
- Section 06 is REMOVED — flow is 01 > 02 > 03 > 04 > 05 > 07 GET STARTED
- No double dashes (--) anywhere, and no em dash or en dash either. Amit never uses
  them. Restructure the sentence instead, and do not swap in a comma to fake one.
  Grep the finished text for the em dash and en dash characters before shipping.
- No mention of a baseline period (Sona-2 produces signal from first call)
- No mention of Winterlight Labs or Sonde Health
- Final page: "07 · GET STARTED" with three resource boxes and day-one table

**Execution:** Write the batch script to mnt/outputs, then run via osascript using the discovered Mac OUTPUT_DIR path.

After generation: copy each PDF to the CRO folder and remove the company from the target list.

---

## Step 5 — Visual Verification (MANDATORY)

For each PDF, generate a thumbnail, copy to outputs, and display with the Read tool:
```bash
qlmanage -t -s 800 -o /tmp/b_thumbs/ '/path/to/Amplifier_and_[Name]_Proposal.pdf' 2>&1
cp /tmp/b_thumbs/*.png '[MAC_OUTPUT_DIR]'
```
Then Read each .png to visually confirm:
- Hero name renders without clipping
- WHAT THIS IS callout text fits cleanly
- No overflow at right margin or bottom
- The partner's logo renders sharp, correctly proportioned, and not stretched
- Brand colors match the BRAND block and every text run is comfortably legible
- The word "and" appears everywhere the partnership is named. No " x ", no `_x_`,
  no multiplication sign anywhere on any page or in the filename

---

## Step 6 — Create Gmail Drafts

Read `scripts/create_drafts_template.py` for the Gmail API pattern (MIMEMultipart + MIMEApplication for PDF attachment).

**Email structure — fixed elements never change:**

Salutation: `[First name] -`

Opening paragraph (exact, word for word):
"I wanted to introduce you to our novel acoustic frontier foundation model - Sona-2. We've built what is the first and largest frontier acoustic foundation model that perceives physicality in the voice to detect biomarkers - depression, anxiety, cognitive decline, respiratory, cardiac - all from the audio itself without any friction and non invasively."

Middle paragraph (company-specific, ~50 words):
One concrete paragraph on why this company specifically. Focus on the audio touchpoint that already exists in their product, the clinical signal Sona-2 extracts, and why there is zero UX disruption. No lists. No features. Founder-to-founder tone. Amit drops apostrophes (dont, cant, lets) — preserve this in the fit paragraph.

Closing (exact):
"I've attached a short proposal. Happy to jump on a call if it's useful — or feel free to delete if it doesn't fit."

Sign-off:
```
Thanks
a

Amit Mehta, MD, FRCP
e: amit@amplifierhealth.com
```

Subject: `Amplifier Health and [Partner]`
From: always `amit@amplifierhealth.com`
Attachment: the matching PDF from the CRO folder (not from outputs)

---

## Step 7 — Update Obsidian Tracker

File: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/contacted_companies.md`

Two updates:
1. Increment `## CONTACTED (N total)` header count
2. Insert a new Batch section immediately before `## EXCLUDED`:

```markdown
### Batch N — [Month Day, Year]
- Company 1
- Company 2 (flag note if applicable)

---

```

---

## Step 8 — Surface Flags and Report

Report concisely at the end. Lead with what's done:

"N drafts in Gmail. N PDFs in CRO. Tracker updated to N total."

Then flags (if any):
- **Pending acquisition**: [Company] — [deal details, expected close]
- **Public company**: [Company] (NYSE/NASDAQ:[ticker]) — partnership route more formal
- **No recent funding**: [Company] — no raise since [year]
- **Email confidence**: [Company] — sources conflicted, used [source]

---

## Reference Files

- `references/proposal-sections.md` — Content rules for each of the 5 proposal sections
- `references/pdf-template.md` — Full ReportLab helper functions, cover spec, section flow, Get Started page
- `scripts/create_drafts_template.py` — Gmail API draft creation with PDF attachment
