# Getting an Abstract API key

Verified against their site and docs, September 2026. I cannot create the
account: it needs your email, a password and your acceptance of their terms.
Everything after step 4 is mine.

## 1. Sign up

https://www.abstractapi.com/api/email-verification-validation-api

Click to start the free plan. **No credit card is required.** Sign up with an
address you control. Use a personal or alias address rather than
amit@amplifierhealth.com if you would rather this not sit against the company
domain in a vendor's CRM, it makes no difference to how the API behaves.

## 2. Get the key for the right API

Abstract sells about a dozen APIs and **each one has its own separate key**.
From your dashboard, open the **Email Validation** API specifically and copy the
key shown there. A key from any of their other products returns HTTP 401 against
this endpoint, and that is the single most common setup mistake.

## 3. Paste it into config.env

```bash
cd tools/check-if-email-exists
cp config.env.example config.env     # if you have not already
```

Set these two lines:

```
VERIFY_PROVIDER="abstract"
VERIFY_API_KEY="the key you copied"
```

`config.env` is gitignored. The key never reaches the repository.

## 4. Confirm it works

```bash
./verify-api.py --test
```

One credit, one address, and it prints the parsed verdict and the raw response.
If the key is wrong it says so and stops rather than working through anything.

## 5. Run a real list

```bash
./prefilter.py prospects.csv                    # free, removes a large share
./verify-api.py prospects.pass.txt --dry-run    # how many credits this costs
./verify-api.py prospects.pass.txt --yes        # spend them
```

## What the free plan gives you

| | |
| --- | --- |
| Requests | 100 a month |
| Rate limit | 1 per second |
| Included | full deliverability, including the SMTP check, plus disposable, role, catch-all and MX |
| Credit card | not required |

100 a month is a real test of the workflow, not a demo. Against a stage one
filtered list it is roughly 150 to 250 raw addresses a month.

## When to leave Abstract

Their paid plans are monthly subscriptions, roughly $17 a month for 5,000, which
is about $3.40 per thousand and only worth it if you use the volume every month.

MillionVerifier is pay as you go at roughly $2.50 per thousand with no monthly
commitment, which suits lumpy outreach far better. Switching is one line:

```
VERIFY_PROVIDER="millionverifier"
VERIFY_API_KEY="..."
```

Nothing else changes. Verdicts are normalised to the same vocabulary either way.

So: start free on Abstract, and if you are regularly hitting the 100 ceiling,
move to MillionVerifier rather than paying Abstract's monthly minimum.
