# Getting a MillionVerifier key

Verified against their API and public pricing, September 2026. I cannot create
the account: it needs your email, a password and your acceptance of their terms.
Everything from step 4 is mine.

## Why this one

Pay as you go, no subscription, and **credits never expire**. That matters more
than the headline rate when outreach is lumpy: you buy once and draw down over
months instead of paying a monthly minimum whether or not you use it.

**Signup gives 500 free credits and asks for no credit card.** That is five
times what Abstract's free tier offers, so start there and only buy once you
have run real lists through it.

## 1. Sign up

https://www.millionverifier.com

Create the account. No card required for the free credits. Use an address you
control.

## 2. Find the API key

In the dashboard, open the API section. MillionVerifier issues one key for the
account, so there is no per-product confusion to fall into here.

## 3. Paste it into config.env

```bash
cd tools/check-if-email-exists
cp config.env.example config.env     # if you have not already
```

```
VERIFY_PROVIDER="millionverifier"
VERIFY_API_KEY="the key from the dashboard"
```

`config.env` is gitignored. The key never reaches the repository.

## 4. Confirm it works

```bash
./verify-api.py --test
```

One credit, one address. It prints the verdict, the raw response and **your
remaining credit balance**, which MillionVerifier returns on every call. If the
key is wrong it stops immediately: their API answers a bad key with HTTP 200 and
an error field rather than a 401, so the script reads the body, not just the
status code.

## 5. Run a real list

```bash
./prefilter.py prospects.csv                    # free, removes a large share
./verify-api.py prospects.pass.txt --dry-run    # how many credits this costs
./verify-api.py prospects.pass.txt --yes        # spend them
```

Each run prints the remaining balance as it goes, resumes from its own output so
no address is ever paid for twice, and halts the moment credits run out.

## Buying credits, when the 500 run out

Roughly, from their published pricing:

| Credits | Price | Per 1,000 |
| --- | --- | --- |
| 10,000 | about $37 | about $3.70 |
| 50,000 | about $89 | about $1.78 |
| 100,000 | about $129 | about $1.29 |

The cost estimate in `verify-api.py` uses the $3.70 figure, so it never
understates what a run will cost. Credits never expire, so buying the larger
package is only a cash flow question, not a use-it-or-lose-it one.

Against a stage one filtered list, 10,000 credits is a lot of outreach. Do not
buy ahead of what you know you need.
