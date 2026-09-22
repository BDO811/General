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
        self.need(70)
        self.y -= 6
        hrule(self.c, self.y, color=BRAND["primary"], thickness=1.6)
        self.y -= 14
        draw(self.c, ML, self.y, "SECTION %s  ·  %s" % (number, name.upper()),
             "Inter-Bold", 7.4, BRAND["secondary"])
        self.y -= 16

    def h2(self, text):
        self.need(34)
        lines = wrap_text(self.c, text, "Inter-Bold", 15.1, TW)
        for ln in lines:
            draw(self.c, ML, self.y, ln, "Inter-Bold", 15.1, BRAND["ink"])
            self.y -= 18
        self.y -= 3

    def h3(self, text):
        self.need(30)
        self.y -= 4
        draw(self.c, ML, self.y, text, "Inter-Bold", 11.5, BRAND["ink"])
        self.y -= 15

    def kicker(self, text):
        self.need(22)
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
        "A revenue and risk case for running Sona-2's acoustic layer on the encounters "
        "Theris clinicians already record, built around what a facility operator and a "
        "behavioral health P&L actually pay for: more of the revenue Theris is already "
        "eligible for and currently leaves on the table, and lower downstream cost per "
        "resident. No new product for Theris to sell, and no added clinician hours.")
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
def build(out):
    d = Doc(out)
    cover(d)

    # ============================================================ 01
    d.section("01", "The Four Arguments")
    d.h2("Where This Makes Theris Money")
    d.para("Four ways to look at this partnership: what it does for Theris's technology "
           "story, what it does for residents and patients, where it adds revenue inside "
           "the United States and everywhere else, and where it takes cost out by taking "
           "risk out.")
    d.para("One constraint shapes all four. This is not a new product for Theris to sell. "
           "Theris does not have the proof points to stand up a separate SKU today, and "
           "trying would slow the deal down. Everything below runs on encounters Theris "
           "already records, with the clinicians Theris already employs, inside contracts "
           "Theris has already signed.")

    d.h3("1.  New Technology: Why It Is Good for Theris (PR, Cutting Edge)")
    d.bullet("Theris already extracts digital biomarkers from voice cadence and facial "
             "micro-expressions, on models built over open-source Qwen. The acoustic layer "
             "is not a new idea to this team. The question is whether Theris builds a "
             "clinical-grade acoustic foundation model itself or licenses one that already "
             "exists, and licensing gets the capability to market years earlier.")
    d.bullet("Sona-2 reads the physiology in the voice rather than the words. That is a "
             "defensible technical talking point in an analyst or press conversation, and "
             "it is materially different from a general speech model fine-tuned on "
             "encounter audio.")
    d.bullet("Theris is pursuing FDA Class II status. Amplifier's own regulatory work on a "
             "voice-derived depression biomarker runs in parallel and can be cited as "
             "supporting evidence rather than duplicated, which shortens the path instead "
             "of competing with it.")
    d.bullet("Theris publishes a 94 percent diagnostic accuracy figure against human "
             "psychology assessment. An independently developed acoustic model agreeing "
             "with that number is a stronger external validation story than another "
             "in-house metric, and it is the kind of proof point a payer or a VA contracting "
             "officer weighs differently.")
    d.bullet("Being first to scale a clinical acoustic biomarker across facility-based care "
             "matters more for the narrative than being first to clear. Nobody else is "
             "running this in sober living, VA community residences, skilled nursing and "
             "schools at once.")

    d.stats([
        ("8", "STATES", "Current Theris footprint"),
        ("100s", "FACILITIES", "SNF, ALF, VA, sober living, K-12"),
        ("150K+", "HOURS", "Encounter audio already captured"),
    ])

    # ============================================================ 02
    d.section("02", "Patient Care")
    d.h2("How This Helps Patients")
    d.bullet("Depression is the most prevalent mental health disorder in nursing homes and "
             "affects close to half of residents. In one Ohio study, 48 percent of residents "
             "were depressed, 23 percent of them were receiving no treatment at all, and "
             "only 2.5 percent were receiving any behavioral therapy. That gap is the whole "
             "patient care argument in one statistic.")
    d.bullet("Among residents newly admitted without pre-existing depression, 9.3 to 14.2 "
             "percent are diagnosed within 90 days and 21.6 percent within a year. The "
             "condition develops during the stay, which means a one-time intake screen "
             "cannot catch it and a continuous signal can.")
    d.bullet("Zero added burden on the resident. No new test, no wearable, no extra time in "
             "the session. The signal rides on audio that was going to be recorded anyway, "
             "under a consent Theris already obtains, with an opt-out rate under 1 percent.")
    d.bullet("It augments the clinician rather than replacing them. Every signal is "
             "something a Theris clinician reviews and acts on or does not, which matters to "
             "a facility medical director worried about AI reaching into diagnosis.")
    d.bullet("It extends specialty-level pattern recognition into settings that are "
             "chronically underserved by in-person behavioral health: sober living homes, VA "
             "community residences, and rural skilled nursing. These are exactly the places "
             "where a psychiatrist is not walking the hall.")
    d.bullet("Repeated encounters turn single visits into a trend line. Gradual mood, "
             "cognitive or respiratory decline between visits is precisely what a single "
             "snapshot assessment misses and a continuous one catches.")

    # ============================================================ 03
    d.section("03", "Increased Revenue")
    d.h2("United States")
    d.para("Two payment rails matter here, and they pay different people. The first is "
           "fee-for-service billing through CPT and HCPCS codes, which pays Theris directly "
           "for behavioral health services it already delivers. The second is facility and "
           "plan payment, PDPM for skilled nursing and risk adjustment for Medicare "
           "Advantage, which pays the operator and the plan. The second rail is the one "
           "that renews Theris's contracts, and it is the one nobody is pitching them on.")

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
    d.para("Rates vary by state and payer, and these are national midpoints rather than "
           "exact figures. Two things are worth pulling out. First, the collaborative care "
           "codes pay roughly two and a half times what the general BHI code pays for the "
           "same enrolled patient, so which code an eligible patient lands in matters as "
           "much as whether they are enrolled at all. Second, 99483 is a single-encounter "
           "code worth more than five months of BHI, and it maps directly onto the memory "
           "care population Theris already focuses on.")

    d.kicker("The enrollment gap, sized")
    d.para("Behavioral health programs pay monthly, per enrolled patient, but only for "
           "patients somebody identified. Sona-2 runs on every encounter, so it surfaces "
           "eligible patients who are not being enrolled today. The model is straightforward:")
    d.callout("The Formula",
        "(newly enrolled patients per facility)  x  (number of facilities)  x  ($55 per month)  "
        "=  monthly recurring revenue. At 10 newly enrolled patients across 200 facilities, "
        "that is 2,000 patients, about $110,000 a month, about $1.3 million a year. Only the "
        "$55 is a real number. The other two inputs are illustrative and have to come from "
        "Theris.")
    d.para("The same formula run on collaborative care rather than general BHI, at roughly "
           "$130 per patient per subsequent month, produces about $260,000 a month or $3.1 "
           "million a year on the identical patient count. The spread between those two "
           "outcomes is larger than the spread between any two assumptions about facility "
           "count, which is why the code mix is worth getting right before the volume "
           "estimate is.")

    d.note("Two inputs needed from Theris",
        "This stops being an illustrative model and becomes an actual one with two numbers "
        "only Theris has: the real facility count, and the current missed enrollment rate, "
        "meaning how many patients per facility plausibly qualify for 99484 or the "
        "collaborative care codes today and are not enrolled. Everything else above is "
        "public.")

    d.kicker("Rail two: what the facility and the plan get paid")
    d.para("This is the part that defends the renewal, and it is worth more attention than "
           "it usually gets. Under PDPM, signs and symptoms of depression identified through "
           "the PHQ-9 resident mood interview or the staff assessment are a case-mix split "
           "in the Nursing component. A resident in Clinically Complex with a function score "
           "of 0 to 5 classifies at a nursing CMI of 1.62 without depression indicators and "
           "1.87 with them. Depression is also a split in Special Care High and Special Care "
           "Low.")
    d.para("That 0.25 CMI difference, applied against an FY2026 urban nursing base of "
           "roughly $122 per day, is about $30 per resident per day, or roughly $800 to $900 "
           "across a typical covered Part A stay. The base rate figure is the FY2025 base "
           "carried forward at the finalized 3.2 percent update and should be confirmed "
           "against Table 6 of the FY2026 final rule before it goes in front of an operator.")
    d.para("The point is not that Theris bills this. The operator does. The point is that a "
           "Theris contract becomes the reason the operator's MDS reflects the resident "
           "accurately, which is a dollar argument Theris can make to a facility "
           "administrator in a language that administrator already speaks.")

    d.note("The guardrail, and it is not optional",
        "This argument only works as accuracy, never as inflation. The value is identifying "
        "residents who genuinely screen positive and are currently going unidentified, "
        "roughly a quarter of residents in the prevalence data. It is not producing "
        "depression codes. Any version of this that reads as upcoding assistance fails "
        "compliance review at the first sophisticated operator and puts the whole "
        "relationship at risk, so the acoustic signal has to route to a clinician "
        "assessment that stands on its own, with an audit trail showing it did.")

    d.bullet("Medicare Advantage risk adjustment: every 0.1 increase in a member's RAF score "
             "is worth roughly $1,000 to $1,040 per member per year in plan revenue. "
             "Depression carries HCC weight under version 28 when coded as moderate or "
             "severe active major depressive disorder. Where Theris serves MA-covered "
             "residents, the plan is the natural buyer for a tool that catches one more "
             "condition accurately.")
    d.bullet("The Department of Veterans Affairs is among Theris's largest clients and runs "
             "on a different rail again, contract terms rather than per-code billing. A "
             "measurable improvement in identification rates across VA community residences "
             "is scope-expansion leverage at the next contract cycle rather than a billable "
             "line, and it should be modeled that way rather than forced into the CPT math.")
    d.bullet("Sober living homes, assisted living and K-12 are mostly outside Medicare Part "
             "A entirely. Those settings are commercial, Medicaid and private-pay, and the "
             "revenue argument there is program-level rather than code-level. They belong in "
             "the volume story, not in the $55 arithmetic.")

    # ---- outside US
    d.h2("Outside the United States")
    d.para("Theris operates in eight US states today, so this is an expansion map rather "
           "than current revenue, and it should be presented that way. It is included "
           "because the facility-based structure Theris has built is portable, and every "
           "major market pays for exactly the identification work Sona-2 does, through its "
           "own mechanics.")
    d.numbered(1, "United Kingdom. The QOF pay-for-performance layer runs at roughly "
                  "£225 per point across 582 points. Care home residents sit inside GP "
                  "practice registers, and the hypertension indicator HYP008 alone moved "
                  "from 14 to 38 points in 2025/26, worth about £5,400 per practice at full "
                  "achievement. The depression case-finding indicator was retired, so "
                  "dementia and severe mental illness physical health checks are the "
                  "stronger ground here, not depression.")
    d.numbered(2, "Germany. New 2026 Disease Management Programs for depression and heart "
                  "failure pay recurring documentation and coordination fees of €13 to €25, "
                  "up to twice yearly, on top of the consultation. A flagged signal that "
                  "leads to a DMP enrollment is a recurring line, not a one-time fee, and "
                  "the new depression DMP maps directly onto Amplifier's own model domain.")
    d.numbered(3, "Australia. Residential aged care sits alongside MBS billing. GP Mental "
                  "Health Treatment Plan items 2715 and 2717 pay $103.70 and $152.80, and "
                  "Chronic Condition Management items 965 and 967 pay $156.55 each.")
    d.numbered(4, "Japan. Long-term care is the whole national cost problem. Combined "
                  "medical and long-term care spend is projected to reach ¥80 to 83 trillion "
                  "by 2040, about one and a half times the 2020 level, driven by the 75-plus "
                  "and 85-plus population. The chronic disease management fee pays a monthly "
                  "per-patient amount once a physician documents ongoing management.")
    d.numbered(5, "Canada. Long-term care is provincially funded with case-mix methodologies "
                  "closer to the US PDPM logic than to any European model, which makes it "
                  "the most structurally similar first export market and the one worth "
                  "sizing first if Theris ever moves.")

    # ============================================================ 04
    d.section("04", "Decreased Risk")
    d.h2("Where Risk Turns Into Cost")
    d.numbered(1, "Avoidable hospitalization. More than a third of residents in Medicare and "
                  "Medicaid-covered nursing facilities are hospitalized at least once, "
                  "totaling 958,837 hospitalizations, and up to 39 percent of those, about "
                  "382,846 admissions, are considered potentially avoidable with more "
                  "effective care. Medicare spent $14.3 billion on nursing home resident "
                  "hospitalizations in a single year, with $4 billion a year attributed to "
                  "the avoidable share. Untreated depression is an independent driver of "
                  "that transfer rate, not a side issue.")
    d.numbered(2, "Missed-condition exposure. Every flagged signal is one the clinician "
                  "either acts on or documents a reason not to. A single missed-diagnosis "
                  "claim in a facility setting runs into six or seven figures with defense "
                  "costs. This is the line item that turns safer directly into cheaper, and "
                  "it accrues to Theris and to the operator simultaneously.")
    d.numbered(3, "Clinician capacity, which is a cost problem wearing a quality costume. "
                  "Today every resident gets roughly the same level of attention regardless "
                  "of risk. Sorting residents into low, moderate and high risk lets Theris "
                  "clinicians concentrate where it matters. Theris already markets seeing "
                  "more patients as a benefit. This is a sharper way to actually deliver it, "
                  "and it prices out as freed clinician hours rather than as new revenue.")
    d.numbered(4, "Renewal and churn protection on Theris's own book. Contracts renew on "
                  "proof of value. A facility-level view of how residents are trending over "
                  "time is that proof, and nothing else in the Theris stack produces it "
                  "today. It is the argument for keeping Theris, for expanding to more "
                  "facilities in the same operator group, and for defending price at "
                  "renewal. This is risk to Theris's own recurring revenue, priced with the "
                  "same avoided-cost logic as everything above.")

    d.note("What number 3 and number 4 still need",
        "Neither of these prices out from public data. Capacity needs the average caseload "
        "per Theris clinician and how visit frequency is currently allocated across risk "
        "levels. Renewal protection needs the current facility-level churn or renewal rate. "
        "Both live inside Theris. They are the second and third asks on the call, after the "
        "facility count.")

    # ============================================================ 05
    d.section("05", "Unit Economics")
    d.h2("What This Costs to Run")
    d.bullet("Haven, Amplifier's mental and behavioral health model, is the direct fit for "
             "the encounters Theris already runs. Pricing is $0.18 per assessment, or $0.12 "
             "per minute of audio, scaling linearly with encounter volume.")
    d.bullet("At one assessment per resident per week, that is $9.36 per resident per year. "
             "Against a single avoided hospitalization, or against the roughly $800 to $900 "
             "of nursing component accuracy on one Part A stay, or against $55 a month of "
             "newly captured BHI revenue, the cost side is not the variable that decides "
             "this.")
    d.bullet("A free evaluation tier covers 100 assessments per month, so Theris can test on "
             "real encounters before committing to anything.")
    d.bullet("Clarity, the cognitive model, runs on the same endpoint and the same audio, "
             "which is the natural second step for the memory care and skilled nursing "
             "populations Theris already serves.")
    d.para("The core objection to a second foundation model on every encounter is that it "
           "adds cost to serve. At $9.36 per resident per year against events costing "
           "thousands, that gap is wide enough that even a deliberately conservative "
           "scenario clears several times over before Sona-2 has generated a single outcome "
           "data point of its own inside Theris.")

    # ============================================================ 06
    d.section("06", "The Ask")
    d.h2("What We Need From Theris")
    d.para("Three numbers turn this from a structured argument into an actual model. All "
           "three live inside Theris and none of them are in anything public.")
    d.table("THE THREE INPUTS", [
        ("Facility count", "The real number behind “hundreds of facilities”, by setting type", ""),
        ("Missed enrollment", "Patients per facility eligible for BHI or CoCM, not enrolled", ""),
        ("Clinician caseload", "Average caseload and how visit frequency is allocated", ""),
    ], col_x=(0, 150), row_h=19)
    d.para("With those three, the pitch resolves into one signal with three effects: a "
           "revenue effect, a capacity effect, and a retention effect. Without them it stays "
           "four competing ideas, and the second one is the only one anybody can size.")

    d.h3("The Proposed Path")
    d.bullet("Run Sona-2 against a retrospective slice of encounter audio Theris has already "
             "captured. No workflow change, no consent change, no clinician time. The output "
             "is a count of residents the model flags who are not currently enrolled.")
    d.bullet("Compare that count against Theris's own enrollment records to produce the real "
             "missed enrollment rate, which is input number two above and the input the "
             "entire revenue case rests on.")
    d.bullet("If the rate holds, move to a prospective pilot of 200 to 500 residents across "
             "60 to 90 days in a single operator group, instrumented to measure enrollment "
             "lift, clinician time reallocation, and facility-level trend reporting at once.")
    d.bullet("Integration is one HTTPS POST returning a JSON response with depression, "
             "anxiety and stress fields in seconds, asynchronous and server side, sitting "
             "inside the post-encounter documentation pipeline Theris already runs. A HIPAA "
             "BAA is executed at account creation, audio is processed and discarded, and no "
             "audio is stored on Amplifier systems.")

    d.callout("From Amit Mehta  ·  CEO, Amplifier Health",
        "The retrospective run is the whole proposal. It costs Theris nothing but a data "
        "pull, it changes nothing about how a visit runs, and it either produces a missed "
        "enrollment number that justifies everything above or it does not. Everything else "
        "here is scaffolding around that one measurement. amplifierhealth.com, "
        "docs.amplifierhealth.com, console.amplifierhealth.com. Up and running in under five "
        "minutes.")

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
