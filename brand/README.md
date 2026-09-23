# Amplifier Health brand kit

Named palettes and a document kit that renders a PDF in either of them.
**AMPLIFIER-DESIGN-PALETTE is the default for every document.**

```
brand/
  amplifier_palettes.py    the two named palettes, DEFAULT set to the design palette
  amplifier_doc_kit.py     AmplifierDoc, a palette aware layer over ReportLab
  fetch_fonts.py           pulls the four brand faces from Google Fonts
  AMPLIFIER-PALETTES.md    the written spec, hex values and signature moves
  assets/                  logo, forest green and light cuts
  fonts/                   Cormorant Garamond, Newsreader, Inter, JetBrains Mono
  examples/token_run_rate.py   five page worked example, renders in either palette
```

Quick start

```bash
pip install reportlab matplotlib
python3 brand/fetch_fonts.py        # only if brand/fonts is empty
cd brand/examples
python3 token_run_rate_charts.py && python3 token_run_rate.py
```

The design palette hex values were read out of the production flyer's PDF
content stream, not sampled by eye, so they match the printed collateral exactly.
