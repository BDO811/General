# -*- coding: utf-8 -*-
"""Token run rate charts, rendered in a named Amplifier palette.

    python3 token_run_rate_charts.py [PALETTE]

Defaults to AMPLIFIER-DESIGN-PALETTE.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import os, sys

D    = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(D)
sys.path.insert(0, BRAND)
from amplifier_palettes import get as get_palette

for f in os.listdir(os.path.join(BRAND, "fonts")):
    fm.fontManager.addfont(os.path.join(BRAND, "fonts", f))

MONO = "JetBrains Mono"

WEEKS = [
 ("May 15",  4688,   4688),   ("May 22", 15625,  20313),
 ("May 29",  26563,  46876),  ("Jun 5",  37500,  84376),
 ("Jun 12",  48438,  132814), ("Jun 19", 59375,  192189),
 ("Jun 26",  70313,  262502), ("Jul 3",  81251,  343753),
 ("Jul 10",  92188,  435941), ("Jul 17", 103126, 539067),
 ("Jul 24",  114063, 653130), ("Jul 31", 125001, 778131),
 ("Aug 7",   135938, 914069), ("Aug 14", 146876, 1060945),
 ("Aug 21",  157814, 1218759),("Aug 28", 168751, 1387510),
 ("Sep 4",   127233, 1514743),
]

MONTHS = [
 ("SEP",  776790,        0,        0), ("OCT",  802683,   957037,        0),
 ("NOV",  776790,  6650000,        0), ("DEC",  802683, 13525185,        0),
 ("JAN",  802683, 19084444,  7750000), ("FEB",  725004, 17733333, 20766667),
 ("MAR",  802683, 19633333, 38233333), ("APR",  776790, 19000000, 45000000),
 ("MAY",  802683, 19633333, 46500000), ("JUN",  776790, 19000000, 45000000),
]

def theme(pal_name):
    p = get_palette(pal_name)
    dark = p["name"] == "AMPLIFIER-DARK-PALETTE"
    return {
        "panel":  p["surface"],
        "grid":   p["panel"] if dark else p["surface_2"],
        "ink":    p["ink"],
        "muted":  p["muted"],
        "bars":   p["accent"],
        "line":   p["accent_2"] if dark else p["ink"],
        "s_plat": p["ink"] if dark else p["muted"],
        "s_glow": p["accent_2"] if dark else p["accent_2"],
        "s_brk":  p["accent_2"] if dark else p["accent"],
        "s_glow_dark": p["accent"],
    }

def _style(ax, t):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=t["muted"], length=0, labelsize=6.2)
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontname(MONO)

def chart_weekly(path, pal_name):
    t = theme(pal_name)
    labels = [w[0] for w in WEEKS]; vals = [w[1] for w in WEEKS]; cum = [w[2] for w in WEEKS]
    x = range(len(WEEKS))

    fig, ax = plt.subplots(figsize=(7.0, 3.02), dpi=300)
    fig.patch.set_facecolor(t["panel"]); ax.set_facecolor(t["panel"])

    bars = ax.bar(x, vals, width=0.62, color=t["bars"], zorder=3)
    bars[16].set_alpha(0.34); bars[16].set_edgecolor(t["bars"]); bars[16].set_linewidth(0.7)

    ax.set_ylim(0, 200000)
    ax.set_yticks([0, 60000, 120000, 180000])
    ax.set_yticklabels(["0", "60k", "120k", "180k"])
    ax.yaxis.grid(True, color=t["grid"], linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    for i, lb in enumerate(ax.get_xticklabels()):
        if i % 3 != 0:
            lb.set_visible(False)
    _style(ax, t)

    ax2 = ax.twinx(); ax2.set_facecolor("none")
    ax2.plot(x, cum, color=t["line"], linewidth=1.4, zorder=5)
    ax2.scatter([16], [cum[16]], s=13, color=t["line"], zorder=6)
    ax2.set_ylim(0, 1800000)
    ax2.set_yticks([0, 600000, 1200000, 1800000])
    ax2.set_yticklabels(["0", "0.6M", "1.2M", "1.8M"])
    _style(ax2, t)

    ax.annotate("4,688", (0, vals[0]), textcoords="offset points", xytext=(0, 6),
                ha="center", color=t["muted"], fontname=MONO, fontsize=6.0, zorder=7)
    ax.annotate("168,751", (15, vals[15]), textcoords="offset points", xytext=(0, 7),
                ha="center", color=t["ink"], fontname=MONO, fontsize=6.6,
                fontweight="bold", zorder=7)
    ax.annotate("5 DAY\nSTUB", (16, vals[16]), textcoords="offset points", xytext=(0, 6),
                ha="center", va="bottom", color=t["muted"], fontname=MONO, fontsize=5.4,
                linespacing=1.3, zorder=7)

    leg = ax.legend(handles=[Patch(facecolor=t["bars"], label="TOKENS CONSUMED THAT WEEK"),
                             Line2D([0], [0], color=t["line"], lw=1.4,
                                    label="CUMULATIVE TOKENS CONSUMED")],
                    loc="upper left", bbox_to_anchor=(0.005, 0.90), frameon=False,
                    fontsize=6.0, handlelength=1.6, borderpad=0.1, labelspacing=0.45)
    for tx in leg.get_texts():
        tx.set_color(t["muted"]); tx.set_fontname(MONO)

    fig.subplots_adjust(left=0.062, right=0.925, top=0.94, bottom=0.115)
    fig.savefig(path, facecolor=t["panel"]); plt.close(fig)

def chart_projection(path, pal_name):
    t = theme(pal_name)
    labels = [m[0] for m in MONTHS]
    plat = [m[1] for m in MONTHS]; glow = [m[2] for m in MONTHS]; brk = [m[3] for m in MONTHS]
    x = range(len(MONTHS))

    fig, ax = plt.subplots(figsize=(7.0, 2.78), dpi=300)
    fig.patch.set_facecolor(t["panel"]); ax.set_facecolor(t["panel"])

    ax.bar(x, plat, width=0.60, color=t["s_plat"], zorder=3, label="PLATFORM")
    ax.bar(x, glow, width=0.60, bottom=plat, color=t["s_glow"], zorder=3, label="GLOW")
    ax.bar(x, brk, width=0.60, bottom=[p + g for p, g in zip(plat, glow)],
           color=t["s_brk"], zorder=3, label="BRECKA")

    ax.set_ylim(0, 74000000)
    ax.set_yticks([0, 24000000, 48000000, 72000000])
    ax.set_yticklabels(["0", "24M", "48M", "72M"])
    ax.yaxis.grid(True, color=t["grid"], linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    _style(ax, t)

    ax.annotate("0.78M", (0, plat[0]), textcoords="offset points", xytext=(0, 6),
                ha="center", color=t["muted"], fontname=MONO, fontsize=6.0, zorder=7)
    tot8 = plat[8] + glow[8] + brk[8]
    ax.annotate("66.9M", (8, tot8), textcoords="offset points", xytext=(0, 7),
                ha="center", color=t["ink"], fontname=MONO, fontsize=6.6,
                fontweight="bold", zorder=7)

    leg = ax.legend(loc="upper left", bbox_to_anchor=(0.005, 0.93), frameon=False,
                    fontsize=6.0, ncol=1, handlelength=1.3, borderpad=0.1, labelspacing=0.42)
    for tx in leg.get_texts():
        tx.set_color(t["muted"]); tx.set_fontname(MONO)

    fig.text(0.5, 0.012, "PROJECTED MONTHLY TOKENS  ·  SEP 2026 TO JUN 2027",
             ha="center", color=t["muted"], fontname=MONO, fontsize=5.6)
    fig.subplots_adjust(left=0.068, right=0.985, top=0.94, bottom=0.135)
    fig.savefig(path, facecolor=t["panel"]); plt.close(fig)

if __name__ == "__main__":
    pal = sys.argv[1] if len(sys.argv) > 1 else "AMPLIFIER-DESIGN-PALETTE"
    tag = "design" if "DESIGN" in pal.upper() else "dark"
    chart_weekly(os.path.join(D, "chart_weekly_%s.png" % tag), pal)
    chart_projection(os.path.join(D, "chart_projection_%s.png" % tag), pal)
    print("charts done:", tag)
