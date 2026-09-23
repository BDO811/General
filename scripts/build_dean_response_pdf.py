# -*- coding: utf-8 -*-
"""Amplifier Health, LP diligence response to Dean Kelly.
Amplifier design set, TEMPLATE 1, black and white.
Text is Amit's, from his edited draft. Four typo corrections only.
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

BK  = HexColor("#050505"); DK  = HexColor("#1A1A1A"); MED = HexColor("#444444")
MU  = HexColor("#888888"); LT  = HexColor("#BBBBBB"); HLT = HexColor("#DDDDDD")
DV  = HexColor("#D0D0D0"); LB  = HexColor("#F5F5F5"); BOX = HexColor("#0A0A0A")

c = canvas.Canvas("out/Amplifier_LP_Diligence_Response.pdf", pagesize=(PW, PH))
PAGE = [1]

def base(top_pt, size_pt, frac=0.758): return PH - top_pt - size_pt * frac
def draw(x, y, t, f, s, col):
    c.setFont(f, s); c.setFillColor(col); c.drawString(x, y, t)
def draw_right(x, y, t, f, s, col):
    c.setFont(f, s); c.setFillColor(col); c.drawRightString(x, y, t)
def hrule(y, color=DV, thickness=0.4):
    c.setStrokeColor(color); c.setLineWidth(thickness); c.line(ML, y, PW - MR, y)
def thick_hrule(y, color=BK, thickness=1.5):
    c.setStrokeColor(color); c.setLineWidth(thickness); c.line(ML, y, PW - MR, y)
def filled_rect(x, y, w, h, col):
    c.setFillColor(col); c.rect(x, y, w, h, stroke=0, fill=1)
def wrap_text(t, f, s, max_w):
    out = []; line = ""
    for w in t.split():
        test = (line + " " + w).strip()
        if c.stringWidth(test, f, s) <= max_w: line = test
        else:
            if line: out.append(line)
            line = w
    if line: out.append(line)
    return out
def fit_width(t, f, max_w, max_size=72, min_size=20):
    s = max_size
    while s >= min_size:
        if c.stringWidth(t, f, s) <= max_w: return s
        s -= 0.5
    return min_size
def top_bar():
    draw(ML, base(76.8, 11.04), "AMPLIFIER HEALTH", "Inter-Bold", 11.04, BK)
    draw_right(PW - MR, base(76.8, 7.44),
               "CONFIDENTIAL  ·  FOR AUTHORIZED USE ONLY", "Inter-Bold", 7.44, MU)
def footer():
    hrule(MB + 10)
    draw_right(PW - MR, MB - 2,
               "Amplifier Health  ·  Confidential  ·  %d" % PAGE[0], "Inter", 7.44, MU)
def new_page():
    footer(); c.showPage(); PAGE[0] += 1
    top_bar()
    return base(106.8, 0) - 8
def need(y, h):
    return new_page() if y - h < MB + 34 else y

def section(y, num, title):
    y = need(y, 78)
    y -= 6; hrule(y); y -= 14
    draw(ML, y, "ANSWER %s" % num, "Inter-Bold", 7.4, MU); y -= 16
    draw(ML, y, title, "Inter-Bold", 15.1, BK); y -= 20
    return y
def h3(y, t):
    y = need(y, 30); draw(ML, y, t, "Inter-Bold", 11.5, DK); return y - 16
def body(y, t, indent=0, size=10.1, col=DK, lead=12.4):
    for ln in wrap_text(t, "Inter", size, TW - indent):
        y = need(y, lead + 2)
        draw(ML + indent, y, ln, "Inter", size, col); y -= lead
    return y
def dash(y, t, indent=10, lead=12.4):
    bx = ML + indent; tx = bx + 9; avail = TW - indent - 9
    lines = wrap_text(t, "Inter", 10.1, avail)
    y = need(y, len(lines) * lead + 4)
    draw(bx, y + 2, "–", "Inter-Bold", 7.4, MED)
    for ln in lines:
        draw(tx, y, ln, "Inter", 10.1, DK); y -= lead
    return y
def num_item(y, n, t, label=None):
    bx = ML + 10; tx = bx + 22; avail = TW - 32
    first = t
    lines = wrap_text(first, "Inter", 10.1, avail)
    y = need(y, len(lines) * 12.4 + 4)
    draw(bx, y, n + ".", "Inter-Bold", 10.1, BK)
    if label:
        draw(tx, y, label, "Inter-Bold", 10.1, BK)
        off = c.stringWidth(label + " ", "Inter-Bold", 10.1)
        lines = wrap_text(t, "Inter", 10.1, avail - off)
        draw(tx + off, y, lines[0], "Inter", 10.1, DK); y -= 12.4
        for ln in wrap_text(" ".join(lines[1:]), "Inter", 10.1, avail):
            y = need(y, 14); draw(tx, y, ln, "Inter", 10.1, DK); y -= 12.4
        return y
    for ln in lines:
        draw(tx, y, ln, "Inter", 10.1, DK); y -= 12.4
    return y
def callout(y, label, text, pad_v=10, pad_h=12, line_h=12.5):
    lines = wrap_text(text, "Inter", 9.6, TW - pad_h * 2)
    box_h = pad_v + 11 + 6 + len(lines) * line_h + pad_v
    y = need(y, box_h + 12)
    filled_rect(ML, y - box_h, TW, box_h, BOX)
    ty = y - pad_v - 7.9 * 0.758
    draw(ML + pad_h, ty, label.upper(), "Inter-Bold", 7.9, HLT); ty -= 11
    for ln in lines:
        draw(ML + pad_h, ty, ln, "Inter", 9.6, LT); ty -= line_h
    return y - box_h - 10
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
def row(y, label, desc, row_h=18, split=180):
    y = need(y, row_h + 6)
    hrule(y, color=DV, thickness=0.4)
    ty = y - row_h * 0.5 - 10 * 0.758
    draw(ML + 8, ty, label, "Inter-Bold", 9.6, BK)
    draw(ML + split, ty, desc, "Inter", 9.6, MED)
    return y - row_h

# ------------------------------------------------------------------ COVER
top_bar()
draw(ML, base(106.8, 8.40), "LP DILIGENCE RESPONSE  ·  SEPTEMBER 2026",
     "Inter-Bold", 8.40, MU)
hero = "DILIGENCE RESPONSE"
hs = fit_width(hero, "Inter-Bold", TW, 72, 20); hy = base(155, hs)
draw(ML, hy, hero, "Inter-Bold", hs, BK)
sub = "PREPARED FOR DEAN KELLY AND HIS LP GROUP"
ss = min(hs - 4, fit_width(sub, "Inter-Bold", TW)); sy = hy - hs * 0.92 - 10
draw(ML, sy, sub, "Inter-Bold", ss, MED)
ry = sy - ss * 0.92 - 20; thick_hrule(ry)

y = callout(ry - 14, "WHAT THIS IS",
    "Answers to the fifteen questions of September 22 2026, numbered to match. Amplifier "
    "is a frontier foundation model company, not an AI application company, and the "
    "diligence that fits it is dataset uniqueness, benchmarked model capability, talent "
    "density and regulatory positioning. Answer 2 sets out why. Supporting attachments "
    "are referenced by answer number.")

y = stat_block(y, [
    ("$7.6M", "CASH ON HAND", "No new revenue assumed"),
    ("$306K", "MONTHLY BURN", "Includes one time GTM charges"),
    ("30+", "MONTHS RUNWAY", "At current burn"),
    ("90", "DAYS IN MARKET", "Model went live May 1"),
])

y -= 14; hrule(y); y -= 16
draw(ML, y, "ATTACHMENTS REFERENCED", "Inter-Bold", 7.4, MU); y -= 16
for n, t in [("03", "Token usage report"),
             ("10", "Sona-2 validation report"),
             ("11", "Per condition validation reports"),
             ("12", "Regulatory position and FDA exempt analysis"),
             ("13", "Funding table, previously sent")]:
    draw(ML + 8, y, n, "Inter-Bold", 9.6, BK)
    draw(ML + 40, y, t, "Inter", 9.6, MED); y -= 15
y -= 6; hrule(y); y -= 16
draw(ML, y, "Amit Mehta, MD, FRCP   ·   amit@amplifierhealth.com", "Inter-Bold", 9.6, BK)

# ------------------------------------------------------------------ ANSWERS
y = new_page()

y = section(y, "01", "Cash Balance And Monthly Burn")
y = dash(y, "Cash on hand is $7.6M")
y = dash(y, "Current burn is 306k per month and will slightly bump through March 2027 as we finish the pre Series A engineering plan.")
y = dash(y, "There are several one time charges in that number for GTM and Marketing functions.")
y = dash(y, "This is calculated at over 30 months of runway with no new revenue. I would say the take home is we are not raising at this point because we need cash, more we want strategics who can open doors")
y -= 8

y = section(y, "02", "Revenue And Cash Collections, Last 12 Months")
y = body(y, "Trailing twelve months recognized revenue is just over $1M. The twelve months isn't a metric that is realistic as the model went live May 1st and so we have only been in market for 90 days of which there is a ramp up. We are pre scale on revenue by design. This round by all has not been underwritten on trailing revenue. It's underwritten on the dataset, the model and the moat.")
y -= 6
y = body(y, "I don't want to give you the next two paragraphs of narrative as a “defensive position”, but more to give you optics on what all the other investors see and what we've talked about this before: as you know, there are two very different kinds of AI investments in the market right now, and I believe as we invest our fund that they have very different evaluation criteria.")
y -= 10

y = h3(y, "Category one. AI infrastructure and AI application companies.")
y = body(y, "These businesses build on top of someone else's foundation model. Harvey wraps GPT-4 for legal workflows. Glean wraps multiple LLMs for enterprise search. Hippocratic wraps Llama for healthcare ops. They do not own the underlying model. Their defensibility comes from distribution, workflow integration, vertical specialization, brand, and sales motion. Their gross margin is structurally bounded by what they pay OpenAI or Anthropic per token.")
y -= 6
y = body(y, "For this class of company, revenue traction is exactly the right diligence signal. The underlying technology is commoditized, so the only way to verify durable product-market fit, defensibility, and unit economics is paying customers, expansion revenue, and NRR. I agree fully with your framework for this category.")
y -= 10

y = h3(y, "Category two. Frontier foundation model companies.")
y = body(y, "Anthropic, OpenAI, Mistral, Cohere, xAI. These businesses build the model itself. The value is not the customer list. The value is the model weights, the dataset used to train them, the talent that designed the architecture, and the compute infrastructure to keep training. These companies have structurally long pre-revenue periods, and that is not a bug. It is the shape of the asset class:")
y -= 8
y = num_item(y, "1", "Training a frontier model takes two to four years before it's useful enough to monetize - we've done it in 90 days. Capability has to cross a usefulness threshold before real customer demand exists. Having said that, we have real B2B, B2C and B2B2C contracts live.")
y -= 3
y = num_item(y, "2", "Infrastructure, data acquisition, and safety work are capex- and time-heavy.")
y -= 3
y = num_item(y, "3", "Once capability crosses the threshold, monetization compounds extraordinarily fast because the marginal cost of inference is near-zero and distribution is global from day one.")
y -= 12

y = h3(y, "Anthropic is the cleanest case study.")
y = body(y, "Founded January 2021. Raised over $700M entirely pre-product on the model thesis. Claude 1 didn't launch until March 2023. Meaningful revenue didn't arrive until late 2023, roughly 3 years in. By mid-2024 they were at $100M ARR. By end of 2024 they were past $1B ARR. The valuation went from zero to $60B+ before classical SaaS metrics were even measurable.")
y -= 6
y = body(y, "The diligence framework that built early Anthropic conviction was not ARR or NRR. It was: dataset uniqueness, benchmarked model capability, talent density, and regulatory positioning. The same was true of OpenAI through 2020, Mistral through 2023, and Cohere through 2022.")
y -= 10

y = h3(y, "Amplifier maps to the foundation model side, not the infrastructure side.")
y = body(y, "We are training Sona, the world's only Large Acoustic Model. The acoustic analog to an LLM. Our 2.5M+ clinically-labeled voice interactions mapped to 15,000+ ICD-10 codes is the irreplaceable asset. The pilots in our deck are not enterprise customers in the SaaS sense. They are model validation and data acquisition channels. When Sona-2 crosses the next capability threshold (which is on a defined training and inference roadmap, not a hope), the monetization curve will look like Anthropics, not like a vertical SaaS company.")
y -= 6
y = body(y, "So our investors have asked the right diligence questions at this stage which are likely: how irreplaceable is the dataset, how well does the model perform on emergent biomarkers it was not trained to find and how strong is the team at the model layer. To that extent, I'm happy to continue to walk you through the dataset, the architecture, and what Sona-2 is unlocking that no other model in the world can touch.")
y -= 8

y = section(y, "03", "Calls Per Week")
y = body(y, "See attachment of token usage. Capacity is still massive per week with no additional infrastructure spend. Volume is gated by partner launch schedules, not by engineering.")
y -= 6
y = body(y, "The self serve API is 90 days old and growing double digits monthly off a small base.")
y -= 8

y = section(y, "04", "Executed Contracts")
y = body(y, "Most of our contracts carry several mutual confidentiality obligations and one counterparty is a regulated insurer.")
y -= 8

y = section(y, "05", "Which Are Paid, Which Are Unpaid Pilots Or Evaluations")
y = body(y, "Model went live May 1.", size=9.6, col=MU); y -= 6
y = num_item(y, "1", "Platform access fee covering three custom models, invoiced on MSA signing, with per protocol token revenue post launch.", label="B2B: Flagship Pioneering.")
y -= 3
y = num_item(y, "2", "Contracted and active.", label="B2C: Glow.")
y -= 3
y = num_item(y, "3", "MSA and TO drafted and in legal.", label="B2C2B: Canada Life.")
y -= 3
y = num_item(y, "4", "Contracted. Revenue milestones negotiated. They are both personal investors (Gary and Eddie) and Ultimate Human has also put $1M into the round.", label="B2B2C: Ultimate Human, Gary Brecka.")
y -= 10

y = section(y, "06", "How Much Has Been Paid")
y = body(y, "Glow invoiced and will collect at the end of this month. The remainder are all scheduled against kickoff meetings and milestones.")
y -= 8

y = section(y, "07", "Cancellation Rights")
y = body(y, "There are no real risks of cancellation. We are running the B2C deals internally with development teams with them. The B2B deal is constructed from THEIR request and being executed on a mandate that they have.")
y -= 8

y = section(y, "08", "Can Partners Revoke Data Rights")
y = body(y, "Two different things."); y -= 4
y = dash(y, "Identifiable data is subject to deletion rights under the agreements and under privacy law. We honor those.")
y = dash(y, "De identified data licensed for model development is perpetual and irrevocable under our DUA, Data Use Agreements, and survives termination.")
y = dash(y, "The practical point matters more. Model weights trained on de-identified data are not reversible by contract termination. A partner leaving takes future data flow. It doesn't take back what Sona has already learned.")
y -= 8

y = section(y, "09", "Launch Dates")
for label, d in [("Glow", "Launched"),
                 ("Flagship Pioneering", "November 2026"),
                 ("Cleveland Clinic", "December 2026"),
                 ("RuralAI", "December 2026"),
                 ("Spark", "December 2026"),
                 ("Ultimate Human", "January 2027"),
                 ("Canada Life scoping", "January 2027")]:
    y = row(y, label, d)
hrule(y, color=DV, thickness=0.4); y -= 14

y = section(y, "10", "DAIC-WOZ, Bridge2AI, And Outside Validation")
y = body(y, "I've attached a report on Sona-2 validation. Let me know if you want more.")
y -= 8

y = section(y, "11", "Full Validation Report And False Positive Rates")
y = body(y, "Per condition reports attached. They carry cohort size and demographics, prevalence in the test set, threshold selection, sensitivity, specificity, false positive rate, PPV and NPV at realistic prevalence, and confidence intervals.")
y -= 8

y = section(y, "12", "Regulatory Counsel Assessment")
y = body(y, "I'm attaching a document that goes deeper. Everything we sell today sits in the FDA exempt per attachment. Nothing in market requires clearance.")
y -= 6
y = body(y, "The FDA work is a second phase by design, not a gap we haven't gotten to.")
y -= 8
y = num_item(y, "1", "I spent 10 years running Intrinsic Imaging (www.IntrinsicImaging.com) which is a FDA regulated CRO so I have experience in this exact area. We are not ultimately seeking clearance for a foundation model. You clear one intended use on one indication. A submission is only as strong as the evidence behind that single claim.")
y -= 3
y = num_item(y, "2", "That evidence is real world data. We will plan through commercial deployments, from the people the product is actually for a dataset for the submission. If we file before we have it means filing a weaker one.")
y -= 3
y = num_item(y, "3", "Phase one builds the regulatory infrastructure once. QMS, CFR Part 11, validation architecture, SOC 2 Type II, HIPAA BAA. Following that every indication after the first rides the same rails at marginal cost.")
y -= 3
y = num_item(y, "4", "The phases don't depend on each other. Revenue today doesn't require clearance. Clearance doesn't require revenue. If FDA timelines move, the business keeps running.")
y -= 8
y = body(y, "The device pathway applies to [X], with [SUBMISSION TYPE] targeted for [DATE], funded out of the Series A.")
y -= 6
y = body(y, "Claim language is what determines device status, so we control it. Every commercial and marketing asset goes through the same review.")
y -= 8

y = section(y, "13", "Wired Versus Committed")
y = body(y, "The amounts are unchanged from the previous table I sent you. The only outstanding funds are the $1M from Ultimate Shares which is a double close with their fund on October 15. They have wired their personal checks already. Let me know if you need more color.")
y -= 8

y = section(y, "14", "Builders VC, Valuation And Approval")
y = body(y, "Builders went through a formal evaluation process through the partnership as well as Investment Committee where I recused myself. The valuation was set with the other investors at arms length. I recused myself from the pricing discussion and from the board vote.")
y -= 8

y = section(y, "15", "Share Class, Price, Preferences, Reporting, Future Rounds")
y = body(y, "Yes. The caveat operationally as you know is when the investment comes through a single vehicle, that vehicle is the holder of record and holds one position with one set of rights. What individual LPs get is governed by the vehicles operating agreement, which is your document, not ours.")
y -= 6
y = dash(y, "Terms. Same share class and same price per share as the lead for anyone in the same closing.")
y -= 14

y = need(y, 60)
hrule(y); y -= 18
draw(ML, y, "Amit Mehta, MD, FRCP", "Inter-Bold", 10.1, BK); y -= 13
draw(ML, y, "amit@amplifierhealth.com", "Inter", 9.6, MED)

footer()
c.save()
print("OK")
