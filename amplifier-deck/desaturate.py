#!/usr/bin/env python3
"""Bake an 8% desaturation into the background plates.

Doing this at rest instead of with a CSS filter keeps Chrome from rasterizing
the whole background layer on print, which roughly tripled the exported PDF.
Run once; the assets are already baked.
"""
import sys, pathlib
from PIL import Image

AMOUNT = 0.08
A = pathlib.Path(__file__).resolve().parent / "assets"

for name in ["s1_earth.jpg", "s2_wave.jpg", "s3_ai.jpg", "s5_wave.jpg"]:
    p = A / name
    im = Image.open(p).convert("RGB")
    grey = im.convert("L").convert("RGB")
    out = Image.blend(im, grey, AMOUNT)
    before = p.stat().st_size
    out.save(p, "JPEG", quality=88, optimize=True, progressive=True)
    print(f"  {name:14s} {before/1024:6.0f} KB -> {p.stat().st_size/1024:6.0f} KB")
print(f"desaturated by {AMOUNT:.0%}")
