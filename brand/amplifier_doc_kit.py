# -*- coding: utf-8 -*-
"""Amplifier Health document kit.

A thin layer over ReportLab that renders a page in a named Amplifier palette.
Defaults to AMPLIFIER-DESIGN-PALETTE. Pass AMPLIFIER-DARK-PALETTE only when the
destination is a screen and the dark cut was asked for by name.

    from amplifier_doc_kit import AmplifierDoc

    d = AmplifierDoc("out.pdf", title="Token Run Rate")
    d.new_page(1, 5)
    d.eyebrow("GROWTH SINCE LAUNCH  ·  SEPTEMBER 2026")
    d.hero("36x in sixteen weeks.")
    y = d.para(d.ML, 604, [("Amplifier went live on ", "r"), ("15 May 2026", "b")])
    d.end_page(); d.save()

Styles inside para(): r body, b emphasis, c accent, e secondary accent.
"""
import os, re
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

from amplifier_palettes import get as get_palette, DEFAULT

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

FONT_FILES = [
    ("Corm-L",  "CormorantGaramond-300.ttf"),
    ("Corm",    "CormorantGaramond-400.ttf"),
    ("Corm-SB", "CormorantGaramond-600.ttf"),
    ("News-I",  "Newsreader-italic-400.ttf"),
    ("News-MI", "Newsreader-italic-500.ttf"),
    ("Sans",    "Inter-400.ttf"),
    ("Sans-M",  "Inter-500.ttf"),
    ("Sans-SB", "Inter-600.ttf"),
    ("Sans-B",  "Inter-700.ttf"),
    ("Mono",    "JetBrainsMono-400.ttf"),
    ("Mono-M",  "JetBrainsMono-500.ttf"),
    ("Mono-B",  "JetBrainsMono-700.ttf"),
]

_registered = False

def register_fonts(font_dir=None):
    """Register the four brand faces. Run fetch_fonts.py first if missing."""
    global _registered
    if _registered:
        return
    fd = font_dir or FONT_DIR
    missing = [fn for _, fn in FONT_FILES if not os.path.exists(os.path.join(fd, fn))]
    if missing:
        raise IOError("missing brand fonts in %s: %s\nrun: python3 %s"
                      % (fd, ", ".join(missing), os.path.join(HERE, "fetch_fonts.py")))
    for name, fn in FONT_FILES:
        pdfmetrics.registerFont(TTFont(name, os.path.join(fd, fn)))
    _registered = True


class AmplifierDoc(object):
    PW, PH = 612.0, 792.0
    ML = MR = 52.0

    def __init__(self, path, palette=None, title=None, author="Amplifier Health",
                 subject=None, font_dir=None, logo=None,
                 confidential="CONFIDENTIAL  ·  FOR AUTHORIZED USE ONLY",
                 footer="AMPLIFIER HEALTH  ·  CONFIDENTIAL  ·  AMPLIFIERHEALTH.COM"):
        register_fonts(font_dir)
        self.P = get_palette(palette)
        self.dark = self.P["name"] == "AMPLIFIER-DARK-PALETTE"
        self.TW = self.PW - self.ML - self.MR
        self.R = self.PW - self.MR
        self.confidential = confidential
        self.footer_text = footer

        self.BG    = HexColor(self.P["bg"])
        self.SURF  = HexColor(self.P["surface"])
        self.SURF2 = HexColor(self.P["surface_2"])
        self.PANEL = HexColor(self.P["panel"])
        self.TX    = HexColor(self.P["ink"])
        self.BODY  = HexColor(self.P["ink_2"])
        self.MUT   = HexColor(self.P["muted"])
        self.AC    = HexColor(self.P["accent"])
        self.AC2   = HexColor(self.P["accent_2"])
        self.LINE  = self.PANEL if self.dark else self.SURF2
        self.POS   = self.AC2 if self.dark else self.AC
        self.NEG   = HexColor("#f87171") if self.dark else self.BODY

        self.DISPLAY = "Corm-SB" if self.dark else "Corm-L"
        self.QUOTE   = "Corm-SB" if self.dark else "News-I"

        default_logo = "logo_light.png" if self.dark else "logo_green.png"
        lp = logo or os.path.join(HERE, "assets", default_logo)
        self.logo = ImageReader(lp) if os.path.exists(lp) else None

        self.c = canvas.Canvas(path, pagesize=(self.PW, self.PH))
        if title:
            self.c.setTitle(title)
        self.c.setAuthor(author)
        if subject:
            self.c.setSubject(subject)

    # ------------------------------------------------------------ primitives
    def draw(self, x, y, text, font, size, color):
        self.c.setFont(font, size); self.c.setFillColor(color)
        self.c.drawString(x, y, text)

    def draw_right(self, x, y, text, font, size, color):
        self.c.setFont(font, size); self.c.setFillColor(color)
        self.c.drawRightString(x, y, text)

    def tracked(self, x, y, text, font, size, color, track=1.1):
        """Letter spaced microtype, the mono voice of the system."""
        c = self.c
        c.setFont(font, size); c.setFillColor(color)
        for ch in text:
            c.drawString(x, y, ch)
            x += c.stringWidth(ch, font, size) + track
        return x

    def tracked_w(self, text, font, size, track=1.1):
        return sum(self.c.stringWidth(ch, font, size) + track for ch in text) - track

    def rule(self, y, color=None, w=0.5, x0=None, x1=None):
        self.c.setStrokeColor(color or self.LINE); self.c.setLineWidth(w)
        self.c.line(x0 if x0 is not None else self.ML, y,
                    x1 if x1 is not None else self.R, y)

    def rect(self, x, y, w, h, color):
        self.c.setFillColor(color); self.c.rect(x, y, w, h, stroke=0, fill=1)

    def wrap_plain(self, text, font, size, max_w):
        out, line = [], ""
        for word in text.split():
            t = (line + " " + word).strip()
            if self.c.stringWidth(t, font, size) <= max_w:
                line = t
            else:
                if line:
                    out.append(line)
                line = word
        if line:
            out.append(line)
        return out

    # ------------------------------------------------------------ page shell
    def new_page(self, page_no, total):
        c = self.c
        self.rect(0, 0, self.PW, self.PH, self.BG)
        if self.dark:
            c.saveState(); c.setStrokeColor(HexColor("#ffffff")); c.setStrokeAlpha(0.035)
            c.setLineWidth(0.3)
            for i in range(9):
                x = self.ML + i * (self.TW / 8.0); c.line(x, 58, x, 736)
            yy = 58.0
            while yy <= 736:
                c.line(self.ML, yy, self.R, yy); yy += 67.8
            c.restoreState()
        if self.logo:
            c.drawImage(self.logo, self.ML, 719.0, width=80,
                        height=80 * 191 / 700.0, mask="auto")
        lbl = self.confidential
        self.tracked(self.R - self.tracked_w(lbl, "Mono-M", 6.2, 0.9), 725.0,
                     lbl, "Mono-M", 6.2, self.MUT, 0.9)
        self.rule(708.0)
        self.rect(self.ML, 707.6, 34, 0.9, self.AC)
        self.rule(52.0)
        self.tracked(self.ML, 40.0, self.footer_text, "Mono-M", 6.0, self.MUT, 0.85)
        pg = "%02d / %02d" % (page_no, total)
        self.tracked(self.R - self.tracked_w(pg, "Mono-B", 6.4, 0.9), 40.0,
                     pg, "Mono-B", 6.4, self.AC, 0.9)
        return 690.0

    def end_page(self):
        self.c.showPage()

    def save(self):
        self.c.save()

    # ------------------------------------------------------------ components
    def eyebrow(self, text, y=686):
        self.tracked(self.ML, y, text, "Mono-B", 6.6, self.AC, 1.4)
        return y - 20

    def hero(self, text, y=636, size=None):
        """Display line. In the design palette a wash block sits behind it."""
        size = size or (47 if self.dark else 44)
        if not self.dark:
            w = self.c.stringWidth(text, self.DISPLAY, size)
            self.rect(self.ML - 8, y - 13, w + 26, size * 0.93, self.SURF)
        self.draw(self.ML, y, text, self.DISPLAY, size, self.TX)
        return y - size * 0.62

    def _style(self, st):
        return {"r": ("Sans", self.BODY), "b": ("Sans-SB", self.TX),
                "c": ("Sans-SB", self.AC),
                "e": ("Sans-SB", self.AC2 if self.dark else self.AC)}[st]

    @staticmethod
    def _tokenize(segs):
        words, cur = [], []
        for text, st in segs:
            for part in re.split(r"(\s+)", text):
                if not part:
                    continue
                if part.isspace():
                    if cur:
                        words.append(cur); cur = []
                else:
                    cur.append((part, st))
        if cur:
            words.append(cur)
        return words

    def para(self, x, y, segs, size=9.6, leading=14.2, max_w=None):
        """Styled paragraph. segs = [(text, style)], style in r / b / c / e."""
        c = self.c
        max_w = max_w or self.TW
        words = self._tokenize(segs)
        sp = c.stringWidth(" ", "Sans", size)

        def wword(word):
            return sum(c.stringWidth(t, self._style(st)[0], size) for t, st in word)

        def flush(ln, yy):
            cx = x
            for k, word in enumerate(ln):
                if k:
                    cx += sp
                for t, st in word:
                    f, col = self._style(st)
                    c.setFont(f, size); c.setFillColor(col)
                    c.drawString(cx, yy, t); cx += c.stringWidth(t, f, size)
            return yy - leading

        line, line_w = [], 0.0
        for word in words:
            ww = wword(word)
            add = ww if not line else ww + sp
            if line and line_w + add > max_w:
                y = flush(line, y); line, line_w = [word], ww
            else:
                line.append(word); line_w += add
        if line:
            y = flush(line, y)
        return y

    def section_head(self, y, num, name):
        self.rule(y + 15)
        self.tracked(self.ML, y, num, "Mono-B", 9.0, self.AC, 1.0)
        self.tracked(self.ML + 26, y, "·", "Mono-B", 9.0, self.MUT, 1.0)
        if self.dark:
            self.tracked(self.ML + 40, y, name.upper(), "Sans-SB", 9.4, self.TX, 1.6)
        else:
            self.tracked(self.ML + 40, y, name.upper(), "Mono-B", 8.6, self.AC, 1.6)
        return y - 20

    def stat_cells(self, y, stats, h=64):
        """stats = [(number, suffix, label_line_1, label_line_2)]"""
        n = len(stats); gap = 9.0
        cw = (self.TW - gap * (n - 1)) / n
        for i, (num, suffix, l1, l2) in enumerate(stats):
            x = self.ML + i * (cw + gap)
            self.rect(x, y - h, cw, h, self.SURF)
            self.rect(x, y - 1.4, cw, 1.4, self.AC)
            ny = y - 12 - 25 * 0.72
            self.draw(x + 11, ny, num, self.DISPLAY, 25, self.TX)
            nw = self.c.stringWidth(num, self.DISPLAY, 25)
            if suffix:
                self.draw(x + 11 + nw + 2.5, ny, suffix, "Mono-M", 9.2, self.AC)
            self.tracked(x + 11, y - h + 20, l1, "Mono-M", 5.5, self.MUT, 0.7)
            if l2:
                self.tracked(x + 11, y - h + 11, l2, "Mono-M", 5.5, self.MUT, 0.7)
        return y - h

    def pullquote(self, label, text, y_bottom=72.0):
        """Serif statement anchored above the footer. Gives a page its landing."""
        size = 16.5 if self.dark else 16.0
        lines = self.wrap_plain(text, self.QUOTE, size, self.TW - 44)
        h = 24 + len(lines) * 20.5 + 14
        y_top = y_bottom + h
        self.rect(self.ML, y_top - h, self.TW, h, self.SURF)
        self.rect(self.ML, y_top - h, 1.6, h, self.AC)
        self.tracked(self.ML + 22, y_top - 16, label.upper(), "Mono-B", 5.8, self.AC, 1.0)
        ty = y_top - 36
        for ln in lines:
            self.draw(self.ML + 22, ty, ln, self.QUOTE, size, self.TX); ty -= 20.5
        return y_top - h

    def table_header(self, y, cols):
        """cols = [(label, x, align)] with align in l / r"""
        for lbl, x, al in cols:
            if al == "l":
                self.tracked(x, y, lbl, "Mono-M", 5.6, self.MUT, 0.9)
            else:
                self.tracked(x - self.tracked_w(lbl, "Mono-M", 5.6, 0.9), y,
                             lbl, "Mono-M", 5.6, self.MUT, 0.9)
        self.rule(y - 7, self.AC, 0.8)
        return y - 7

    def table_row(self, y, h, cells, shade=False):
        """cells = [(text, x, align, font, size, color)]"""
        if shade:
            self.rect(self.ML, y - h, self.TW, h, self.SURF)
        ty = y - h + (h - 7.4) / 2.0 + 0.6
        for text, x, al, font, size, color in cells:
            if al == "l":
                self.draw(x, ty, text, font, size, color)
            else:
                self.draw_right(x, ty, text, font, size, color)
        return y - h

    def image_panel(self, y_top, path, aspect_w=7.0, aspect_h=3.0):
        """Full width chart or image with the accent keyline on top."""
        ih = self.TW * aspect_h / aspect_w
        self.c.drawImage(ImageReader(path), self.ML, y_top - ih,
                         width=self.TW, height=ih, mask=None)
        self.rect(self.ML, y_top - 0.9, self.TW, 0.9, self.AC)
        return y_top - ih

    def strip(self, y, label, pairs, h=34):
        """Wash strip: a mono label and number / unit pairs. Good page closer."""
        self.rect(self.ML, y - h, self.TW, h, self.SURF)
        self.tracked(self.ML + 14, y - 14, label.upper(), "Mono-B", 5.8, self.AC, 1.0)
        cx = self.ML + 14
        for num, unit in pairs:
            self.draw(cx, y - 26, num, "Mono-B", 9.0, self.TX)
            cx += self.c.stringWidth(num, "Mono-B", 9.0) + 5
            self.draw(cx, y - 26, unit, "Sans", 8.6, self.BODY)
            cx += self.c.stringWidth(unit, "Sans", 8.6) + 26
        return y - h
