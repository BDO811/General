# Replacement for the email verification step

Drop-in replacement for **Step 3** of `amplifier-proposal` and **Step 4** of
`amplifier-gmail`, both currently titled "Verify email (MANDATORY, 3 sources)".

---

## Step N - Confirm the email address (MANDATORY)

Do not guess a pattern and hope. Ask the receiving mail server.

```bash
python3 ~/.amplifier/verify_email.py \
  --first "Sarah" --last "Chen" --domain "acme.com"
```

It builds the likely addresses in order of how common they are at
venture-backed companies, tests each one, and stops at the first the mail
server accepts. Typical cost is 1 to 3 credits per company.

Act on the result:

| Outcome | What it means | What to do |
| --- | --- | --- |
| `USE: name@domain` | The mail server confirmed that mailbox exists | Use it. **No further sourcing needed.** Record confidence CONFIRMED |
| `CATCH-ALL DOMAIN` | The domain accepts every address, so no test can tell a real mailbox from a typo | **Fall back to the 3-source method below.** Record confidence CATCH-ALL and flag it |
| `NO CANDIDATE CONFIRMED` | Every pattern was rejected | Re-check the domain is right, then fall back to the 3-source method. Flag it |

To check an address a data broker already gave you, rather than searching:

```bash
python3 ~/.amplifier/verify_email.py --email "sarah.chen@acme.com"
```

### Why this replaces three sources when it confirms

Three brokers agreeing is three copies of the same scrape, often years stale.
A `USE:` result is the destination mail server saying that mailbox exists right
now. That is a stronger signal than any number of agreeing directories, and it
is what actually predicts whether the mail lands.

### Fallback: the 3-source method

Use this **only** when the tool reports catch-all or confirms nothing.

Acceptable sources: ZoomInfo, RocketReach, ContactOut, EasyLeadz, LeadIQ, Wiza,
Adapt.io, Growjo, SignalHire, confirmed company email domain pattern.

1. Confirm the company's active email domain
2. Confirm the format pattern (first@, flast@, first.last@)
3. Cross-reference the executive across 3+ sources
4. If all agree, mark CONFIRMED. If they conflict, use the most authoritative
   (ZoomInfo > RocketReach) and note the conflict as a flag

### Never send to an unconfirmed address without saying so

In the final flag report (Step 8 in amplifier-proposal, Step 10 in amplifier-gmail), every company must carry one of:

- **CONFIRMED** by the mail server, the normal case
- **CATCH-ALL**, address inferred, cannot be verified, delivery not guaranteed
- **3-SOURCE**, verification found nothing, address from directories, lower confidence

A bounced cold email on a new domain costs far more than a credit.
