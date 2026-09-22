---
name: amplifier-proposal
description: Runs the full Amplifier Health partnership proposal pipeline end-to-end. Use this skill whenever Amit says 'run the proposal pipeline', 'generate proposals', 'generate more proposals', 'run the skill', 'do the next batch', or any variation of generating Amplifier Health partnership proposals, outreach emails, or CRO outreach. This skill handles everything: company research, active-status verification, 3-source email confirmation, PDF generation, visual verification, Gmail draft creation with PDF attachment, and Obsidian tracker update. Always invoke this skill for any Amplifier proposal or outreach generation task.
---

# Amplifier Health Partnership Proposal Pipeline

## What This Skill Does

End-to-end pipeline for generating Amplifier Health partnership proposals:
1. Identify and verify target companies
2. Research each company for proposal content
3. Confirm CEO/founder email against the receiving mail server
4. Generate a 5-page PDF proposal (ReportLab, TEMPLATE 1 / BLACK AND WHITE TEMPLATE)
5. Run visual verification on each cover
6. Copy PDF to the CRO folder
7. Create a Gmail draft with PDF attachment
8. Update the Obsidian contacted_companies.md tracker
9. Surface any flags before sending

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

## Step 3 - Confirm the email address (MANDATORY)

Do not guess a pattern and hope. Ask the receiving mail server.

```bash
python3 ~/.amplifier/verify_email.py \
  --first "Sarah" --last "Chen" --domain "acme.com"
```

It builds the likely addresses in order of how common they are at
venture-backed companies, tests each one, and stops at the first the mail
server accepts. Typical cost is 1 to 3 credits per company.

Act on the result:

| Outcome | What it means | What to do |
| --- | --- | --- |
| `USE: name@domain` | The mail server confirmed that mailbox exists | Use it. **No further sourcing needed.** Record confidence CONFIRMED |
| `CATCH-ALL DOMAIN` | The domain accepts every address, so no test can tell a real mailbox from a typo | **Fall back to the 3-source method below.** Record confidence CATCH-ALL and flag it |
| `NO CANDIDATE CONFIRMED` | Every pattern was rejected | Re-check the domain is right, then fall back to the 3-source method. Flag it |

To check an address a data broker already gave you, rather than searching:

```bash
python3 ~/.amplifier/verify_email.py --email "sarah.chen@acme.com"
```

### Why this replaces three sources when it confirms

Three brokers agreeing is three copies of the same scrape, often years stale.
A `USE:` result is the destination mail server saying that mailbox exists right
now. That is a stronger signal than any number of agreeing directories, and it
is what actually predicts whether the mail lands.

### Fallback: the 3-source method

Use this **only** when the tool reports catch-all or confirms nothing.

Acceptable sources: ZoomInfo, RocketReach, ContactOut, EasyLeadz, LeadIQ, Wiza,
Adapt.io, Growjo, SignalHire, confirmed company email domain pattern.

1. Confirm the company's active email domain
2. Confirm the format pattern (first@, flast@, first.last@)
3. Cross-reference the executive across 3+ sources
4. If all agree, mark CONFIRMED. If they conflict, use the most authoritative
   (ZoomInfo > RocketReach) and note the conflict as a flag

### Never send to an unconfirmed address without saying so

In the Step 8 flag report, every company must carry one of:

- **CONFIRMED** by the mail server, the normal case
- **CATCH-ALL**, address inferred, cannot be verified, delivery not guaranteed
- **3-SOURCE**, verification found nothing, address from directories, lower confidence

A bounced cold email on a new domain costs far more than a credit.

---

## Step 4 — Generate PDF Proposals

Read `references/pdf-template.md` for the full ReportLab code: all helper functions, section structure, cover layout, and the Get Started page spec.

The fastest path: read the MEELA_REFERENCE_TEMPLATE.py from the CRO folder, copy it, and swap in partner-specific content (hero name, callout text, section bullets, stats, email address).

**Hard rules (every proposal, no exceptions):**
- Fonts: Inter-Bold (headings) + Inter-Regular (body) from /tmp/
- `base()` always uses `frac=0.758`
- Cover hero: partner name ALL CAPS, auto-sized via `fit_width()` to fill TW=504
- Callout label: always "WHAT THIS IS"
- Section 01 heading: always "What We Know About [Partner]"
- Section 06 is REMOVED — flow is 01 > 02 > 03 > 04 > 05 > 07 GET STARTED
- No double dashes (--) anywhere. Use em dash (unicode \u2014) or rewrite.
- No mention of a baseline period (Sona-2 produces signal from first call)
- No mention of Winterlight Labs or Sonde Health
- Final page: "07 · GET STARTED" with three resource boxes and day-one table

**Execution:** Write the batch script to mnt/outputs, then run via osascript using the discovered Mac OUTPUT_DIR path.

After generation: copy each PDF to the CRO folder and remove the company from the target list.

---

## Step 5 — Visual Verification (MANDATORY)

For each PDF, generate a thumbnail, copy to outputs, and display with the Read tool:
```bash
qlmanage -t -s 800 -o /tmp/b_thumbs/ '/path/to/Amplifier_x_[Name]_Proposal.pdf' 2>&1
cp /tmp/b_thumbs/*.png '[MAC_OUTPUT_DIR]'
```
Then Read each .png to visually confirm:
- Hero name renders without clipping
- WHAT THIS IS callout text fits cleanly
- No overflow at right margin or bottom

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

Subject: `Amplifier Health x [Partner]`
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
- **Email confidence**: [Company] - CATCH-ALL or 3-SOURCE rather than CONFIRMED

---

## Reference Files

- `references/proposal-sections.md` — Content rules for each of the 5 proposal sections
- `references/pdf-template.md` — Full ReportLab helper functions, cover spec, section flow, Get Started page
- `scripts/create_drafts_template.py` — Gmail API draft creation with PDF attachment
