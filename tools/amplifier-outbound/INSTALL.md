# Installing email verification into the outbound skills

At 20 emails a day, a wrong address is the most expensive failure in the
pipeline: the proposal is written, the PDF is generated, the draft is sent, and
it bounces. This adds an empirical check at the one step that decides it.

## 1. Put the script somewhere stable

```bash
mkdir -p ~/.amplifier
cp scripts/verify_email.py ~/.amplifier/
chmod +x ~/.amplifier/verify_email.py
```

`~/.amplifier/` is used deliberately rather than a path inside the skill
directory, because synced skills move and a broken path fails silently mid-run.

## 2. Store the API key

```bash
echo "YOUR_MILLIONVERIFIER_KEY" > ~/.millionverifier_key
chmod 600 ~/.millionverifier_key
```

The script also reads `MV_API_KEY` if you prefer an environment variable.

## 3. Update the two skills

`skills/amplifier-proposal/SKILL.md` and `skills/amplifier-gmail/SKILL.md` in
this directory are the patched versions. Copy each over the corresponding file
in your skills directory.

Only one section changed in each: Step 3 in amplifier-proposal and Step 4 in
amplifier-gmail, both previously "Verify email (MANDATORY, 3 sources)".
`STEP3-REPLACEMENT.md` holds that section on its own if you would rather merge
it by hand.

## 4. Check it works

```bash
python3 ~/.amplifier/verify_email.py --first Sarah --last Chen --domain acme.com
```

## What changed in the pipeline

Before: guess the pattern, cross-reference three data brokers, hope.

After: generate the likely addresses for the person, ask the receiving mail
server which one exists, stop at the first hit. Three outcomes, each with a
defined action:

- **`USE: name@domain`** the mail server confirmed the mailbox. No further
  sourcing. This is the normal case.
- **`CATCH-ALL DOMAIN`** the domain accepts everything, so no test can
  discriminate. Falls back to the 3-source method, and the company is flagged.
- **`NO CANDIDATE CONFIRMED`** every pattern was rejected. Falls back to the
  3-source method, and the company is flagged.

The 3-source method is retained, demoted to a fallback for the two cases where
verification genuinely cannot answer. Every company now carries a confidence
label into the final flag report, so an inferred address is never silently
treated like a confirmed one.

## Cost

One to three credits per company, since it stops at the first confirmation.
At 20 a day that is roughly 400 to 1,200 credits a month. The smallest
MillionVerifier package, about $37 for 10,000 credits, covers something like a
year. Credits do not expire.

## Known limitation

Catch-all domains defeat every verification service, not just this one. Your own
amplifierhealth.com is one, which is why nothing can confirm your address either.
Expect a meaningful minority of targets to land in that bucket and need the
fallback.
