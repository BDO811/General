# -*- coding: utf-8 -*-
"""Amplifier Health and Theris: Business Case. Rendered in the Theris brand."""
import io, os, sys
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("Inter", "/tmp/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Bold", "/tmp/Inter-Bold.ttf"))

PW, PH = 612, 792
ML = MR = 54
MB = 42
TW = PW - ML - MR          # 504

# ---- Amplifier neutrals (fixed) ----
BK  = HexColor("#050505")
DK  = HexColor("#1A1A1A")
MED = HexColor("#444444")
MU  = HexColor("#888888")
LT  = HexColor("#BBBBBB")
HLT = HexColor("#DDDDDD")
DV  = HexColor("#D0D0D0")
LB  = HexColor("#F5F5F5")
BOX = HexColor("#0A0A0A")

# ---- Theris brand, extracted from theris.ai favicon.svg and index-x07e0SnK.css ----
BRAND = {
    "primary":   HexColor("#CB550B"),   # logo mark fill
    "secondary": HexColor("#B87A5C"),   # highest frequency CSS accent
    "tertiary":  HexColor("#8FA38F"),   # sage, second accent
    "surface":   HexColor("#F5E6D3"),   # cream card fill
    "ink":       HexColor("#2D3748"),   # brand dark, headings
    "logo_png":  os.path.join(os.path.dirname(os.path.abspath(__file__)), "theris-logo.png"),
}

PARTNER_UPPER   = "THERIS"
PARTNER_DISPLAY = "Theris"
DATELINE        = "PARTNERSHIP PROPOSAL  ·  SEPTEMBER 2026"

# ----------------------------------------------------------------- primitives
def base(top_pt, size_pt, frac=0.758):
    return PH - top_pt - size_pt * frac

def draw(c, x, y, text, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, text)

def draw_right(c, x, y, text, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawRightString(x, y, text)

def hrule(c, y, color=DV, thickness=0.4, x0=None, x1=None):
    c.setStrokeColor(color); c.setLineWidth(thickness)
    c.line(x0 or ML, y, x1 or (PW - MR), y)

def thick_hrule(c, y, color=BK, thickness=1.5):
    c.setStrokeColor(color); c.setLineWidth(thickness); c.line(ML, y, PW - MR, y)

def filled_rect(c, x, y, w, h, color):
    c.setFillColor(color); c.rect(x, y, w, h, stroke=0, fill=1)

def logo(c, x, y, size, path=None):
    img = ImageReader(path or BRAND["logo_png"])
    iw, ih = img.getSize()
    w, h = (size, size * ih / iw) if iw >= ih else (size * iw / ih, size)
    c.drawImage(img, x, y, width=w, height=h, mask="auto")
    return w, h

def wrap_text(c, text, font, size, max_w):
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

def fit_width(c, text, font, max_w, max_size=72, min_size=20):
    size = max_size
    while size >= min_size:
        if c.stringWidth(text, font, size) <= max_w: return size
        size -= 0.5
    return min_size

# ----------------------------------------------------------------- chrome
def top_bar(c):
    draw(c, ML, base(76.8, 11.04), "AMPLIFIER HEALTH AND " + PARTNER_UPPER,
         "Inter-Bold", 11.04, BK)
    lw, _ = logo(c, PW - MR - 13, base(76.8, 11.04) - 2.6, 13)
    draw_right(c, PW - MR - lw - 7, base(76.8, 7.44),
               "CONFIDENTIAL  ·  FOR AUTHORIZED USE ONLY", "Inter-Bold", 7.44, MU)

def footer(c, n):
    hrule(c, MB + 10)
    draw_right(c, PW - MR, MB - 2,
               "Amplifier Health and %s  ·  Confidential  ·  %d" % (PARTNER_DISPLAY, n),
               "Inter", 7.44, MU)

# ----------------------------------------------------------------- flow engine
class Doc(object):
    TOP = PH - 106.8 - 8
    BOT = MB + 20

    def __init__(self, path):
        self.c = pdfcanvas.Canvas(path, pagesize=(PW, PH))
        self.page = 0
        self.y = 0
        self._newpage()

    def _newpage(self):
        if self.page:
            footer(self.c, self.page); self.c.showPage()
        self.page += 1
        top_bar(self.c)
        self.y = self.TOP

    def need(self, h):
        if self.y - h < self.BOT:
            self._newpage()

    # ---- blocks
    def section(self, number, name):
        # reserve the label, its h2, and enough body that a heading never strands
        # alone at the foot of a page
        self.need(150)
        self.y -= 6
        hrule(self.c, self.y, color=BRAND["primary"], thickness=1.6)
        self.y -= 14
        draw(self.c, ML, self.y, "SECTION %s  ·  %s" % (number, name.upper()),
             "Inter-Bold", 7.4, BRAND["secondary"])
        self.y -= 16

    def h2(self, text):
        self.need(88)
        lines = wrap_text(self.c, text, "Inter-Bold", 15.1, TW)
        for ln in lines:
            draw(self.c, ML, self.y, ln, "Inter-Bold", 15.1, BRAND["ink"])
            self.y -= 18
        self.y -= 3

    def h3(self, text):
        self.need(78)
        self.y -= 4
        draw(self.c, ML, self.y, text, "Inter-Bold", 11.5, BRAND["ink"])
        self.y -= 15

    def kicker(self, text):
        # a kicker introduces the block after it, so it reserves room for both
        self.need(165)
        draw(self.c, ML, self.y, text.upper(), "Inter-Bold", 7.4, BRAND["primary"])
        self.y -= 13

    def para(self, text, size=10.1, leading=12.8, color=DK, gap=6.5):
        lines = wrap_text(self.c, text, "Inter", size, TW)
        self.need(len(lines) * leading + gap)
        # a paragraph that would split badly gets its own page
        if self.y - (len(lines) * leading) < self.BOT:
            self._newpage()
        for ln in lines:
            draw(self.c, ML, self.y, ln, "Inter", size, color)
            self.y -= leading
        self.y -= gap

    def bullet(self, text, indent=10, leading=12.4, gap=3.5):
        avail = TW - indent - 10
        lines = wrap_text(self.c, text, "Inter", 10.1, avail)
        self.need(len(lines) * leading + gap)
        if self.y - (len(lines) * leading) < self.BOT:
            self._newpage()
        draw(self.c, ML + indent, self.y + 2.5, "–", "Inter-Bold", 7.4, BRAND["secondary"])
        for i, ln in enumerate(lines):
            draw(self.c, ML + indent + 10, self.y, ln, "Inter", 10.1, DK)
            self.y -= leading
        self.y -= gap

    def numbered(self, n, text, indent=10, leading=12.4, gap=4):
        avail = TW - indent - 18
        lines = wrap_text(self.c, text, "Inter", 10.1, avail)
        self.need(len(lines) * leading + gap)
        if self.y - (len(lines) * leading) < self.BOT:
            self._newpage()
        draw(self.c, ML + indent, self.y, "%d." % n, "Inter-Bold", 10.1, BRAND["primary"])
        for ln in lines:
            draw(self.c, ML + indent + 18, self.y, ln, "Inter", 10.1, DK)
            self.y -= leading
        self.y -= gap

    def callout(self, label, text, pad_v=11, pad_h=13, line_h=12.8):
        lines = wrap_text(self.c, text, "Inter", 9.6, TW - pad_h * 2)
        h = pad_v + 11 + 6 + len(lines) * line_h + pad_v - 4
        self.need(h + 12)
        if self.y - h < self.BOT:
            self._newpage()
        filled_rect(self.c, ML, self.y - h, TW, h, BOX)
        filled_rect(self.c, ML, self.y - h, 3.2, h, BRAND["primary"])
        ty = self.y - pad_v - 7.9 * 0.758
        draw(self.c, ML + pad_h, ty, label.upper(), "Inter-Bold", 7.9, HLT)
        ty -= 12
        for ln in lines:
            draw(self.c, ML + pad_h, ty, ln, "Inter", 9.6, LT)
            ty -= line_h
        self.y -= h + 12

    def note(self, label, text, pad_v=10, pad_h=12, line_h=12.4):
        """Light brand-tinted card, for guardrails and open items."""
        lines = wrap_text(self.c, text, "Inter", 9.4, TW - pad_h * 2)
        h = pad_v + 10 + 5 + len(lines) * line_h + pad_v - 4
        self.need(h + 12)
        if self.y - h < self.BOT:
            self._newpage()
        filled_rect(self.c, ML, self.y - h, TW, h, BRAND["surface"])
        filled_rect(self.c, ML, self.y - h, 3.2, h, BRAND["tertiary"])
        ty = self.y - pad_v - 7.6 * 0.758
        draw(self.c, ML + pad_h, ty, label.upper(), "Inter-Bold", 7.6, BRAND["ink"])
        ty -= 11
        for ln in lines:
            draw(self.c, ML + pad_h, ty, ln, "Inter", 9.4, DK)
            ty -= line_h
        self.y -= h + 12

    def stats(self, cells):
        bh = 54
        self.need(bh + 14)
        if self.y - bh < self.BOT:
            self._newpage()
        n = len(cells); cw = TW / n
        by = self.y - bh
        for i, (num, lbl, sub) in enumerate(cells):
            cx = ML + i * cw
            filled_rect(self.c, cx, by, cw - 3, bh, BRAND["surface"])
            filled_rect(self.c, cx, self.y - 2.2, cw - 3, 2.2, BRAND["primary"])
            ns = fit_width(self.c, num, "Inter-Bold", cw - 19, max_size=22, min_size=11)
            draw(self.c, cx + 9, by + bh - 9 - ns * 0.758, num, "Inter-Bold", ns, BRAND["ink"])
            draw(self.c, cx + 9, by + 13, lbl, "Inter-Bold", 7.2, DK)
            draw(self.c, cx + 9, by + 4.5, sub, "Inter", 7.0, MED)
        self.y = by - 14

    def table(self, header, rows, col_x=(0, 250, 372), row_h=17):
        self.need(row_h * 2 + 20)
        draw(self.c, ML, self.y, header.upper(), "Inter-Bold", 7.4, BRAND["primary"])
        self.y -= 8
        hrule(self.c, self.y, color=BRAND["ink"], thickness=1.1)
        self.y -= 2
        for r in rows:
            self.need(row_h + 4)
            if self.y - row_h < self.BOT:
                self._newpage()
                hrule(self.c, self.y, color=BRAND["ink"], thickness=1.1)
                self.y -= 2
            ty = self.y - row_h * 0.62
            draw(self.c, ML + 4, ty, r[0], "Inter-Bold", 9.0, BRAND["ink"])
            draw(self.c, ML + col_x[1], ty, r[1], "Inter", 9.0, DK)
            if len(r) > 2 and len(col_x) > 2:
                draw_right(self.c, PW - MR - 4, ty, r[2], "Inter-Bold", 9.0, BRAND["primary"])
            self.y -= row_h
            hrule(self.c, self.y, color=DV, thickness=0.4)
        self.y -= 12

    def finish(self):
        footer(self.c, self.page)
        self.c.save()


# ----------------------------------------------------------------- cover
def cover(d):
    c = d.c
    draw(c, ML, base(106.8, 8.40), DATELINE, "Inter-Bold", 8.40, MU)
    lw, lh = logo(c, ML, base(106.8, 8.40) - 74, 56)
    hero_top = 106.8 + 96
    hs = fit_width(c, PARTNER_UPPER, "Inter-Bold", TW, max_size=96, min_size=20)
    hy = base(hero_top, hs)
    draw(c, ML, hy, PARTNER_UPPER, "Inter-Bold", hs, BRAND["ink"])
    ss = min(hs - 4, fit_width(c, "AMPLIFIER HEALTH BUSINESS CASE", "Inter-Bold", TW))
    sy = hy - hs * 0.92 - 12
    draw(c, ML, sy, "AMPLIFIER HEALTH BUSINESS CASE", "Inter-Bold", ss, BRAND["secondary"])
    ry = sy - ss * 0.92 - 22
    thick_hrule(c, ry, color=BRAND["primary"], thickness=2.6)
    d.y = ry - 16
    d.callout("What This Is",
        "A revenue and outcomes case for running Sona-2's acoustic layer on the telehealth "
        "sessions Theris already records, measured against the four things Theris already "
        "tells the market it delivers: better outcomes, maximized reimbursement, increased "
        "utilization and reduced liability. United States only. No new product for Theris "
        "to sell, no added Care Coordinator or clinician time, and no change to how a "
        "session runs.")
    d.y -= 6
    draw(c, ML, d.y, "Prepared by Amit Mehta, MD, FRCP  ·  CEO, Amplifier Health  ·  amit@amplifierhealth.com",
         "Inter", 8.6, MED)
    footer(c, 1)
    c.showPage()
    # start page 2 directly. Going through _newpage() here would emit a second
    # footer and an empty page.
    d.page = 2
    top_bar(c)
    d.y = d.TOP


# ----------------------------------------------------------------- content
# Every claim about Theris below traces to theris.ai (Home, Technology,
# ClinicalServices, About, Team) unless explicitly marked as press coverage.
def build(out):
    d = Doc(out)
    cover(d)

    # ============================================================ 01
    d.section("01", "What Theris Does")
    d.h2("Read From Your Own Site, Not From Press Coverage")
    d.bullet("Theris delivers geriatric behavioral health into congregate living "
             "facilities. The company was founded as Empower Nation and rebranded to "
             "Theris around a mission to transform geriatric behavioral health delivery. "
             "This is a senior living company, not a general behavioral health company.")
    d.bullet("The delivery model is hybrid and it is the most interesting thing about "
             "the business. A dedicated Care Coordinator is physically on site, sets up "
             "and facilitates the session, and handles documentation. The clinician "
             "joins by telehealth. Familiar faces on site, specialist supply from "
             "anywhere. Psychiatrists, psychologists, nurse practitioners, LCSWs and "
             "LPCs sit behind that screen.")
    d.bullet("Seven active states with three more launching in Q1 2026, built out from "
             "Oklahoma City through New Jersey, Colorado, Ohio, Texas, Pennsylvania and "
             "Virginia. In network with all major insurance plans.")
    d.bullet("The clinical scope is depression in high acuity patients with PHQ-9 "
             "monitoring, anxiety and PTSD with GAD-7 assessment, dementia related "
             "behaviors, mood disorders, substance use, and adjustment and loss. Two of "
             "those instruments matter enormously for what follows.")
    d.bullet("The promise to the facility operator is zero staff burden. The promise to "
             "the market is From Treatment to Outcome: measurable disease progression "
             "tracking, predictive models, evidence based pathways to recovery. Theris "
             "is selling measurement, not sessions.")
    d.bullet("The stack integrates with Athena Health and Point Click Care. The founding "
             "team previously took the largest US mobile healthcare company public on "
             "Nasdaq at a $1.1 billion valuation, and the AI organization is led by a "
             "KAUST computer science professor with published researchers under him.")

    d.stats([
        ("7 + 3", "STATES", "Active, plus three in Q1 2026"),
        ("2", "ROLES PER VISIT", "Coordinator on site, clinician remote"),
        ("0", "STAFF BURDEN", "Theris's own promise to operators"),
    ])

    d.note("One open item on scope",
        "Press coverage at launch described a broader facility mix than the site does, "
        "including VA community residences, sober living homes and K-12 schools, and "
        "named the Department of Veterans Affairs as a major client. None of that appears "
        "on theris.ai, which is entirely congregate and senior living. This document is "
        "built on the site. Worth one question on the call, because a VA book changes the "
        "contracting rail and the size of the opportunity.")

    # ============================================================ 02
    d.section("02", "Where Sona-2 Sits")
    d.h2("The Session Is Already Recorded. We Read the Voice.")
    d.bullet("The telehealth encounter is captured end to end today, facilitated by the "
             "Care Coordinator who is already in the room. That is the integration point. "
             "No new capture step, no consent change, no clinician time, no change to how "
             "a visit runs.")
    d.bullet("Theris already charts PHQ-9 and GAD-7. Sona-2's classifiers are calibrated "
             "against PHQ-9, GAD-7 and PCL-5. The output lands inside the instruments "
             "Theris already uses rather than arriving as a parallel score nobody knows "
             "how to read or chart.")
    d.bullet("Sona-2 analyzes acoustics, not the transcript. It reads how the resident "
             "sounds rather than what they said. That makes it a genuinely independent "
             "second read on the same session, not a second opinion drawn from the same "
             "evidence the clinician already weighed.")
    d.bullet("Signal starts at the first encounter. There is no enrollment period and no "
             "baseline to establish before the measurement is usable. In a population "
             "with the turnover of congregate living, a model that needs history before "
             "it says anything is a model that misses the residents who move fastest.")
    d.bullet("Integration is one HTTPS POST after the session and a JSON response in "
             "seconds, asynchronous and server side, sitting inside the documentation "
             "pipeline Theris already runs into Athena and Point Click Care. A HIPAA BAA "
             "is executed at account creation, audio is processed and discarded, and no "
             "audio is stored on Amplifier systems.")

    # ============================================================ 03
    d.section("03", "Against Theris's Own Claims")
    d.h2("Measured On What You Already Sell")
    d.para("Theris tells the market it delivers Better Outcomes, Maximized Reimbursement "
           "and Increased Utilization, and adds Reduced Liability on the technology page. "
           "Those four are the right frame for this conversation, so this section uses "
           "them rather than inventing a new one. In each case the question is the same: "
           "what does an acoustic read add to a claim Theris is already making?")

    d.h3("Better Outcomes")
    d.para("The site claims standardized protocols, SOP compliance and objective "
           "measurement. Today that objectivity comes from a clinician administered "
           "PHQ-9 or GAD-7, which is self report filtered through a rater on a video "
           "call. Sona-2 measures something the resident is not choosing to report. "
           "That gap matters most exactly where Theris's clinical scope is heaviest: "
           "dementia related behaviors, where self report is least reliable, and high "
           "acuity depression, where it is least candid. The site also promises "
           "longitudinal tracking against baseline and historical data. Sona-2 produces "
           "that trend line from session one.")

    d.h3("Maximized Reimbursement")
    d.para("Theris already auto codes billing and diagnosis, auto generates audit "
           "documentation and claims it never misses a modifier. That is a strong engine "
           "and it solves coding for a patient somebody already identified. It does not "
           "find the patient. Sona-2 runs on every encounter and surfaces residents who "
           "qualify for a behavioral health program and are not enrolled. The existing "
           "Theris engine then does what it already does well. This is the highest value "
           "seam in the whole partnership, because Theris's strength sits directly "
           "downstream of the gap.")

    d.h3("Increased Utilization")
    d.para("The site sells see more patients through time saved, 10 to 15 minutes per "
           "session from auto drafted charts. That is the supply side of utilization and "
           "it is already solved. Risk stratification is the demand side. Sorting "
           "residents into low, moderate and high risk puts the clinician hours Theris "
           "just freed up in front of the residents where they change an outcome, rather "
           "than spreading them evenly across a census. Same pillar Theris already "
           "markets, a lever it does not have yet.")

    d.h3("Reduced Liability")
    d.para("Theris generates multi page audit reports for CMS audits on every session. An "
           "independent acoustic measurement in that record strengthens the same "
           "documentation, and it contributes something the audit report does not "
           "currently contain: a data point not derived from the clinician's own note.")

    # ============================================================ 04
    d.section("04", "The Revenue Math")
    d.h2("United States Only, Two Payment Rails")
    d.para("Theris operates in seven states with three more coming, in network with all "
           "major plans. Everything below is US mechanics. Two rails matter and they pay "
           "different people. The first pays Theris directly for services it already "
           "delivers. The second pays the facility operator and the health plan, and it "
           "is the rail that decides whether Theris's contract gets renewed.")

    d.kicker("Rail one: codes Theris bills")
    d.table("CODE AND SERVICE  ·  2026 MEDICARE NATIONAL AVERAGE", [
        ("99484", "Behavioral Health Integration, general, per month", "~$55"),
        ("99492", "Collaborative Care, initial month, first 70 min", "~$163"),
        ("99493", "Collaborative Care, subsequent month, 60 min", "~$130"),
        ("99494", "Collaborative Care, each additional 30 min", "~$70"),
        ("99490", "Chronic Care Management, per month, stackable", "~$66"),
        ("99483", "Cognitive assessment and care plan, non-facility", "~$293"),
        ("99483", "Cognitive assessment and care plan, facility", "~$170"),
        ("G0444", "Annual depression screening", "~$18"),
    ])
    d.para("National midpoints, not exact figures, and they move by state and payer. Two "
           "things are worth pulling out. The collaborative care codes pay roughly two "
           "and a half times the general BHI code for the same enrolled patient, so which "
           "code a patient lands in matters as much as whether they are enrolled. And "
           "99483 is a single encounter worth more than five months of BHI, sitting "
           "directly on the dementia population that is already a named part of the "
           "Theris clinical scope.")

    d.kicker("The enrollment gap, sized")
    d.callout("The Formula",
        "(newly enrolled patients per facility)  x  (number of facilities)  x  ($55 per "
        "month)  =  monthly recurring revenue. At 10 newly enrolled residents across 200 "
        "facilities, that is 2,000 residents, about $110,000 a month, about $1.3 million "
        "a year. Only the $55 is a real number. The other two inputs are illustrative and "
        "have to come from Theris.")
    d.para("Run on collaborative care instead of general BHI, at roughly $130 per patient "
           "per subsequent month, the same resident count produces about $260,000 a month "
           "or $3.1 million a year. The spread between those two outcomes is wider than "
           "the spread between any two honest guesses at facility count, which is why the "
           "code mix is worth settling before the volume estimate is.")

    d.kicker("Rail two: what the operator and the plan get paid")
    d.para("Under PDPM, signs and symptoms of depression identified through the PHQ-9 "
           "resident mood interview or the staff assessment are a case mix split in the "
           "Nursing component. A resident in Clinically Complex with a function score of "
           "0 to 5 classifies at a nursing CMI of 1.62 without depression indicators and "
           "1.87 with them. Depression splits Special Care High and Special Care Low too.")
    d.para("That 0.25 CMI difference against an FY2026 urban nursing base of roughly $122 "
           "a day is about $30 per resident per day, or roughly $800 to $900 across a "
           "typical covered Part A stay. The base rate is the FY2025 figure carried "
           "forward at the finalized 3.2 percent update and should be confirmed against "
           "Table 6 of the FY2026 final rule before it goes in front of an operator.")
    d.para("Theris does not bill that. The operator does. Which is the point, because the "
           "operator is who renews the contract. And the data path already exists: Theris "
           "integrates with Point Click Care, which is where the MDS lives. A behavioral "
           "signal that reaches Section D accurately is worth real money to the "
           "administrator Theris is already selling zero staff burden to.")

    d.note("The guardrail, and it is not optional",
        "This only works as accuracy, never as inflation. The value is identifying "
        "residents who genuinely screen positive and are currently going unidentified. It "
        "is not producing depression codes. Any version that reads as upcoding assistance "
        "fails compliance review at the first sophisticated operator and puts the whole "
        "relationship at risk, so the acoustic signal has to route to a clinician "
        "assessment that stands on its own, with an audit trail showing that it did. "
        "Theris already generates audit documentation on every session, so the mechanism "
        "for that trail is built.")

    d.bullet("Medicare Advantage risk adjustment: every 0.1 increase in a member's RAF "
             "score is worth roughly $1,000 to $1,040 per member per year in plan "
             "revenue, and depression carries HCC weight under version 28 when coded as "
             "moderate or severe active major depressive disorder. Where Theris serves "
             "MA covered residents, the plan is a natural third buyer.")
    d.bullet("Avoidable transfer is the cost side. More than a third of residents in "
             "Medicare and Medicaid covered nursing facilities are hospitalized at least "
             "once, and up to 39 percent of those admissions are considered potentially "
             "avoidable with more effective care. Untreated behavioral health is an "
             "independent driver of that transfer rate, which is the same argument "
             "Theris's own site makes about behavioral incidents and outcomes.")

    # ============================================================ 05
    d.section("05", "Buy Versus Build")
    d.h2("The Honest Version of This Conversation")
    d.para("Theris has a real AI organization: a KAUST computer science professor as "
           "Chief AI Officer, a head of AI research publishing in Nature Methods and "
           "Nature Machine Intelligence, a senior researcher working on multimodal "
           "foundation models that integrate vision, language and behavioral signals, and "
           "a biostatistician on longitudinal modeling in aging populations. The site "
           "claims training on the most comprehensive behavioral health dataset in the "
           "world across millions of clinical encounters. This is not a capability gap "
           "and it would be insulting to pitch it as one.")
    d.para("So the question is not whether Theris could build an acoustic layer. It is "
           "whether that is where this particular team should spend the next eighteen "
           "months. Two things are genuinely different about Sona-2 and both are worth "
           "stating plainly.")
    d.bullet("The assets are not the same. A behavioral health encounter corpus is "
             "enormously valuable for the scribe, coding and outcomes stack Theris has "
             "built on it. Sona-2 is trained on 2.5 million clinically labeled voice "
             "interactions with validated ground truth, which is a different asset built "
             "for a different job: mapping acoustic features to a calibrated clinical "
             "score. Volume of encounters and volume of labeled acoustic ground truth are "
             "not interchangeable, and the second one is the harder one to accumulate.")
    d.bullet("Sona-2 is a purpose built acoustic foundation model rather than a general "
             "model adapted to audio. That distinction is defensible in an analyst "
             "conversation, in a payer conversation and in a regulatory file, and it is "
             "the kind of claim that is difficult to make credibly about a model that "
             "started life somewhere else.")
    d.para("On regulation, press coverage says Theris is pursuing FDA Class II. Amplifier "
           "is working the same ground on a voice derived depression biomarker. Those two "
           "efforts are complementary rather than competitive, and citing external "
           "validation is faster and more credible than generating a second internal "
           "metric.")

    # ============================================================ 06
    d.section("06", "The Ask")
    d.h2("Three Numbers and One Retrospective Run")
    d.para("Three numbers turn this from a structured argument into an actual model. All "
           "three live inside Theris and none are public.")
    d.table("THE THREE INPUTS", [
        ("Facility count", "The real number, by state and by facility type", ""),
        ("Missed enrollment", "Residents per facility eligible for BHI or CoCM, not enrolled", ""),
        ("Clinician caseload", "Average caseload and how visit frequency is allocated today", ""),
    ], col_x=(0, 150), row_h=19)

    d.h3("The Proposed Path")
    d.bullet("Run Sona-2 against a retrospective slice of telehealth session audio Theris "
             "has already captured. No workflow change, no consent change, no Care "
             "Coordinator or clinician time. The output is a count of residents the model "
             "flags who are not currently enrolled, plus agreement statistics against the "
             "PHQ-9 and GAD-7 scores already in those charts.")
    d.bullet("That second output is the one worth optimizing for. Agreement against "
             "instruments Theris already trusts is the fastest credible proof, and it is "
             "a validation datapoint Theris can use independently of whether this "
             "partnership goes anywhere.")
    d.bullet("Compare the flagged count against enrollment records to produce the real "
             "missed enrollment rate, which is input two above and the number the entire "
             "revenue case rests on.")
    d.bullet("If it holds, move to a prospective pilot of 200 to 500 residents across 60 "
             "to 90 days in a single operator group, instrumented to measure enrollment "
             "lift, clinician time reallocation and facility level trend reporting at "
             "once. A free evaluation tier covers 100 assessments a month before any of "
             "this costs anything.")
    d.bullet("Pricing when it does: $0.18 per assessment, or $0.12 per minute of audio, "
             "scaling linearly with encounter volume. At one assessment per resident per "
             "week that is $9.36 per resident per year, against events costing thousands. "
             "Cost to serve is not the variable that decides this.")

    d.callout("From Amit Mehta  ·  CEO, Amplifier Health",
        "The retrospective run is the whole proposal. It costs Theris a data pull and "
        "nothing else, it changes nothing about how a visit runs, and it either produces "
        "a missed enrollment number and an agreement statistic that justify everything "
        "above, or it does not. Everything else here is scaffolding around that one "
        "measurement. amplifierhealth.com, docs.amplifierhealth.com, "
        "console.amplifierhealth.com. Up and running in under five minutes.")

    d.finish()
    return d.page


# ----------------------------------------------------------------- guard
def guard(path):
    """Scan the RENDERED text, not the source. Amit's rules: no em dash, no double
    dash, no multiplication sign, and the partnership is always named with 'and'."""
    import pymupdf
    doc = pymupdf.open(path)
    txt = "\n".join((p.get_text() or "") for p in doc)
    bad = []
    for ch, name in ((u"—", "em dash"), (u"--", "double dash"),
                     (u"×", "multiplication sign"), ("_x_", "x-naming")):
        n = txt.count(ch)
        if n:
            bad.append("%s x%d" % (name, n))
    # an en dash is only legal as the bullet glyph at the start of a line
    stray = [l for l in txt.split("\n")
             if u"–" in l and not l.strip().startswith(u"–")]
    if stray:
        bad.append("en dash in prose x%d" % len(stray))
    for page in doc:
        if len((page.get_text() or "").strip()) < 40:
            bad.append("blank page %d" % (page.number + 1))
    return bad


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "Amplifier_and_Theris_BusinessCase.pdf"
    pages = build(out)
    print("wrote", out, pages, "pages", os.path.getsize(out), "bytes")
    b = guard(out)
    print("guard:", "CLEAN" if not b else "VIOLATIONS %s" % b)
