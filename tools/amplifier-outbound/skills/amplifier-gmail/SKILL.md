---
name: amplifier-gmail
description: Check Gmail for unread AP emails with screenshot attachments, download each image, run the full Amplifier Health proposal pipeline on each one, then delete the email. Can also be invoked directly with a single image path argument.
---

# Amplifier Health Proposal — AP Inbox Pipeline

If called with no arguments (or "run from inbox"): scrape Gmail for unread AP emails, process each image, delete each email when done.

If called with a single image path argument (e.g. `/tmp/ap_proposals/abc123.jpg`): skip inbox scraping and process that image directly.

**NEVER SKIP A SCREENSHOT.** Even if the company is not a healthcare company, process it. Amit has intentionally included it.

---

## MANDATORY FIRST ACTION

Before writing any code or doing any research, read:

`/var/folders/n5/fpz5ljtx01n4gfbn5spxkvdw0000gn/T/claude-hostloop-plugins/444901de9c453dac/skills/amplifier-proposal/references/CANONICAL_SETTINGS.md`

This is the single source of truth for fonts, layout, execution method, and content rules. Read it fresh every run. Do not rely on memory.

---

## Step 0 — Inbox Scraping (skip if image path was provided as argument)

Use the Gmail token at `~/.gmail_mcp_token.json` to fetch a fresh access token, then:

```python
import json, urllib.request, os, base64

creds_file = os.path.expanduser("~/.gmail_mcp_token.json")
with open(creds_file) as f:
    creds_data = json.load(f)

token_data = json.dumps({
    "client_id": creds_data["client_id"],
    "client_secret": creds_data["client_secret"],
    "refresh_token": creds_data["refresh_token"],
    "grant_type": "refresh_token"
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data,
    headers={"Content-Type": "application/json"}, method="POST")
token = json.loads(urllib.request.urlopen(req).read())["access_token"]
```

1. Search for unread AP emails:
   `GET https://gmail.googleapis.com/gmail/v1/users/me/threads?q=subject:AP+is:unread&maxResults=10`

2. For each thread, get full message payload:
   `GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{messageId}?format=full`

3. Walk the MIME parts tree. For each part where `mimeType` starts with `image/` and `body.attachmentId` is present:
   `GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{messageId}/attachments/{attachmentId}`
   Decode: `base64.urlsafe_b64decode(data["data"])`

4. Save each image to `/tmp/ap_proposals/{threadId}.jpg`

5. Store the thread IDs for deletion after successful proposal generation.

If no unread AP emails are found, print "No unread AP emails." and stop.

---

## Step 1 — Read the image

Use the Read tool on the image path to view the screenshot. Identify:
- The company name (from the account name, bio, or handle)
- The product or service shown
- Any clinical, health, or wellness context visible

If the company cannot be identified, log the image path to `~/ap_processor.log` and move on.

---

## Step 2 — Active verification (MANDATORY)

Web search: `"[Company] acquired closed shutdown 2024 2025 2026"`

Fail conditions (note in tracker as INACTIVE, stop for this company):
- Acquired and integrated
- Shut down or bankrupt
- WARN Act layoffs >50%

Flag conditions (note in final report, do not stop):
- Pending acquisition not yet closed
- Public company (NYSE/NASDAQ)
- No funding in 3+ years

---

## Step 3 — Research the company

Read proposal-sections.md for exact content rules:
`/var/folders/n5/fpz5ljtx01n4gfbn5spxkvdw0000gn/T/claude-hostloop-plugins/444901de9c453dac/skills/amplifier-proposal/references/proposal-sections.md`

Key research targets:
- Product and delivery mechanism (video sessions? coaching calls? app-based?)
- Member or patient volume, employer or payer distribution
- Funding and valuation
- Clinical evidence or outcomes data they publish
- The specific audio touchpoint where Sona-2 would operate
- The comorbidity or clinical gap Sona-2 fills for this company
- Any AI or data infrastructure already in place

---

## Step 4 - Confirm the email address (MANDATORY)

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

In the Step 10 flag report, every company must carry one of:

- **CONFIRMED** by the mail server, the normal case
- **CATCH-ALL**, address inferred, cannot be verified, delivery not guaranteed
- **3-SOURCE**, verification found nothing, address from directories, lower confidence

A bounced cold email on a new domain costs far more than a credit.

## Step 5 — Generate PDF proposal

Read the full ReportLab spec:
`/var/folders/n5/fpz5ljtx01n4gfbn5spxkvdw0000gn/T/claude-hostloop-plugins/444901de9c453dac/skills/amplifier-proposal/references/pdf-template.md`

The fastest path: read the MEELA_REFERENCE_TEMPLATE.py, copy it, and swap in partner-specific content.
`/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/MEELA_REFERENCE_TEMPLATE.py`

**Hard rules (no exceptions):**
- Fonts: HN-Black = LiberationSans-Bold, HN = LiberationSans-Regular (from `/usr/share/fonts/truetype/liberation/`)
- Run script IN THE LINUX SANDBOX via mcp__workspace__bash — NEVER via osascript on Mac
- `base()` always uses `frac=0.758`
- Cover hero: partner name ALL CAPS, sized via `hero_layout()`, hero anchor at `top_pt=175`
- Callout label: always "WHAT THIS IS"
- Section 01 heading: always "What We Know About [Partner]"
- Section 06 is REMOVED — flow is 01 > 02 > 03 > 04 > 05 > 07 GET STARTED
- No dashes anywhere: no em dash, no en dash, no double dash. Rewrite sentences.
- No mention of baseline period
- No mention of Winterlight Labs or Sonde Health
- No mention of the FDA anywhere in any proposal section
- Section 01 covers ONLY the product. No CEO names, no people, no funding amounts or rounds, no founding year, no location. Every bullet must be about what the product is or does.
- Final page: "07 · GET STARTED" with three resource boxes and day-one table

After generating in sandbox, copy PDF to CRO folder via osascript:
```
CRO folder: /Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/
```

---

## Step 6 — Visual verification (MANDATORY)

For each PDF, generate a thumbnail and display with the Read tool:
```bash
qlmanage -t -s 800 -o /tmp/b_thumbs/ '/path/to/PDF' 2>&1
```
Then Read the .png to visually confirm:
- Hero name renders without clipping
- WHAT THIS IS callout text fits cleanly
- No overflow at right margin or bottom

---

## Step 7 — Create Gmail draft

Read the draft creation template:
`/var/folders/n5/fpz5ljtx01n4gfbn5spxkvdw0000gn/T/claude-hostloop-plugins/444901de9c453dac/skills/amplifier-proposal/scripts/create_drafts_template.py`

**Email structure (fixed — never change):**

Salutation: `[First name] -`

Opening paragraph (exact, word for word):
"I wanted to introduce you to our novel acoustic frontier foundation model - Sona-2. We've built what is the first and largest frontier acoustic foundation model that perceives physicality in the voice to detect biomarkers - depression, anxiety, cognitive decline, respiratory, cardiac - all from the audio itself without any friction and non invasively."

Middle paragraph (company-specific, ~50 words):
One concrete paragraph on why this company specifically. Focus on the audio touchpoint that already exists in their product, the clinical signal Sona-2 extracts, and why there is zero UX disruption. No lists. No features. Founder-to-founder tone. Amit drops apostrophes (dont, cant, lets) — preserve this.

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
Attachment: PDF from the CRO folder (not from /tmp/outputs)

Use the gmail-mcp `gmail_create_draft` tool or the direct Python API with `~/.gmail_mcp_token.json`.

---

## Step 8 — Delete the AP email

After the proposal and draft are successfully created, trash the source AP email thread:

```python
url = f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}/trash"
req = urllib.request.Request(url, method="POST",
    headers={"Authorization": f"Bearer {token}", "Content-Length": "0"})
urllib.request.urlopen(req)
print(f"Trashed thread {thread_id}")
```

If this fails, log the thread ID to `~/ap_processor.log` for manual cleanup.

---

## Step 9 — Update Obsidian tracker

File: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/contacted_companies.md`

Two updates:
1. Increment `## CONTACTED (N total)` header count
2. Insert the company name into the current batch section, or create a new batch section immediately before `## EXCLUDED`:

```markdown
### Batch N — [Month Day, Year]
- Company Name
- Company 2 (flag note if applicable)

---

```

---

## Step 10 — Report

Return concisely:
- Companies identified from screenshots
- Drafts created: yes/no per company
- PDF paths
- Email addresses used (and confidence level)
- AP emails deleted
- Any flags (public company, pending acquisition, email unconfirmed, etc.)

---

## Key paths (hardcoded — never change)

- CRO folder: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/`
- Tracker: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/contacted_companies.md`
- Target list: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/amplifier_target_companies.txt`
- Gmail token: `~/.gmail_mcp_token.json`
- Reference template: `/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/MEELA_REFERENCE_TEMPLATE.py`
- Canonical settings: `/var/folders/n5/fpz5ljtx01n4gfbn5spxkvdw0000gn/T/claude-hostloop-plugins/444901de9c453dac/skills/amplifier-proposal/references/CANONICAL_SETTINGS.md`
