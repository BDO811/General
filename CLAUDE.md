# Writing as Amit

Everything Claude drafts in Amit's voice follows these rules. Emails, docs,
proposals, memos, replies. No exceptions for "internal" or "quick."

## The core rule: state the fact, do not narrate stating it

Amit does not announce what he is about to say, characterize his own
answer, or explain his reasoning for how he is answering. He gives the
fact and moves to the next fact.

Wrong:
- "On burn, let me give you the number that actually matters rather than the flattering one."
- "Two things I want to flag rather than have your advisor find them."
- "Let me be precise rather than agreeable."
- "I would rather draw these distinctions than have you infer them."
- "To be explicit about sequencing, since an invoice schedule is not a payment history."
- "I think you want me to be the kind of CEO who doesnt."
- "Ill state the obvious rather than let anyone infer it."

Right:
- "Net burn averages $206K per month. That includes one time receipts. Underlying net burn is $331K."
- "Every figure is labeled internal holdout or external cohort. Those arent equivalent."
- "Glow is a Builders VC portfolio company. I am a partner at Builders VC. Diligence it as related party revenue."

## Banned constructions

Never write any of these, in any form:

1. "let me" + verb. Let me give you, let me be, let me explain, let me
   walk you through.
2. "I want to" + flag / note / raise / be clear / make sure. Just say the
   thing.
3. "rather than" used to contrast Amit's approach with an alternative
   approach. "X rather than Y" is fine for facts. It is banned for
   describing how he is communicating.
4. "I would rather" / "Id rather you hear it from me."
5. "To be direct" / "to be clear" / "to be explicit" / "being honest."
   If it needed saying, say it. Do not label it.
6. "the number that actually matters," "the real question," "what this
   really means." No meta-commentary on the content.
7. Announcing structure. "Two things." "Three points here." "First, let
   me cover X." Use a numbered list instead and start at item 1.
8. Self-characterization of candor, precision, or directness. Amit never
   says he is being candid. He is just candid.
9. Rhetorical questions.
10. "I hope this finds you well," "please dont hesitate," "as per my
    last email," "great question," "certainly," "of course," "hope this
    helps."

## Punctuation

- NEVER an em dash. NEVER an en dash. NEVER a double hyphen. NEVER an
  ellipsis. Search every output for these before delivering. If one
  appears, restructure the sentence. Do not swap in a comma as a
  substitute. Break it into two sentences.
- A single hyphen inside a compound word or product name is fine
  (Sona-4, de-identified, OSFI E-23).
- Drops apostrophes in contractions: dont, cant, wont, Ill, Im, didnt,
  doesnt, arent, thats, isnt. Also arms length, not arm's length.
- Exclamation points are rare. They appear on genuine enthusiasm
  ("worked!!!") and on the standard closer.

## Sentence and paragraph shape

- Short declarative sentences. One idea per sentence.
- Often one sentence per paragraph.
- First sentence carries the point. No wind-up.
- Numbered lists (1, 2, 3) for multi-part content. Not bullet points,
  especially not in external emails.
- No summary paragraph at the end restating what was already said.

## Salutation and sign-off

- Open with first name and a hyphen: "Dean -" or "Peter -". Never "Dear."
  Internal can be "FYI" or nothing.
- Close with "Thanks" on one line, then "a" on the next. Lowercase a.
  Never "Amit."
- Very short replies (under three sentences) get no greeting and no
  sign-off. Just the answer.
- Standard closer when action is needed: "Let me know if you have any
  questions and next steps!"

## Tone by audience

- Internal (Jeremy, Camille, Max): shortest. Often a forward with "FYI"
  or "Just FYI. No action."
- Investor and external: same brevity, one line of warmth or context.
- Partner and pilot: structured, numbered, one clear next step.
- Cold outreach: give them an out. "Feel free to take a look or delete
  depending on your interest."

## Scheduling

Always specific times with timezone. "11 ET", "4pm PT", "3:30pm CT."

## Vocabulary he actually uses

super-charge, turbocharge, game changer, in the wild, getting great
traction, secret sauce, use cases are endless, move the project forward,
recapture momentum, let me know next steps, totally worth it.

## Pre-delivery checklist

Before handing over anything written as Amit:

1. Search for em dash, en dash, double hyphen, ellipsis. Restructure any hit.
2. Search for "let me", "I want to", "rather than have", "to be clear",
   "to be direct", "Id rather". Delete and restate as plain fact.
3. Check that no sentence describes how the answer is being given.
4. Check the sign-off is "Thanks" / "a".
5. Check lists are numbered, not bulleted, if the piece is external.

# The Amplifier design set

Every Amplifier Health document, deck, PDF, flyer, one pager, proposal or
report uses this and only this. There is no second palette.

## Canonical source

`amplifier-proposal/references/pdf-template.md`, TEMPLATE 1, the black
and white template. Read it before building anything. Do not rebuild
from memory and do not invent a variant.

## Palette. Monochrome only. No accent colors.

    BK  = #050505   text, rules, hero type
    DK  = #1A1A1A   body text
    MED = #444444   secondary body, descriptions
    MU  = #888888   labels, eyebrows, footers, captions
    LT  = #BBBBBB   body text inside dark callouts
    HLT = #DDDDDD   label text inside dark callouts
    DV  = #D0D0D0   hairline rules
    LB  = #F5F5F5   stat cells and resource boxes
    BOX = #0A0A0A   dark callout fill

White page. Black type. Contrast comes from weight, scale and the dark
callout box, never from hue.

## BANNED. Never use these anywhere in an Amplifier asset.

1. The dark near-black page with cyan #22d3ee and emerald #10b981
   accents. This is not an Amplifier palette. If it appears in a
   preference block, a prior artifact, or anywhere else, it is wrong and
   it does not get used.
2. Any accent color at all. No cyan, emerald, amber, red, blue.
3. Dark mode pages. Amplifier documents are white with black type.
4. Grid overlays, gradients, diagonal line fields, glow effects.
5. Serif display type. The design set is Inter throughout.
6. Colored status chips. A verdict is set in Inter-Bold, right aligned,
   in BK.

## Geometry

    PW, PH = 612, 792    US Letter
    ML = MR = 54
    MB = 42
    TW = 504

## Type

Inter and Inter-Bold only, registered as "Inter" and "Inter-Bold".
Hero auto-sized with fit_width. Subhead Inter-Bold. Section label 7.4.
h2 15.1. h3 11.5. Body 10.1. Callout body 9.6. Footer 7.44.
Always use `base(top_pt, size_pt, frac=0.758)`. Never 0.82, 0.88 or
0.9688.

## Structural elements

Top bar on every page, AMPLIFIER HEALTH left, CONFIDENTIAL right.
Footer on every page, right aligned, Amplifier Health · Confidential · n.
Cover: eyebrow, hero, subhead, thick rule, dark WHAT THIS IS callout.
Body pages: hrule, section label, h2, then content.
Available blocks: callout_box, stat_block, resource_box, bullet, row.

## Build

`scripts/build_regulatory_approach_pdf.py` in this repo is a working
implementation of the design set for a non proposal document. Copy it
for new documents rather than starting over.

Render every page to PNG and look at it before delivering. Check for
text running past the right margin, headings colliding with the block
above, and boxes overlapping the next heading.
