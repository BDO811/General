# Amplifier Health, 5 Slide Deck

A self contained 16:9 deck. `amplifier-deck.html` embeds every font and image as
base64, so it renders identically offline, in a browser, and in PDF.

## Files

| File | What it is |
| --- | --- |
| `amplifier-deck.html` | The deck. Open it in any browser. Arrow keys or space to advance. |
| `Amplifier-Health-5-Slide.pdf` | 5 pages, 13.333in x 7.5in (16:9), ready to send or present. |
| `deck.template.html` | Source template. Edit this, not the built file. |
| `build.py` | Inlines assets into `amplifier-deck.html`. |
| `make-pdf.sh` | Re-exports the PDF. |
| `shots.sh` | Renders each slide to PNG for review. |

## Slides

1. Imagine a technology that could touch every human on the planet.
2. Introducing Amplifier Health, with the registered brandmark.
3. Sona-2, a Large Acoustic Model at the frontier of foundation model generative AI.
4. What comes back from 15 seconds of speech.
5. try.amplifierhealth.com

## Rebuilding

```bash
python3 build.py     # deck.template.html + assets -> amplifier-deck.html
./make-pdf.sh        # amplifier-deck.html -> PDF
./shots.sh /tmp/out  # per slide PNGs
```

## Notes on content

Slide 4 is not illustrative. The 17 biomarker signals, the 24 conditions and their
evidence tiers, and the 8 model pipelines were read from the Amplifier v2
production API, so the slide matches what the platform actually returns today.

## Assets

Backgrounds are Pixabay stock, laid in at 10 percent opacity under a vignette and
grid. Typography is Cormorant Garamond with JetBrains Mono accents, latin subsets
only. The logo is the official `Amplifier_Brandmark_White_RGB.svg` pulled from
amplifierhealth.com.
