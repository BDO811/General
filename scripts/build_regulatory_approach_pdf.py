# -*- coding: utf-8 -*-
"""Amplifier Health Regulatory Approach.
Built on the Amplifier proposal design set: TEMPLATE 1, black and white.
Geometry, palette and helpers follow references/pdf-template.md exactly.
Fonts registered as Inter. Point the paths at Inter-Regular.ttf and
Inter-Bold.ttf when available; Liberation Sans is the metric-compatible
fallback used when Inter cannot be fetched.
"""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

REG = "/tmp/Inter-Regular.ttf"
BLD = "/tmp/Inter-Bold.ttf"
if not (os.path.exists(REG) and os.path.getsize(REG) > 50000):
    REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    BLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("Inter", REG))
pdfmetrics.registerFont(TTFont("Inter-Bold", BLD))

PW, PH = 612, 792
ML = MR = 54
MB = 42
TW = 504

BK  = HexColor("#050505")
DK  = HexColor("#1A1A1A")
MED = HexColor("#444444")
MU  = HexColor("#888888")
LT  = HexColor("#BBBBBB")
HLT = HexColor("#DDDDDD")
DV  = HexColor("#D0D0D0")
LB  = HexColor("#F5F5F5")
BOX = HexColor("#0A0A0A")

c = canvas.Canvas("out/Amplifier_Regulatory_Approach.pdf", pagesize=(PW, PH))


def base(top_pt, size_pt, frac=0.758):
    return PH - top_pt - size_pt * frac

def draw(x, y, text, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, text)

def draw_right(x, y, text, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawRightString(x, y, text)

def hrule(y, color=DV, thickness=0.4):
    c.setStrokeColor(color); c.setLineWidth(thickness); c.line(ML, y, PW - MR, y)

def thick_hrule(y, color=BK, thickness=1.5):
    c.setStrokeColor(color); c.setLineWidth(thickness); c.line(ML, y, PW - MR, y)

def filled_rect(x, y, w, h, color):
    c.setFillColor(color); c.rect(x, y, w, h, stroke=0, fill=1)

def section_label(y, number, name):
    draw(ML, y, "SECTION %s  ·  %s" % (number, name), "Inter-Bold", 7.4, MU)

def h2(y, text):
    draw(ML, y, text, "Inter-Bold", 15.1, BK)

def h3(y, text):
    draw(ML, y, text, "Inter-Bold", 11.5, DK)

def body_line(y, text, indent=0):
    draw(ML + indent, y, text, "Inter", 10.1, DK)

def wrap_text(text, font, size, max_w):
    words = text.split(); lines = []; line = ""
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, font, size) <= max_w:
            line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    return lines

def bullet(y, text, max_w=None, indent=10, leading=12):
    bx = ML + indent; tx = bx + 9; avail = (max_w or TW) - indent - 9
    draw(bx, y + 2, "–", "Inter-Bold", 7.4, MED)
    c.setFont("Inter", 10.1); c.setFillColor(DK)
    for line in wrap_text(text, "Inter", 10.1, avail):
        c.drawString(tx, y, line); y -= leading
    return y

def fit_width(text, font, max_w, max_size=72, min_size=20):
    size = max_size
    while size >= min_size:
        if c.stringWidth(text, font, size) <= max_w:
            return size
        size -= 0.5
    return min_size

def callout_box(y, label, text, pad_v=10, pad_h=12, line_h=12.5):
    lines = wrap_text(text, "Inter", 9.6, TW - pad_h * 2)
    box_h = pad_v + 11 + 6 + len(lines) * line_h + pad_v
    filled_rect(ML, y - box_h, TW, box_h, BOX)
    ty = y - pad_v - 7.9 * 0.758
    draw(ML + pad_h, ty, label.upper(), "Inter-Bold", 7.9, HLT)
    ty -= 11
    c.setFont("Inter", 9.6); c.setFillColor(LT)
    for line in lines:
        c.drawString(ML + pad_h, ty, line); ty -= line_h
    return y - box_h - 8

def stat_block(y, stats):
    n = len(stats); cell_w = TW / n; bh = 52; by = y - bh
    for i, (num, lbl, sub) in enumerate(stats):
        cx = ML + i * cell_w
        filled_rect(cx, by, cell_w - 2, bh, LB)
        c.setStrokeColor(BK); c.setLineWidth(2); c.line(cx, y, cx + cell_w - 2, y)
        draw(cx + 8, by + bh - 8 - 22 * 0.758, num, "Inter-Bold", 22, BK)
        draw(cx + 8, by + 12, lbl, "Inter-Bold", 7.4, DK)
        draw(cx + 8, by + 4, sub, "Inter", 7.9, MU)
    return by - 10

def resource_box(y, label, title, desc, box_h=48):
    filled_rect(ML, y - box_h, TW, box_h, LB)
    ty = y - 10 - 7.9 * 0.758
    draw(ML + 10, ty, label.upper(), "Inter-Bold", 7.9, MU); ty -= 13
    draw(ML + 10, ty, title, "Inter-Bold", 11.5, BK); ty -= 12
    draw(ML + 10, ty, desc, "Inter", 9.6, MED)
    return y - box_h - 6

def row(y, label, desc, row_h=18, split=170):
    hrule(y, color=DV, thickness=0.4)
    ty = y - row_h * 0.5 - 10 * 0.758
    draw(ML + 8, ty, label, "Inter-Bold", 9.6, BK)
    draw(ML + split, ty, desc, "Inter", 9.6, MED)
    return y - row_h

def top_bar():
    draw(ML, base(76.8, 11.04), "AMPLIFIER HEALTH", "Inter-Bold", 11.04, BK)
    draw_right(PW - MR, base(76.8, 7.44),
               "CONFIDENTIAL  ·  FOR AUTHORIZED USE ONLY", "Inter-Bold", 7.44, MU)

def footer(page_num):
    hrule(MB + 10)
    draw_right(PW - MR, MB - 2,
               "Amplifier Health  ·  Confidential  ·  %d" % page_num,
               "Inter", 7.44, MU)

def page_start():
    top_bar()
    return base(106.8, 0) - 8

def sect(y, num, name, title):
    y -= 6; hrule(y); y -= 14
    section_label(y, num, name); y -= 16
    h2(y, title); y -= 22
    return y


# ------------------------------------------------------------------ COVER
top_bar()
draw(ML, base(106.8, 8.40), "REGULATORY APPROACH  ·  SEPTEMBER 2026",
     "Inter-Bold", 8.40, MU)

hero = "REGULATORY APPROACH"
hs = fit_width(hero, "Inter-Bold", TW, max_size=72, min_size=20)
hy = base(155, hs)
draw(ML, hy, hero, "Inter-Bold", hs, BK)

sub = "FDA PATHWAY AND THE TWO PHASE STRATEGY"
ss = min(hs - 4, fit_width(sub, "Inter-Bold", TW))
sy = hy - hs * 0.92 - 10
draw(ML, sy, sub, "Inter-Bold", ss, MED)

ry = sy - ss * 0.92 - 20
thick_hrule(ry)

y = callout_box(ry - 14, "WHAT THIS IS",
    "Voice analysis that interprets clinical state fails Criterion 1 of the Cures Act "
    "clinical decision support exclusion. The CDS carve out is not the lane it was "
    "assumed to be. The non device position rests on general wellness and non patient "
    "care uses. Everything carrying a disease claim is a device and needs clearance. "
    "This document sets out the three lanes that remain, why clearance is sequenced as "
    "a second phase, and what phase one must hold to stay clean.")

y -= 6
y = stat_block(y, [
    ("3", "REGULATORY LANES", "Wellness / Non care / Device"),
    ("4", "CURES CRITERIA", "All four must be met"),
    ("1", "INDICATION FIRST", "You clear a use, not a model"),
    ("$3.5M", "VALIDATION", "Allocated in the Series A"),
])

y -= 14
hrule(y); y -= 16
draw(ML, y, "CONTENTS", "Inter-Bold", 7.4, MU); y -= 16
for n, t, d in [
    ("01", "The Final Guidance", "Four criteria, the 2026 changes, enforcement discretion"),
    ("02", "Where Amplifier Sits", "Criterion by criterion, and the Criterion 1 problem"),
    ("03", "The Three Lanes", "Wellness, non patient care, device, partners mapped"),
    ("04", "Why Two Phases", "The sequencing argument and the decisions still open"),
    ("05", "Controls And Open Items", "Claim language, owners, the Pre Submission"),
]:
    draw(ML + 8, y, n, "Inter-Bold", 9.6, BK)
    draw(ML + 34, y, t, "Inter-Bold", 9.6, BK)
    draw(ML + 190, y, d, "Inter", 9.6, MED)
    y -= 15

y -= 6
hrule(y); y -= 16
for ln in wrap_text("Sources: CDRH town hall on the Clinical Decision Support Software "
                    "Final Guidance, March 11 2026. Amplifier Financial Model v6. LP "
                    "diligence request of September 22 2026. This is analysis of published "
                    "guidance. It is not legal advice.", "Inter", 8.4, TW):
    draw(ML, y, ln, "Inter", 8.4, MU); y -= 11

footer(1)
c.showPage()

# ------------------------------------------------------------------ PAGE 2
y = page_start()
y = sect(y, "01", "THE FINAL GUIDANCE", "What The Guidance Says")

for b in [
    "The 21st Century Cures Act amended the device definition in December 2016, excluding five categories of software function under 520(o). Two matter to us: general wellness under 520(o)(1)(B), and clinical decision support under 520(o)(1)(E).",
    "The CDS guidance history runs draft December 2017, revised draft September 2019, final September 2022, and a new final published January 6 2026 and reissued January 29 2026. The January 2026 version is operative and supersedes September 2022.",
]:
    y = bullet(y, b); y -= 3

y -= 10
h3(y, "The four criteria. All four must be met."); y -= 18
for n, t, d in [
    ("1", "Signal exclusion", "Not intended to acquire, process or analyze a medical image, a signal from an IVD, or a pattern or signal from a signal acquisition system."),
    ("2", "Medical information", "Intended to display, analyze or print medical information about a patient or other medical information."),
    ("3", "Recommendations", "Intended to support or provide recommendations to an HCP about prevention, diagnosis or treatment."),
    ("4", "Independent review", "Intended to enable the HCP to independently review the basis, so the HCP does not rely primarily on the output."),
]:
    draw(ML + 8, y, "CRITERION " + n, "Inter-Bold", 7.4, MU)
    draw(ML + 90, y, t, "Inter-Bold", 9.6, BK)
    yy = y - 13
    for ln in wrap_text(d, "Inter", 9.6, TW - 98):
        draw(ML + 90, yy, ln, "Inter", 9.6, MED); yy -= 11.5
    y = yy - 8

y -= 4
h3(y, "Two changes in the 2026 guidance"); y -= 18
for b in [
    "The interpretation that software must not support time critical decision making was removed from Criterion 3. It still bears on Criterion 4.",
    "FDA added an enforcement discretion policy. Where a function provides one clinically appropriate output and therefore fails Criterion 3, but meets every other criterion, FDA intends to exercise enforcement discretion. The guidance carries eight worked examples.",
]:
    y = bullet(y, b); y -= 3

y -= 8
y = callout_box(y, "THE LIMIT OF BOTH CHANGES",
    "Neither change helps a function that fails Criterion 1. Enforcement discretion is "
    "scoped to Criterion 3 failures only.")

footer(2)
c.showPage()

# ------------------------------------------------------------------ PAGE 3
y = page_start()
y = sect(y, "02", "WHERE AMPLIFIER SITS", "Criterion By Criterion")

for n, t, verdict, d in [
    ("1", "Signal exclusion", "FAILS", "A microphone capturing voice for clinical inference is a system measuring a parameter external to the body for a medical purpose through streaming measurement. FDA states that software which assesses or interprets the clinical implications of a signal does not meet Criterion 1."),
    ("2", "Medical information", "FAILS", "Raw acoustic waveform is not on FDA's list of medical information. Where the input is a physician note, a symptom set or a lab value, Criterion 2 is satisfied. Where the input is the audio itself, it is not."),
    ("3", "Recommendations", "ACHIEVABLE", "Output presented as a list or prioritized list of options for an HCP to consider, not a directive. A binary result would fail, but that failure alone now falls inside the enforcement discretion policy if every other criterion is met."),
    ("4", "Independent review", "BUILD FOR IT", "Worth building regardless of pathway. Intended use and intended HCP user, required input medical information, a plain language description of algorithm development and validation, and stated knowns and unknowns."),
]:
    draw(ML + 8, y, "CRITERION " + n, "Inter-Bold", 7.4, MU)
    draw(ML + 90, y, t, "Inter-Bold", 9.6, BK)
    draw_right(PW - MR, y, verdict, "Inter-Bold", 8.4, BK)
    yy = y - 13
    for ln in wrap_text(d, "Inter", 9.6, TW - 98):
        draw(ML + 90, yy, ln, "Inter", 9.6, MED); yy -= 11.5
    y = yy - 6
    hrule(y + 2); y -= 10

y -= 2
y = callout_box(y, "THE ONE ARGUMENT WE HAVE, AND ITS LIMIT",
    "FDA says discrete, episodic or intermittent point in time measurements, giving "
    "routine vital signs at a clinical encounter as the example, generally do not by "
    "themselves constitute a pattern. A single voice sample at one encounter is arguably "
    "not a pattern. That defeats the pattern prong. It does not defeat the signal prong, "
    "because Criterion 1 excludes a signal from a signal acquisition system independently. "
    "Longitudinal voice monitoring, core to the product thesis, fails both prongs.")

y -= 10
h3(y, "FDA's own device examples land close"); y -= 18
for d, r in [
    ("Analyzes multiple signals from wearable products, being perspiration rate, heart rate, eye movement and breathing rate, to monitor whether a person is having a heart attack or narcolepsy episode.",
     "Device. Criterion 1, it analyzes signals."),
    ("Analyzes hourly pulse oximetry and heart rate measurements from the EHR to identify signs of patient deterioration and alert an HCP.",
     "Device. Criterion 1, it analyzes a pattern."),
]:
    y = bullet(y, d)
    draw(ML + 19, y, r, "Inter-Bold", 9.6, BK); y -= 16

y -= 2
h3(y, "What this means"); y -= 16
for ln in wrap_text("Assume every Amplifier function that interprets voice for clinical "
                    "meaning falls outside the CDS carve out. Counsel confirms that in "
                    "writing, or builds the contrary argument in writing. Planning on the "
                    "carve out without a written position is the risk.", "Inter", 10.1, TW):
    body_line(y, ln); y -= 12

footer(3)
c.showPage()

# ------------------------------------------------------------------ PAGE 4
y = page_start()
y = sect(y, "03", "THE THREE LANES", "The Lanes We Actually Have")

for ln in wrap_text("The prior working assumption was general wellness plus the CDS carve "
                    "out. The correct statement is general wellness plus non patient care "
                    "uses. That distinction matters in writing, to investors, to partners "
                    "and to counsel.", "Inter", 10.1, TW):
    body_line(y, ln); y -= 12
y -= 10

for tag, title, cite, d in [
    ("LANE A", "General wellness", "520(o)(1)(B)",
     "Software for maintaining or encouraging a healthy lifestyle and unrelated to the diagnosis, cure, mitigation, prevention or treatment of a disease. Narrow. A single disease claim breaks it, in our marketing or in a partner's."),
    ("LANE B", "Non patient care uses", "Outside the device definition",
     "Insurance risk assessment, actuarial and underwriting work, enterprise analytics, research use. Outside the device definition because they are not intended for the diagnosis or treatment of an individual patient. Different regulation, not lighter: insurance regulators, OSFI E-23, state insurance law, adverse action exposure."),
    ("LANE C", "Device pathway", "510(k) or De Novo",
     "Anything that detects, screens for, diagnoses, predicts or monitors a disease in an individual. Anemia detection. Depression screening. Clinical deployment at a health system. The CDS carve out does not rescue these because of Criterion 1."),
]:
    draw(ML + 8, y, tag, "Inter-Bold", 7.4, MU)
    draw(ML + 90, y, title, "Inter-Bold", 11.5, BK)
    draw_right(PW - MR, y, cite, "Inter", 8.4, MU)
    yy = y - 15
    for ln in wrap_text(d, "Inter", 9.6, TW - 98):
        draw(ML + 90, yy, ln, "Inter", 9.6, MED); yy -= 11.5
    y = yy - 6
    hrule(y + 2); y -= 12

y -= 2
h3(y, "Partner map"); y -= 15
draw(ML, y, "Every counterparty sits in one lane. Where it is unresolved, that is the open item.",
     "Inter", 8.4, MU)
y -= 14
for name, lane, note in [
    ("Glow", "A or C", "Largest recurring line, related party. Endpoint and claim dependent."),
    ("Flagship Pioneering", "B", "Per protocol custom models. Confirm no patient facing output."),
    ("Ultimate Human", "A", "Consumer wellness. Highest marketing drift risk. Warrants, no cash."),
    ("Canada Life", "B", "OSFI E-23 model risk scoping. Not FDA. In negotiation."),
    ("QBE", "UNRESOLVED", "Not in the financial model. Confirm an agreement exists."),
    ("Sutter Health", "C", "Clinical in substance. Research use with IRB, or restructure."),
    ("AssemblyAI, Amical", "B or C", "They build the product. Responsibility allocation is the issue."),
    ("zebraMD", "C", "Clinical integration. Determine the output and who acts on it."),
]:
    hrule(y, color=DV, thickness=0.4)
    ty = y - 9 - 10 * 0.758
    draw(ML + 8, ty, name, "Inter-Bold", 9.6, BK)
    draw(ML + 140, ty, lane, "Inter-Bold", 8.4, MED)
    draw(ML + 210, ty, note, "Inter", 9.6, MED)
    y -= 18
hrule(y, color=DV, thickness=0.4)

y -= 14
y = callout_box(y, "THE CONTROL THAT KEEPS THE LANES SEPARATE",
    "Wellness and clinical endpoints separately gated in the API, separately labeled and "
    "separately contracted. One endpoint serving both lanes collapses the distinction the "
    "whole position depends on.")

footer(4)
c.showPage()

# ------------------------------------------------------------------ PAGE 5
y = page_start()
y = sect(y, "04", "WHY TWO PHASES", "Clearance Is Sequenced Second")

y = resource_box(y, "PHASE ONE  ·  NOW", "Sell in clean lanes",
                 "Deployments generate clinically labeled voice at population scale.")
y = resource_box(y, "PHASE TWO  ·  SERIES A FUNDED", "File on one indication",
                 "The dataset built in phase one is the submission.")

y -= 6
h3(y, "The argument"); y -= 18
for n, t, d in [
    ("01", "You do not clear a foundation model",
     "You clear one intended use on one indication. A submission is only as strong as the evidence behind that single claim. Filing broadly is not an option FDA offers."),
    ("02", "The evidence is real world data",
     "Commercial deployments generate clinically labeled voice from the people the product is for, in the environment it runs in. That dataset is the submission. Filing before we hold it means filing a weaker one."),
    ("03", "Trial generated evidence costs multiples more",
     "And it produces data less representative of deployment. Both 510(k) and De Novo trial scenarios are modeled in the financial model."),
    ("04", "The infrastructure gets built once",
     "QMS, CFR Part 11, validation architecture, labeling discipline, SOC 2 Type II, HIPAA BAA. Every indication after the first rides the same rails at marginal cost."),
    ("05", "The phases do not depend on each other",
     "Revenue today does not require clearance. Clearance does not require revenue. If FDA timelines move, the business keeps running."),
]:
    draw(ML + 8, y, n, "Inter-Bold", 9.6, BK)
    draw(ML + 32, y, t, "Inter-Bold", 9.6, BK)
    yy = y - 13
    for ln in wrap_text(d, "Inter", 9.6, TW - 40):
        draw(ML + 32, yy, ln, "Inter", 9.6, MED); yy -= 11.5
    y = yy - 7

y -= 2
h3(y, "Phase two, four decisions not yet made"); y -= 16
for label, d in [
    ("Which indication first", "Evidence in hand, prevalence in our dataset, predicate availability."),
    ("510(k) or De Novo", "Turns on predicate availability. De Novo creates the classification others then use."),
    ("Evidence design", "Prospective with a prespecified protocol, or retrospective with an independent holdout."),
    ("Pre Submission", "A Q-Sub settles Criterion 1, classification and evidence design with the agency."),
]:
    y = row(y, label, d, row_h=20, split=170)
hrule(y, color=DV, thickness=0.4)

y -= 14
y = callout_box(y, "THE CHEAPEST STEP ON THIS LIST",
    "Schedule the Pre Submission early rather than after the evidence is built. It settles "
    "the Criterion 1 question, the classification question and the evidence question with "
    "FDA instead of with our own lawyers.")

footer(5)
c.showPage()

# ------------------------------------------------------------------ PAGE 6
y = page_start()
y = sect(y, "05", "CONTROLS AND OPEN ITEMS", "Claim Language Is The Control")

for ln in wrap_text("Intended use, as evidenced by labeling and promotional material, "
                    "determines device status. Not architecture. Not who ships the product. "
                    "If a partner markets a clinical claim on top of our inference, that "
                    "claim can attach to us.", "Inter", 10.1, TW):
    body_line(y, ln); y -= 12
y -= 10

colw = (TW - 16) / 2
h3(y, "Remove from materials"); draw(ML + colw + 16, y, "Defensible in Lane A and B", "Inter-Bold", 11.5, DK)
y -= 16
left = ["Diagnostic, diagnose, detects disease", "Screens for",
        "Clinical grade vital sign", "Identifies patients with",
        "Predicts onset of, monitors for", "Any disease name plus a detection verb"]
right = ["Acoustic measurement", "Vocal biomarker signal", "Wellness insight",
         "Performance and recovery signal", "Population level risk stratification",
         "Research use only, where accurate"]
yy = y
for i in range(len(left)):
    draw(ML + 8, yy, "–", "Inter-Bold", 7.4, MED)
    draw(ML + 17, yy, left[i], "Inter", 9.6, DK)
    draw(ML + colw + 24, yy, "–", "Inter-Bold", 7.4, MED)
    draw(ML + colw + 33, yy, right[i], "Inter", 9.6, DK)
    yy -= 13
y = yy - 4
draw(ML + 17, y, "Clinical grade vital sign is in circulation today.", "Inter-Bold", 8.4, BK)
draw(ML + colw + 33, y, "After clearance: the cleared use verbatim.", "Inter-Bold", 8.4, BK)
y -= 20

hrule(y); y -= 16
section_label(y, "06", "OPEN ITEMS"); y -= 16
h2(y, "Owners"); y -= 20

for owner, items in [
    ("REGULATORY COUNSEL", [
        "Written position on Criterion 1. If there is a contrary argument it goes in writing before it is relied on.",
        "Confirm the written assessment exists and produce the non privileged diligence summary.",
        "Advise whether any live deployment has drifted into Lane C without labeling."]),
    ("CORPORATE COUNSEL", [
        "Review Glow, Flagship, Ultimate Human, AssemblyAI and Amical for regulatory responsibility allocation and claim restriction clauses."]),
    ("PRODUCT AND ENGINEERING", [
        "Separate wellness and clinical endpoints with distinct gating, labeling and contracts.",
        "Build the Criterion 4 disclosure set. It serves the carve out argument, enterprise buyers and the submission."]),
    ("MARKETING AND GTM", [
        "Audit every live asset against the claim language list."]),
    ("AMIT", [
        "Pick the first indication and the pathway. Schedule the FDA Pre Submission."]),
]:
    draw(ML, y, owner, "Inter-Bold", 7.4, MU); y -= 13
    for it in items:
        y = bullet(y, it, leading=11.5); y -= 2
    y -= 5

footer(6)
c.showPage()

c.save()
print("OK")
