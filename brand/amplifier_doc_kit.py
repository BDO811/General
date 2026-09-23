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

        self.backdrop_img = None
        self.backdrop_pages = None

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
    def set_backdrop(self, image_path, alpha=0.10, pages=None, band=None):
        """Topical imagery sitting behind the page at 10%.

        The image is composited against the page colour in advance rather than
        drawn with a transparency group, so it prints exactly as it screens and
        the PDF carries no alpha. pages limits it to specific page numbers;
        band is (y_bottom, y_top) in points, defaulting to the full text block.
        """
        from PIL import Image
        if not os.path.exists(image_path):
            raise IOError("backdrop not found: %s" % image_path)
        band = band or (58.0, 700.0)
        w_pt = self.TW
        h_pt = band[1] - band[0]
        px_w, px_h = int(w_pt * 3), int(h_pt * 3)

        im = Image.open(image_path).convert("RGB")
        scale = max(px_w / im.width, px_h / im.height)
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))),
                       Image.LANCZOS)
        left = (im.width - px_w) // 2
        top = (im.height - px_h) // 2
        im = im.crop((left, top, left + px_w, top + px_h))

        # feather to the page colour on every edge, so the imagery dissolves
        # into the sheet instead of sitting in a visible box
        bg = Image.new("RGB", im.size, self.P["bg"])
        blended = Image.blend(bg, im, alpha)
        fx, fy = max(1, int(px_w * 0.22)), max(1, int(px_h * 0.28))
        mask = Image.new("L", im.size, 255)
        mp = mask.load()
        for x in range(px_w):
            gx = min(1.0, x / fx, (px_w - 1 - x) / fx)
            for y in range(px_h):
                gy = min(1.0, y / fy, (px_h - 1 - y) / fy)
                g = gx * gy
                mp[x, y] = int(255 * (g * g * (3 - 2 * g)))
        im = Image.composite(blended, bg, mask)

        out = os.path.splitext(image_path)[0] + "_backdrop.png"
        im.save(out)
        self.backdrop_img = (ImageReader(out), self.ML, band[0], w_pt, h_pt)
        self.backdrop_pages = pages
        return out

    def new_page(self, page_no, total):
        c = self.c
        self.rect(0, 0, self.PW, self.PH, self.BG)
        if self.backdrop_img and (self.backdrop_pages is None
                                  or page_no in self.backdrop_pages):
            img, bx, by, bw, bh = self.backdrop_img
            c.drawImage(img, bx, by, width=bw, height=bh, mask=None)
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
    def cover(self, topic=None, date=None, url="try.amplifierhealth.com",
              wordmark="Amplifier Health", logo_width=212.0):
        """Brand cover. Centred: logo large, the company name, the document's
        topic under it in the accent, the try link at the foot. No page chrome,
        no page number."""
        c = self.c
        cx = self.PW / 2.0
        self.rect(0, 0, self.PW, self.PH, self.BG)
        if self.backdrop_img:
            img, bx, by, bw, bh = self.backdrop_img
            c.drawImage(img, bx, by, width=bw, height=bh, mask=None)

        if self.logo:
            lh = logo_width * 191 / 700.0
            c.drawImage(self.logo, cx - logo_width / 2.0, 516, width=logo_width,
                        height=lh, mask="auto")

        c.setFont(self.DISPLAY, 52); c.setFillColor(self.TX)
        c.drawCentredString(cx, 428, wordmark)

        if topic:
            size = 32
            while size > 18 and c.stringWidth(topic, self.DISPLAY, size) > self.TW - 40:
                size -= 1
            c.setFont(self.DISPLAY, size); c.setFillColor(self.AC)
            c.drawCentredString(cx, 428 - 40, topic)
            ry = 428 - 40 - 26
        else:
            ry = 428 - 30

        self.rect(cx - 26, ry, 52, 1.2, self.AC)

        if date:
            w = self.tracked_w(date.upper(), "Mono-B", 6.4, 1.4)
            self.tracked(cx - w / 2.0, ry - 22, date.upper(), "Mono-B", 6.4, self.MUT, 1.4)

        # the try link, set the way the deck sets it: the host in the accent
        head, tail = url.split("amplifier", 1)
        head = head + "amplifier"
        usize = 30
        wh = c.stringWidth(head, self.DISPLAY, usize)
        wt = c.stringWidth(tail, self.DISPLAY, usize)
        x0 = cx - (wh + wt) / 2.0
        lw = self.tracked_w("TRY IT YOURSELF", "Mono-B", 6.2, 1.4)
        self.rect(cx - lw / 2.0 - 22, 190.5, 14, 0.9, self.AC)
        self.tracked(cx - lw / 2.0, 188, "TRY IT YOURSELF", "Mono-B", 6.2, self.MUT, 1.4)
        self.draw(x0, 150, head, self.DISPLAY, usize, self.TX)
        self.draw(x0 + wh, 150, tail, self.DISPLAY, usize, self.AC)

        lab = self.confidential
        w = self.tracked_w(lab, "Mono-M", 6.0, 0.9)
        self.tracked(cx - w / 2.0, 96, lab, "Mono-M", 6.0, self.MUT, 0.9)
        return self

    def eyebrow(self, text, y=686):
        self.tracked(self.ML, y, text, "Mono-B", 6.6, self.AC, 1.4)
        return y - 20

    def hero(self, text, y=636, size=None):
        """Display line. Set on the open page, no block behind it."""
        size = size or (47 if self.dark else 44)
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
            avail = cw - 22
            lsize = 5.5
            while lsize > 4.2 and max(self.tracked_w(l1, "Mono-M", lsize, 0.7),
                                      self.tracked_w(l2 or "", "Mono-M", lsize, 0.7)) > avail:
                lsize -= 0.2
            self.tracked(x + 11, y - h + 20, l1, "Mono-M", lsize, self.MUT, 0.7)
            if l2:
                self.tracked(x + 11, y - h + 11, l2, "Mono-M", lsize, self.MUT, 0.7)
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

    # ------------------------------------------------- additional components
    def deck(self, x, y, text, size=15.0, max_w=None):
        """Italic deck line under a hero. The Newsreader voice."""
        lines = self.wrap_plain(text, "News-I" if not self.dark else "Corm-SB",
                                size, max_w or self.TW)
        f = "News-I" if not self.dark else "Corm-SB"
        for ln in lines:
            self.draw(x, y, ln, f, size, self.BODY if not self.dark else self.TX)
            y -= size * 1.28
        return y

    def h2(self, y, text, size=17.0):
        self.draw(self.ML, y, text, self.DISPLAY, size, self.TX)
        return y - size * 0.55

    def label(self, y, text, color=None):
        """Mono microtype label above a block."""
        self.tracked(self.ML, y, text.upper(), "Mono-B", 5.8, color or self.AC, 1.0)
        return y - 13

    def callout_dark(self, y, label, text, pad=13.0, size=8.8, leading=12.2,
                     y_bottom=None):
        """Inverted panel. The flyer uses this weight for code and for the one
        statement that must not be skimmed past."""
        bg = self.PANEL if not self.dark else self.SURF2
        body = HexColor("#e9e3d5") if not self.dark else self.TX
        lab = self.AC2 if not self.dark else self.AC
        lines = self.wrap_plain(text, "Sans", size, self.TW - pad * 2)
        h = pad + 9 + 7 + len(lines) * leading + pad - 6
        if y_bottom is not None:
            y = y_bottom + h
        self.rect(self.ML, y - h, self.TW, h, bg)
        self.tracked(self.ML + pad, y - pad - 4, label.upper(), "Mono-B", 5.8, lab, 1.0)
        ty = y - pad - 18
        for ln in lines:
            self.draw(self.ML + pad, ty, ln, "Sans", size, body); ty -= leading
        return y - h

    # rhythm constants for def_row, so every row in every document measures
    # the same: the keyline is a separator between rows, not a hat on a title
    RULE_ABOVE_TITLE = 18.0
    TITLE_TO_BODY = 15.0
    BODY_TO_NEXT_RULE = 14.0
    TITLE_LINE = 13.0

    def def_row(self, y, tag, title, body, right=None, right_color=None,
                tag_w=78.0, size=8.8, leading=11.8, gap=0.0, shade=False):
        """Definition row: mono tag at the left, title, optional right hand
        verdict, wrapped body under the title. y is the title baseline.
        The workhorse for criteria, lanes, tiers and numbered arguments."""
        x_body = self.ML + tag_w
        rw = (self.tracked_w(right, "Mono-B", 6.4, 1.0) + 16) if right else 0.0
        t_lines = self.wrap_plain(title, "Sans-SB", 10.4, self.R - x_body - rw) or [title]
        lines = self.wrap_plain(body, "Sans", size, self.R - x_body) if body else []
        t_extra = (len(t_lines) - 1) * self.TITLE_LINE
        if lines:
            consumed = (t_extra + self.TITLE_TO_BODY + (len(lines) - 1) * leading
                        + self.BODY_TO_NEXT_RULE + self.RULE_ABOVE_TITLE)
        else:
            consumed = t_extra + 12.0 + self.RULE_ABOVE_TITLE
        if shade:
            self.rect(self.ML, y + self.RULE_ABOVE_TITLE - consumed, self.TW,
                      consumed - 1, self.SURF)
        self.rule(y + self.RULE_ABOVE_TITLE)
        self.tracked(self.ML, y, tag.upper(), "Mono-B", 5.8, self.MUT, 0.9)
        ty = y
        for tl in t_lines:
            self.draw(x_body, ty, tl, "Sans-SB", 10.4, self.TX)
            ty -= self.TITLE_LINE
        if right:
            self.tracked(self.R - self.tracked_w(right, "Mono-B", 6.4, 1.0), y,
                         right, "Mono-B", 6.4, right_color or self.AC, 1.0)
        by = y - t_extra - self.TITLE_TO_BODY
        for ln in lines:
            self.draw(x_body, by, ln, "Sans", size, self.BODY)
            by -= leading
        return y - consumed - gap

    def rows_start(self, y, after="para"):
        """Where the first def_row title baseline goes, so its keyline keeps
        the same clearance from whatever sits above it."""
        return y - {"para": 21.0, "label": 19.0, "head": 24.0}[after]

    def bullet_list(self, y, items, size=8.8, leading=12.0, gap=7.0, indent=13.0):
        """Square marker in the accent. No dashes anywhere in this system."""
        for item in items:
            lines = self.wrap_plain(item, "Sans", size, self.TW - indent)
            self.rect(self.ML, y + 2.2, 3.0, 3.0, self.AC)
            for k, ln in enumerate(lines):
                self.draw(self.ML + indent, y, ln, "Sans", size, self.BODY)
                y -= leading
            y -= gap
        return y + gap

    def contents(self, y, rows, x_title=None, x_desc=None):
        """rows = [(number, title, description)]"""
        x_title = x_title or self.ML + 34
        x_desc = x_desc or self.ML + 190
        for num, title, desc in rows:
            self.rule(y + 12)
            self.tracked(self.ML, y, num, "Mono-B", 7.6, self.AC, 1.0)
            self.draw(x_title, y, title, "Sans-SB", 9.4, self.TX)
            self.draw(x_desc, y, desc, "Sans", 8.6, self.BODY)
            y -= 21
        self.rule(y + 12)
        return y

    def fine_print(self, y, text, size=6.4, leading=9.0):
        lines = self.wrap_plain(text, "Sans", size, self.TW)
        for ln in lines:
            self.draw(self.ML, y, ln, "Sans", size, self.MUT); y -= leading
        return y

    def two_col_list(self, y, left_head, left_items, right_head, right_items,
                     size=8.4, leading=13.2):
        """Two lists side by side under mono heads. Used for claim language."""
        mid = self.ML + self.TW / 2.0 + 6
        col_w = self.TW / 2.0 - 12
        self.tracked(self.ML, y, left_head.upper(), "Mono-B", 5.8, self.AC, 1.0)
        self.tracked(mid, y, right_head.upper(), "Mono-B", 5.8, self.AC2 if not self.dark
                     else self.AC2, 1.0)
        self.rule(y - 7)
        ly = ry = y - 20
        for item in left_items:
            for ln in self.wrap_plain(item, "Sans", size, col_w - 13):
                self.draw(self.ML + 13, ly, ln, "Sans", size, self.BODY); ly -= leading
            self.rect(self.ML, ly + leading + 2.2, 3.0, 3.0, self.AC)
        for item in right_items:
            for ln in self.wrap_plain(item, "Sans", size, col_w - 13):
                self.draw(mid + 13, ry, ln, "Sans", size, self.BODY); ry -= leading
            self.rect(mid, ry + leading + 2.2, 3.0, 3.0, self.AC2)
        return min(ly, ry)
