# -*- coding: utf-8 -*-
"""Reference flyer. Rebuilds Amplifier_Flyer_06_Consumer_Wellness from the grid.

Copy this file, replace CONTENT, keep every call in the same order.
The grid is fixed. Write to the length budget, do not stretch the layout.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amplifier_design import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "flyer.pdf"

CONTENT = dict(
    tagline  = "Six markets, one signal",
    eyebrow  = "Sona-2 · Frontier voice model — in production",
    hero     = "Imagine if just 15 seconds of speech revealed deep insight "
               "about a person's health and wellbeing.",
    subhead  = "No needle, no X-ray, no stethoscope. Voice already carries the "
               "signal, passively and over time.",
    stats    = [("2.4M",   "World's largest dataset"),
                ("14,000", "Physician-labeled conditions & states"),
                ("75+",    "Production indicators"),
                ("40+",    "Languages")],
    section  = "Applied to · Consumer & wellness",
    lede     = "Your retention curve looks like every wellness product's retention "
               "curve. People sign up, log a few things, and stop, because the "
               "product asks more of them than it returns.",
    blocks   = [
        ("What's missing",
         "Voice is the only input that costs the user nothing extra, because they are "
         "already talking. Thirty seconds of speech produces a read that no amount of "
         "manual logging would give them."),
        ("What arrives",
         "Wellness signal across mood, energy, stress, sleep disturbance, hydration and "
         "cognitive load, framed as observation, never as a finding. Repeat samples build "
         "a personal baseline, which is where the retention argument actually lives."),
        ("Where it fits",
         "An SDK call from your existing application. The voice capture can be a dedicated "
         "moment in your product or attached to something the user is already doing."),
        ("What it doesn't do",
         "No clinical language reaches your user. No condition names, no diagnostic framing. "
         "We are not a substitute for care and your product should not imply that we are."),
    ],
    code_label = "Sample response",
    endpoint   = "POST /v2/signs/sleep_disturbance/analyze",
    code = [
        (0, None,              "{"),
        (1, '"signal": ',      '{ "name": "sleep_disturbance", "label": "Sleep disturbance detected",'),
        (2, None,              '"score": 0.58, "level": "moderate", "flagged": false },'),
        (1, '"audio_quality": ', '{ "voice_percentage": 0.90, "audio_clarity": "good" }'),
        (0, None,              "}"),
    ],
    cta        = "Request a walkthrough ->",
    contact    = "hello@amplifierhealth.com",
    foot_left  = "Amplifier Health",
    foot_right = "amplifierhealth.com",
    disclaimer = "Amplifier's voice analysis is not FDA approved and is not a diagnostic "
                 "device. Narrative interpretations are provided to qualified care or "
                 "research staff only, never as automated alerts and never directly to "
                 "the person analyzed.",
)

C = CONTENT
d = Doc(OUT, kind="flyer")
flyer_header(d, C["tagline"])
flyer_eyebrow(d, C["eyebrow"])
flyer_hero(d, C["hero"])
flyer_subhead(d, C["subhead"])
flyer_stats(d, C["stats"])
flyer_body(d, C["section"], C["lede"], C["blocks"])
flyer_code(d, C["code_label"], C["endpoint"], C["code"])
flyer_cta(d, C["cta"], C["contact"])
flyer_footer(d, C["foot_left"], C["foot_right"], C["disclaimer"])
d.save()
print("wrote %s" % OUT)
