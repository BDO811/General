# -*- coding: utf-8 -*-
"""Amplifier Health design system for ReportLab.

Two document forms share one system:
    Flyer     one page, cream ground, green logo top left, pink accent
    Proposal  multi page, cream ground, black logo top right, no pink

Tokens and geometry are measured from the shipped reference PDFs.
Import this module, call new_doc(), then compose with the primitives.
"""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
FONTDIR = os.environ.get("AMPLIFIER_FONTS", os.path.expanduser("~/.amplifier-fonts"))

# ---------------------------------------------------------------- tokens
PW, PH = 612, 792

# ground
CREAM   = HexColor("#F0EAE0")   # every page, edge to edge
BOXFILL = HexColor("#DDDDD3")   # proposal callout and stat cell fill

# ink
INK     = HexColor("#0B0B0A")   # proposal headline, rules, mono headers
BLACK   = HexColor("#000000")   # flyer hero serif, flyer CTA pill
BODY    = HexColor("#181716")   # flyer body copy
BODY_P  = HexColor("#555550")   # proposal body copy
ITALIC  = HexColor("#32322E")   # proposal italic subhead, serif subheads
ITAL_F  = HexColor("#484643")   # flyer italic subhead
MUTED   = HexColor("#6C6965")   # flyer mono labels, disclaimer
MUTED_P = HexColor("#7C7C7B")   # proposal mono meta and footer

# accent
PINK    = HexColor("#FF4AF2")   # flyer only. never appears in a proposal
BAND    = HexColor("#F1DDE1")   # pale band behind the flyer hero
GREEN   = HexColor("#1E5631")   # flyer logo only

# rules and blocks
HAIR    = HexColor("#D8D0C2")   # flyer hairline
CODEBG  = HexColor("#12241A")   # flyer sample response block
CODETX  = HexColor("#E9E3D5")   # code punctuation and values
BTNTX   = HexColor("#F0EAE0")   # CTA pill label

# geometry
FLY_ML, FLY_MR = 50, 50
FLY_TW = PW - FLY_ML - FLY_MR          # 512
PRO_ML, PRO_MR = 54, 54
PRO_TW = PW - PRO_ML - PRO_MR          # 504

# fonts
MONO   = "JetBrainsMono"
MONO_B = "JetBrainsMono-Bold"
CORM   = "CormorantGaramond-Light"
NEWS   = "Newsreader"
NEWS_I = "Newsreader-Italic"
INTER  = "Inter"
INTER_B = "Inter-Bold"

_FACES = [
    (MONO,    "JetBrainsMono-Regular.ttf"),
    (MONO_B,  "JetBrainsMono-Bold.ttf"),
    (CORM,    "CormorantGaramond-Light.ttf"),
    (NEWS,    "Newsreader-Regular.ttf"),
    (NEWS_I,  "Newsreader-Italic.ttf"),
    (INTER,   "Inter-Regular.ttf"),
    (INTER_B, "Inter-Bold.ttf"),
]

def register_fonts(fontdir=None):
    d = fontdir or FONTDIR
    missing = [f for _, f in _FACES if not os.path.exists(os.path.join(d, f))]
    if missing:
        raise SystemExit(
            "Missing fonts in %s: %s\nRun: python3 %s/fetch_fonts.py"
            % (d, ", ".join(missing), HERE))
    for name, fn in _FACES:
        pdfmetrics.registerFont(TTFont(name, os.path.join(d, fn)))


# ---------------------------------------------------------------- doc
class Doc(object):
    def __init__(self, path, kind="flyer"):
        register_fonts()
        self.c = canvas.Canvas(path, pagesize=(PW, PH))
        self.kind = kind
        self.page = 1
        self.total = None
        self.ML = FLY_ML if kind == "flyer" else PRO_ML
        self.TW = FLY_TW if kind == "flyer" else PRO_TW
        self.ground()

    # -- ground and text ------------------------------------------------
    def ground(self):
        self.c.setFillColor(CREAM)
        self.c.rect(0, 0, PW, PH, stroke=0, fill=1)

    def text(self, x, y, s, font, size, color, align="left", tracking=0):
        c = self.c
        if not tracking:
            c.setFont(font, size); c.setFillColor(color)
            if align == "right":
                c.drawRightString(x, y, s)
            elif align == "center":
                c.drawCentredString(x, y, s)
            else:
                c.drawString(x, y, s)
            return
        w = self.width(s, font, size, tracking)
        if align == "right":
            x -= w
        elif align == "center":
            x -= w / 2.0
        t = c.beginText(x, y)
        t.setFont(font, size)
        t.setFillColor(color)
        t.setCharSpace(tracking)
        t.textOut(s)
        t.setCharSpace(0)          # Tc is text state and persists. always reset.
        c.drawText(t)

    def width(self, s, font, size, tracking=0):
        return self.c.stringWidth(s, font, size) + tracking * max(len(s) - 1, 0)

    def wrap(self, s, font, size, max_w, tracking=0):
        out, line = [], ""
        for w in s.split():
            t = (line + " " + w).strip()
            if self.width(t, font, size, tracking) <= max_w:
                line = t
            else:
                if line:
                    out.append(line)
                line = w
        if line:
            out.append(line)
        return out

    def para(self, x, y, s, font, size, color, max_w, lead, tracking=0):
        for ln in self.wrap(s, font, size, max_w, tracking):
            self.text(x, y, ln, font, size, color, tracking=tracking)
            y -= lead
        return y

    def fit(self, s, font, max_w, hi=90, lo=14, tracking=0):
        size = hi
        while size >= lo:
            if self.width(s, font, size, tracking) <= max_w:
                return size
            size -= 0.5
        return lo

    # -- rules and blocks ------------------------------------------------
    def rule(self, y, color=HAIR, w=0.5, x0=None, x1=None):
        x0 = self.ML if x0 is None else x0
        x1 = (PW - (FLY_MR if self.kind == "flyer" else PRO_MR)) if x1 is None else x1
        self.c.setStrokeColor(color); self.c.setLineWidth(w)
        self.c.line(x0, y, x1, y)

    def fill(self, x, y, w, h, color):
        self.c.setFillColor(color); self.c.rect(x, y, w, h, stroke=0, fill=1)

    def box(self, x, y, w, h, fill=BOXFILL, stroke=INK, lw=0.6):
        self.c.setFillColor(fill); self.c.setStrokeColor(stroke); self.c.setLineWidth(lw)
        self.c.rect(x, y, w, h, stroke=1 if stroke else 0, fill=1 if fill else 0)

    # -- logo -------------------------------------------------------------
    def logo(self, x, y, width=72, variant="black"):
        """Place the Amplifier wordmark. y is the baseline of the mark."""
        fn = "amplifier_logo_%s.png" % ("green" if variant == "green" else "black")
        path = os.path.join(ASSETS, fn)
        ratio = 0.2247 if variant == "black" else 0.2157   # measured from source
        h = width * ratio
        self.c.drawImage(path, x, y, width=width, height=h,
                         mask=None, preserveAspectRatio=True, anchor="sw")
        return h

    def new_page(self):
        self.c.showPage()
        self.page += 1
        self.ground()

    def save(self):
        self.c.save()


# ---------------------------------------------------------------- flyer
# Grid measured from Amplifier_Flyer_06_Consumer_Wellness.pdf.
# Every number is a baseline in ReportLab coordinates unless named _TOP/_H.
FG = dict(
    LOGO_X=56.6, LOGO_Y=734.6, LOGO_W=96.6,
    TAGLINE_Y=742.05,
    EYEBROW_Y=706.05,
    BAND_Y=634.0, BAND_H=90.1,          # pale pink band behind the hero
    HERO_Y=675.96, HERO_SIZE=26, HERO_LEAD=26.0,
    SUB_Y=616.03, SUB_SIZE=19, SUB_LEAD=22.8,
    STAT_NUM_Y=560.42, STAT_LBL_Y=543.44, STAT_LBL_LEAD=7.2,
    PINK_RULE_Y=530.2,
    SECTION_Y=518.19,
    LEDE_Y=505.22, BODY_LEAD=10.6,
    FIRST_RULE_Y=482.0, BLOCK_PITCH=52.2,
    BLOCK_LABEL_DY=17.96, BLOCK_BODY_DY=29.98,
    CODE_LABEL_Y=255.39, CODE_BOX_Y=194.2, CODE_BOX_H=49.0,
    CODE_FIRST_Y=234.53, CODE_LEAD=8.8,
    CODE_X0=64, CODE_X1=76, CODE_X2=88,
    CTA_Y=144.0, CTA_W=190.0, CTA_H=26.0, CTA_LABEL_X=70, CTA_LABEL_Y=154.25,
    FOOT_RULE_Y=108.0, FOOT_Y=94.04,
    DISC_Y=81.99, DISC_LEAD=9.0,
)

def flyer_header(d, tagline):
    """Green wordmark top left, mono tagline top right."""
    d.logo(FG["LOGO_X"], FG["LOGO_Y"], width=FG["LOGO_W"], variant="green")
    d.text(PW - FLY_MR, FG["TAGLINE_Y"], tagline.upper(), MONO, 7.5, MUTED,
           align="right", tracking=1.0)

def flyer_eyebrow(d, text):
    d.text(FLY_ML, FG["EYEBROW_Y"], text.upper(), MONO_B, 9.5, PINK, tracking=1.1)

def flyer_hero(d, text, band=True):
    """Serif hero over the pale pink band. Two lines is the design target."""
    if band:
        d.fill(FLY_ML, FG["BAND_Y"], FLY_TW, FG["BAND_H"], BAND)
    y = FG["HERO_Y"]
    for ln in d.wrap(text, CORM, FG["HERO_SIZE"], FLY_TW - 4):
        d.text(FLY_ML, y, ln, CORM, FG["HERO_SIZE"], BLACK)
        y -= FG["HERO_LEAD"]

def flyer_subhead(d, text):
    y = FG["SUB_Y"]
    for ln in d.wrap(text, NEWS_I, FG["SUB_SIZE"], FLY_TW):
        d.text(FLY_ML, y, ln, NEWS_I, FG["SUB_SIZE"], ITAL_F)
        y -= FG["SUB_LEAD"]

def flyer_stats(d, stats):
    """Four across on a 128pt pitch. stats = [(value, label), ...]."""
    n = len(stats); cw = FLY_TW / n
    for i, (val, lbl) in enumerate(stats):
        x = FLY_ML + i * cw
        d.text(x, FG["STAT_NUM_Y"], val, CORM, 14, BLACK)
        y = FG["STAT_LBL_Y"]
        for ln in d.wrap(lbl.upper(), MONO, 5.8, cw - 16, 0.55):
            d.text(x, y, ln, MONO, 5.8, MUTED, tracking=0.55)
            y -= FG["STAT_LBL_LEAD"]
    d.rule(FG["PINK_RULE_Y"], PINK, 1.4)

def flyer_body(d, section, lede, blocks):
    """Pink section label, lede, then up to four labelled blocks on a 52.2pt pitch.

    blocks = [(label, text), ...]. Each block is one label line plus two body
    lines. Write to that budget. The grid does not stretch.
    """
    d.text(FLY_ML, FG["SECTION_Y"], section.upper(), MONO_B, 8.3, PINK, tracking=1.0)
    y = FG["LEDE_Y"]
    for ln in d.wrap(lede, INTER, 8.8, FLY_TW):
        d.text(FLY_ML, y, ln, INTER, 8.8, BODY); y -= FG["BODY_LEAD"]
    rule_y = FG["FIRST_RULE_Y"]
    d.rule(rule_y)
    for label, text in blocks:
        d.text(FLY_ML, rule_y - FG["BLOCK_LABEL_DY"], label.upper(), MONO_B, 7.8,
               PINK, tracking=0.9)
        by = rule_y - FG["BLOCK_BODY_DY"]
        for ln in d.wrap(text, INTER, 8.8, FLY_TW):
            d.text(FLY_ML, by, ln, INTER, 8.8, BODY); by -= FG["BODY_LEAD"]
        rule_y -= FG["BLOCK_PITCH"]
        d.rule(rule_y)

def flyer_code(d, label, endpoint, lines):
    """Dark sample response block. lines = [(indent 0|1|2, key_or_None, rest), ...]
    key renders pink, rest renders in the pale code ink."""
    d.text(FLY_ML, FG["CODE_LABEL_Y"], label.upper(), MONO_B, 8.3, PINK, tracking=1.0)
    d.text(PW - FLY_MR, FG["CODE_LABEL_Y"], endpoint.upper(), MONO, 6.8, MUTED,
           align="right", tracking=0.5)
    d.fill(FLY_ML, FG["CODE_BOX_Y"], FLY_TW, FG["CODE_BOX_H"], CODEBG)
    xs = [FG["CODE_X0"], FG["CODE_X1"], FG["CODE_X2"]]
    y = FG["CODE_FIRST_Y"]
    for indent, key, rest in lines:
        x = xs[min(indent, 2)]
        if key:
            d.text(x, y, key, MONO, 7.1, PINK)
            x += d.width(key, MONO, 7.1)
        d.text(x, y, rest, MONO, 7.1, CODETX)
        y -= FG["CODE_LEAD"]

def flyer_cta(d, label, contact):
    d.fill(FLY_ML, FG["CTA_Y"], FG["CTA_W"], FG["CTA_H"], BLACK)
    d.text(FG["CTA_LABEL_X"], FG["CTA_LABEL_Y"], label.upper(), MONO_B, 8.5, BTNTX,
           tracking=1.0)
    d.text(PW - FLY_MR, FG["CTA_LABEL_Y"], contact.upper(), MONO, 7.7, MUTED,
           align="right", tracking=0.55)

def flyer_footer(d, left, right, disclaimer):
    d.rule(FG["FOOT_RULE_Y"], HAIR, 0.75)
    d.text(FLY_ML, FG["FOOT_Y"], left.upper(), MONO, 6.8, MUTED, tracking=0.8)
    d.text(PW - FLY_MR, FG["FOOT_Y"], right.upper(), MONO, 6.8, MUTED,
           align="right", tracking=0.6)
    y = FG["DISC_Y"]
    for ln in d.wrap(disclaimer, INTER, 6.6, FLY_TW):
        d.text(FLY_ML, y, ln, INTER, 6.6, MUTED); y -= FG["DISC_LEAD"]


# ---------------------------------------------------------------- proposal
# Grid measured from Amplifier_and_NiceHealthcare_Proposal.pdf.
PG = dict(
    LOGO_X=482.3, LOGO_Y=716.9, LOGO_W=70.8,
    HEAD_RULE_Y=697.0,
    META_L_Y=679.52, META_R_Y=678.82,
    HERO_Y=559.86, HERO_LEAD=76.8, HERO_MAX=75.3,
    TAGLINE_Y=400.27, TAG_SIZE=18,
    COVER_RULE_Y=384.3,
    COVER_BOX_Y=266.3, COVER_BOX_H=102.0,
    RUN_HEAD_Y=706.85,
    SECTION_Y=679.95, SECTION_TITLE_X=96,
    SUBHEAD_DY=16.0, SUBHEAD_X=69, SUBHEAD_SIZE=12.0,
    BODY_START=660.04, BULLET_LEAD=11.8, BULLET_GAP=4.0,
    BULLET_MARK_X=58, BULLET_TEXT_X=69, BULLET_MARK_DY=-1.4,
    STAT_H=54.0, STAT_GAP=3.0, STAT_NUM_DY=28.5, STAT_LBL_DY=13.0, STAT_SUB_DY=5.0,
    FOOT_RULE_Y=52.0, FOOT_Y=40.05,
    BOTTOM=70.0,
)

def proposal_chrome(d, running_title=None):
    """Logo, rules and footer furniture. Call once per page, before content."""
    d.logo(PG["LOGO_X"], PG["LOGO_Y"], width=PG["LOGO_W"], variant="black")
    if running_title:
        d.text(PRO_ML, PG["RUN_HEAD_Y"], running_title.upper(), MONO, 10.5, INK,
               tracking=0.6)
    d.rule(PG["HEAD_RULE_Y"], INK, 0.5)

def proposal_footer(d, left, total=None):
    d.rule(PG["FOOT_RULE_Y"], INK, 0.5)
    d.text(PRO_ML, PG["FOOT_Y"], left.upper(), MONO, 8.5, MUTED_P, tracking=0.6)
    right = "%d / %d" % (d.page, total) if total else str(d.page)
    d.text(PW - PRO_MR, PG["FOOT_Y"], right, MONO, 8.5, MUTED_P, align="right",
           tracking=0.6)

def proposal_cover(d, partner, tagline, meta_left, meta_right,
                   bg_label="Background", bg_text=""):
    """Cover page. Partner name sets in huge Inter Bold, one or two lines."""
    proposal_chrome(d)
    d.text(PRO_ML, PG["META_L_Y"], meta_left.upper(), MONO, 7.4, MUTED_P, tracking=0.8)
    d.text(PW - PRO_MR, PG["META_R_Y"], meta_right.upper(), MONO, 8.4, MUTED_P,
           align="right", tracking=0.8)

    words = partner.upper().split()
    lines = [words[0], " ".join(words[1:])] if len(words) > 1 else [words[0]]
    size = min([d.fit(l, INTER_B, PRO_TW, PG["HERO_MAX"], 26) for l in lines])
    y = PG["HERO_Y"]
    for l in lines:
        d.text(PRO_ML, y, l, INTER_B, size, INK)
        y -= PG["HERO_LEAD"] * (size / PG["HERO_MAX"])

    d.para(PRO_ML, PG["TAGLINE_Y"], tagline, NEWS_I, PG["TAG_SIZE"], ITALIC,
           PRO_TW, 24)
    d.rule(PG["COVER_RULE_Y"], INK, 0.5)

    by, bh = PG["COVER_BOX_Y"], PG["COVER_BOX_H"]
    d.box(PRO_ML, by, PRO_TW, bh)
    ty = by + bh - 17.9
    d.text(PRO_ML + 13, ty, bg_label.upper(), MONO, 7.9, INK, tracking=0.8)
    ty -= 14.9
    for ln in d.wrap(bg_text, INTER, 9.6, PRO_TW - 26):
        d.text(PRO_ML + 13, ty, ln, INTER, 9.6, BODY_P)
        ty -= 13.0

def proposal_section(d, y, number, title, serif_sub=None):
    """Mono section header. number is a two digit string. Returns next y.

    The title shrinks if it would cross the right margin. Prefer a shorter
    title over a shrunk one: the header size carries the hierarchy.
    """
    d.text(PRO_ML, y, "/ %s" % number, MONO, 13.5, INK, tracking=0.5)
    avail = PW - PRO_MR - PG["SECTION_TITLE_X"]
    size = 13.5
    while size > 9.5 and d.width(title.upper(), MONO, size, 0.5) > avail:
        size -= 0.25
    d.text(PG["SECTION_TITLE_X"], y, title.upper(), MONO, size, INK, tracking=0.5)
    y -= PG["SUBHEAD_DY"]
    if serif_sub:
        d.text(PG["SUBHEAD_X"], y, serif_sub, NEWS, PG["SUBHEAD_SIZE"], ITALIC)
        y -= 14.0
    return y - 5.5

def proposal_bullet(d, y, text):
    """Mono slash marker, Inter body. Returns next y."""
    d.text(PG["BULLET_MARK_X"], y + PG["BULLET_MARK_DY"], "/", MONO, 6.6, INK)
    for ln in d.wrap(text, INTER, 9.3, PW - PRO_MR - PG["BULLET_TEXT_X"]):
        d.text(PG["BULLET_TEXT_X"], y, ln, INTER, 9.3, ITALIC)
        y -= PG["BULLET_LEAD"]
    return y - PG["BULLET_GAP"]

def proposal_stats(d, y, stats):
    """Two or three cells across, each with a 2pt black cap rule.
    stats = [(value, label, sublabel), ...]. Returns next y."""
    n = len(stats); gap = PG["STAT_GAP"]
    cw = (PRO_TW - 3 - gap * (n - 1)) / n
    h = PG["STAT_H"]; by = y - h
    for i, (val, lbl, sub) in enumerate(stats):
        x = PRO_ML + i * (cw + gap)
        d.fill(x, by, cw, h, BOXFILL)
        d.c.setStrokeColor(INK); d.c.setLineWidth(2.0)
        d.c.line(x, y, x + cw, y)
        d.text(x + 9, y - PG["STAT_NUM_DY"], val, NEWS, 21.8, INK)
        d.text(x + 9, by + PG["STAT_LBL_DY"], lbl.upper(), MONO, 7.4, INK, tracking=0.6)
        d.text(x + 9, by + PG["STAT_SUB_DY"], sub, MONO, 7.0, MUTED_P)
    return by - 26

def proposal_callout(d, y, label, text):
    """Bordered fill box. Returns next y."""
    lines = d.wrap(text, INTER, 9.3, PRO_TW - 26)
    h = 18 + 15 + len(lines) * 13.0 + 10
    d.box(PRO_ML, y - h, PRO_TW, h)
    ty = y - 18
    d.text(PRO_ML + 13, ty, label.upper(), MONO, 7.4, INK, tracking=0.8)
    ty -= 15
    for ln in lines:
        d.text(PRO_ML + 13, ty, ln, INTER, 9.3, BODY_P)
        ty -= 13.0
    return y - h - 20

def proposal_body_page(d, running_title):
    """Start a fresh body page. Returns the first content y."""
    d.new_page()
    proposal_chrome(d, running_title)
    return PG["SECTION_Y"]
