#!/usr/bin/env python3
"""
Gmail Draft Creation Template — Amplifier Health CRO Outreach
Copy this script, populate EMAILS list, and run via osascript.

Usage:
  python3 '/Users/amitmehta/Library/.../outputs/create_drafts_batchN.py'
"""

import os, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = os.path.expanduser("~/.gmail_mcp_token.json")
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("gmail", "v1", credentials=creds)

CRO = "/Users/amitmehta/Claude/obsidian-vault/Amplifier Health/Amplifier CRO/"

# Populate one dict per company. 'fit' is the company-specific middle paragraph.
EMAILS = [
    {
        "to": "ceo@company.com",
        "subject": "Amplifier Health and Company Name",   # always "and", never "x"
        "greeting": "FirstName",
        "fit": "One paragraph. The audio touchpoint that already exists. The clinical gap Sona-2 fills. Why zero UX disruption. Under 60 words. Amit voice — drops apostrophes (dont, cant) intentionally.",
        "pdf": CRO + "Amplifier_and_CompanyName_Proposal.pdf",
    },
    # Add more companies here...
]

OPENING = (
    "I wanted to introduce you to our novel acoustic frontier foundation model - Sona-2. "
    "We've built what is the first and largest frontier acoustic foundation model that perceives "
    "physicality in the voice to detect biomarkers - depression, anxiety, cognitive decline, respiratory, "
    "cardiac - all from the audio itself without any friction and non invasively."
)

CLOSE = (
    "I've attached a short proposal. "
    "Happy to jump on a call if it's useful \u2014 or feel free to delete if it doesn't fit."
)

SIG = "Amit Mehta, MD, FRCP\ne: amit@amplifierhealth.com"

for e in EMAILS:
    body = f"{e['greeting']} -\n\n{OPENING}\n\n{e['fit']}\n\n{CLOSE}\n\nThanks\na\n\n{SIG}"

    msg = MIMEMultipart()
    msg["From"] = "amit@amplifierhealth.com"
    msg["To"] = e["to"]
    msg["Subject"] = e["subject"]
    msg.attach(MIMEText(body, "plain"))

    with open(e["pdf"], "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(e["pdf"]))
    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(e["pdf"])}"'
    msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()
    print(f"Created: {e['subject']} -> {e['to']} (id: {draft['id']})")

print(f"\nDone. {len(EMAILS)} drafts created.")
