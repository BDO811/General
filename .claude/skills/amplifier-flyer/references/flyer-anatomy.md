# Flyer anatomy

One page. A locked grid. Every slot has a copy budget and the grid does not
stretch. If the copy does not fit, cut the copy.

## Order of calls

```python
d = Doc(out, kind="flyer")
flyer_header(d, tagline)
flyer_eyebrow(d, eyebrow)
flyer_hero(d, hero)
flyer_subhead(d, subhead)
flyer_stats(d, stats)
flyer_body(d, section, lede, blocks)
flyer_code(d, code_label, endpoint, code)
flyer_cta(d, cta, contact)
flyer_footer(d, foot_left, foot_right, disclaimer)
d.save()
```

## Slot by slot

**Tagline.** Top right, mono, letter spaced. Three or four words naming the
market frame. "Six markets, one signal."

**Eyebrow.** Pink mono bold. Names the model and its status.
"Sona-2 · Frontier voice model — in production."

**Hero.** Cormorant Garamond Light 26 over the pale band. **Two lines, about
95 characters.** Written as a provocation, not a product claim. It opens with
"Imagine if" or an equivalent invitation. It never names a disease.

**Subhead.** Newsreader Italic 19. **Two lines, about 100 characters.** States
what voice replaces, in plain physical terms. "No needle, no X-ray, no
stethoscope."

**Stats.** Four cells on a 128pt pitch. Value in serif, label in mono over
one or two lines. Labels run about 30 characters. Keep the four consistent
in kind: dataset size, labelled conditions, production indicators, languages.

**Section label.** Pink mono bold. "Applied to · [Market]".

**Lede.** Inter 8.8. **Two lines, about 190 characters.** Names the reader's
problem in their own vocabulary, not ours. A wellness flyer talks about
retention curves. A payer flyer talks about risk adjustment.

**Blocks.** Exactly four, on a 52.2pt pitch. Each one pink mono label plus
**two body lines, about 190 characters.** The four are a fixed argument:

1. What's missing. Why voice is the input nothing else can be.
2. What arrives. The signal set, framed as observation.
3. Where it fits. The integration, in one sentence.
4. What it doesn't do. The compliance boundary, stated plainly.

Block four is not optional and is not softened. It is what makes the rest
credible.

**Sample response.** Pink label left, mono endpoint right. Five lines of
JSON in the dark block. Keys render pink, everything else pale. Use a real
endpoint and a real response shape.

**CTA.** Black pill, 190 x 26, mono bold label ending in `->`. Contact on
the right in mono.

**Footer.** Hairline, then company left and domain right in mono, then the
required disclaimer in Inter 6.6.

## Optional full bleed image

The original flyer carries a faint photograph behind the lower half. It is a
full page raster placed under everything, at low contrast so body copy stays
readable. If you use one, place it first, then draw the cream ground over it
at partial opacity, then all the type. Test the body copy contrast.
