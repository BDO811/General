# -*- coding: utf-8 -*-
"""LP diligence response to Dean Kelly, on the Amplifier proposal form.

Text is Amit's, from his edited draft. Four typo corrections only:
  "done in in 90 days"          -> "done it in 90 days"
  "counterparty is are regulated insurers" -> "counterparty is a regulated insurer"
  "before its useful"           -> "before it's useful"
  "Glow. Contacted and active"  -> "Glow. Contracted and active"
Bracketed placeholders in answer 12 are Amit's and are left as written.
"""
import sys, os
SK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "General", ".claude", "skills", "amplifier-flyer", "scripts")
if not os.path.isdir(SK):
    SK = "/home/user/General/.claude/skills/amplifier-flyer/scripts"
sys.path.insert(0, SK)
from amplifier_design import *

OUT   = sys.argv[1] if len(sys.argv) > 1 else "out/Amplifier_LP_Diligence_Response.pdf"
DATE  = "September 2026"
FOOT  = "Amplifier Health  ·  LP diligence response  ·  %s" % DATE
RUN   = "LP diligence response"
TOTAL = [0]

d = Doc(OUT, kind="proposal")

def newpage():
    proposal_footer(d, FOOT, None)
    d.new_page()
    proposal_chrome(d, RUN)
    return PG["SECTION_Y"]

def need(y, h):
    return newpage() if y - h < PG["BOTTOM"] + 12 else y

def section(y, num, title):
    y = need(y, 96)
    return proposal_section(d, y, num, title)

def para(y, text, size=9.6, color=BODY_P, lead=13.0, indent=0):
    for ln in d.wrap(text, INTER, size, PRO_TW - indent):
        y = need(y, lead + 2)
        d.text(PRO_ML + indent, y, ln, INTER, size, color)
        y -= lead
    return y - 5

def serif_sub(y, text):
    y = need(y, 26)
    d.text(PG["SUBHEAD_X"], y, text, NEWS, PG["SUBHEAD_SIZE"], ITALIC)
    return y - 16

def dash(y, text):
    lines = d.wrap(text, INTER, 9.3, PRO_TW - 22)
    y = need(y, len(lines) * 11.8 + 6)
    d.text(PG["BULLET_MARK_X"], y + PG["BULLET_MARK_DY"], "/", MONO, 6.6, INK)
    for ln in lines:
        d.text(PG["BULLET_TEXT_X"], y, ln, INTER, 9.3, ITALIC)
        y -= 11.8
    return y - 4.0

def numbered(y, n, text, label=None):
    avail = PRO_TW - 32
    y = need(y, 34)
    d.text(PRO_ML + 6, y, "%s." % n, MONO, 9.3, INK)
    x = PG["BULLET_TEXT_X"] + 8
    if label:
        d.text(x, y, label, INTER_B, 9.3, INK)
        off = d.width(label + " ", INTER_B, 9.3)
        first = d.wrap(text, INTER, 9.3, avail - off)
        d.text(x + off, y, first[0], INTER, 9.3, ITALIC)
        y -= 11.8
        rest = " ".join(first[1:])
        for ln in d.wrap(rest, INTER, 9.3, avail):
            y = need(y, 14)
            d.text(x, y, ln, INTER, 9.3, ITALIC)
            y -= 11.8
        return y - 4
    for ln in d.wrap(text, INTER, 9.3, avail):
        y = need(y, 14)
        d.text(x, y, ln, INTER, 9.3, ITALIC)
        y -= 11.8
    return y - 4

def row(y, label, value):
    y = need(y, 22)
    d.rule(y + 10, HAIR, 0.5)
    d.text(PRO_ML + 8, y, label, INTER_B, 9.3, INK)
    d.text(PRO_ML + 200, y, value, INTER, 9.3, BODY_P)
    return y - 19

# ------------------------------------------------------------------ cover
proposal_cover(
    d, "Diligence Response",
    "Fifteen questions, answered in order.",
    "Confidential  ·  For authorized use only",
    "LP diligence  ·  %s" % DATE,
    "Note on framing",
    "Amplifier is a frontier foundation model company, not an AI application "
    "company. The two are diligenced on different criteria, and answer 2 sets "
    "out why that distinction decides how to read everything else in here. "
    "Supporting material is attached and referenced by answer number.")
proposal_footer(d, FOOT, None)

# ------------------------------------------------------------------ answers
y = newpage()

y = section(y, "01", "Cash balance and monthly burn")
y = dash(y, "Cash on hand is $7.6M")
y = dash(y, "Current burn is 306k per month and will slightly bump through March 2027 as we finish the pre Series A engineering plan.")
y = dash(y, "There are several one time charges in that number for GTM and Marketing functions.")
y = dash(y, "This is calculated at over 30 months of runway with no new revenue. I would say the take home is we are not raising at this point because we need cash, more we want strategics who can open doors")
y -= 10

y = section(y, "02", "Revenue and cash collections, last 12 months")
y = para(y, "Trailing twelve months recognized revenue is just over $1M. The twelve months isn't a metric that is realistic as the model went live May 1st and so we have only been in market for 90 days of which there is a ramp up. We are pre scale on revenue by design. This round by all has not been underwritten on trailing revenue. It's underwritten on the dataset, the model and the moat.")
y = para(y, "I don't want to give you the next two paragraphs of narrative as a “defensive position”, but more to give you optics on what all the other investors see and what we've talked about this before: as you know, there are two very different kinds of AI investments in the market right now, and I believe as we invest our fund that they have very different evaluation criteria.")
y -= 6

y = serif_sub(y, "Category one. AI infrastructure and AI application companies.")
y = para(y, "These businesses build on top of someone else's foundation model. Harvey wraps GPT-4 for legal workflows. Glean wraps multiple LLMs for enterprise search. Hippocratic wraps Llama for healthcare ops. They do not own the underlying model. Their defensibility comes from distribution, workflow integration, vertical specialization, brand, and sales motion. Their gross margin is structurally bounded by what they pay OpenAI or Anthropic per token.")
y = para(y, "For this class of company, revenue traction is exactly the right diligence signal. The underlying technology is commoditized, so the only way to verify durable product-market fit, defensibility, and unit economics is paying customers, expansion revenue, and NRR. I agree fully with your framework for this category.")
y -= 6

y = serif_sub(y, "Category two. Frontier foundation model companies.")
y = para(y, "Anthropic, OpenAI, Mistral, Cohere, xAI. These businesses build the model itself. The value is not the customer list. The value is the model weights, the dataset used to train them, the talent that designed the architecture, and the compute infrastructure to keep training. These companies have structurally long pre-revenue periods, and that is not a bug. It is the shape of the asset class:")
y = numbered(y, "1", "Training a frontier model takes two to four years before it's useful enough to monetize - we've done it in 90 days. Capability has to cross a usefulness threshold before real customer demand exists. Having said that, we have real B2B, B2C and B2B2C contracts live.")
y = numbered(y, "2", "Infrastructure, data acquisition, and safety work are capex- and time-heavy.")
y = numbered(y, "3", "Once capability crosses the threshold, monetization compounds extraordinarily fast because the marginal cost of inference is near-zero and distribution is global from day one.")
y -= 8

y = serif_sub(y, "Anthropic is the cleanest case study.")
y = para(y, "Founded January 2021. Raised over $700M entirely pre-product on the model thesis. Claude 1 didn't launch until March 2023. Meaningful revenue didn't arrive until late 2023, roughly 3 years in. By mid-2024 they were at $100M ARR. By end of 2024 they were past $1B ARR. The valuation went from zero to $60B+ before classical SaaS metrics were even measurable.")
y = para(y, "The diligence framework that built early Anthropic conviction was not ARR or NRR. It was: dataset uniqueness, benchmarked model capability, talent density, and regulatory positioning. The same was true of OpenAI through 2020, Mistral through 2023, and Cohere through 2022.")
y -= 6

y = serif_sub(y, "Amplifier maps to the foundation model side.")
y = para(y, "We are training Sona, the world's only Large Acoustic Model. The acoustic analog to an LLM. Our 2.5M+ clinically-labeled voice interactions mapped to 15,000+ ICD-10 codes is the irreplaceable asset. The pilots in our deck are not enterprise customers in the SaaS sense. They are model validation and data acquisition channels. When Sona-2 crosses the next capability threshold (which is on a defined training and inference roadmap, not a hope), the monetization curve will look like Anthropics, not like a vertical SaaS company.")
y = para(y, "So our investors have asked the right diligence questions at this stage which are likely: how irreplaceable is the dataset, how well does the model perform on emergent biomarkers it was not trained to find and how strong is the team at the model layer. To that extent, I'm happy to continue to walk you through the dataset, the architecture, and what Sona-2 is unlocking that no other model in the world can touch.")
y -= 10

y = section(y, "03", "Calls per week")
y = para(y, "See attachment of token usage. Capacity is still massive per week with no additional infrastructure spend. Volume is gated by partner launch schedules, not by engineering.")
y = para(y, "The self serve API is 90 days old and growing double digits monthly off a small base.")
y -= 10

y = section(y, "04", "Executed contracts")
y = para(y, "Most of our contracts carry several mutual confidentiality obligations and one counterparty is a regulated insurer.")
y -= 10

y = section(y, "05", "Which are paid, which are unpaid pilots or evaluations")
y = para(y, "Model went live May 1.", size=9.0, color=MUTED_P, lead=12)
y = numbered(y, "1", "Platform access fee covering three custom models, invoiced on MSA signing, with per protocol token revenue post launch.", label="B2B: Flagship Pioneering.")
y = numbered(y, "2", "Contracted and active.", label="B2C: Glow.")
y = numbered(y, "3", "MSA and TO drafted and in legal.", label="B2C2B: Canada Life.")
y = numbered(y, "4", "Contracted. Revenue milestones negotiated. They are both personal investors (Gary and Eddie) and Ultimate Human has also put $1M into the round.", label="B2B2C: Ultimate Human, Gary Brecka.")
y -= 10

y = section(y, "06", "How much has been paid")
y = para(y, "Glow invoiced and will collect at the end of this month. The remainder are all scheduled against kickoff meetings and milestones.")
y -= 10

y = section(y, "07", "Cancellation rights")
y = para(y, "There are no real risks of cancellation. We are running the B2C deals internally with development teams with them. The B2B deal is constructed from THEIR request and being executed on a mandate that they have.")
y -= 10

y = section(y, "08", "Can partners revoke data rights")
y = para(y, "Two different things.")
y = dash(y, "Identifiable data is subject to deletion rights under the agreements and under privacy law. We honor those.")
y = dash(y, "De identified data licensed for model development is perpetual and irrevocable under our DUA, Data Use Agreements, and survives termination.")
y = dash(y, "The practical point matters more. Model weights trained on de-identified data are not reversible by contract termination. A partner leaving takes future data flow. It doesn't take back what Sona has already learned.")
y -= 10

y = section(y, "09", "Launch dates")
for lbl, val in [("Glow", "Launched"),
                 ("Flagship Pioneering", "November 2026"),
                 ("Cleveland Clinic", "December 2026"),
                 ("RuralAI", "December 2026"),
                 ("Spark", "December 2026"),
                 ("Ultimate Human", "January 2027"),
                 ("Canada Life scoping", "January 2027")]:
    y = row(y, lbl, val)
d.rule(y + 10, HAIR, 0.5)
y -= 14

y = section(y, "10", "DAIC-WOZ, Bridge2AI, and outside validation")
y = para(y, "I've attached a report on Sona-2 validation. Let me know if you want more.")
y -= 10

y = section(y, "11", "Full validation report and false positive rates")
y = para(y, "Per condition reports attached. They carry cohort size and demographics, prevalence in the test set, threshold selection, sensitivity, specificity, false positive rate, PPV and NPV at realistic prevalence, and confidence intervals.")
y -= 10

y = section(y, "12", "Regulatory counsel assessment")
y = para(y, "I'm attaching a document that goes deeper. Everything we sell today sits in the FDA exempt per attachment. Nothing in market requires clearance.")
y = para(y, "The FDA work is a second phase by design, not a gap we haven't gotten to.")
y = numbered(y, "1", "I spent 10 years running Intrinsic Imaging (www.IntrinsicImaging.com) which is a FDA regulated CRO so I have experience in this exact area. We are not ultimately seeking clearance for a foundation model. You clear one intended use on one indication. A submission is only as strong as the evidence behind that single claim.")
y = numbered(y, "2", "That evidence is real world data. We will plan through commercial deployments, from the people the product is actually for a dataset for the submission. If we file before we have it means filing a weaker one.")
y = numbered(y, "3", "Phase one builds the regulatory infrastructure once. QMS, CFR Part 11, validation architecture, SOC 2 Type II, HIPAA BAA. Following that every indication after the first rides the same rails at marginal cost.")
y = numbered(y, "4", "The phases don't depend on each other. Revenue today doesn't require clearance. Clearance doesn't require revenue. If FDA timelines move, the business keeps running.")
y = para(y, "The device pathway applies to [X], with [SUBMISSION TYPE] targeted for [DATE], funded out of the Series A.")
y = para(y, "Claim language is what determines device status, so we control it. Every commercial and marketing asset goes through the same review.")
y -= 10

y = section(y, "13", "Wired versus committed")
y = para(y, "The amounts are unchanged from the previous table I sent you. The only outstanding funds are the $1M from Ultimate Shares which is a double close with their fund on October 15. They have wired their personal checks already. Let me know if you need more color.")
y -= 10

y = section(y, "14", "Builders VC, valuation and approval")
y = para(y, "Builders went through a formal evaluation process through the partnership as well as Investment Committee where I recused myself. The valuation was set with the other investors at arms length. I recused myself from the pricing discussion and from the board vote.")
y -= 10

y = section(y, "15", "Share class, price and investor rights")
y = para(y, "Yes. The caveat operationally as you know is when the investment comes through a single vehicle, that vehicle is the holder of record and holds one position with one set of rights. What individual LPs get is governed by the vehicles operating agreement, which is your document, not ours.")
y = dash(y, "Terms. Same share class and same price per share as the lead for anyone in the same closing.")
y -= 16

y = need(y, 70)
d.rule(y + 8, INK, 0.5)
y -= 8
d.text(PRO_ML, y, "Thanks", INTER, 9.6, BODY_P); y -= 14
d.text(PRO_ML, y, "a", INTER, 9.6, BODY_P); y -= 22
d.text(PRO_ML, y, "Amit Mehta, MD, FRCP", INTER_B, 9.6, INK); y -= 13
d.text(PRO_ML, y, "amit@amplifierhealth.com", INTER, 9.3, BODY_P)

proposal_footer(d, FOOT, None)
d.save()
print("wrote %s, %d pages" % (OUT, d.page))
