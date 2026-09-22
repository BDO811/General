# amplifierhealth.com: read-only audit

Recorded 2026-09-22. **Nothing in this toolchain touches this domain.** The
verification identity lives on a separate domain precisely so that no change here
is ever required. This file exists so the findings are not lost.

Reproduce any time with:

```bash
./check-dns.sh audit amplifierhealth.com
```

## Healthy

| Record | Value |
| --- | --- |
| MX | Google Workspace, `aspmx.l.google.com` and alternates |
| SPF | `v=spf1 include:_spf.google.com include:342367096.spf.hubspotemail.net ~all` |
| DKIM | `google._domainkey` present, HubSpot `hs1`/`hs2` selectors present |

Google and HubSpot are both correctly authorized. No action needed on either.

## Open finding: DMARC reporting is black-holed and the policy is not enforced

Current record:

```
v=DMARC1; p=none; pct=100; rua=mailto:dmarcreports@lovable.dev
```

Two separate problems.

**The reports go nowhere.** RFC 7489 section 7.1 requires the receiving domain to
publish an authorization record before any mail receiver will send it aggregate
reports for another domain. Lovable has not:

```
amplifierhealth.com._report._dmarc.lovable.dev  ->  NXDOMAIN
```

So Google, Microsoft and everyone else discard the reports rather than deliver
them. Nobody is reading them, Lovable included. The address appears to be left
over from the website build.

**Nothing is enforced.** `p=none` tells receivers to take no action on mail that
fails authentication. Combined with the reporting gap, the domain can be spoofed
and there is no telemetry that would reveal it.

## Proposed remedy, for whoever owns this zone

1. Create `dmarc@amplifierhealth.com` as a Workspace group that accepts external
   senders.
2. Replace the `_dmarc` TXT record with
   `v=DMARC1; p=none; rua=mailto:dmarc@amplifierhealth.com; fo=1; pct=100`
3. Read reports for two to three weeks and confirm Google and HubSpot are the only
   legitimate senders.
4. Move to `p=quarantine`, then after another two weeks to `p=reject`.

Step 4 is what actually stops spoofing. Steps 1 through 3 exist so that step 4
does not silently break a sender nobody remembered.

This affects every mailbox on the domain, so it is a change for the domain owner
to schedule, not something to slip in alongside a sales tooling project.
