# Runbook: standing up email verification on an isolated domain

This design deliberately shares nothing with amplifierhealth.com. A separate
domain, a separate host, a separate reputation. Nobody else at the company is
affected by any step here, and no change to the corporate zone is ever required.

That is not only a coordination convenience. SMTP probing attracts blocklist
attention by design. If it ever lands, it lands on a domain whose only job is
probing, and Workspace and HubSpot delivery for the whole company is untouched.

## What you do, once

Three things need your account and your card. Everything after them is mine.

### 1. Register a domain

It is an envelope sender for probes, nobody reads it, so the name does not
matter much. Checked available as of 2026-09-22:

- `mxprobe.io`
- `sendercheck.io`
- `probemail.io`
- `mailproof.io`
- `listhygiene.io`

Register at Cloudflare directly and step 2 is already done. Roughly ten dollars
a year.

### 2. Put the zone on Cloudflare and create a scoped token

Cloudflare dashboard, My Profile, API Tokens, Create Token, Edit zone DNS
template. Set Zone Resources to **this one zone only**. Not All zones.

The token can edit DNS on that single throwaway domain and nothing else. It
cannot see amplifierhealth.com, cannot read mail, cannot touch billing. That is
the whole point of scoping it.

### 3. Create the probe host

Hetzner or Vultr, smallest instance, a few dollars a month. Both allow outbound
port 25 and let you set reverse DNS yourself. Hetzner asks new accounts for a
one line unblock request for port 25 and grants it routinely.

Not Google Cloud, AWS or Azure. Google blocks outbound port 25 to anything
outside your VPC with no documented unblock path, which is fatal even though
Cloud DNS and Compute Engine PTR records both work fine. See
`dns/hosting-options.md` for the provider by provider breakdown.

DNS is a separate question from the host. If you would rather keep DNS in the
Google Cloud account you already have, use `setup-dns-gcloud.sh` instead of the
Cloudflare version. The records and the verification are identical.

Give me the token, the domain and the instance IP.

## What I do from there

### 4. Every DNS record, in one command

```bash
CF_API_TOKEN=... ./setup-dns-cloudflare.sh <probe-domain> <probe-ip>
```

Creates or updates, idempotently:

| Name | Type | Value |
| --- | --- | --- |
| `<domain>` | A | probe IP |
| `mail.<domain>` | A | probe IP |
| `<domain>` | MX 10 | `mail.<domain>` |
| `<domain>` | TXT | `v=spf1 ip4:<probe-ip> -all` |
| `_dmarc.<domain>` | TXT | `v=DMARC1; p=reject; rua=mailto:amit@amplifierhealth.com` |

`--dry-run` prints the exact payloads and sends nothing.

`p=reject` on a domain that never sends real mail costs nothing and means anyone
spoofing it gets rejected outright.

### 5. Reverse DNS

The one record Cloudflare cannot hold. In the Hetzner or Vultr console, set the
PTR for the instance IP to `mail.<domain>`. If you give me an API token for the
provider I do this too. Otherwise it is one field in their UI.

This is the single most important record for getting honest answers out of
receiving mail servers.

### 6. Verify

```bash
./check-dns.sh probe <probe-domain> <probe-ip>
```

Checks delegation, both A records, MX, SPF coverage of the exact IP, DMARC
policy, and forward-confirmed reverse DNS. Exits nonzero and names what is wrong.

### 7. Install on the host

```bash
ssh root@<probe-ip>
apt update && apt install -y git curl build-essential pkg-config perl
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
. "$HOME/.cargo/env"

git clone https://github.com/BDO811/General.git
cd General/tools/check-if-email-exists
./install.sh
cp config.env.example config.env
```

Set `FROM_EMAIL=probe@<probe-domain>` and `HELLO_NAME=mail.<probe-domain>` in
`config.env`, then:

```bash
./preflight.sh
```

Nine checks: binary, public IP, port 25 egress, PTR, forward-confirmed reverse
DNS, MAIL FROM routability, SPF, and one live verification to prove the path.
Do not run a batch until it is clean.

### 8. Make the probe address readable

Point `probe@<probe-domain>` somewhere you can see, or add a Cloudflare Email
Routing rule forwarding it to your inbox. Bounces and abuse complaints land
there, and a sender that black-holes mail is itself a spam signal.

### 9. First batch

```bash
./verify-batch.sh prospects.csv results/2026-09-22
```

Start with fifty, read the verdict summary, then scale. Keep `SLEEP_SECONDS` at
5 or above.

## What this design does not do

It does not fix the DMARC problem on amplifierhealth.com. That finding is
recorded in `dns/amplifierhealth-audit.md` with the remedy. It affects every
mailbox on the domain, so it belongs to whoever schedules changes to that zone,
and it is deliberately out of scope here.
