# -*- coding: utf-8 -*-
"""Sona-2 model performance, validation summary and publication status.

    python3 sona2_charts.py && python3 sona2_performance.py
    python3 sona2_charts.py AMPLIFIER-DARK-PALETTE && python3 sona2_performance.py AMPLIFIER-DARK-PALETTE
"""
import os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(D))
from amplifier_doc_kit import AmplifierDoc
from amplifier_palettes import DEFAULT

PAL = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).upper()
TAG = "dark" if "DARK" in PAL else "design"
OUT = os.path.join(D, "Sona2_Model_Performance_Summary_%s.pdf" % TAG)
CHART = os.path.join(D, "chart_auc_%s.png" % TAG)
BACKDROP = os.path.join(os.path.dirname(D), "assets", "imagery", "sona2.jpg")
TOTAL = 6

FLAGSHIP = [
    ("Traumatic brain injury",      "0.962", "0.896", "0.891", "1,773"),
    ("COPD",                        "0.944", "0.848", "0.876", "1,312"),
    ("Dehydration",                 "0.942", "0.869", "0.871", "1,008"),
    ("Acute stress and nervousness","0.910", "0.780", "0.891", "1,177"),
    ("PTSD",                        "0.907", "0.888", "0.745", "309"),
    ("Anxiety (GAD)",               "0.884", "0.764", "0.850", "9,607"),
    ("Overweight and obesity",      "0.871", "0.744", "0.833", "3,120"),
    ("Depression (MDD)",            "0.874", "0.722", "0.866", "4,062"),
    ("Sleep disorders",             "0.823", "0.661", "0.831", "1,440"),
    ("Cognitive impairment",        "0.777", "0.735", "0.635", "756"),
]

GARDEN = [
    ("Anemia (India)", "0.860", "57"),      ("ADHD", "0.848", "1,605"),
    ("Alcohol use disorder", "0.846", "422"),
    ("Psychoactive substance use", "0.845", "1,088"),
    ("Dry mouth", "0.841", "101"),          ("Depression (female)", "0.836", "2,605"),
    ("Depression (male)", "0.836", "1,486"),("Elevated blood pressure", "0.834", "6,859"),
    ("Anxiety (female)", "0.832", "5,457"), ("Allergy", "0.830", "3,517"),
    ("Fatigue and malaise", "0.827", "1,784"), ("Anxiety (male)", "0.825", "3,241"),
    ("PCOS", "0.811", "418"),               ("OCD", "0.786", "120"),
    ("Anemia", "0.779", "1,555"),           ("Bipolar disorder", "0.726", "229"),
    ("Migraine", "0.722", "2,581"),         ("Allergic rhinitis", "n/r", "n/r"),
]

PURGATORY = [
    ("ADHD v0.3.0", "0.848", "1,605"),      ("PTSD, voice activity only", "0.822", "110"),
    ("Type 1 diabetes", "0.756", "335"),    ("Hypoglycemia", "0.690", "57"),
    ("Pregnancy", "0.680", "1,156"),        ("Type 2 diabetes", "0.673", "809"),
    ("Hypertension", "0.653", "14,479"),    ("Suicide risk, experimental", "0.640", "279"),
    ("Ischemic heart disease", "0.628", "216"), ("Heart failure", "0.592", "160"),
    ("Mild cognitive impairment", "0.560", "76"),
    ("Sensorineural hearing loss", "0.415", "33"),
]

BENCHMARKS = [
    ("PTSD", "0.907",
     "Marmar et al. 2019, Depress Anxiety: AUC 0.954 in US veterans, the landmark study. "
     "Sona-2 performs above benchmark."),
    ("Depression", "0.874",
     "Briganti and Lechien 2025 systematic review, 12 studies and 16,872 people: AUC 0.71 to "
     "0.93. Lu et al. 2025 meta analysis: pooled AUC 0.89 to 0.91. Sona-2 sits at the top of "
     "the published range."),
    ("Anxiety", "0.884",
     "Lin et al. 2022, Ellipsis Health: AUC 0.82 combined depression and anxiety. Riad et al. "
     "2024: GAD-7 AUC 0.77. Sona-2 sits at or above the top of the published field."),
    ("COPD", "0.944",
     "Yan et al. 2025, Comput Methods Programs Biomed: AUC 0.955 on a comparable respiratory "
     "dataset. Sona-2 is at the leading edge of published result."),
    ("TBI", "0.962",
     "One of the first speech based screening benchmarks published for this condition, "
     "positioning Amplifier as an early leader in an emerging area of clinical voice research."),
    ("Dehydration", "0.942",
     "Establishing a new benchmark in an emerging area of voice based clinical screening, "
     "ahead of the published field."),
]


def grid_two(d, y, rows, cols=2, row_h=14.6, head=("CONDITION", "AUC", "N")):
    """Compact three up grid of condition, AUC and n. Reads faster than prose."""
    colw = d.TW / cols
    for c in range(cols):
        x = d.ML + c * colw
        d.tracked(x, y, head[0], "Mono-M", 5.2, d.MUT, 0.8)
        d.tracked(x + colw - 86, y, head[1], "Mono-M", 5.2, d.MUT, 0.8)
        d.tracked(x + colw - 38, y, head[2], "Mono-M", 5.2, d.MUT, 0.8)
    d.rule(y - 6, d.AC, 0.7)
    per = (len(rows) + cols - 1) // cols
    y0 = y - 6
    for i, (name, auc, n) in enumerate(rows):
        c, r = i // per, i % per
        x = d.ML + c * colw
        yy = y0 - 12 - r * row_h
        if r % 2 == 0:
            d.rect(x, yy - 4, colw - 8, row_h, d.SURF)
        d.draw(x, yy, name, "Sans", 8.0, d.BODY)
        d.draw_right(x + colw - 62, yy, auc, "Mono-M", 7.6, d.TX)
        d.draw_right(x + colw - 18, yy, n, "Mono", 7.2, d.MUT)
    return y0 - 12 - per * row_h


def page_one(d):
    d.new_page(1, TOTAL)
    d.eyebrow("SONA-2 MODEL PERFORMANCE  ·  AUGUST 2026")
    y = d.hero("Sona-2 model performance.")
    y = d.deck(d.ML, 596, "Validation summary and publication status.")

    y = d.callout_dark(y - 16, "What this is",
        "Sona-2 is the acoustic foundation model underneath all of Amplifier's condition "
        "classifiers, running production architecture v0.2.0 across a 40 model registry, 28 in "
        "general release and 12 experimental. In domain held out AUCs are top of market and "
        "stable across multiple reporting periods, ranging from 0.777 to 0.962 across the ten "
        "flagship conditions.")

    y = d.stat_cells(y - 22, [
        ("0.962",  "",  "HIGHEST IN DOMAIN AUC,", "TRAUMATIC BRAIN INJURY"),
        ("40",     "",  "MODEL REGISTRY, 28 IN", "RELEASE, 12 EXPERIMENTAL"),
        ("1.42",   "M", "VOICE SAMPLES UTILIZED,", "843,069 UNIQUE PATIENTS"),
        ("14,285", "",  "DISTINCT ICD-10 CODES", "MAPPED TO THE CORPUS"),
    ], h=62)

    y = d.label(y - 26, "Contents")
    y = d.contents(y - 4, [
        ("01", "What Sona-2 Is",            "The registry, the product families, the corpus"),
        ("02", "Held Out Validation",       "Current production results across the full registry"),
        ("03", "What It Does Not Show",     "Consistency verified, generalizability in progress"),
        ("04", "Next Generation",           "WavLM architecture, evaluated and held for release"),
        ("05", "Published Literature",      "What the team has in print and in review"),
        ("06", "Against The Field",         "Sona-2 next to published benchmarks, condition by condition"),
        ("07", "Publication Timeline",      "Manuscripts, venues and the sequence to Series A"),
    ])

    d.fine_print(78, "Every metric in this document is measured against conversational primary "
                     "care visits with English speaking US adults aged 18 and over. Internal use "
                     "only.")
    d.end_page()


def page_two(d):
    d.new_page(2, TOTAL)
    y = d.section_head(680, "01", "What Sona-2 Is")
    y = d.h2(y - 4, "The Model Underneath Everything")
    y = d.para(d.ML, y - 14, [
        ("Sona-2 is Amplifier's underlying acoustic foundation model, the shared engine behind "
         "the Amplifier Voice API. ", "r"),
        ("It is not itself a single diagnostic score.", "b"),
        (" Individual per condition classifiers are trained on top of it and organized into a "
         "two tier internal registry.", "r"),
    ], size=9.2, leading=13.2)

    y = d.rows_start(y, "para")
    for tag, title, right, body in [
        ("Tier one", "Model Garden", "28 MODELS",
         "General release and production eligible. The ten flagship conditions in Section 02 sit "
         "here, alongside eighteen more."),
        ("Tier two", "Purgatory", "12 MODELS",
         "Experimental, gated behind a minimum bar of AUC at or above 0.69, balanced sensitivity "
         "and specificity at or above 60%, and n greater than 100 before graduating."),
        ("On top", "Product families", "HAVEN / BREATH / CLARITY",
         "Haven covers depression risk and PTSD risk, Breath covers COPD, Clarity covers "
         "cognitive impact markers and TBI. Apex, Aria, Harbor and Pulse sit separately. "
         "Sona-Pulse and Sona-Aria have been shared externally with at least one partner under "
         "confidentiality."),
        ("Architecture", "Production v0.2.0", "FEATURE BASED",
         "A newer WavLM based neural architecture, internally v1.0 or v0.4.0, has been trained "
         "and evaluated but deliberately held back from release for GTM cadence. Section 04."),
    ]:
        y = d.def_row(y, tag, title, body, right=right, right_color=d.MUT, tag_w=84.0)

    y = d.label(y - 14, "The corpus every metric is measured against")
    y = d.stat_cells(y - 4, [
        ("1,418,206", "", "VOICE SAMPLES IN THE", "UTILIZED PORTION"),
        ("843,069",   "", "UNIQUE PATIENTS", "REPRESENTED"),
        ("14,285",    "", "DISTINCT ICD-10", "CODES MAPPED"),
        ("18+",       "", "ENGLISH SPEAKING US ADULTS,", "PRIMARY CARE VISITS"),
    ], h=62)

    d.callout_dark(0, "Read the registry this way",
        "One foundation model, forty classifiers on top of it, and a published bar a model must "
        "clear before it leaves the experimental tier. The bar is what makes the Model Garden "
        "numbers mean something.", y_bottom=72.0)
    d.end_page()


def page_three(d):
    d.new_page(3, TOTAL)
    y = d.section_head(680, "02", "Held Out Validation")
    y = d.h2(y - 4, "Current Production Results")
    y = d.para(d.ML, y - 14, [
        ("The ten conditions below are the flagship models in the Model Garden. ", "r"),
        ("Every AUC value here is identical to the pre production snapshot", "b"),
        (", a strong signal of model stability.", "r"),
    ], size=9.0, leading=12.8)

    y = d.image_panel(y - 10, CHART, 7.0, 2.95)

    X_C, X_AUC, X_SENS, X_SPEC, X_N = d.ML + 2, 330, 396, 462, d.R - 2
    y = d.table_header(y - 22, [("CONDITION", X_C, "l"), ("AUC", X_AUC, "r"),
                                ("SENS", X_SENS, "r"), ("SPEC", X_SPEC, "r"),
                                ("N (TEST)", X_N, "r")])
    for i, (cond, auc, sens, spec, n) in enumerate(FLAGSHIP):
        y = d.table_row(y, 17.6, [
            (cond, X_C, "l", "Sans-SB", 8.6, d.TX),
            (auc, X_AUC, "r", "Mono-B", 8.4, d.AC),
            (sens, X_SENS, "r", "Mono", 8.0, d.BODY),
            (spec, X_SPEC, "r", "Mono", 8.0, d.BODY),
            (n, X_N, "r", "Mono", 8.0, d.MUT),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    d.callout_dark(0, "What the table is measured on",
        "Every figure is in domain held out performance on the corpus described in Section 01. "
        "Cross dataset validation and acoustic robustness work is ongoing and is covered in "
        "Section 03.", y_bottom=72.0)
    d.end_page()


def page_four(d):
    d.new_page(4, TOTAL)
    y = d.section_head(680, "02", "Held Out Validation, Continued")
    y = d.h2(y - 4, "The Rest Of The Registry")

    y = d.label(y - 18, "The other eighteen Model Garden conditions")
    y = grid_two(d, y - 4, GARDEN)

    y = d.label(y - 22, "The twelve Purgatory models, active development pipeline")
    y = grid_two(d, y - 4, PURGATORY)

    y = d.label(y - 24, "Evidence tiers")
    y = d.para(d.ML, y - 2, [
        ("Each model carries an internal evidence tier reflecting clinical confidence. The "
         "majority of Model Garden conditions, including depression, anxiety, elevated blood "
         "pressure, acute stress and nervousness, fatigue and malaise, depression in females "
         "and anxiety in females, are rated ", "r"),
        ("CS Established", "c"),
        (", meaning strong clinical evidence validated across multiple datasets. "
         "Hyperandrogenism, PCOS, is rated ", "r"),
        ("Emerging", "c"),
        (", with promising results supporting further validation. Anemia and dehydration remain "
         "in active early stage development.", "r"),
    ], size=8.8, leading=12.6)

    d.callout_dark(0, "Why the weak models are published here",
        "The Purgatory tier is shown in full, including the models below the bar. A registry "
        "that only reports its winners is not a registry, it is a marketing page.",
        y_bottom=72.0)
    d.end_page()


def page_five(d):
    d.new_page(5, TOTAL)
    y = d.section_head(680, "03", "What It Does Not Show")
    y = d.h2(y - 4, "Verified Consistency, Generalizability In Progress")
    y = d.bullet_list(y - 16, [
        "The production pipeline has been verified for consistency between the live staging "
        "environment and the offline reference implementation, with matching results, 0.8743 "
        "against 0.8715, confirming that deployed performance faithfully reflects the model as "
        "trained.",
        "The team continues to broaden testing across additional populations and recording "
        "conditions to further strengthen generalizability, including ongoing work on cross "
        "dataset validation and acoustic robustness, building on an already strong in domain "
        "performance base.",
    ], size=9.0, leading=12.8)

    y = d.section_head(y - 24, "04", "Next Generation Architecture")
    y = d.h2(y - 4, "WavLM, Evaluated And Held")
    y = d.para(d.ML, y - 16, [
        ("A WavLM based neural architecture, internal v1.0 and sometimes called the shared "
         "representation or deepband approach, was evaluated head to head against current "
         "production across ten conditions in July 2026. It reached ", "r"),
        ("near parity with production", "b"),
        (", mean AUC 0.854 against 0.866, and improved results on PTSD, allergy and "
         "hypertension. It is held for the next scheduled platform update, targeted for the "
         "end of Q3 2026, as part of the quarterly release cadence.", "r"),
    ], size=9.0, leading=12.8)

    y = d.section_head(y - 26, "05", "Published Literature")
    y = d.h2(y - 4, "What The Team Has In Print")
    y = d.rows_start(y, "head")
    for tag, title, right, body in [
        ("In print", "Conversational speech for respiratory triage in primary care",
         "FRONTIERS IN MEDICINE 2026",
         "Ravi, V. and Noufi, C., 2026;13:1895376, both authors affiliated with Amplifier "
         "Health. Used 514,377 ambient recorded primary care visits across 379,225 patients to "
         "train eleven binary respiratory classifiers, with test set AUCs from 0.602 to 0.745. "
         "A medRxiv preprint went live in June 2026."),
        ("In print", "Translating AI research into reality, the 2025 Voice AI Symposium",
         "FRONTIERS IN DIGITAL HEALTH 2026",
         "Camille Noufi, lead model scientist, co authored this field overview, 2026;8:1754426, "
         "tied to the NIH funded Bridge2AI-Voice consortium."),
        ("In review", "Voice and aging, JHU collaborative study", "TARGETING JMIR AGING",
         "Drafted with external co authors and circulated for author review in June 2026."),
        ("Foundation", "Pediatric TBI vocal biomarkers", "INTERSPEECH 2019",
         "Noufi's pre Amplifier academic work, the academic foundation behind the TBI model."),
    ]:
        y = d.def_row(y, tag, title, body, right=right, right_color=d.MUT, tag_w=66.0,
                      size=8.6, leading=11.4)
    d.end_page()


def page_six(d):
    d.new_page(6, TOTAL)
    y = d.section_head(680, "06", "Against The Field")
    y = d.h2(y - 4, "Sona-2 Next To Published Benchmarks")
    y -= 20

    X_C, X_A, X_B = d.ML + 2, d.ML + 120, d.ML + 162
    y = d.table_header(y, [("CONDITION", X_C, "l"), ("SONA-2", X_A, "r"),
                           ("PUBLISHED BENCHMARK", X_B, "l")])
    for i, (cond, auc, note) in enumerate(BENCHMARKS):
        lines = d.wrap_plain(note, "Sans", 8.2, d.R - X_B - 2)
        h = max(21.0, 11 + len(lines) * 11.0)
        if i % 2 == 0:
            d.rect(d.ML, y - h, d.TW, h, d.SURF)
        ty = y - h + (h - len(lines) * 11.0) / 2.0 + (len(lines) - 1) * 11.0
        d.draw(X_C, ty, cond, "Sans-SB", 8.8, d.TX)
        d.draw_right(X_A, ty, auc, "Mono-B", 8.4, d.AC)
        for ln in lines:
            d.draw(X_B, ty, ln, "Sans", 8.2, d.BODY); ty -= 11.0
        y -= h
    d.rule(y, d.AC, 0.8)

    y = d.section_head(y - 30, "07", "Publication Timeline")
    y = d.h2(y - 4, "Manuscripts, Venues And Sequence")
    y = d.para(d.ML, y - 16, [
        ("Several Sona-2 publications are in active development. The prepared manuscripts are a "
         "technical paper on the model's self supervised architecture and a clinical validation "
         "paper, targeting ", "r"),
        ("npj Digital Medicine", "c"),
        (" as the primary venue, with Lancet Digital Health, Communications Medicine and "
         "Scientific Reports as strong alternates.", "r"),
    ], size=9.0, leading=12.8)

    y = d.label(y - 14, "The planned sequence")
    y -= 4
    X_S, X_D = d.ML + 2, d.ML + 150
    for i, (step, desc) in enumerate([
        ("01  Provisional patent", "Filed first, before anything goes public."),
        ("02  arXiv preprint", "Establishes the timestamp and circulates the architecture work."),
        ("03  Peer reviewed submission", "npj Digital Medicine primary, three named alternates."),
        ("04  Publication", "Targeted ahead of the Series A raise in 2027."),
    ]):
        y = d.table_row(y, 19.0, [
            (step, X_S, "l", "Sans-SB", 8.8, d.TX),
            (desc, X_D, "l", "Sans", 8.4, d.BODY),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    d.callout_dark(0, "Why this matters for the raise",
        "This builds on the team's existing publication record in Section 05 and puts peer "
        "reviewed validation of Sona-2 in front of the market alongside the next fundraise.",
        y_bottom=72.0)
    d.end_page()


def main():
    d = AmplifierDoc(OUT, palette=PAL,
                     title="Sona-2 Model Performance, Validation Summary, August 2026",
                     subject="Held out validation, benchmarks and publication status",
                     confidential="CONFIDENTIAL  ·  INTERNAL USE ONLY",
                     footer="AMPLIFIER HEALTH  ·  CONFIDENTIAL  ·  INTERNAL")
    if os.path.exists(BACKDROP):
        d.set_backdrop(BACKDROP, alpha=0.10)
    d.cover(topic="Sona-2 Model Performance", date="August 2026")
    d.end_page()
    page_one(d); page_two(d); page_three(d); page_four(d)
    page_five(d); page_six(d)
    d.save()
    print("wrote", OUT, "in", d.P["name"])


if __name__ == "__main__":
    main()
