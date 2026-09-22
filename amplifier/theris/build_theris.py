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
DATELINE        = "BUSINESS CASE REVIEW  ·  SEPTEMBER 2026"

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

    def case(self, title, today, gap, adds, econ):
        """One reviewed Theris activity: what it is today, where the economics leak,
        what an acoustic read adds, and the money line. Never splits across pages."""
        LBLW = 96
        tw = TW - LBLW
        rows = [("TODAY", today), ("THE GAP", gap), ("SONA-2 ADDS", adds)]
        wrapped = [(l, wrap_text(self.c, t, "Inter", 9.7, tw)) for l, t in rows]
        econ_lines = wrap_text(self.c, econ, "Inter-Bold", 9.4, TW - 24)
        h = 20 + sum(len(w) * 12.2 + 5 for _, w in wrapped) + 10 + len(econ_lines) * 12.2 + 14
        self.need(h + 10)
        if self.y - h < self.BOT:
            self._newpage()
        draw(self.c, ML, self.y, title, "Inter-Bold", 11.5, BRAND["ink"])
        self.y -= 17
        for label, lines in wrapped:
            draw(self.c, ML, self.y, label, "Inter-Bold", 7.2, BRAND["secondary"])
            for ln in lines:
                draw(self.c, ML + LBLW, self.y, ln, "Inter", 9.7, DK)
                self.y -= 12.2
            self.y -= 5
        eh = 10 + len(econ_lines) * 12.2
        filled_rect(self.c, ML, self.y - eh + 4, TW, eh, BRAND["surface"])
        filled_rect(self.c, ML, self.y - eh + 4, 3.0, eh, BRAND["primary"])
        ty = self.y - 3
        for ln in econ_lines:
            draw(self.c, ML + 12, ty, ln, "Inter-Bold", 9.4, BRAND["ink"])
            ty -= 12.2
        self.y -= eh + 12

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
    ss = min(hs - 4, fit_width(c, "ECONOMIC REVIEW BY AMPLIFIER HEALTH", "Inter-Bold", TW))
    sy = hy - hs * 0.92 - 12
    draw(c, ML, sy, "ECONOMIC REVIEW BY AMPLIFIER HEALTH", "Inter-Bold", ss, BRAND["secondary"])
    ry = sy - ss * 0.92 - 22
    thick_hrule(c, ry, color=BRAND["primary"], thickness=2.6)
    d.y = ry - 16
    d.callout("What This Is",
        "A line by line economic review of the Theris business. Each clinical service "
        "line, the Care Coordinator operating model, each of the four claims on the "
        "technology page, and the facility relationship, taken one at a time, asking "
        "where reading the voice inside that activity creates an economic case and what "
        "it is worth. United States only. Written after your reply, not as an "
        "introduction.")
    d.y -= 6
    # Attribution: company only. No byline, no "prepared by", no person's name.
    draw(c, ML, d.y,
         "Amplifier Health  ·  amplifierhealth.com  ·  partnerships@amplifierhealth.com",
         "Inter", 8.6, MED)
    footer(c, 1)
    c.showPage()
    # start page 2 directly. Going through _newpage() here would emit a second
    # footer and an empty page.
    d.page = 2
    top_bar(c)
    d.y = d.TOP


# ----------------------------------------------------------------- content
# A line by line economic review of the Theris business. Every description of what
# Theris does traces to theris.ai (Home, Technology, ClinicalServices, About, Team).
def build(out):
    d = Doc(out)
    cover(d)

    # ============================================================ 01
    d.section("01", "How To Read This")
    d.h2("A Review of Your Business, Not a Pitch")
    d.para("This document does not argue that Theris needs an acoustic model. It works "
           "the other way around. It takes each thing Theris already does, one at a "
           "time, and asks a single question: is there an economic case for reading the "
           "voice inside that activity, and what is it worth?")
    d.para("Six clinical service lines, one operating model, four product claims and one "
           "facility relationship. Each gets the same treatment: what it is today, where "
           "the economics leak, what an acoustic read adds, and the money line. Where "
           "there is no case, or where the evidence is thin, that is stated rather than "
           "papered over. Section 06 collects the weak spots in one place.")
    d.para("Everything below is United States mechanics, because Theris operates in seven "
           "states with three more launching in Q1 2026 and nowhere else.")

    d.callout("The One Idea Underneath All Of It",
        "Theris already captures a telehealth session, facilitated by a Care Coordinator "
        "who is physically in the room, across every one of these service lines. That "
        "audio is currently used once, to deliver and document care. Sona-2 reads it a "
        "second time, acoustically, and returns a clinical signal. Every case below is a "
        "different answer to the question of what that second read is worth in that "
        "specific part of the business.")

    # ============================================================ 02
    d.section("02", "The Six Clinical Service Lines")
    d.h2("Depression, Anxiety, Dementia, Mood, Substance Use, Loss")

    d.case("Depression in High Acuity Patients",
        "PHQ-9 monitoring and evidence based intervention, administered by a clinician "
        "over telehealth, episodically.",
        "PHQ-9 is self report filtered through a rater on a video call, and it is least "
        "reliable exactly here: high acuity, cognitively impaired, and often not candid. "
        "Close to half of nursing home residents are depressed. In one Ohio study 48 "
        "percent screened positive, 23 percent were receiving no treatment at all, and "
        "only 2.5 percent were getting any behavioral therapy.",
        "A passive acoustic depression severity read on every session, calibrated against "
        "PHQ-9, that does not depend on what the resident chooses to report. It lands in "
        "the instrument Theris already charts.",
        "Two revenue paths at once. Enrollment: 99484 at about $55 per patient per month, "
        "or the collaborative care codes at about $130 per subsequent month. Facility: a "
        "PDPM nursing case mix split worth roughly $30 per resident per day. This is the "
        "largest line in the business and the largest case in this document.")

    d.case("Anxiety and PTSD",
        "GAD-7 assessment and trauma informed care, covering generalized anxiety, PTSD "
        "and social anxiety.",
        "GAD-7 is a point in time questionnaire for a condition that fluctuates day to "
        "day. Social anxiety in particular suppresses the very self report the instrument "
        "depends on, and late life PTSD is chronically under identified.",
        "An acoustic anxiety index on every session, plus PCL-5 calibration, which turns "
        "an episodic questionnaire into a continuous measure without adding a single "
        "question to the visit.",
        "Anxiety is a qualifying diagnosis for the same BHI and collaborative care "
        "enrollment as depression, so it feeds the same $55 to $130 per month line from a "
        "population that is currently harder to identify. If there is a VA book behind "
        "this business, PCL-5 calibration is the single most relevant thing Amplifier has.")

    d.case("Dementia Related Behaviors",
        "Person centered, non pharmacological management of BPSD: agitation and "
        "aggression, wandering and restlessness, sleep disturbance.",
        "BPSD is managed reactively, after an incident. The intervention is the right one "
        "and the timing is the problem, because nobody sees the escalation coming.",
        "Clarity, the cognitive model, runs on the same session audio and reads acoustic "
        "markers of agitation and cognitive decline ahead of the incident, turning a "
        "reactive service into a scheduled one.",
        "This is the most undervalued line. 99483, cognitive assessment and care plan, "
        "pays about $293 non facility or $170 facility as a single encounter, more than "
        "five months of BHI. And the operator side is bigger: see the Five-Star "
        "antipsychotic case in Section 05.")

    d.case("Mood Disorders",
        "Bipolar disorder management and mood stabilization, with dosing and physiology "
        "considerations specific to older adults.",
        "Relapse happens between visits. A switch into hypomania or a depressive turn is "
        "visible in days and the next scheduled session may be weeks out.",
        "Prosodic change detection against the resident's own prior sessions, which "
        "flags the direction of travel rather than the absolute score.",
        "Collaborative care subsequent month billing on a population already enrolled, "
        "plus avoided transfer. Honest caveat: acoustic detection of a manic switch is "
        "less validated in our own work than depression or anxiety, and this line should "
        "be scoped as exploratory in any pilot rather than promised.")

    d.case("Substance Use",
        "Age appropriate treatment for alcohol use disorder, prescription medication "
        "misuse and addiction recovery.",
        "Identification, almost entirely. Older adult substance use is massively under "
        "detected, and the standard screening instruments were not built for this cohort "
        "or for a resident whose family is in the room.",
        "Acoustic markers associated with sedation and intoxication on a session the "
        "resident is already attending for another reason, which is the only realistic "
        "way to surface this population at scale.",
        "SBIRT billing through G0396 and G0397, roughly $29 and $58 per encounter, is the "
        "direct code path, though the identification value is worth more than the code. "
        "Honest caveat: this is the least validated of the six for Sona-2 today. Treat it "
        "as a research line in a pilot, not a revenue commitment.")

    d.case("Adjustment and Loss",
        "Adjustment disorders, loss of independence and end of life support, including "
        "grief and bereavement.",
        "These are transition triggered and time boxed. Catching the transition is the "
        "entire clinical and commercial game, and the transitions that matter are a new "
        "admission, a death on the unit, and a functional decline.",
        "Change detection against the resident's own baseline from session one, with no "
        "enrollment period, which matters in a population that turns over fast.",
        "This is the enrollment pipeline for everything above it. Among residents "
        "admitted without pre-existing depression, 9.3 to 14.2 percent are diagnosed "
        "within 90 days and 21.6 percent within a year. Those are new billable episodes "
        "that only exist if somebody notices the transition.")

    # ============================================================ 03
    d.section("03", "The Operating Model")
    d.h2("The Care Coordinator Is the P&L")
    d.para("A dedicated Care Coordinator physically on site, in every facility, is the "
           "most expensive fixed cost in this business and the thing that makes it work. "
           "Familiar faces improve engagement, the coordinator handles setup, "
           "facilitation and documentation, and the operator gets the zero staff burden "
           "Theris promises. It is also the number that decides the margin, because "
           "everything scales with how many residents one coordinator can carry.")
    d.case("Care Coordinator Throughput",
        "One coordinator facilitates sessions for a facility's residents, queuing whoever "
        "is scheduled.",
        "Every resident gets roughly the same allocation of coordinator and clinician "
        "time regardless of risk. That is the default in the absence of a way to rank "
        "them, and it caps residents per coordinator.",
        "A risk ranking across every resident in the facility, refreshed every session, "
        "so the coordinator queues by who is deteriorating rather than by who is next on "
        "the list.",
        "This is the highest leverage number in the whole business. Every additional "
        "resident one coordinator can carry drops straight to gross margin, and it needs "
        "no new headcount, no new contract and no new facility. It cannot be sized from "
        "outside: it needs the current average caseload per coordinator, which is ask "
        "number three in Section 06.")

    # ============================================================ 04
    d.section("04", "The Four Product Claims")
    d.h2("Tested Against What the Technology Page Promises")

    d.case("Realtime Analysis and Improved Outcomes",
        "Continuous AI analysis during the encounter, longitudinal tracking against "
        "baseline, recovery markers, compared against billions of clinical datapoints.",
        "It is one modality. Language and the clinician's own observation both flow from "
        "the same evidence, so a second opinion drawn from them is not independent.",
        "A genuinely independent second read. Sona-2 analyzes acoustics, not the "
        "transcript: how the resident sounds rather than what they said.",
        "Two independent modalities agreeing is a materially stronger outcomes claim than "
        "one modality repeated, in an analyst conversation, a payer conversation and a "
        "regulatory file. It is also the cheapest credibility Theris can buy.")

    d.case("Maximized Reimbursement",
        "Automatic billing code determination, intelligent modifier suggestions, auto "
        "generated audit documentation.",
        "It codes a patient somebody already identified. It does not find the patient. "
        "Every unenrolled but eligible resident is invisible to a coding engine no matter "
        "how good the engine is.",
        "A read on every encounter, which surfaces residents who qualify and are not "
        "enrolled. The existing Theris engine then does what it already does well.",
        "The formula is (newly enrolled per facility) x (facilities) x ($55 per month). At "
        "10 residents across 200 facilities that is about $1.3 million a year on general "
        "BHI, or about $3.1 million on collaborative care at $130. Only the rates are "
        "real numbers. This is the highest value seam in the partnership, because the "
        "Theris strength sits directly downstream of the gap.")

    d.case("Increased Utilization",
        "10 to 15 minutes saved per session through auto drafted charts syncing to the "
        "EHR, sold as see more patients.",
        "That is the supply side of utilization and it is already solved. Freeing an hour "
        "does not say whose hour it should become.",
        "The demand side. Stratification puts the recovered time in front of the "
        "residents where it changes an outcome instead of spreading it evenly.",
        "Same pillar Theris already markets, a lever it does not have yet. Sizes off the "
        "same caseload number as Section 03, and the two compound: more time freed, "
        "better aimed.")

    d.case("Reduced Liability",
        "Multi page audit reports generated for every session, ready for CMS audits.",
        "Every element of that report derives from the clinician's own note. It documents "
        "the encounter thoroughly, and it corroborates nothing.",
        "One data point in the record that was not produced by the person being audited.",
        "It also supplies the audit trail the coding accuracy argument in Section 05 "
        "requires, so the mechanism is already built and this costs nothing to add.")

    # ============================================================ 05
    d.section("05", "The Facility Relationship")
    d.h2("What the Operator Gets Paid, and Why That Decides Renewals")
    d.para("Theris sells to facility operators and bills insurance. The operator renews "
           "the contract. So the strongest commercial argument in this document is not "
           "about what Theris earns, it is about what the operator earns because Theris "
           "is in the building. Two levers, and the Point Click Care integration means "
           "the data path for both already exists.")

    d.case("PDPM Nursing Case Mix",
        "Depression identified through the PHQ-9 resident mood interview or the staff "
        "assessment is a case mix split in the PDPM Nursing component.",
        "A resident in Clinically Complex with a function score of 0 to 5 classifies at a "
        "nursing CMI of 1.62 without depression indicators and 1.87 with them. The gap "
        "between those two is a resident who screens positive and is not identified.",
        "An acoustic read that routes to a clinician assessment, which either confirms "
        "the finding or does not, with an audit trail either way.",
        "The 0.25 CMI difference against an FY2026 urban nursing base of roughly $122 a "
        "day is about $30 per resident per day, or $800 to $900 across a typical covered "
        "Part A stay. Theris does not bill it. The operator does, which is exactly why it "
        "works as a renewal argument.")

    d.case("Five-Star and the Antipsychotic Measure",
        "Theris treats dementia related behaviors with person centered, non "
        "pharmacological interventions.",
        "The long stay antipsychotic quality measure moved to a hybrid method in January "
        "2026, combining MDS section N with claims data. The national rate rises from "
        "14.64 percent to 16.98 percent under the new calculation, and it rolls into "
        "Five-Star with providers sorted into deciles. Every operator's number just got "
        "worse through no change in their own behavior.",
        "Earlier detection of escalating behavior, which is what makes a non "
        "pharmacological intervention possible instead of theoretical.",
        "Five-Star drives census and Medicare Advantage network inclusion. A service that "
        "measurably protects an operator's antipsychotic decile in the year the measure "
        "got harder is not a nice to have, it is the reason the contract survives. This "
        "is the most timely argument Theris has available right now and it is worth "
        "leading with in operator conversations.")

    d.note("The guardrail on both of these, and it is not optional",
        "Both levers work as accuracy and never as inflation. The value is identifying "
        "residents who genuinely screen positive and are currently going unidentified, "
        "roughly a quarter of residents in the prevalence data. It is not producing "
        "depression codes or gaming a decile. Any version that reads as upcoding "
        "assistance fails compliance review at the first sophisticated operator and puts "
        "the relationship at risk. The acoustic signal routes to a clinician assessment "
        "that stands on its own, and the Theris audit report is where that shows.")

    # ============================================================ 06
    d.section("06", "Cost, Limits and the Ask")
    d.h2("What It Costs, Where It Is Weak, What Is Needed")

    d.h3("Cost to serve")
    d.para("Haven, the mental and behavioral health model, is $0.18 per assessment or "
           "$0.12 per minute of audio, scaling linearly with encounter volume. At one "
           "assessment per resident per week that is $9.36 per resident per year, against "
           "a PDPM swing of $800 to $900 a stay and single encounters worth $293. A free "
           "evaluation tier covers 100 assessments a month. Cost to serve is not the "
           "variable that decides any case in this document.")

    d.h3("Where this is weakest, stated plainly")
    d.bullet("Substance use is the least validated of the six service lines for Sona-2. "
             "It belongs in a pilot as a research line, not as a revenue commitment.")
    d.bullet("Acoustic detection of a manic switch is less validated than depression or "
             "anxiety. Scope the mood disorder line as exploratory.")
    d.bullet("The Five-Star antipsychotic argument is causally plausible and not yet "
             "demonstrated. It needs an operator willing to measure it, which is a "
             "different and slower pilot than the enrollment one.")
    d.bullet("Every dollar figure here is a public benchmark. None of it is Theris data, "
             "and the spread between the illustrative and the real numbers is the whole "
             "reason for the three asks below.")

    d.h3("The three numbers")
    d.table("WHAT ONLY THERIS HAS", [
        ("Facility count", "The real number, by state and by facility type", ""),
        ("Missed enrollment", "Residents per facility eligible for BHI or CoCM, not enrolled", ""),
        ("Coordinator caseload", "Average residents per Care Coordinator today", ""),
    ], col_x=(0, 160), row_h=19)

    d.h3("The one step that tests all of it")
    d.para("Run Sona-2 against a retrospective slice of telehealth session audio Theris "
           "has already captured. No workflow change, no consent change, no Care "
           "Coordinator or clinician time. It returns two things: a count of residents "
           "the model flags who are not currently enrolled, and agreement statistics "
           "against the PHQ-9 and GAD-7 scores already sitting in those charts.")
    d.para("The second output is the one worth optimizing for. Agreement against "
           "instruments Theris already trusts is the fastest credible proof available, "
           "and it is a validation datapoint Theris keeps regardless of whether anything "
           "else here goes forward. Integration when it does: one HTTPS POST after the "
           "session, JSON back in seconds, asynchronous and server side, inside the "
           "documentation pipeline already running into Athena and Point Click Care. BAA "
           "at account creation, audio processed and discarded, nothing stored.")

    d.callout("From Amplifier Health",
        "The retrospective run costs a data pull and nothing else, and it either produces "
        "a missed enrollment number and an agreement statistic that carry the cases above "
        "or it does not. Every number in this document is a public benchmark waiting to "
        "be replaced by a real one. amplifierhealth.com, docs.amplifierhealth.com, "
        "console.amplifierhealth.com.")

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
