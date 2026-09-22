# Runbook: make voice-free email verification actually work

Two tracks. Track A is five minutes and fixes a live security gap. Track B stands
up the verification host. They are independent, do A first.

After each track, run `./check-dns.sh amplifierhealth.com` and it will tell you
pass or fail on every record. No guessing.

---

## Track A: fix DMARC (5 minutes, do this today)

Right now `amplifierhealth.com` publishes `p=none` and sends its aggregate reports
to `dmarcreports@lovable.dev`, which has no authorization record, so every receiver
drops them. No enforcement, no visibility. Anyone can spoof the domain at an
investor or a hospital CIO and nothing stops it.

### A1. Create the reporting address

In Google Workspace admin, create a group `dmarc@amplifierhealth.com`. Add yourself.
Allow external senders to post to it, otherwise the reports bounce.

### A2. Replace the DMARC record

In the Squarespace domain dashboard, open `amplifierhealth.com`, go to the DNS
settings, and find the custom record with host `_dmarc`. Edit it, or delete and
re-add:

```
Host:  _dmarc
Type:  TXT
Data:  v=DMARC1; p=none; rua=mailto:dmarc@amplifierhealth.com; fo=1; pct=100
```

Leave every other record alone. SPF and DKIM are correct and do not need touching.

### A3. Verify

```bash
./check-dns.sh amplifierhealth.com
```

Both DMARC lines should flip to PASS except the policy line, which stays FAIL by
design until A4.

### A4. Tighten, two to three weeks later

Read the reports. Confirm the only senders passing are Google Workspace and
HubSpot. Then change `p=none` to `p=quarantine`, wait another two weeks, then
`p=reject`. Do not skip to reject: if any legitimate sender is unaccounted for,
their mail starts disappearing.

---

## Track B: stand up the verification host

### B1. Pick a provider that allows port 25 and reverse DNS

Hetzner or Vultr. A small instance is a few dollars a month. Both let you set
reverse DNS on the IP yourself. Hetzner requires a short unblock request for port
25 on new accounts and grants it routinely.

Do not use AWS, GCP or Azure. They block outbound 25 by default and will not grant
reverse DNS control without a support fight. That is the whole reason this cannot
run in the Claude container.

### B2. Add the DNS records

Same Squarespace DNS panel. Replace `PROBE_IP` with the instance IP.

```
Host: verify           Type: A     Data: PROBE_IP
Host: mail.verify      Type: A     Data: PROBE_IP
Host: verify           Type: MX    Priority: 10    Data: mail.verify.amplifierhealth.com.
Host: verify           Type: TXT   Data: v=spf1 ip4:PROBE_IP -all
Host: _dmarc.verify    Type: TXT   Data: v=DMARC1; p=reject; rua=mailto:dmarc@amplifierhealth.com
```

### B3. Set reverse DNS at the provider

Not in Squarespace. In the provider console, on the instance or the IP, set the
PTR record to `mail.verify.amplifierhealth.com`. This is the single most important
record for getting honest answers from receivers.

### B4. Verify DNS before touching the host

```bash
./check-dns.sh amplifierhealth.com PROBE_IP
```

All PASS before continuing. DNS propagation is minutes, not days, on Google Cloud
DNS.

### B5. Install and preflight on the host

```bash
ssh root@PROBE_IP
apt update && apt install -y git curl build-essential pkg-config perl
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
. "$HOME/.cargo/env"

git clone https://github.com/BDO811/General.git
cd General/tools/check-if-email-exists
./install.sh
cp config.env.example config.env
```

Edit `config.env` so `FROM_EMAIL=probe@verify.amplifierhealth.com` and
`HELLO_NAME=mail.verify.amplifierhealth.com`, then:

```bash
./preflight.sh
```

Nine checks. It exits nonzero and names the exact record to fix on any failure.
Do not run a batch until it is clean.

### B6. Make the probe address receive mail

Point `probe@verify.amplifierhealth.com` somewhere readable, or route the verify
subdomain's MX to Workspace instead of the host. Bounces and abuse complaints
arrive there, and a sender address that black-holes mail is itself a spam signal.

### B7. First batch

```bash
./verify-batch.sh prospects.csv results/2026-09-22
```

Start with fifty addresses, read the verdict summary, then scale. Keep
`SLEEP_SECONDS` at 5 or higher.

---

## If you would rather I did all of this without you clicking

DNS is the only part that needs your account, and it needs it because Squarespace
has no DNS API. Move the zone to Cloudflare (free, ten minutes, no downtime if the
records are copied first), create a scoped API token limited to that one zone, and
every future DNS change becomes something I make directly and verify in the same
session. Same for the host: a Hetzner or Vultr API token and I provision the
instance, set the PTR, install, preflight and run the first batch end to end.

Your call. Until then the records above are exact and `check-dns.sh` tells you
whether you got them right.
