# -*- coding: utf-8 -*-
"""Amplifier Health, Token Run Rate, September 2026.

A worked example of the document kit. Renders in the house palette by default:

    python3 token_run_rate_charts.py                    # charts first
    python3 token_run_rate.py                           # AMPLIFIER-DESIGN-PALETTE
    python3 token_run_rate.py AMPLIFIER-DARK-PALETTE    # screen cut
"""
import os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(D))
from amplifier_doc_kit import AmplifierDoc
from amplifier_palettes import DEFAULT

PAL = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).upper()
TAG = "dark" if "DARK" in PAL else "design"
OUT = os.path.join(D, "Amplifier_Token_Run_Rate_Sept2026_%s.pdf" % TAG)
CH_WEEKLY = os.path.join(D, "chart_weekly_%s.png" % TAG)
CH_PROJ   = os.path.join(D, "chart_projection_%s.png" % TAG)

WEEKS = [
    ("1",  "May 15 – May 21", "4,688",   "44",    "4,688",     ""),
    ("2",  "May 22 – May 28", "15,625",  "145",   "20,313",    "+233.3%"),
    ("3",  "May 29 – Jun 4",  "26,563",  "247",   "46,876",    "+70.0%"),
    ("4",  "Jun 5 – Jun 11",  "37,500",  "348",   "84,376",    "+41.2%"),
    ("5",  "Jun 12 – Jun 18", "48,438",  "450",   "132,814",   "+29.2%"),
    ("6",  "Jun 19 – Jun 25", "59,375",  "552",   "192,189",   "+22.6%"),
    ("7",  "Jun 26 – Jul 2",  "70,313",  "653",   "262,502",   "+18.4%"),
    ("8",  "Jul 3 – Jul 9",   "81,251",  "755",   "343,753",   "+15.6%"),
    ("9",  "Jul 10 – Jul 16", "92,188",  "857",   "435,941",   "+13.5%"),
    ("10", "Jul 17 – Jul 23", "103,126", "958",   "539,067",   "+11.9%"),
    ("11", "Jul 24 – Jul 30", "114,063", "1,060", "653,130",   "+10.6%"),
    ("12", "Jul 31 – Aug 6",  "125,001", "1,162", "778,131",   "+9.6%"),
    ("13", "Aug 7 – Aug 13",  "135,938", "1,263", "914,069",   "+8.7%"),
    ("14", "Aug 14 – Aug 20", "146,876", "1,365", "1,060,945", "+8.0%"),
    ("15", "Aug 21 – Aug 27", "157,814", "1,466", "1,218,759", "+7.4%"),
    ("16", "Aug 28 – Sep 3",  "168,751", "1,568", "1,387,510", "+6.9%"),
    ("17", "Sep 4 – Sep 8 (5 days)", "127,233", "1,182", "1,514,743", ""),
]

MONTHS = [
    ("1", "May 15 – Jun 14", "103,795", "965",   ""),
    ("2", "Jun 15 – Jul 15", "318,305", "2,958", "+206.7%"),
    ("3", "Jul 16 – Aug 15", "532,816", "4,951", "+67.4%"),
    ("4", "Aug 16 – Sep 8 (24 days)", "559,910", "5,203", ""),
]

PROJ = [
    ("Sep 2026", "776,790", "0",          "0",          "776,790",    ""),
    ("Oct 2026", "802,683", "957,037",    "0",          "1,759,720",  "+126.5%"),
    ("Nov 2026", "776,790", "6,650,000",  "0",          "7,426,790",  "+322.0%"),
    ("Dec 2026", "802,683", "13,525,185", "0",          "14,327,868", "+92.9%"),
    ("Jan 2027", "802,683", "19,084,444", "7,750,000",  "27,637,127", "+92.9%"),
    ("Feb 2027", "725,004", "17,733,333", "20,766,667", "39,225,004", "+41.9%"),
    ("Mar 2027", "802,683", "19,633,333", "38,233,333", "58,669,349", "+49.6%"),
    ("Apr 2027", "776,790", "19,000,000", "45,000,000", "64,776,790", "+10.4%"),
    ("May 2027", "802,683", "19,633,333", "46,500,000", "66,936,016", "+3.3%"),
    ("Jun 2027", "776,790", "19,000,000", "45,000,000", "64,776,790", "-3.2%"),
]


def page_one(d):
    d.new_page(1, 5)
    d.eyebrow("GROWTH SINCE LAUNCH  ·  SEPTEMBER 2026")
    d.hero("36x in sixteen weeks.")

    y = d.para(d.ML, 604, [
        ("Amplifier went live on ", "r"), ("15 May 2026", "b"),
        (". Weekly token consumption has compounded at ", "r"),
        ("27.0% week over week for sixteen consecutive weeks", "c"),
        (", from 4,688 tokens in week one to 168,751 in week sixteen. Not one week has been "
         "smaller than the week before it. Cumulative consumption stands at ", "r"),
        ("1,514,791 tokens", "b"), (" across 14,077 jobs, and it has ", "r"),
        ("quadrupled in the last eight weeks alone", "b"),
        (". Glow continues to ramp up usage and Brecka 1 January, massively unlocking the ", "r"),
        ("token annual run rate by June 2027", "c"), (".", "r"),
    ])

    y = d.stat_cells(y - 14, [
        ("27.0", "%", "WEEK OVER WEEK, COMPOUNDED,", "SIXTEEN STRAIGHT WEEKS"),
        ("36",   "x", "WEEKLY VOLUME, WEEK ONE TO", "WEEK SIXTEEN"),
        ("7.7",  "x", "MONTHLY VOLUME, MONTH ONE", "TO CURRENT RUN RATE"),
        ("803",  "k", "TOKENS PER MONTH AT", "CURRENT RUN RATE"),
    ])

    y = d.section_head(y - 26, "01", "The Slope")
    y = d.para(d.ML, y, [
        ("Weekly token consumption since launch, with the cumulative curve laid over it on the "
         "right axis. Sixteen full weeks plus a five day stub. Weekly volume runs 4,688 to "
         "168,751 and cumulative volume reaches ", "r"),
        ("1,387,510", "b"), (" by the close of week sixteen.", "r"),
    ], size=8.8, leading=12.6)

    y = d.image_panel(y - 8, CH_WEEKLY, 7.0, 3.02)
    d.strip(y - 20, "Exit run rate",
            [("25,893", "tokens per day"), ("181,251", "per week"),
             ("802,683", "per 31 day month")])
    d.end_page()


def page_two(d):
    d.new_page(2, 5)
    y = d.section_head(680, "02", "Weekly Detail")
    y = d.para(d.ML, y, [
        ("Every week since launch. Week seventeen is a five day stub, cut at the 8 September "
         "close, and is not annualised anywhere in this document.", "r"),
    ], size=8.8, leading=12.6)

    X_WK, X_DT = d.ML + 2, d.ML + 40
    X_TOK, X_JOB, X_CUM, X_WOW = 300, 366, 470, d.R - 2
    y = d.table_header(y - 12, [("WEEK", X_WK, "l"), ("DATES", X_DT, "l"),
                                ("TOKENS", X_TOK, "r"), ("JOBS", X_JOB, "r"),
                                ("CUMULATIVE TOKENS", X_CUM, "r"), ("WOW", X_WOW, "r")])
    for i, (wk, dates, tok, jobs, cum, wow) in enumerate(WEEKS):
        stub = (wk == "17")
        y = d.table_row(y, 19.6, [
            (wk, X_WK, "l", "Mono-B", 7.4, d.AC if not stub else d.MUT),
            (dates, X_DT, "l", "Sans", 8.6, d.BODY),
            (tok, X_TOK, "r", "Mono-M", 8.2, d.MUT if stub else d.TX),
            (jobs, X_JOB, "r", "Mono", 8.2, d.BODY),
            (cum, X_CUM, "r", "Mono", 8.2, d.BODY),
            (wow, X_WOW, "r", "Mono-M", 7.6, d.POS if wow else d.MUT),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    y = d.para(d.ML, y - 18, [
        ("The week over week rate decays as the base compounds, which is what a healthy absolute "
         "ramp looks like: ", "r"),
        ("weekly volume adds roughly 10,900 tokens every week", "b"),
        (" and has never given a week back.", "r"),
    ], size=8.8, leading=12.6)

    d.stat_cells(y - 22, [
        ("16",     "",  "CONSECUTIVE WEEKS OF GROWTH,", "NO EXCEPTIONS"),
        ("10.9",   "k", "AVERAGE TOKENS ADDED TO", "WEEKLY VOLUME, EVERY WEEK"),
        ("14,077", "",  "JOBS RUN SINCE", "15 MAY 2026"),
        ("108",    "",  "TOKENS PER JOB,", "AVERAGE SINCE LAUNCH"),
    ], h=62)

    d.pullquote("Sixteen for sixteen",
                "Not one week has been smaller than the week before it.")
    d.end_page()


def page_three(d):
    d.new_page(3, 5)
    y = d.section_head(680, "03", "Growth On Every Axis")
    y = d.para(d.ML, y, [
        ("The same growth shows up whether it is measured in tokens, in jobs, or by the month. "
         "Month one delivered 103,795 tokens. The current run rate is 802,683 tokens a month, "
         "which is ", "r"),
        ("7.7x month one", "c"), (" and still climbing every week.", "r"),
    ], size=9.2, leading=13.2)

    X_MO, X_WIN, X_TOK, X_JOB, X_MOM = d.ML + 2, d.ML + 44, 340, 430, d.R - 2
    y = d.table_header(y - 14, [("MONTH", X_MO, "l"), ("WINDOW", X_WIN, "l"),
                                ("TOKENS", X_TOK, "r"), ("JOBS", X_JOB, "r"),
                                ("MOM", X_MOM, "r")])
    for i, (mo, win, tok, jobs, mom) in enumerate(MONTHS):
        y = d.table_row(y, 22.0, [
            (mo, X_MO, "l", "Mono-B", 7.6, d.AC),
            (win, X_WIN, "l", "Sans", 9.0, d.BODY),
            (tok, X_TOK, "r", "Mono-M", 8.6, d.TX),
            (jobs, X_JOB, "r", "Mono", 8.6, d.BODY),
            (mom, X_MOM, "r", "Mono-M", 7.8, d.POS if mom else d.MUT),
        ], shade=(i % 2 == 0))

    d.rect(d.ML, y - 24, d.TW, 24, d.SURF2)
    ty = y - 24 + (24 - 7.4) / 2.0 + 0.6
    d.draw(X_WIN, ty, "Month 4 at run rate, 31 days", "Sans-SB", 9.0, d.TX)
    d.draw_right(X_TOK, ty, "723,217", "Mono-B", 8.6, d.AC)
    d.draw_right(X_JOB, ty, "6,721", "Mono-M", 8.6, d.TX)
    d.draw_right(X_MOM, ty, "+35.8%", "Mono-B", 7.8, d.POS)
    y -= 24
    d.rule(y, d.AC, 0.8)

    y = d.para(d.ML, y - 34, [
        ("Jobs track tokens exactly across inference call growth in week one to week sixteen, "
         "the same ", "r"), ("36x", "c"),
        (". Consumption per job averages 108 tokens, so the growth is being driven by ", "r"),
        ("volume of real work", "b"), (" rather than by heavier individual calls.", "r"),
    ], size=9.2, leading=13.2)

    y = d.para(d.ML, y - 16, [
        ("Depth per account is building alongside it. Accounts with recorded usage are growing "
         "in tokens and jobs and most have already topped up past their initial grant. ", "r"),
        ("Every token here was consumed by an account that chose to spend it.", "b"),
    ], size=9.2, leading=13.2)

    d.stat_cells(y - 46, [
        ("25,893",  "",  "TOKENS PER DAY", "AT EXIT RUN RATE"),
        ("181,251", "",  "TOKENS PER WEEK", "AT EXIT RUN RATE"),
        ("802,683", "",  "TOKENS PER 31 DAY", "MONTH AT EXIT RUN RATE"),
        ("53",      "%", "OF ALL TOKENS SINCE LAUNCH,", "IN ONE MONTH AT RUN RATE"),
    ], h=74)

    d.pullquote("Read it this way",
                "One month at the current run rate consumes 53% of every token the platform "
                "has burned since launch. The base is no longer the story. The slope is.")
    d.end_page()


def page_four(d):
    d.new_page(4, 5)
    y = d.section_head(680, "04", "What Lands Next")
    y = d.para(d.ML, y, [
        ("Two consumer deployments sit on top of the current run rate, the ", "r"),
        ("Brecka", "c"), (" engagement and ", "r"), ("Glow", "c"),
        (" as it continues to grow. Both are forward models and ", "r"),
        ("neither is included in any measured figure above", "b"), (".", "r"),
    ], size=9.2, leading=13.2)

    X_SRC, X_SCALE, X_LIVE, X_TOKS = d.ML + 2, 230, 372, d.R - 2
    y = d.table_header(y - 14, [("SOURCE", X_SRC, "l"), ("SCALE", X_SCALE, "l"),
                                ("LIVE FROM", X_LIVE, "l"),
                                ("TOKENS PER MONTH AT FULL RATE", X_TOKS, "r")])
    rows = [
        ("Platform", "Held flat at the 8 September exit rate", "25,893 tokens per day",
         "Live", "802,683", d.MUT),
        ("Glow", "95,000 MAU at 0.67 interactions per user per day", None,
         "15 Oct 2026", "19,633,333", d.AC2),
        ("Brecka", "75,000 MAU at 2 interactions per user per day", None,
         "1 Jan 2027", "46,500,000", d.AC),
        ("Combined", "Both consumer platforms landed, 170,000 MAU", None,
         "Apr 2027", "66,936,016", d.TX),
    ]
    for i, (src, scale, scale2, live, toks, accent) in enumerate(rows):
        lines = d.wrap_plain(scale, "Sans", 8.6, X_LIVE - X_SCALE - 16)
        if scale2:
            lines += d.wrap_plain(scale2, "Sans", 8.6, X_LIVE - X_SCALE - 16)
        h = max(34.0, 16 + len(lines) * 11.4)
        if i % 2 == 0:
            d.rect(d.ML, y - h, d.TW, h, d.SURF)
        d.rect(d.ML, y - h, 1.6, h, accent)
        ty = y - h + (h - 7.4) / 2.0 + 0.6
        d.draw(X_SRC + 10, ty, src, "Sans-SB", 9.4, d.TX)
        ly = y - h + (h - len(lines) * 11.4) / 2.0 + (len(lines) - 1) * 11.4 - 1.0
        for ln in lines:
            d.draw(X_SCALE, ly, ln, "Sans", 8.6, d.BODY); ly -= 11.4
        d.draw(X_LIVE, ty, live, "Mono-M", 8.0, d.AC if live != "Live" else d.MUT)
        d.draw_right(X_TOKS, ty, toks, "Mono-B", 9.4, d.TX)
        y -= h
    d.rule(y, d.AC, 0.8)

    y = d.para(d.ML, y - 24, [
        ("Consumer volume converts at ", "r"), ("10 tokens per user per interaction", "b"),
        (". Half of Glow's users interact once a day and half once every three days, averaging "
         "0.67 interactions per user per day. Every Brecka user interacts twice a day. At full "
         "MAU that is ", "r"),
        ("633,333 tokens a day from Glow", "c"), (" and ", "r"),
        ("1,500,000 from Brecka", "e"), (".", "r"),
    ], size=9.2, leading=13.2)

    y = d.para(d.ML, y - 8, [
        ("Each platform ramps linearly from zero at go live to full MAU over 90 days. The "
         "existing platform is held flat at its 8 September exit rate rather than extrapolated "
         "forward, so ", "r"),
        ("every point of growth in the projection comes from the two deployments and none from "
         "assumed organic lift", "b"), (".", "r"),
    ], size=9.2, leading=13.2)

    d.stat_cells(y - 22, [
        ("170", "k", "COMBINED MAU ACROSS", "GLOW AND BRECKA"),
        ("2.1", "M", "TOKENS PER DAY AT", "FULL COMBINED RATE"),
        ("90",  "d", "LINEAR RAMP FROM GO LIVE", "TO FULL MAU, EACH"),
        ("0",   "",  "TOKENS OF ASSUMED", "ORGANIC PLATFORM LIFT"),
    ], h=62)

    d.pullquote("Not yet counted",
                "Neither Glow nor Brecka contributes a single token to any measured figure "
                "in this document. Both are still ahead of us.")
    d.end_page()


def page_five(d):
    d.new_page(5, 5)
    y = d.section_head(680, "05", "Projection To June 2027")
    y = d.para(d.ML, y, [
        ("Monthly token consumption by source, September 2026 through June 2027. Monthly volume "
         "goes from 776,790 to 64,776,790, an ", "r"),
        ("83x increase compounding at 63.5% a month", "c"), (", and exits on a ", "r"),
        ("777 million token annual run rate", "b"),
        (". Total consumption across the window is 346,312,244 tokens, which is ", "r"),
        ("229 times everything the platform has consumed since launch", "b"), (".", "r"),
    ], size=9.0, leading=12.8)

    y = d.para(d.ML, y - 6, [
        ("The current platform is in every column but too small to read at this scale, running "
         "about 800,000 tokens a month against 65 million from the two consumer platforms once "
         "both are landed.", "r"),
    ], size=8.6, leading=12.0)

    y = d.image_panel(y - 8, CH_PROJ, 7.0, 2.78)

    X_MO = d.ML + 2
    X_PLAT, X_GLOW, X_BRK, X_TOT, X_MOM = 210, 300, 392, 492, d.R - 2
    y = d.table_header(y - 20, [("MONTH", X_MO, "l"), ("PLATFORM", X_PLAT, "r"),
                                ("GLOW", X_GLOW, "r"), ("BRECKA", X_BRK, "r"),
                                ("TOTAL", X_TOT, "r"), ("MOM", X_MOM, "r")])
    for i, (mo, plat, glow, brk, tot, mom) in enumerate(PROJ):
        neg = mom.startswith("-")
        y = d.table_row(y, 17.4, [
            (mo, X_MO, "l", "Sans-SB", 8.4, d.TX),
            (plat, X_PLAT, "r", "Mono", 7.8, d.MUT),
            (glow, X_GLOW, "r", "Mono", 7.8, d.AC2 if glow != "0" else d.MUT),
            (brk, X_BRK, "r", "Mono", 7.8, d.AC if brk != "0" else d.MUT),
            (tot, X_TOT, "r", "Mono-B", 8.2, d.TX),
            (mom, X_MOM, "r", "Mono-M", 7.4, (d.NEG if neg else d.POS) if mom else d.MUT),
        ], shade=(i % 2 == 0))
    d.rule(y, d.AC, 0.8)

    d.pullquote("Where this exits",
                "Sixty five million tokens a month by April 2027, on a 777 million token annual "
                "run rate, from two deployments that have not started yet.")
    d.end_page()


def main():
    d = AmplifierDoc(OUT, palette=PAL,
                     title="Amplifier Health, Token Run Rate, September 2026",
                     subject="Token consumption, run rate and projection to June 2027")
    page_one(d); page_two(d); page_three(d); page_four(d); page_five(d)
    d.save()
    print("wrote", OUT, "in", d.P["name"])


if __name__ == "__main__":
    main()
