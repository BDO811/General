# -*- coding: utf-8 -*-
"""Amplifier Health, LP Diligence Response, September 2026.

    python3 lp_diligence_response.py                          # AMPLIFIER-DESIGN-PALETTE
    python3 lp_diligence_response.py AMPLIFIER-DARK-PALETTE   # screen cut
"""
import os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(D))
from amplifier_doc_kit import AmplifierDoc
from amplifier_palettes import DEFAULT

PAL = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).upper()
TAG = "dark" if "DARK" in PAL else "design"
OUT = os.path.join(D, "Amplifier_LP_Diligence_Response_%s.pdf" % TAG)
BACKDROP = os.path.join(os.path.dirname(D), "assets", "imagery", "lp_diligence.jpg")
TOTAL = 6


def page_one(d):
    d.new_page(1, TOTAL)
    d.eyebrow("LP DILIGENCE  ·  SEPTEMBER 2026")
    y = d.hero("Diligence request.")

    y = d.callout_dark(y - 40, "Note on framing",
        "Amplifier is a frontier foundation model company, not an AI application company. The "
        "two are diligenced on different criteria, and answer 02 sets out why that distinction "
        "decides how to read everything else in here. Supporting material is attached and "
        "referenced by answer number.")

    y = d.stat_cells(y - 22, [
        ("$7.6", "M", "CASH ON HAND", "AT 30 SEPTEMBER 2026"),
        ("306",  "k", "CURRENT BURN", "PER MONTH"),
        ("30+",  "",  "MONTHS OF RUNWAY,", "NO NEW REVENUE ASSUMED"),
        ("$1",   "M", "TRAILING TWELVE MONTH", "RECOGNIZED REVENUE"),
    ], h=62)

    y = d.label(y - 26, "What is answered here")
    y = d.contents(y - 4, [
        ("01–02", "Capital And Revenue",       "Cash, burn, runway, and how this round is underwritten"),
        ("03–09", "Commercial Position",       "Volume, contracts, what is paid, data rights, launch dates"),
        ("10–12", "Validation And Regulatory", "Outside validation, false positive rates, FDA posture"),
        ("13–15", "The Round",                 "Wired against committed, the Builders process, investor rights"),
    ], x_desc=None)

    d.fine_print(78, "Prepared in response to the LP diligence request of 22 September 2026. "
                     "Attachments are referenced by answer number. Confidential, for authorized "
                     "use only.")
    d.end_page()


def page_two(d):
    d.new_page(2, TOTAL)
    y = d.section_head(680, "01", "Cash Balance And Monthly Burn")
    y = d.bullet_list(y - 6, [
        "Cash on hand is $7.6M.",
        "Current burn is 306k per month and will bump slightly through March 2027 as we finish "
        "the pre Series A engineering plan.",
        "There are several one time charges in that number for GTM and marketing functions.",
        "That calculates to over 30 months of runway with no new revenue.",
    ], size=9.0, leading=12.8)

    y = d.callout_dark(y - 10, "The take home",
        "We are not raising because we need cash. We are raising because we want strategics who "
        "can open doors.")

    y = d.section_head(y - 26, "02", "Revenue And Cash Collections, Last 12 Months")
    y = d.para(d.ML, y - 4, [
        ("Trailing twelve month recognized revenue is just over $1M. Twelve months is not a "
         "realistic metric: the model went live 1 May and we have been in market 90 days, of "
         "which part was ramp. ", "r"),
        ("We are pre scale on revenue by design.", "b"),
        (" This round has not been underwritten on trailing revenue. It is underwritten on the "
         "dataset, the model and the moat.", "r"),
    ], size=9.2, leading=13.2)

    y = d.para(d.ML, y - 8, [
        ("What follows is not a defensive position. It is what every other investor in this "
         "round is seeing. There are two very different kinds of AI investment in the market "
         "right now, and they carry different evaluation criteria.", "r"),
    ], size=9.2, leading=13.2)

    y = d.rows_start(y, "para")
    y = d.def_row(y, "Category one", "AI infrastructure and AI application companies",
                  "These businesses build on top of someone else's foundation model. Harvey "
                  "wraps GPT-4 for legal workflows. Glean wraps multiple LLMs for enterprise "
                  "search. Hippocratic wraps Llama for healthcare ops. They do not own the "
                  "underlying model. Defensibility comes from distribution, workflow "
                  "integration, vertical specialization, brand and sales motion. Gross margin "
                  "is structurally bounded by what they pay OpenAI or Anthropic per token. "
                  "For this class of company, revenue traction is exactly the right diligence "
                  "signal. The underlying technology is commoditized, so the only way to verify "
                  "durable product market fit, defensibility and unit economics is paying "
                  "customers, expansion revenue and NRR. I agree fully with your framework for "
                  "this category.",
                  right="REVENUE IS THE SIGNAL", tag_w=94.0)
    y = d.def_row(y, "Category two", "Frontier foundation model companies",
                  "Anthropic, OpenAI, Mistral, Cohere, xAI. These businesses build the model "
                  "itself. The value is not the customer list. It is the model weights, the "
                  "dataset used to train them, the talent that designed the architecture and "
                  "the compute infrastructure to keep training. These companies have "
                  "structurally long pre revenue periods, and that is not a bug. It is the "
                  "shape of the asset class.",
                  right="THE ASSET IS THE SIGNAL", tag_w=94.0)
    d.end_page()


def page_three(d):
    d.new_page(3, TOTAL)
    y = d.section_head(680, "02", "Revenue, Continued")
    y = d.h2(y - 4, "Why The Shape Of The Asset Class Matters")

    y = d.rows_start(y, "head")
    for num, title, body in [
        ("01", "Capability precedes demand",
         "Training a frontier model takes two to four years before it is useful enough to "
         "monetize. We have done it in 90 days. Capability has to cross a usefulness threshold "
         "before real customer demand exists, and we already have live B2B, B2C and B2B2C "
         "contracts."),
        ("02", "The early spend is capex and time",
         "Infrastructure, data acquisition and safety work are capital heavy and time heavy, "
         "and they land before revenue does."),
        ("03", "Then monetization compounds",
         "Once capability crosses the threshold, monetization compounds extraordinarily fast, "
         "because the marginal cost of inference is near zero and distribution is global from "
         "day one."),
    ]:
        y = d.def_row(y, num, title, body, tag_w=40.0)

    y = d.label(y - 12, "Anthropic is the cleanest case study")
    y -= 2
    X_A, X_B = d.ML + 2, d.ML + 168
    for i, (when, what) in enumerate([
        ("Founded January 2021", "Raised over $700M entirely pre product, on the model thesis."),
        ("Claude 1, March 2023", "Meaningful revenue did not arrive until late 2023, roughly three years in."),
        ("Mid 2024", "$100M ARR."),
        ("End of 2024", "Past $1B ARR. Valuation went from zero to $60B before classical SaaS metrics were measurable."),
    ]):
        y = d.table_row(y, 19.0, [
            (when, X_A, "l", "Sans-SB", 8.8, d.TX),
            (what, X_B, "l", "Sans", 8.4, d.BODY),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    y = d.para(d.ML, y - 20, [
        ("The diligence framework that built early Anthropic conviction was not ARR or NRR. It "
         "was ", "r"),
        ("dataset uniqueness, benchmarked model capability, talent density and regulatory "
         "positioning", "c"),
        (". The same was true of OpenAI through 2020, Mistral through 2023 and Cohere through "
         "2022.", "r"),
    ], size=9.2, leading=13.2)

    y = d.para(d.ML, y - 8, [
        ("Amplifier maps to the foundation model side. We are training Sona, the world's only "
         "Large Acoustic Model, the acoustic analog to an LLM. Our 2.5M clinically labeled voice "
         "interactions mapped to 15,000 ICD-10 codes are the irreplaceable asset. ", "r"),
        ("The pilots in our deck are not enterprise customers in the SaaS sense. They are model "
         "validation and data acquisition channels.", "b"),
        (" When Sona-2 crosses the next capability threshold, which is on a defined training and "
         "inference roadmap rather than a hope, the monetization curve will look like "
         "Anthropic's, not like a vertical SaaS company's.", "r"),
    ], size=9.2, leading=13.2)

    d.callout_dark(0, "The questions worth asking at this stage",
        "How irreplaceable is the dataset. How well does the model perform on emergent "
        "biomarkers it was not trained to find. How strong is the team at the model layer. I am "
        "happy to keep walking you through the dataset, the architecture, and what Sona-2 "
        "unlocks that no other model can touch.", y_bottom=72.0)
    d.end_page()


def page_four(d):
    d.new_page(4, TOTAL)
    y = d.section_head(680, "03", "Calls Per Week")
    y = d.bullet_list(y - 6, [
        "See the attached token usage report. Capacity is still massive per week with no "
        "additional infrastructure spend.",
        "Volume is gated by partner launch schedules, not by engineering.",
        "The self serve API is 90 days old and growing double digits monthly off a small base.",
    ], size=9.0, leading=12.8)

    y = d.section_head(y - 20, "04", "Executed Contracts")
    y = d.para(d.ML, y - 4, [
        ("Most of our contracts carry mutual confidentiality obligations and one counterparty "
         "is a regulated insurer.", "r"),
    ], size=9.0, leading=12.8)

    y = d.section_head(y - 20, "05", "Which Are Paid, Which Are Pilots")
    y = d.para(d.ML, y - 4, [("Model went live 1 May.", "r")], size=9.0, leading=12.8)
    y = d.rows_start(y, "para")
    for tag, title, right, body in [
        ("B2B", "Flagship Pioneering", "PLATFORM ACCESS FEE",
         "Covers three custom models, invoiced on MSA signing, with per protocol token revenue "
         "post launch."),
        ("B2C", "Glow", "CONTRACTED AND ACTIVE", ""),
        ("B2C2B", "Canada Life", "MSA AND TO IN LEGAL", ""),
        ("B2B2C", "Ultimate Human, Gary Brecka", "CONTRACTED",
         "Revenue milestones negotiated. Gary and Eddie are both personal investors and "
         "Ultimate Human has put $1M into the round."),
    ]:
        y = d.def_row(y, tag, title, body, right=right, right_color=d.MUT, tag_w=54.0)

    y = d.section_head(y - 14, "06", "How Much Has Been Paid")
    y = d.para(d.ML, y - 4, [
        ("Glow is invoiced and collects at the end of this month. The remainder are scheduled "
         "against kickoff meetings and milestones.", "r"),
    ], size=9.0, leading=12.8)

    y = d.section_head(y - 20, "07", "Cancellation Rights")
    d.para(d.ML, y - 4, [
        ("There is no real cancellation risk. ", "r"),
        ("We run the B2C deals internally with their development teams.", "b"),
        (" The B2B deal was constructed from their request and is being executed on a mandate "
         "they already hold.", "r"),
    ], size=9.0, leading=12.8)
    d.end_page()


def page_five(d):
    d.new_page(5, TOTAL)
    y = d.section_head(680, "08", "Can Partners Revoke Data Rights")
    y = d.para(d.ML, y - 4, [("Two different things.", "b")], size=9.0, leading=12.8)
    y = d.bullet_list(y - 6, [
        "Identifiable data is subject to deletion rights under the agreements and under privacy "
        "law. We honor those.",
        "De identified data licensed for model development is perpetual and irrevocable under "
        "our Data Use Agreements, and survives termination.",
    ], size=9.0, leading=12.8)

    y = d.callout_dark(y - 8, "The practical point matters more",
        "Model weights trained on de identified data are not reversible by contract "
        "termination. A partner leaving takes future data flow. It does not take back what Sona "
        "has already learned.")

    y = d.section_head(y - 26, "09", "Launch Dates")
    y -= 6
    X_P, X_W = d.ML + 2, d.ML + 200
    for i, (partner, when) in enumerate([
        ("Glow", "LAUNCHED"), ("Flagship Pioneering", "NOVEMBER 2026"),
        ("Cleveland Clinic", "DECEMBER 2026"), ("RuralAI", "DECEMBER 2026"),
        ("Spark", "DECEMBER 2026"), ("Ultimate Human", "JANUARY 2027"),
        ("Canada Life scoping", "JANUARY 2027"),
    ]):
        live = when == "LAUNCHED"
        y = d.table_row(y, 18.6, [
            (partner, X_P, "l", "Sans-SB", 8.8, d.TX),
            (when, X_W, "l", "Mono-B", 7.4, d.AC if live else d.MUT),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    y = d.section_head(y - 26, "10", "DAIC-WOZ, Bridge2AI And Outside Validation")
    y = d.para(d.ML, y - 4, [
        ("A report on Sona-2 validation is attached. Let me know if you want more.", "r"),
    ], size=9.0, leading=12.8)

    y = d.section_head(y - 20, "11", "Full Validation Report And False Positive Rates")
    d.para(d.ML, y - 4, [
        ("Per condition reports are attached. They carry cohort size and demographics, "
         "prevalence in the test set, threshold selection, sensitivity, specificity, ", "r"),
        ("false positive rate, PPV and NPV at realistic prevalence", "b"),
        (", and confidence intervals.", "r"),
    ], size=9.0, leading=12.8)

    d.callout_dark(0, "What the attachments carry",
        "Answers 10 and 11 are evidenced rather than asserted. The validation report and the "
        "per condition reports are attached and carry the operating characteristics an LP would "
        "test us on, including false positive rates at realistic prevalence.", y_bottom=72.0)
    d.end_page()


def page_six(d):
    d.new_page(6, TOTAL)
    y = d.section_head(680, "12", "Regulatory Counsel Assessment")
    y = d.para(d.ML, y - 4, [
        ("A fuller document is attached. ", "r"),
        ("Everything we sell today sits outside the device definition per that attachment, and "
         "nothing in market requires clearance.", "b"),
        (" The FDA work is a second phase by design, not a gap we have not gotten to.", "r"),
    ], size=9.0, leading=12.8)

    y = d.rows_start(y, "para")
    for num, title, body in [
        ("01", "I have run this before",
         "I spent ten years running Intrinsic Imaging, an FDA regulated CRO. We are not seeking "
         "clearance for a foundation model. You clear one intended use on one indication, and a "
         "submission is only as strong as the evidence behind that single claim."),
        ("02", "The evidence is real world data",
         "We build it through commercial deployments, from the people the product is actually "
         "for. Filing before we hold that dataset means filing a weaker submission."),
        ("03", "The infrastructure gets built once",
         "Phase one builds QMS, CFR Part 11, validation architecture, SOC 2 Type II and HIPAA "
         "BAA. Every indication after the first rides the same rails at marginal cost."),
        ("04", "The phases do not depend on each other",
         "Revenue today does not require clearance. Clearance does not require revenue. If FDA "
         "timelines move, the business keeps running."),
    ]:
        y = d.def_row(y, num, title, body, tag_w=40.0, size=8.6, leading=11.4)

    y = d.para(d.ML, y - 8, [
        ("Claim language is what determines device status, so we control it. Every commercial "
         "and marketing asset goes through the same review. ", "r"),
        ("The device pathway applies to [INDICATION], with [SUBMISSION TYPE] targeted for "
         "[DATE], funded out of the Series A.", "b"),
    ], size=8.8, leading=12.4)

    y = d.section_head(y - 20, "13", "Wired Versus Committed")
    y = d.para(d.ML, y - 4, [
        ("The amounts are unchanged from the previous table. The only outstanding funds are the "
         "$1M from Ultimate Human, a double close with their fund on 15 October. They have "
         "wired their personal checks already.", "r"),
    ], size=8.8, leading=12.4)

    y = d.section_head(y - 18, "14", "Builders VC, Valuation And Approval")
    y = d.para(d.ML, y - 4, [
        ("Builders went through a formal evaluation by the partnership and by Investment "
         "Committee. ", "r"),
        ("The valuation was set with the other investors at arm's length. I recused myself from "
         "the pricing discussion and from the board vote.", "b"),
    ], size=8.8, leading=12.4)

    y = d.section_head(y - 18, "15", "Share Class, Price And Investor Rights")
    y = d.para(d.ML, y - 4, [
        ("Same share class and same price per share as the lead, for anyone in the same closing. "
         "The operational caveat is that when an investment comes through a single vehicle, that "
         "vehicle is the holder of record and holds one position with one set of rights. What "
         "individual LPs receive is governed by that vehicle's operating agreement, which is "
         "your document, not ours.", "r"),
    ], size=8.8, leading=12.4)

    d.rule(96)
    d.draw(d.ML, 80, "Thanks", "News-I" if not d.dark else "Corm-SB", 12.0, d.BODY)
    d.draw(d.ML, 66, "a", "News-I" if not d.dark else "Corm-SB", 12.0, d.BODY)
    d.tracked(d.R - d.tracked_w("AMIT MEHTA, MD, FRCP  ·  AMIT@AMPLIFIERHEALTH.COM",
                                "Mono-M", 6.4, 0.9), 80,
              "AMIT MEHTA, MD, FRCP  ·  AMIT@AMPLIFIERHEALTH.COM", "Mono-M", 6.4, d.MUT, 0.9)
    d.end_page()


def main():
    d = AmplifierDoc(OUT, palette=PAL,
                     title="Amplifier Health, LP Diligence Response, September 2026",
                     subject="Response to the LP diligence request of 22 September 2026")
    if os.path.exists(BACKDROP):
        d.set_backdrop(BACKDROP, alpha=0.10)
    d.cover(topic="Due Diligence Questions", date="September 2026")
    d.end_page()
    page_one(d); page_two(d); page_three(d)
    page_four(d); page_five(d); page_six(d)
    d.save()
    print("wrote", OUT, "in", d.P["name"])


if __name__ == "__main__":
    main()
