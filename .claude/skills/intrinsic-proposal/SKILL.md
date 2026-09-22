---
name: intrinsic-proposal
description: Finds a target company (if none is named) and generates a professional 3-page Intrinsic Imaging partnership proposal PDF for it, then creates a Gmail draft with the proposal attached. Use this skill whenever Amit says 'generate a proposal', 'run the proposal', 'create an Intrinsic proposal', names a company they want to pitch, or asks to 'find a company and pitch them' with no company specified. Handles prospect discovery (when needed), company research, PDF generation, visual verification, and Gmail draft creation end-to-end.
---

# Intrinsic Imaging Partnership Proposal Pipeline

## What This Skill Does

End-to-end pipeline for generating Intrinsic Imaging partnership proposals:
0. Find a target company, if none was given (via prospect discovery)
1. Research the target company
2. Populate the 3-page PDF template with company-specific content
3. Generate the PDF (ReportLab, Intrinsic Imaging Design System v2 visual style)
4. Visually verify all pages with two independent renderers
5. Copy PDF to the Proposals folder
6. Create a Gmail draft with the PDF attached

---

## Step 0 — Environment Setup

**Mac path discovery:** The sandbox `/sessions/.../mnt/outputs/` maps to a Mac path needed to run Python scripts via osascript. Discover it at the start of every session:

```python
# Write a sentinel file from bash
with open('/sessions/.../mnt/outputs/findme_UNIQUE.txt', 'w') as f:
    f.write('x')
```
Then osascript:
```applescript
do shell script "find '/Users/amitmehta/Library/Application Support/Claude/local-agent-mode-sessions' -name 'findme_UNIQUE.txt' 2>/dev/null | head -1"
```
Strip the filename to get OUTPUT_DIR (Mac path to outputs).

**Key paths (stable — do not use ephemeral per-session paths):**
- Template script (canonical, v2): `/Users/amitmehta/Library/CloudStorage/GoogleDrive-mehta@helix.harvard7.net/My Drive/1 Ventures/Acquired Imaging/INTRINSIC_PROPOSAL_TEMPLATE.py`
- Logo asset: `.../Acquired Imaging/intrinsic_logo.png`
- Fonts: `.../Acquired Imaging/fonts/` (IBM Plex Sans + IBM Plex Mono, Regular/Medium/SemiBold/Bold — downloaded from the official IBM/plex GitHub repo, not the Mac system fonts)
- Proposals folder: `.../Acquired Imaging/Proposals/`
- Gmail account for drafts: `mehta@helix.harvard7.net` via the Gmail API OAuth token at `/Users/amitmehta/.gmail_mcp_token.json` — see Step 6. Never `amplifier-gmail-mcp` (that's `.gmail_mcp_token_amplifier.json` / `amit@amplifierhealth.com`, a different account reserved for the Amplifier Health proposal skill) and never raw IMAP (breaks HTML rendering, see Step 6).

**Design system (v2 — confirmed 2026-07-02 against the Intrinsic Imaging Design System at claude.ai/design, id db8d4b3e-a7c2-4a0d-a674-6179e2fb77aa):**
- Typography: IBM Plex Sans (body/headings — Regular 400 / Medium 500 / SemiBold 600 / Bold 700), IBM Plex Mono (eyebrows, section labels, data, "CONFIDENTIAL" line, mono accents).
- Colors — Brand/Intrinsic Blue: `#EAF2FB`(50) → `#1E6FB8`(500, interactive) → `#0A2540`(900, navy ink). Accent/Diagnostic Teal: `#0E9AA6`(500) — reserved, not currently used in the proposal template, available for future AI/data-heavy sections. Neutrals/Cool Slate: `#F6F8FB`(50) → `#131A22`(900).
- Hero and H2 headings render in Brand-900 navy (`#0A2540`), not black.
- Thick cover rule and stat-block accent bars render in Brand-500 (`#1E6FB8`).
- Callout boxes ("WHAT THIS IS" / "THE FIT") are light rounded cards — Brand-50 background, Brand-200 hairline border, 10pt corner radius — NOT solid black/near-black boxes. Label text is Brand-700 mono uppercase; body text is Slate-800. This was a deliberate legibility fix: the v1 template used light-gray text (`#BBBBBB`) on a near-black box (`#0A0A0A`), which read as low-contrast/hard-to-read even though it technically passed contrast ratio checks. Do not regress to a dark box.
- Stat blocks and the contact card are also rounded, tinted cards (Brand-50 / Slate-50 respectively) with a short colored top accent bar, not flat boxes with a black top rule.
- "CONFIDENTIAL · FOR AUTHORIZED USE ONLY" and the footer render in Slate-500, IBM Plex Mono / Plex respectively — not generic gray Helvetica.

**Hard rule — always regenerate, never binary-overlay a finished PDF.** If a change (e.g. swapping the logo) needs to reach PDFs that already exist in the Proposals folder, rebuild each one fresh by calling `build()` in the template module with that company's stored content — do not use PyMuPDF/`fitz` to draw over or `doc.save(garbage=..., deflate=...)` an already-rendered PDF. Resaving a PDF that has embedded subsetted fonts through fitz's garbage-collector has previously produced files that rendered correctly in PyMuPDF and Poppler but corrupted small embedded-font text in at least one stricter viewer. Regenerating from the ReportLab template avoids this class of bug entirely and is not meaningfully slower.

---

## Step 0.5 — Find the Target (only if no company name was given)

If Amit named a specific company, skip this step and go straight to Step 1.

If no company was named, run prospect discovery inline, using the same methodology as the intrinsic-prospect-finder skill:

**Phase A — Discovery.** Search all four source types in parallel, aim for 20-30 raw candidates:
- ClinicalTrials.gov: active Phase 2/3 trials with imaging endpoints and no imaging core lab named
- Funding news: recently funded biotech, AI imaging, and medical device companies (Series A/B/C, last 18 months)
- FDA databases: AI/ML device list and 510(k)/IDE filings with imaging endpoints
- Scientific literature (bioRxiv/medRxiv/PubMed): imaging validation studies with industry author affiliations

Prospect types:
- **Type A (pharma/biotech):** Phase 2/3 trial with imaging as primary/key secondary endpoint, no imaging CRO named
- **Type B (AI/digital health):** AI imaging product needing an FDA MRMC reader study; non-US company with home-market clearance pursuing US FDA is a strong signal
- **Type C (medical device):** Non-AI device needing imaging performance/safety data for IDE, 510(k), or PMA
- **Type D (international):** Any non-US pharma/device/AI company needing US-based imaging expertise for FDA submission

**Phase B — Research each candidate.** For each: company, type, product/program, imaging need, modality, indication, regulatory/trial status, funding, prior imaging CRO (if any), key contact.

**Phase C — Score out of 10:**
| Signal | Points |
|--------|--------|
| Active trial or regulatory submission with imaging as a primary endpoint | +3 |
| Recent funding ($5M+) in last 18 months | +2 |
| No named imaging CRO in public record | +2 |
| Small-to-mid size company (not large pharma / OEM with internal core lab) | +2 |
| International company needing US-based imaging expertise | +1 |

Score 7-10 = Tier 1. Take the single highest-scoring Tier 1 company as the target and proceed to Step 1 with that company name.

(Skip building the full prospect spreadsheet and skip drafting the finder's own outreach email — this pipeline produces a fuller proposal + Gmail draft downstream in Step 6.)

**Exclusions:** large pharma (Pfizer, Roche, Novartis, AZ, BMS, etc.), large imaging OEMs (GE, Siemens, Philips, Canon), companies with a named imaging CRO already, companies not verifiably active in the last 12 months, and any company where Intrinsic already has an active relationship (e.g. Barreleye).

Report to Amit which company was selected and why (score + signals) before continuing.

---

## Step 1 — Research the Company

Web search the company to gather content for all 4 proposal sections. Target information:

- What the company does — product description in one declarative sentence
- Key clinical or regulatory milestone (CE mark, IND, FDA clearance, Phase 2, NDA)
- Distribution model, customer base, or market context
- Clinical evidence, published outcomes, or peer-reviewed validation
- The specific imaging endpoint or regulatory gap where Intrinsic adds value
- CEO or primary BD contact name and email

**Active verification (mandatory):** Search `"[Company] acquired closed shutdown 2025 2026"`. Skip any company that has been acquired, shut down, or merged. If this was a Step 0.5 auto-selected target and it fails verification, drop it and select the next-highest-scoring Tier 1 candidate.

---

## Step 2 — Populate the Template

Import the canonical template as a module and call `build()` with keyword content — do not hand-edit constants at the top of a copied script (that was the v1 pattern; v2 is parameterized):

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location(
    "tmpl",
    "/Users/amitmehta/Library/CloudStorage/GoogleDrive-mehta@helix.harvard7.net/My Drive/1 Ventures/Acquired Imaging/INTRINSIC_PROPOSAL_TEMPLATE.py",
)
m = importlib.util.module_from_spec(spec)
sys.modules["tmpl"] = m
try:
    spec.loader.exec_module(m)
except FileNotFoundError:
    pass  # the module's own __main__ block tries a placeholder path; ignore

m.build(
    "[MAC_OUTPUT_DIR]/Intrinsic_and_[Company]_Proposal.pdf",
    partner_upper="COMPANY NAME",              # ALL CAPS for cover hero
    partner_display="Company Name",            # Mixed case for headings
    callout_text=(
        "[Company] is [what they do and why it matters]. "
        "Intrinsic Imaging provides independent, regulatory-grade imaging core laboratory "
        "services to support [Company]'s clinical program from study design "
        "through regulatory submission."
    ),
    company_bullets=[
        "[Declarative sentence about the product or platform].",
        "[Key clinical or regulatory milestone].",
        "[Distribution model, customer base, or market context].",
        "[Clinical evidence or published outcomes].",
        "[Specific imaging endpoint or regulatory need where Intrinsic adds value].",
    ],
    fit_text=(
        "[Company]'s program requires [specific imaging endpoint or study type]. "
        "Intrinsic Imaging has designed and executed exactly this type of study, "
        "providing the independent blinded review and regulatory documentation "
        "required for [FDA 510(k) / De Novo / NDA / PMA / CE mark] submission."
    ),
    stats=[
        ("[N]+", "TRIALS SUPPORTED", "Across All Modalities"),
        ("[N]+", "COUNTRIES", "Active Global Network"),
        ("[N]+", "PHYSICIAN READERS", "Qualified Across Specialties"),
    ],
    contact_phone="[+1 xxx xxx xxxx]",   # real number if known, else this placeholder
)
```

**Section 02 always includes the "Modalities and Therapeutic Areas" block** (standardized 2026-07-02 — previously optional/only on 2 of 8 proposals, now default on all). Pass `modalities=[...]`, `therapeutic_areas=[...]`, and `compliance_note="..."` as additional keyword args every time; the template renders this two-column sub-section on page 2 whenever they're present. Standard values (reuse verbatim unless the company's modality mix is genuinely different):

```python
modalities = ["CT, MRI, and PET/CT", "Digital mammography and tomosynthesis",
              "X-ray, ultrasound, and echocardiography", "Digital pathology and whole slide imaging"]
therapeutic_areas = ["Oncology and hematology", "Neurology and neurodegenerative disease",
                      "Cardiology and cardiovascular disease", "Musculoskeletal and rheumatology"]
compliance_note = ("Every reader study and blinded image review runs on GCP and 21 CFR Part 11 compliant "
    "systems, with full audit trail documentation supporting FDA, EMA, and other global regulatory submissions.")
```

`contact_name`, `contact_email`, and `contact_web` default to Amit's standard Intrinsic contact block and normally don't need to be passed. **`contact_phone` should be Amit's real number, `+1 210 883 5709`, on every proposal** — do not use the `[+1 xxx xxx xxxx]` placeholder going forward.

**Section 01 voice rules:**
- Declarative statements only. Subject + verb + object. Active voice.
- Facts that are commercially or clinically relevant to the Intrinsic fit.
- No CEO names, no funding amounts, no founding year. Every bullet is about the product.

---

## Step 3 — Generate the PDF

Run the populated call via osascript:

```applescript
do shell script "cd '[MAC_OUTPUT_DIR]' && python3 [your_build_script].py 2>&1"
```

Expect stdout `PDF written: [path]`.

---

## Step 4 — Visual Verification (MANDATORY, two renderers)

Render every page with **both** PyMuPDF and Poppler (`pdftoppm`) — they use different rendering engines and have caught real font/structure bugs that only one of the two exposed:

```applescript
do shell script "cd '[MAC_OUTPUT_DIR]' && python3 -c \"import fitz; doc = fitz.open('Intrinsic_and_[Company]_Proposal.pdf'); [doc[i].get_pixmap(dpi=150).save(f'verify_fitz_p{i+1}.png') for i in range(len(doc))]; print('done')\" && pdftoppm -png -r 150 'Intrinsic_and_[Company]_Proposal.pdf' verify_poppler 2>&1"
```

Read each `.png` from both sets with the Read tool and confirm:
- Hero name renders without clipping
- Callout card text is fully legible (dark text on the light Brand-50 card, not light-on-dark)
- No text overflows right margin or bottom
- No collision with footer
- The two renderers agree — any visual difference between the PyMuPDF and Poppler output for the same page is a signal something is structurally wrong and must be root-caused before shipping, not papered over

If any issue found: fix the script and regenerate before proceeding. Note: `pdftoppm` and `qpdf` are available in the Cowork sandbox (`mcp__workspace__bash`) if you need to cross-check outside of osascript.

---

## Naming and Partner Brand — Hard Rules

**Never write "Intrinsic x [Company]". The word is always "and".** This covers the PDF
filename (`Intrinsic_and_[Company]_Proposal.pdf`), the cover top bar, every page
footer, the email subject, and the Proposals folder copy. The multiplication sign is
not an acceptable substitute either. Grep the build script and the output filename for
` x `, `_x_` and the multiplication sign before rendering.

**Carry the prospect's own brand into the proposal.** Before building, pull their live
site and stylesheet with curl, rank the hex values by frequency, discard Bootstrap and
Tailwind stock values, and render their logo from SVG to a 512px PNG. Apply their
primary to the cover rule and stat-block accent bars, their brand dark to the hero and
H2 headings, and their tinted surface to cards, keeping the Intrinsic navy and blue for
Intrinsic's own wordmark and identity. Every hex traces to their site or logo file, and
any accent carrying body text clears 4.5:1 contrast. The full extraction procedure is in
the `amplifier-proposal` skill under "Step 2.5 — Extract the Partner's Brand"; it applies
here unchanged.

---

## Step 5 — Copy to Proposals Folder

```bash
cp "[MAC_OUTPUT_DIR]/Intrinsic_and_[Company]_Proposal.pdf" \
   "/Users/amitmehta/Library/CloudStorage/GoogleDrive-mehta@helix.harvard7.net/My Drive/1 Ventures/Acquired Imaging/Proposals/Intrinsic_and_[Company]_Proposal.pdf"
```

---

## Step 6 — Create Gmail Draft

**Account (permanent, do not deviate):** Every Intrinsic proposal draft goes in the `mehta@helix.harvard7.net` mailbox — the same account used for everything else per Amit's standing rule ("always use mcp__56448f86 ... never use mcp__amplifier-gmail-mcp except when running the amplifier-proposal skill"). The `amplifier-gmail-mcp` connector is a **different account** reserved only for the separate `amplifier-proposal` (Amplifier Health) skill — never use it here. This was a real bug in v1 of this skill (it pointed at the wrong connector) and produced drafts Amit could never find. Fixed 2026-07-02.

**Why this step doesn't use the `create_draft` MCP tool.** `mcp__56448f86-...__create_draft` has two hard limitations: (1) its schema has no `from` field, and (2) its own tool description states plainly "Creating drafts with attachments is not supported yet." Since every Intrinsic proposal draft needs both an HTML body and the PDF attached, build the raw MIME message yourself and post it straight to the **Gmail API** — the same method the `amplifier-proposal` skill uses (see its Step 6 / `scripts/create_drafts_template.py`), not the MCP draft tool and not raw IMAP.

**Do not use IMAP APPEND for this** (`imaplib.append()` to `[Gmail]/Drafts`). It was tried and confirmed broken 2026-07-02: Gmail stores the raw bytes as-is but its compose UI opens IMAP-appended multipart/alternative drafts in **plain-text mode**, ignoring the HTML part entirely, even though the MIME structure is valid. The Gmail API's `drafts.create` endpoint parses the same MIME structure into Gmail's internal compose format correctly and the HTML renders. Always use the API path below.

**Method — Gmail API `drafts.create` with the mehta@helix.harvard7.net OAuth token.** Token file: `/Users/amitmehta/.gmail_mcp_token.json` (confirmed via `users.getProfile` to belong to `mehta@helix.harvard7.net` — do not confuse with `.gmail_mcp_token_amplifier.json`, which is `amit@amplifierhealth.com`, the Amplifier Health skill's account). Refresh it via the standard OAuth2 refresh-token grant, then POST a base64url-encoded raw MIME message.

Run as a Python script via `mcp__Control_your_Mac__osascript` (needs network access and needs to read the PDF from the Google Drive-synced Proposals folder on disk — both Mac-side):

```python
import json, base64, os, urllib.request, urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.utils import formataddr, make_msgid

TOKEN_FILE = "/Users/amitmehta/.gmail_mcp_token.json"   # mehta@helix.harvard7.net
FROM_EMAIL = "amit.mehta@intrinsicimaging.com"           # verified Send As alias on that account
FROM_NAME = "Amit Mehta, MD, FRCP"
PROPOSALS_DIR = "/Users/amitmehta/Library/CloudStorage/GoogleDrive-mehta@helix.harvard7.net/My Drive/1 Ventures/Acquired Imaging/Proposals"
LOGO_PATH = "/Users/amitmehta/Library/CloudStorage/GoogleDrive-mehta@helix.harvard7.net/My Drive/1 Ventures/Acquired Imaging/intrinsic_logo.png"
LOGO_W, LOGO_H = 160, 24   # ~1920x287 source, scaled for an email signature

def get_access_token():
    d = json.load(open(TOKEN_FILE))
    data = urllib.parse.urlencode({
        "client_id": d["client_id"], "client_secret": d["client_secret"],
        "refresh_token": d["refresh_token"], "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(d["token_uri"], data=data)) as r:
        return json.load(r)["access_token"]

def get_sendas_signature(access_token, send_as_email):
    """Same pattern as amplifier-proposal Step 6 — fetch the live Gmail signature, never hard-code it."""
    req = urllib.request.Request(
        f"https://www.googleapis.com/gmail/v1/users/me/settings/sendAs/{urllib.parse.quote(send_as_email)}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r).get("signature", "") or ""

def to_html(plain_text):
    paras = plain_text.split("\n\n")
    return "".join(
        f'<p style="margin:0 0 14px 0;font-family:Arial,sans-serif;font-size:14px;line-height:1.5;color:#000000;">{p.replace(chr(10), "<br>")}</p>'
        for p in paras
    )

def sign_off_html(sig_html, logo_cid):
    # NOTE (fixed 2026-07-04): the plain-text body already ends with "Thanks / a",
    # which to_html() renders as the final paragraph. This function must therefore
    # append ONLY the signature — never another "Thanks / a". Adding one here is the
    # bug that produced double sign-offs in a full batch of drafts.
    if sig_html:
        return sig_html   # real Gmail signature, embedded verbatim — tier 1
    # Tier 2 fallback: no signature saved on this alias yet in Gmail settings, so build one with
    # the real logo embedded inline via CID (see MIME structure notes above).
    return (
        '<table cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif;font-size:13px;color:#333333;">'
        f'<tr><td style="padding-bottom:8px;"><img src="cid:{logo_cid}" width="{LOGO_W}" height="{LOGO_H}" '
        f'alt="Intrinsic Imaging" style="display:block;"></td></tr>'
        '<tr><td style="font-weight:bold;color:#000000;">Amit Mehta, MD, FRCP</td></tr>'
        '<tr><td>CMO, Intrinsic Imaging</td></tr>'
        f'<tr><td>e: <a href="mailto:{FROM_EMAIL}" style="color:#1155cc;">{FROM_EMAIL}</a></td></tr>'
        '</table>'
    )

def build_message(to_addr, subject, plain_body, pdf_path, pdf_filename, sig_html):
    msg = MIMEMultipart("mixed")
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))   # MUST use formataddr — a raw f-string with the
    msg["To"] = to_addr                                  # comma-containing display name breaks RFC 5322
    msg["Subject"] = subject                             # parsing and silently reverts From to the account owner

    related = MIMEMultipart("related")               # holds alternative + inline image together
    logo_cid = make_msgid(domain="intrinsicimaging.com")[1:-1]
    html_full = f'<div dir="ltr">{to_html(plain_body)}{sign_off_html(sig_html, logo_cid)}</div>'
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain_body, "plain", "utf-8"))
    alt.attach(MIMEText(html_full, "html", "utf-8"))
    related.attach(alt)
    if not sig_html:   # only embed the CID logo when using the tier-2 fallback signature
        with open(LOGO_PATH, "rb") as f:
            logo_img = MIMEImage(f.read(), _subtype="png")
        logo_img.add_header("Content-ID", f"<{logo_cid}>")
        logo_img.add_header("Content-Disposition", "inline", filename="intrinsic_logo.png")
        related.attach(logo_img)
    msg.attach(related)

    with open(pdf_path, "rb") as f:                   # PDF is a sibling of `related`, not inside it
        part = MIMEApplication(f.read(), _subtype="pdf")
    part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(part)
    return msg

def create_draft(access_token, msg):
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body = json.dumps({"message": {"raw": raw}}).encode("utf-8")
    req = urllib.request.Request(
        "https://www.googleapis.com/gmail/v1/users/me/drafts", data=body, method="POST",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)

access_token = get_access_token()
sig_html = get_sendas_signature(access_token, FROM_EMAIL)
pdf_filename = "Intrinsic_and_[Company]_Proposal.pdf"
msg = build_message(to_addr, subject, plain_body, os.path.join(PROPOSALS_DIR, pdf_filename), pdf_filename, sig_html)
result = create_draft(access_token, msg)
print("draft id:", result.get("id"))
```

**Always verify after creating, don't assume:** fetch the draft back (`drafts.get?format=full`) and check (a) the From header shows the Intrinsic address, not the account owner, and (b) walking the payload tree shows `mixed > related > (alternative > plain, html) + image/png` plus `mixed > application/pdf` — confirming the logo image is actually attached at the right level and the PDF is a sibling, not nested inside `related`. This exact check caught the From-header bug and the missing-logo issue on the first two passes; don't skip it.

**De-dupe:** before creating the new draft, delete any prior draft to the same recipient. The Gmail API path doesn't need IMAP for this either — list drafts via `GET .../drafts?q=to:{email}` and `DELETE .../drafts/{id}` for any matches, then create the new one.

**Email content — same voice rules as before:**

Subject: `Intrinsic Imaging x [Company]`

Plain-text body (the HTML version is auto-generated from this by wrapping each blank-line-separated paragraph in `<p>`, per `to_html()` above — never write the HTML by hand):

```
[First Name] -

My name is Dr. Amit Mehta and I am the CMO of Intrinsic Imaging. We are a global medical imaging core laboratory and CRO. As you are familiar with, as an imaging CRO, we design and support the complex imaging component of clinical trials. We service a wide array of clinical trials from validation studies, and regulatory reader studies for pharmaceutical, biotech, to AI/medical device companies.

Our core services include independent blinded image review, multi-reader multi-case (MRMC) study design and execution, FDA 510(k) and De Novo reader study programs, site qualification, reader training, and statistical analysis for imaging endpoints. [Adapt last sentence to company type: AI imaging companies / international sponsors / pharma companies]

[BESPOKE — company-specific paragraph: describe the specific program, imaging endpoint, or regulatory pathway where Intrinsic is the right fit. 2-3 declarative sentences.]

Happy to connect if its useful. Feel free to delete if the timing isnt right.

Thanks
a
```

**The body ends at "Thanks / a" — full stop.** Never type the name/title/email block (Amit Mehta, MD, FRCP / CMO, Intrinsic Imaging / e: amit.mehta@intrinsicimaging.com) into the body. The signature step below appends the real signature after the body, so writing it in the body produces a duplicated sign-off. This was corrected by Amit on July 4, 2026 after every draft in a batch went out with two signature blocks.

**From-address — resolved 2026-07-02, root cause was a header-quoting bug, not a Gmail restriction.** `amit.mehta@intrinsicimaging.com` IS already a verified ("accepted") Send As alias on the `mehta@helix.harvard7.net` account — confirmed via `GET .../settings/sendAs`. The first attempt still got silently rewritten to `Amit Mehta <mehta@helix.harvard7.net>` because the From header was built as a raw f-string — `f"{FROM_NAME} <{FROM_EMAIL}>"` with `FROM_NAME = "Amit Mehta, MD, FRCP"` — and the unquoted comma inside the display name breaks RFC 5322 address-list parsing (a bare comma outside quotes is a list separator). Gmail's backend couldn't resolve a single valid address from the malformed header and fell back to the account's own identity. **Fix: always build the From header with `email.utils.formataddr((display_name, email_address))`**, which correctly quotes a display name containing commas (`"Amit Mehta, MD, FRCP" <amit.mehta@intrinsicimaging.com>`). With that fix, `drafts.get` confirms the stored From header is exactly the Intrinsic Imaging address, verified on all 6 companies. Never hand-build the From header as a plain string when the display name contains a comma or any other RFC 5322 special character.

**Signature — matches amplifier-proposal's live-fetch pattern, with the real logo embedded until a saved signature exists.** Fetch the alias's signature the same way amplifier-proposal does for `amit@amplifierhealth.com` — `GET .../settings/sendAs/{email}` and read the `signature` field — but for `amit.mehta@intrinsicimaging.com` that field is currently **empty** (confirmed via the API, length 0; no signature has been saved on this alias in Gmail settings, unlike `amit@amplifierhealth.com` which has a 570-character HTML signature with a hosted logo image). Two-tier logic:

1. If `get_sendas_signature()` returns non-empty content, embed it verbatim directly after the body (the body already ends with "Thanks / a" — do NOT add another "Thanks / a" here). Identical to the Amplifier flow otherwise.
2. If it's empty (the current state), fall back to a self-built HTML signature block that embeds the **real Intrinsic Imaging logo** (`intrinsic_logo.png`, the same asset used on the proposal PDF covers, at `.../Acquired Imaging/intrinsic_logo.png`, 1920×287) as an **inline CID image**, not a hosted URL — Gmail's own signature images are hosted via `ci3.googleusercontent.com` links that only exist once a signature is saved through the Gmail UI, which hasn't happened for this alias. An inline CID image achieves the same visual result (logo renders in the signature) without needing that hosted URL.

**MIME structure for the CID image (required, do not skip a level):** `multipart/mixed` (top) → `multipart/related` → `multipart/alternative` (plain + html) as one child of `related`, and the `image/png` logo (with `Content-ID: <cid>` and `Content-Disposition: inline`) as a sibling child of `related`, not nested inside `alternative`. The PDF attachment stays a direct child of the top-level `mixed`, alongside `related`. The HTML references the image via `<img src="cid:{same_id}">` with the angle brackets stripped from the Content-ID value in the `src` attribute (they stay in the `Content-ID` header only). Verified 2026-07-02 by fetching the draft back and confirming the tree: `mixed > related > (alternative > plain, html) + image/png` + `mixed > application/pdf`.

The moment Amit saves a real signature on the `amit.mehta@intrinsicimaging.com` alias in Gmail settings, tier 1 takes over automatically and the CID-logo fallback is no longer used — no code change required, just stop passing the `related`/image branch when `sig_html` is non-empty (already handled by the `if sig_html: ... else: ...` branch in `sign_off_html()` / `build_message()` above).

Do not rely on the `mcp__56448f86-...__list_drafts`/`search_threads` MCP tools to verify drafts right after creating them — they read from a Gmail API index that has been observed to lag well behind drafts just created via the raw API, showing stale/old results for a period after creation. Always query the specific draft by ID directly (`drafts.get`) as described above instead.

---

## Step 7 — Report

Confirm:
- Target company selected (and why, if auto-selected in Step 0.5)
- PDF path
- Draft in Gmail (subject + recipient)
- Any flags (company active status, email confidence, etc.)

---

## PDF Template Structure (reference)

**Page 1 — Cover:**
- Top bar: Intrinsic Imaging logo (image, top-left) / "CONFIDENTIAL · FOR AUTHORIZED USE ONLY" (Plex Mono, Slate-500, top-right)
- Eyebrow: "PARTNERSHIP PROPOSAL · [MONTH YEAR]" — Plex Mono Medium, Brand-600
- Hero: [COMPANY NAME] auto-sized to fill 504pt width, Plex Bold, Brand-900 navy
- Subheading: "INTRINSIC IMAGING PROPOSAL" — Plex Medium, Slate-600
- Thick rule — Brand-500, 2.2pt
- "What This Is" light Brand-50 rounded callout card (not a dark box)

**Page 2 — Company + About:**
- Section 01: "What We Know About [Company Name]" — 5 bespoke bullets
- Section 02: "Independent Imaging. Regulatory Grade." — Intrinsic body paragraph + rounded stat cards
- Optional: "Modalities and Therapeutic Areas" two-column block + compliance note (only if `modalities`/`therapeutic_areas` provided)

**Page 3 — Services + Fit + Contact:**
- Section 03: "What We Do" — 6 service bullets (fixed, not bespoke)
- Section 04: "The Right Partner for [Company Name]" — bespoke "The Fit" callout card
- "Let's Talk" — rounded Slate-50 contact card (Amit Mehta, CMO)

## Design tokens quick reference

| Token | Hex | Use |
|---|---|---|
| Brand-50 | #EAF2FB | callout/stat/card backgrounds |
| Brand-200 | #A7C8EF | card borders |
| Brand-500 | #1E6FB8 | rules, accent bars, links |
| Brand-600 | #175A99 | eyebrow, section labels |
| Brand-700 | #124678 | callout labels |
| Brand-900 | #0A2540 | hero, H2 headings (navy ink) |
| Slate-500 | #6A7A8C | footer, confidential line, mono labels |
| Slate-800 | #212B36 | body text, bullets |
| Slate-50 | #F6F8FB | contact card background |

Fonts: `Plex` / `Plex-Medium` / `Plex-SemiBold` / `Plex-Bold` (IBM Plex Sans), `PlexMono` / `PlexMono-Medium` / `PlexMono-SemiBold` (IBM Plex Mono), registered from the `fonts/` folder next to the template.
