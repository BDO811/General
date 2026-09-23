# -*- coding: utf-8 -*-
"""Sona-2 performance charts in a named Amplifier palette.

    python3 sona2_charts.py [PALETTE]
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import os, sys

D = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(D)
sys.path.insert(0, BRAND)
from amplifier_palettes import get as get_palette

for f in os.listdir(os.path.join(BRAND, "fonts")):
    fm.fontManager.addfont(os.path.join(BRAND, "fonts", f))

MONO = "JetBrains Mono"

FLAGSHIP = [
    ("Traumatic brain injury",     0.962),
    ("COPD",                       0.944),
    ("Dehydration",                0.942),
    ("Acute stress, nervousness",  0.910),
    ("PTSD",                       0.907),
    ("Anxiety (GAD)",              0.884),
    ("Depression (MDD)",           0.874),
    ("Overweight and obesity",     0.871),
    ("Sleep disorders",            0.823),
    ("Cognitive impairment",       0.777),
]


def chart_auc(path, pal_name):
    p = get_palette(pal_name)
    dark = p["name"] == "AMPLIFIER-DARK-PALETTE"
    panel = p["surface"]
    grid = p["panel"] if dark else p["surface_2"]
    ink, muted, bars, mark = p["ink"], p["muted"], p["accent"], p["accent_2"]

    names = [n for n, _ in FLAGSHIP][::-1]
    vals = [v for _, v in FLAGSHIP][::-1]
    ypos = range(len(names))

    fig, ax = plt.subplots(figsize=(7.0, 2.95), dpi=300)
    fig.patch.set_facecolor(panel); ax.set_facecolor(panel)

    ax.barh(ypos, vals, height=0.6, color=bars, zorder=3)
    ax.axvline(0.69, color=mark, linewidth=1.0, zorder=4)
    ax.text(0.693, len(names) - 0.35, "0.69 MINIMUM BAR", color=mark,
            fontname=MONO, fontsize=5.6, va="center")

    ax.set_xlim(0.5, 1.0)
    ax.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_xticklabels(["0.50", "0.60", "0.70", "0.80", "0.90", "1.00"])
    ax.set_yticks(list(ypos)); ax.set_yticklabels(names)
    ax.xaxis.grid(True, color=grid, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=muted, length=0, labelsize=6.4)
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontname(MONO)

    for y, v in zip(ypos, vals):
        ax.text(v + 0.006, y, "%.3f" % v, va="center", color=ink,
                fontname=MONO, fontsize=6.2, fontweight="bold", zorder=5)

    fig.text(0.5, 0.015, "IN DOMAIN HELD OUT AUC  ·  TEN FLAGSHIP CONDITIONS  ·  "
                         "PRODUCTION v0.2.0",
             ha="center", color=muted, fontname=MONO, fontsize=5.6)
    fig.subplots_adjust(left=0.235, right=0.985, top=0.97, bottom=0.135)
    fig.savefig(path, facecolor=panel); plt.close(fig)


if __name__ == "__main__":
    pal = sys.argv[1] if len(sys.argv) > 1 else "AMPLIFIER-DESIGN-PALETTE"
    tag = "dark" if "DARK" in pal.upper() else "design"
    chart_auc(os.path.join(D, "chart_auc_%s.png" % tag), pal)
    print("charts done:", tag)
