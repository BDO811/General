# DNS records for amplifierhealth.com

Audited 2026-09-22. Authoritative nameservers are `ns-cloud-e{1..4}.googledomains.com`,
which is what Squarespace uses for domains inherited from Google Domains, so the
Squarespace DNS panel is the right place to make these edits.

## Current state

| Record | Value | Assessment |
| --- | --- | --- |
| MX | Google Workspace (`aspmx.l.google.com` and alternates) | fine |
| SPF | `v=spf1 include:_spf.google.com include:342367096.spf.hubspotemail.net ~all` | fine |
| DKIM | `google._domainkey` present, HubSpot `hs1`/`hs2` selectors present | fine |
| DMARC | `v=DMARC1; p=none; pct=100; rua=mailto:dmarcreports@lovable.dev` | broken, see below |
| A (apex) | `185.158.133.1`, PTR `lovable-app-cd-1-4.p.l5e.io` | Lovable hosting, expected |

## Fix 1: DMARC reporting goes nowhere (do this regardless of email verification)

The aggregate report address points at `dmarcreports@lovable.dev`, a third party.
Under RFC 7489 section 7.1, a receiver will only send reports to an outside domain
if that domain publishes an authorization record. Lovable has not:

```
amplifierhealth.com._report._dmarc.lovable.dev  ->  NXDOMAIN
```

So no mail receiver is sending those reports anywhere. Nobody is getting them,
including Lovable. The domain has had zero DMARC visibility for as long as that
record has been in place, and `p=none` means nothing is enforced either.

Replace the `_dmarc` TXT record:

| Host | Type | Priority | Data |
| --- | --- | --- | --- |
| `_dmarc` | TXT | | `v=DMARC1; p=none; rua=mailto:dmarc@amplifierhealth.com; fo=1; pct=100` |

`dmarc@amplifierhealth.com` has to be a real mailbox or a Workspace group first.
Run at `p=none` for two to three weeks, read the reports to confirm Google and
HubSpot are the only legitimate senders, then tighten to `p=quarantine` and later
`p=reject`. Enforcement is what stops anyone spoofing the domain in outbound.

## Fix 2: the verification identity

Probing mailboxes draws blocklist attention. Keep it off the corporate domain by
giving it its own subdomain, so a listing hits `verify.amplifierhealth.com` and
never touches Workspace or HubSpot delivery.

Add these once the probe host has a static public IP. Replace `PROBE_IP`.

| Host | Type | Priority | Data |
| --- | --- | --- | --- |
| `verify` | A | | `PROBE_IP` |
| `mail.verify` | A | | `PROBE_IP` |
| `verify` | MX | 10 | `mail.verify.amplifierhealth.com.` |
| `verify` | TXT | | `v=spf1 ip4:PROBE_IP -all` |
| `_dmarc.verify` | TXT | | `v=DMARC1; p=reject; rua=mailto:dmarc@amplifierhealth.com` |

Then, at the hosting provider (not Squarespace), set reverse DNS on `PROBE_IP` to
`mail.verify.amplifierhealth.com`. Providers put this under the instance or IP
settings. Hetzner, OVH, Vultr and DigitalOcean all allow it. AWS and GCP require a
support request and will not grant it without justification, which is one reason
they are poor hosts for this.

Finally, make `probe@verify.amplifierhealth.com` deliver somewhere you can read.
Bounces and abuse complaints arrive there, and a sender address that black-holes
mail is itself a spam signal.

## What actually matters for a probe, and what does not

The SMTP probe stops at `RCPT TO`. It never sends a message body, so:

1. **PTR and forward-confirmed reverse DNS matter most.** The receiver looks up the
   connecting IP, gets a hostname, looks that hostname up again, and expects to land
   back on the same IP. Failing this is the single largest cause of refusals.
2. **SPF matters**, because receivers check the `MAIL FROM` domain against the
   connecting IP during the transaction.
3. **DKIM does not apply.** There is no message to sign. It matters for the actual
   outbound campaign, not for verification.
4. **A routable `MAIL FROM` domain matters.** Receivers reject senders whose domain
   has no MX or A record.

Run `../preflight.sh` on the probe host to check all of this, plus port 25 egress,
before any batch.
