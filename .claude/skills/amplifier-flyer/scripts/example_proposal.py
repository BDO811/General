# -*- coding: utf-8 -*-
"""Reference proposal. Rebuilds the Nice Healthcare partnership proposal.

Copy this file, replace CONTENT, keep the section order.
Sections run 01, 02, 03, 04, 05, 07. There is no section 06.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amplifier_design import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "proposal.pdf"
PARTNER = "Nice Healthcare"
DATE    = "September 2026"
FOOT    = "Amplifier Health Partnership Proposal  ·  %s" % DATE
TOTAL   = 5

d = Doc(OUT, kind="proposal")

# ---- cover
proposal_cover(
    d, PARTNER,
    "A video visit you already run becomes a wellness signal.",
    "Confidential  ·  For authorized use only",
    "Partnership proposal  ·  %s" % DATE,
    "Background",
    "Nice Healthcare delivers employer sponsored primary care through recurring video "
    "or chat visits, with in home follow up when a physical exam or labs are needed, and "
    "runs virtual mental health and physical therapy as core service lines across a "
    "growing set of states. Sona-2 sits on that same visit audio. The default video visit "
    "that already carries every primary care and mental health encounter carries a "
    "parallel acoustic signal, one tied to how a covered member is trending between "
    "visits, that the platform was never built to read.")
proposal_footer(d, FOOT, TOTAL)

# ---- 01 and 02
y = proposal_body_page(d, PARTNER)
y = proposal_section(d, y, "01", "What we've researched on %s" % PARTNER)
for b in [
    "Delivers primary care through video or chat visits, with in-home or at-work follow-up visits when a physical exam, labs, or imaging is required",
    "Also offers virtual mental health therapy and virtual physical therapy as core service lines",
    "Clinicians are board-certified nurse practitioners or physician assistants; in-home visits are dispatched by a care coordinator based on acuity",
    "Prescribes medications at no out-of-pocket cost and integrates with a large network of in-network pharmacies",
    "Distributed primarily as an employer-sponsored benefit positioned to replace a large share of traditional clinic visits",
    "Supports multi-person/family visits in a single scheduling flow, with interpreter services available for non-English speakers",
]:
    y = proposal_bullet(d, y, b)

y = proposal_stats(d, y - 14, [
    ("13+", "States", "Expanding in 2026"),
    ("$0", "Member cost", "Employer sponsored"),
    ("0", "Acoustic layer", "No health signal read today"),
])

y = proposal_section(d, y, "02", "The opportunity",
                     "A VIDEO VISIT THAT ALREADY HEARS EVERYTHING")
for b in [
    "Every default visit already has full audio of the patient and a nurse practitioner talking.",
    "That audio does its job for the visit and then its finished. Nothing clinical is read from how the patient sounds.",
    "The same acoustic signal carries the relevant subclinical signals tied to mood, stress, and physiological drift.",
    "An employer sponsored primary care relationship is recurring by design, with the same members over time.",
    "Sona-2 reads that layer in parallel, adding a wellness signal to a visit you already run.",
]:
    y = proposal_bullet(d, y, b)
proposal_footer(d, FOOT, TOTAL)

# ---- 05
y = proposal_body_page(d, PARTNER)
y = proposal_section(d, y, "05", "Why Amplifier Health",
                     "The Model, the Dataset, the Foundation")
for b in [
    "The model: Sona-2 is a purpose built Large Acoustic Model trained on clinically labeled real world audio. It is not a general speech model retrofitted for health.",
    "The dataset: more than 2.5 million clinically labeled voice interactions with validated ground truth. Every new conversation makes the model more accurate.",
    "Validation: the underlying classifiers are calibrated against clinical instruments including PHQ-9, GAD-7, and PCL-5, with validation partners across MIT, Harvard, Johns Hopkins, UCLA Health, and the VA.",
    "The clinical evidence base grows with every partner integration, and a continuous real world audio stream like this one contributes uniquely diverse signal.",
    "HIPAA architecture was designed for voice from day one. Audio never becomes stored PHI and the BAA is executed at account creation with no friction.",
]:
    y = proposal_bullet(d, y, b)

y = proposal_callout(d, y - 12, "Why this partnership is different",
    "The platform already owns the video visit and the recurring member relationship. "
    "Sona-2 adds a continuous read across a covered population to audio already flowing "
    "through your visit pipeline, on a benefit sold on keeping employees healthier at "
    "lower cost.")
proposal_footer(d, FOOT, TOTAL)

d.save()
print("wrote %s" % OUT)
