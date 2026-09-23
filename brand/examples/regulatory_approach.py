# -*- coding: utf-8 -*-
"""Amplifier Health, Regulatory Approach, September 2026.

    python3 regulatory_approach.py                          # AMPLIFIER-DESIGN-PALETTE
    python3 regulatory_approach.py AMPLIFIER-DARK-PALETTE   # screen cut
"""
import os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(D))
from amplifier_doc_kit import AmplifierDoc
from amplifier_palettes import DEFAULT

PAL = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).upper()
TAG = "dark" if "DARK" in PAL else "design"
OUT = os.path.join(D, "Amplifier_Regulatory_Approach_%s.pdf" % TAG)
BACKDROP = os.path.join(os.path.dirname(D), "assets", "imagery", "regulatory_approach.jpg")
TOTAL = 6


def page_one(d):
    d.new_page(1, TOTAL)
    d.eyebrow("REGULATORY APPROACH  ·  SEPTEMBER 2026")
    y = d.hero("Regulatory approach.")
    y = d.deck(d.ML, 596, "FDA pathway and the two phase strategy.")

    y = d.callout_dark(y - 16, "What this is",
        "Voice analysis that interprets clinical state fails Criterion 1 of the Cures Act "
        "clinical decision support exclusion. The CDS carve out is not the lane it was assumed "
        "to be. The non device position rests on general wellness and non patient care uses. "
        "Everything carrying a disease claim is a device and needs clearance. This document "
        "sets out the three lanes that remain, why clearance is sequenced as a second phase, "
        "and what phase one must hold to stay clean.")

    y = d.stat_cells(y - 22, [
        ("3",     "",  "REGULATORY LANES THAT", "REMAIN OPEN TO US"),
        ("4",     "",  "CURES CRITERIA,", "ALL FOUR MUST BE MET"),
        ("1",     "",  "INDICATION FIRST.", "YOU CLEAR A USE, NOT A MODEL"),
        ("$3.5",  "M", "VALIDATION, ALLOCATED", "IN THE SERIES A"),
    ], h=62)

    y = d.label(y - 26, "Contents")
    y = d.contents(y - 4, [
        ("01", "The Final Guidance",      "Four criteria, the 2026 changes, enforcement discretion"),
        ("02", "Where Amplifier Sits",    "Criterion by criterion, and the Criterion 1 problem"),
        ("03", "The Three Lanes",         "Wellness, non patient care, device, partners mapped"),
        ("04", "Why Two Phases",          "The sequencing argument and the decisions still open"),
        ("05", "Controls And Open Items", "Claim language, owners, the Pre Submission"),
    ])

    d.fine_print(84, "Sources: CDRH town hall on the Clinical Decision Support Software Final "
                     "Guidance, March 11 2026. Amplifier Financial Model v6. LP diligence "
                     "request of September 22 2026. This is analysis of published guidance. "
                     "It is not legal advice.")
    d.end_page()


def page_two(d):
    d.new_page(2, TOTAL)
    y = d.section_head(680, "01", "The Final Guidance")
    y = d.h2(y - 4, "What The Guidance Says")

    y = d.bullet_list(y - 14, [
        "The 21st Century Cures Act amended the device definition in December 2016, excluding "
        "five categories of software function under 520(o). Two matter to us: general wellness "
        "under 520(o)(1)(B), and clinical decision support under 520(o)(1)(E).",
        "The CDS guidance history runs draft December 2017, revised draft September 2019, final "
        "September 2022, and a new final published January 6 2026 and reissued January 29 2026. "
        "The January 2026 version is operative and supersedes September 2022.",
    ])

    y = d.label(y - 14, "The four criteria.  All four must be met")
    y = d.rows_start(y, "label")
    for tag, title, body in [
        ("Criterion 1", "Signal exclusion",
         "Not intended to acquire, process or analyze a medical image, a signal from an IVD, or "
         "a pattern or signal from a signal acquisition system."),
        ("Criterion 2", "Medical information",
         "Intended to display, analyze or print medical information about a patient or other "
         "medical information."),
        ("Criterion 3", "Recommendations",
         "Intended to support or provide recommendations to an HCP about prevention, diagnosis "
         "or treatment."),
        ("Criterion 4", "Independent review",
         "Intended to enable the HCP to independently review the basis, so the HCP does not rely "
         "primarily on the output."),
    ]:
        y = d.def_row(y, tag, title, body)

    y = d.label(y - 14, "Two changes in the 2026 guidance")
    y = d.bullet_list(y - 4, [
        "The interpretation that software must not support time critical decision making was "
        "removed from Criterion 3. It still bears on Criterion 4.",
        "FDA added an enforcement discretion policy. Where a function provides one clinically "
        "appropriate output and therefore fails Criterion 3, but meets every other criterion, "
        "FDA intends to exercise enforcement discretion. The guidance carries eight worked "
        "examples.",
    ])

    d.callout_dark(y - 16, "The limit of both changes",
        "Neither change helps a function that fails Criterion 1. Enforcement discretion is "
        "scoped to Criterion 3 failures only.", y_bottom=72.0)
    d.end_page()


def page_three(d):
    d.new_page(3, TOTAL)
    y = d.section_head(680, "02", "Where Amplifier Sits")
    y = d.h2(y - 4, "Criterion By Criterion")
    y = d.rows_start(y, "head")

    # the palette carries no red; a failed criterion is set in full ink
    fail = d.NEG if d.dark else d.TX
    for tag, title, verdict, vcol, body in [
        ("Criterion 1", "Signal exclusion", "FAILS", fail,
         "A microphone capturing voice for clinical inference is a system measuring a parameter "
         "external to the body for a medical purpose through streaming measurement. FDA states "
         "that software which assesses or interprets the clinical implications of a signal does "
         "not meet Criterion 1."),
        ("Criterion 2", "Medical information", "FAILS", fail,
         "Raw acoustic waveform is not on FDA's list of medical information. Where the input is "
         "a physician note, a symptom set or a lab value, Criterion 2 is satisfied. Where the "
         "input is the audio itself, it is not."),
        ("Criterion 3", "Recommendations", "ACHIEVABLE", d.AC,
         "Output presented as a list or prioritized list of options for an HCP to consider, not "
         "a directive. A binary result would fail, but that failure alone now falls inside the "
         "enforcement discretion policy if every other criterion is met."),
        ("Criterion 4", "Independent review", "BUILD FOR IT", d.AC,
         "Worth building regardless of pathway. Intended use and intended HCP user, required "
         "input medical information, a plain language description of algorithm development and "
         "validation, and stated knowns and unknowns."),
    ]:
        y = d.def_row(y, tag, title, body, right=verdict, right_color=vcol)

    y = d.callout_dark(y - 12, "The one argument we have, and its limit",
        "FDA says discrete, episodic or intermittent point in time measurements, giving routine "
        "vital signs at a clinical encounter as the example, generally do not by themselves "
        "constitute a pattern. A single voice sample at one encounter is arguably not a pattern. "
        "That defeats the pattern prong. It does not defeat the signal prong, because Criterion "
        "1 excludes a signal from a signal acquisition system independently. Longitudinal voice "
        "monitoring, core to the product thesis, fails both prongs.")

    y = d.label(y - 20, "FDA's own device examples land close")
    y = d.bullet_list(y - 4, [
        "Analyzes multiple signals from wearable products, being perspiration rate, heart rate, "
        "eye movement and breathing rate, to monitor whether a person is having a heart attack "
        "or narcolepsy episode. Device. Criterion 1, it analyzes signals.",
        "Analyzes hourly pulse oximetry and heart rate measurements from the EHR to identify "
        "signs of patient deterioration and alert an HCP. Device. Criterion 1, it analyzes a "
        "pattern.",
    ])

    y = d.label(y - 12, "What this means")
    d.para(d.ML, y - 2, [
        ("Assume every Amplifier function that interprets voice for clinical meaning falls "
         "outside the CDS carve out. ", "r"),
        ("Counsel confirms that in writing, or builds the contrary argument in writing.", "b"),
        (" Planning on the carve out without a written position is the risk.", "r"),
    ], size=9.0, leading=12.8)
    d.end_page()


def page_four(d):
    d.new_page(4, TOTAL)
    y = d.section_head(680, "03", "The Three Lanes")
    y = d.h2(y - 4, "The Lanes We Actually Have")
    y = d.para(d.ML, y - 14, [
        ("The prior working assumption was general wellness plus the CDS carve out. The correct "
         "statement is ", "r"),
        ("general wellness plus non patient care uses", "b"),
        (". That distinction matters in writing, to investors, to partners and to counsel.", "r"),
    ], size=9.0, leading=12.8)

    y = d.rows_start(y, "para")
    for tag, title, right, body in [
        ("Lane A", "General wellness", "520(o)(1)(B)",
         "Software for maintaining or encouraging a healthy lifestyle and unrelated to the "
         "diagnosis, cure, mitigation, prevention or treatment of a disease. Narrow. A single "
         "disease claim breaks it, in our marketing or in a partner's."),
        ("Lane B", "Non patient care uses", "OUTSIDE THE DEVICE DEFINITION",
         "Insurance risk assessment, actuarial and underwriting work, enterprise analytics, "
         "research use. Outside the device definition because they are not intended for the "
         "diagnosis or treatment of an individual patient. Different regulation, not lighter: "
         "insurance regulators, OSFI E-23, state insurance law, adverse action exposure."),
        ("Lane C", "Device pathway", "510(K) OR DE NOVO",
         "Anything that detects, screens for, diagnoses, predicts or monitors a disease in an "
         "individual. Anemia detection. Depression screening. Clinical deployment at a health "
         "system. The CDS carve out does not rescue these because of Criterion 1."),
    ]:
        y = d.def_row(y, tag, title, body, right=right, right_color=d.MUT)

    y = d.label(y - 10, "Partner map")
    d.draw(d.ML + 66, y + 13, "Every counterparty sits in one lane. Where it is unresolved, "
           "that is the open item.", "Sans", 8.4, d.MUT)
    X_NAME, X_LANE, X_NOTE = d.ML + 2, d.ML + 128, d.ML + 196
    y = d.table_header(y - 2, [("COUNTERPARTY", X_NAME, "l"), ("LANE", X_LANE, "l"),
                               ("POSITION", X_NOTE, "l")])
    partners = [
        ("Glow", "A or C", "Largest recurring line, related party. Endpoint and claim dependent."),
        ("Flagship Pioneering", "B", "Per protocol custom models. Confirm no patient facing output."),
        ("Ultimate Human", "A", "Consumer wellness. Highest marketing drift risk. Warrants, no cash."),
        ("Canada Life", "B", "OSFI E-23 model risk scoping. Not FDA. In negotiation."),
        ("QBE", "UNRESOLVED", "Not in the financial model. Confirm an agreement exists."),
        ("Sutter Health", "C", "Clinical in substance. Research use with IRB, or restructure."),
        ("AssemblyAI, Amical", "B or C", "They build the product. Responsibility allocation is the issue."),
        ("zebraMD", "C", "Clinical integration. Determine the output and who acts on it."),
    ]
    for i, (name, lane, note) in enumerate(partners):
        unresolved = lane == "UNRESOLVED"
        y = d.table_row(y, 19.4, [
            (name, X_NAME, "l", "Sans-SB", 8.8, d.TX),
            (lane, X_LANE, "l", "Mono-B", 7.2, d.MUT if unresolved else d.AC),
            (note, X_NOTE, "l", "Sans", 8.4, d.BODY),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    d.callout_dark(y - 18, "The control that keeps the lanes separate",
        "Wellness and clinical endpoints separately gated in the API, separately labeled and "
        "separately contracted. One endpoint serving both lanes collapses the distinction the "
        "whole position depends on.")
    d.end_page()


def page_five(d):
    d.new_page(5, TOTAL)
    y = d.section_head(680, "04", "Why Two Phases")
    y = d.h2(y - 4, "Clearance Is Sequenced Second")

    y -= 18
    gap = 10.0
    cw = (d.TW - gap) / 2.0
    h = 58.0
    for i, (lab, title, body) in enumerate([
        ("PHASE ONE  ·  NOW", "Sell in clean lanes",
         "Deployments generate clinically labeled voice at population scale."),
        ("PHASE TWO  ·  SERIES A FUNDED", "File on one indication",
         "The dataset built in phase one is the submission."),
    ]):
        x = d.ML + i * (cw + gap)
        d.rect(x, y - h, cw, h, d.SURF)
        d.rect(x, y - 1.4, cw, 1.4, d.AC)
        d.tracked(x + 12, y - 15, lab, "Mono-B", 5.8, d.AC, 1.0)
        d.draw(x + 12, y - 31, title, "Sans-SB", 10.4, d.TX)
        ty = y - 44
        for ln in d.wrap_plain(body, "Sans", 8.4, cw - 24):
            d.draw(x + 12, ty, ln, "Sans", 8.4, d.BODY); ty -= 11.0
    y -= h

    y = d.label(y - 20, "The argument")
    y = d.rows_start(y, "label")
    for num, title, body in [
        ("01", "You do not clear a foundation model",
         "You clear one intended use on one indication. A submission is only as strong as the "
         "evidence behind that single claim. Filing broadly is not an option FDA offers."),
        ("02", "The evidence is real world data",
         "Commercial deployments generate clinically labeled voice from the people the product "
         "is for, in the environment it runs in. That dataset is the submission. Filing before "
         "we hold it means filing a weaker one."),
        ("03", "Trial generated evidence costs multiples more",
         "And it produces data less representative of deployment. Both 510(k) and De Novo trial "
         "scenarios are modeled in the financial model."),
        ("04", "The infrastructure gets built once",
         "QMS, CFR Part 11, validation architecture, labeling discipline, SOC 2 Type II, HIPAA "
         "BAA. Every indication after the first rides the same rails at marginal cost."),
        ("05", "The phases do not depend on each other",
         "Revenue today does not require clearance. Clearance does not require revenue. If FDA "
         "timelines move, the business keeps running."),
    ]:
        y = d.def_row(y, num, title, body, tag_w=40.0, size=8.6, leading=11.4, gap=6.0)

    y = d.label(y - 10, "Phase two, four decisions not yet made")
    y -= 2
    X_Q, X_A = d.ML + 2, d.ML + 150
    for i, (q, a) in enumerate([
        ("Which indication first", "Evidence in hand, prevalence in our dataset, predicate availability."),
        ("510(k) or De Novo", "Turns on predicate availability. De Novo creates the classification others then use."),
        ("Evidence design", "Prospective with a prespecified protocol, or retrospective with an independent holdout."),
        ("Pre Submission", "A Q-Sub settles Criterion 1, classification and evidence design with the agency."),
    ]):
        y = d.table_row(y, 18.6, [
            (q, X_Q, "l", "Sans-SB", 8.8, d.TX),
            (a, X_A, "l", "Sans", 8.4, d.BODY),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    d.callout_dark(y - 16, "The cheapest step on this list",
        "Schedule the Pre Submission early rather than after the evidence is built. It settles "
        "the Criterion 1 question, the classification question and the evidence question with "
        "FDA instead of with our own lawyers.")
    d.end_page()


def page_six(d):
    d.new_page(6, TOTAL)
    y = d.section_head(680, "05", "Controls And Open Items")
    y = d.h2(y - 4, "Claim Language Is The Control")
    y = d.para(d.ML, y - 14, [
        ("Intended use, as evidenced by labeling and promotional material, determines device "
         "status. Not architecture. Not who ships the product. ", "r"),
        ("If a partner markets a clinical claim on top of our inference, that claim can attach "
         "to us.", "b"),
    ], size=9.0, leading=12.8)

    y = d.two_col_list(y - 14,
        "Remove from materials", [
            "Diagnostic, diagnose, detects disease",
            "Screens for",
            "Clinical grade vital sign",
            "Identifies patients with",
            "Predicts onset of, monitors for",
            "Any disease name plus a detection verb",
        ],
        "Defensible in Lane A and B", [
            "Acoustic measurement",
            "Vocal biomarker signal",
            "Wellness insight",
            "Performance and recovery signal",
            "Population level risk stratification",
            "Research use only, where accurate",
        ])

    y = d.para(d.ML, y - 6, [
        ("Clinical grade vital sign is in circulation today.", "b"),
        ("  After clearance: the cleared use verbatim.", "r"),
    ], size=8.6, leading=12.0)

    y = d.section_head(y - 22, "06", "Open Items")
    y -= 4
    for owner, items in [
        ("Regulatory counsel", [
            "Written position on Criterion 1. If there is a contrary argument it goes in writing "
            "before it is relied on.",
            "Confirm the written assessment exists and produce the non privileged diligence summary.",
            "Advise whether any live deployment has drifted into Lane C without labeling.",
        ]),
        ("Corporate counsel", [
            "Review Glow, Flagship, Ultimate Human, AssemblyAI and Amical for regulatory "
            "responsibility allocation and claim restriction clauses.",
        ]),
        ("Product and engineering", [
            "Separate wellness and clinical endpoints with distinct gating, labeling and contracts.",
            "Build the Criterion 4 disclosure set. It serves the carve out argument, enterprise "
            "buyers and the submission.",
        ]),
        ("Marketing and GTM", [
            "Audit every live asset against the claim language list.",
        ]),
        ("Amit", [
            "Pick the first indication and the pathway. Schedule the FDA Pre Submission.",
        ]),
    ]:
        d.rule(y + 10)
        d.tracked(d.ML, y, owner.upper(), "Mono-B", 5.8, d.AC, 0.9)
        ty = y
        for item in items:
            for ln in d.wrap_plain(item, "Sans", 8.4, d.TW - 150):
                d.draw(d.ML + 150, ty, ln, "Sans", 8.4, d.BODY); ty -= 11.2
            ty -= 3
        y = min(ty, y - 16) - 8

    d.callout_dark(0, "What moves first",
        "Pick the first indication and schedule the Pre Submission. Every other item on this "
        "page is downstream of that one decision.", y_bottom=72.0)
    d.end_page()


def main():
    d = AmplifierDoc(OUT, palette=PAL,
                     title="Amplifier Health, Regulatory Approach, September 2026",
                     subject="FDA pathway and the two phase strategy")
    if os.path.exists(BACKDROP):
        d.set_backdrop(BACKDROP, alpha=0.10)
    page_one(d); page_two(d); page_three(d); page_four(d); page_five(d); page_six(d)
    d.save()
    print("wrote", OUT, "in", d.P["name"])


if __name__ == "__main__":
    main()
