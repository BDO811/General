#!/usr/bin/env python3
"""Render every page of a PDF to PNG and report text crossing the margin.

    python3 verify.py out.pdf [outdir]
"""
import sys, os
import pymupdf

pdf = sys.argv[1]
outdir = sys.argv[2] if len(sys.argv) > 2 else "/tmp"
d = pymupdf.open(pdf)
bad = 0
for i, p in enumerate(d):
    png = os.path.join(outdir, "%s_p%d.png" % (os.path.splitext(os.path.basename(pdf))[0], i + 1))
    p.get_pixmap(dpi=110).save(png)
    right = 0
    for b in p.get_text("dict")["blocks"]:
        if "lines" not in b:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                right = max(right, s["bbox"][2])
    limit = 562.5
    flag = ""
    if right > limit:
        flag = "   OVER MARGIN by %.1fpt" % (right - limit)
        bad += 1
    print("page %d  rightmost text %.1f%s  ->  %s" % (i + 1, right, flag, png))
print("\n%d page(s) over margin" % bad)
sys.exit(1 if bad else 0)
