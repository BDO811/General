# What this costs, and what is genuinely free

Checked September 2026. Vendor prices move, treat the dollar figures as current
estimates and the structure as the durable part.

## The free version, which covers most of the value

`prefilter.py` runs anywhere with Python and an internet connection. Your laptop,
this repository, a GitHub Action. No port 25, no probe host, no domain, no
account, nothing to pay.

```bash
./prefilter.py prospects.csv
```

It checks syntax, resolves MX over DNS over HTTPS, matches against the public
disposable domain blocklist (roughly 9,000 domains, fetched and cached), and
flags role accounts. On a test list of 9 addresses it removed 6. On a real
scraped or purchased list expect 15 to 40 percent removed before anything paid
touches it.

It writes `<name>.stage1.csv` with a verdict and reason per address, and
`<name>.pass.txt` with only the survivors.

What it cannot do is tell you whether a specific mailbox exists. That is the one
signal that requires either an SMTP probe from a host with port 25, or a paid
API. Everything else is free.

## Stage two, three ways

### Pay per verification, no infrastructure

Pay-as-you-go verification APIs run roughly $2.50 to $10 per thousand. Several
carry a real free tier: 100 credits a month is common, and a few give more.

Against a stage one filtered list, a few hundred paid verifications a month costs
single digit dollars. Zero setup, zero maintenance, and none of your domains are
exposed to blocklists because the vendor's IPs do the probing.

### Self-host the probe

| Item | Cost |
| --- | --- |
| Domain, `.com` | about $10 to $12 a year |
| VPS with port 25, Hetzner or Vultr | roughly $3 to $7 a month |
| DNS, Cloudflare free tier | $0 |
| Google Cloud DNS, if you prefer your existing account | about $0.20 per zone per month |

Call it $80 to $90 a year all in. Hetzner raised shared vCPU prices in mid 2026
and some plans have shown as unavailable since, so check current availability
before assuming the cheapest tier exists.

Do not economise on the domain with a $1 `.xyz` or `.top`. Cheap TLDs carry
reputation penalties at receiving mail servers, which is the exact thing you are
trying to avoid on a sender identity. Pay the $10 for a `.com`.

### Free VPS, and why not to plan around it

Oracle Cloud Always Free is the only free tier with a real always-on VM. It
blocks outbound port 25 for every tenancy created after 23 June 2021. An
exemption can be requested through a service limits request, and free tier
requests are frequently declined. Treat it as a lottery ticket, not a plan.

Google Cloud, AWS and Azure free tiers do not help: see `dns/hosting-options.md`.

## The break-even, plainly

Self-hosting costs about $85 a year. At $2.50 to $10 per thousand, that is
roughly 8,500 to 34,000 verifications a year before the VPS pays for itself, and
that ignores your time and the blocklist exposure you take on.

So:

1. **Always run `prefilter.py` first.** It is free and it shrinks everything
   downstream.
2. **Under a few hundred stage two verifications a month, buy them.** A VPS is
   not worth owning at that volume.
3. **Above roughly a thousand a month sustained, self-host.** That is when the
   fixed cost wins and when rate limits on a vendor plan start to bite.

The tooling in this directory supports all three. Stage one is free and always
worth running. Stage two is a switch you flip when volume justifies it.
