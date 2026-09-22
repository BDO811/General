# check-if-email-exists (Reacher)

Two-stage email list hygiene. Stage one is free and runs anywhere. Stage two
confirms individual mailboxes, either through a paid API or a self-hosted SMTP
probe.

Upstream: https://github.com/reacherhq/check-if-email-exists (AGPL-3.0)

## The two-stage pipeline

```bash
./prefilter.py prospects.csv                    # stage one, free, no setup
./verify-api.py prospects.pass.txt --dry-run    # see the cost
./verify-api.py prospects.pass.txt --yes        # stage two, spends credits
```

**Stage one is free and always worth running.** Syntax, MX over DNS over HTTPS,
the public disposable blocklist and role accounts, from any machine with Python.
No port 25, no host, no domain, no account. It writes a verdict CSV and a
`.pass.txt` of survivors. Every address it catches is a credit you never spend.

**Stage two buys the one signal stage one cannot produce**, whether a specific
mailbox exists. Set `VERIFY_PROVIDER` and `VERIFY_API_KEY` in `config.env`:

| Provider | Notes |
| --- | --- |
| `millionverifier` | 500 free credits on signup, no card, pay as you go, credits never expire. See `SIGNUP.md` |
| `abstract` | 100 free credits a month, 1 request/second, monthly subscription beyond that |

Confirm a new key works before running a list. This uses exactly one credit:

```bash
./verify-api.py --test
```

Credits are money, so `verify-api.py` never verifies the same address twice (it
resumes from its own output), prints the count and estimated cost and refuses to
run without `--yes`, stops on an auth rejection rather than working through the
list, and halts the moment the provider reports credits exhausted.

Verdicts are normalised across providers to the same vocabulary the SMTP probe
uses: `safe`, `risky`, `invalid`, `unknown`. A catch-all domain returns `risky`,
not `safe`: the domain accepts everything, so nobody can confirm the mailbox.

Running your own probe host instead of buying verifications is the third option.
`COSTS.md` has the break-even. The rest of this README covers that path.

## Installing the self-hosted probe (only if you are not buying verifications)

```bash
./install.sh            # builds and installs the CLI into ~/.local/bin
./install.sh --backend  # also builds the reacher_backend HTTP server
```

Requires a Rust toolchain plus perl, cc, make and pkg-config. The release build uses
LTO and compiles roughly 500 crates, so budget 10 to 20 minutes on a small machine.

## Start here

`RUNBOOK.md` has the ordered steps. The short version: the verification identity
lives on its own domain and its own host, sharing nothing with
amplifierhealth.com, so no corporate DNS or mail setting is ever touched.

```bash
CF_API_TOKEN=... ./setup-dns-cloudflare.sh <probe-domain> <probe-ip>          # Cloudflare
./setup-dns-gcloud.sh <probe-domain> <probe-ip> <project> <zone>             # or Google Cloud DNS
./check-dns.sh probe <probe-domain> <probe-ip>                                # verify
./check-dns.sh audit amplifierhealth.com                                      # read-only
```

The probe host cannot live on Google Cloud, AWS or Azure: they block outbound
port 25. `dns/hosting-options.md` has the details and the providers that work.

## Configure the identity (do this before any real run)

```bash
cp config.env.example config.env   # gitignored
```

Set `FROM_EMAIL` and `HELLO_NAME` to the probe domain. Never to
amplifierhealth.com: probing draws blocklist attention and an isolated domain
keeps it away from Workspace and HubSpot delivery.

## Preflight

Run on the probe host, before every batch:

```bash
./preflight.sh
```

It checks port 25 egress, the public IP, PTR, forward-confirmed reverse DNS, that
the MAIL FROM domain is routable, that SPF covers the host, and then does one live
check to prove the path. It exits nonzero on any failure and tells you the record
to add.

## Single check

```bash
check_if_email_exists --from-email probe@PROBE_DOMAIN \
                      --hello-name mail.PROBE_DOMAIN \
                      target@example.com
```

Output is JSON with four blocks (`syntax`, `mx`, `smtp`, `misc`) plus a top level
`is_reachable` verdict of `safe`, `risky`, `invalid` or `unknown`.

## Batch

```bash
./verify-batch.sh prospects.csv results/run-2026-09-22
```

Takes a plain list or any CSV containing addresses, extracts and dedupes them,
shuffles so consecutive probes rarely hit the same provider, paces by
`SLEEP_SECONDS` with a longer pause every `BATCH_PAUSE_EVERY` checks, and writes
`.jsonl` (full records) plus `.csv` (email, verdict, syntax, accepts_mail,
disposable, role account, error) with a verdict summary at the end.

## HTTP backend

```bash
reacher_backend                      # listens on 0.0.0.0:8080
curl -X POST http://localhost:8080/v0/check_email \
  -H 'content-type: application/json' \
  -d '{"to_email":"someone@gmail.com"}'
```

The backend supports per-provider verification methods (headless browser flows for
Yahoo and Outlook consumer addresses) that the CLI does not. Read `LICENSING.md`
before exposing it to anything outside our own network.

## Operating notes

1. The SMTP stage needs outbound port 25. Most cloud providers (AWS, GCP, Azure)
   and most sandboxed containers block it. Without it you still get syntax, MX,
   disposable and role account signals, and `is_reachable` degrades to `unknown`.
2. To get port 25 in practice you either run on a provider that allows it, request
   an unblock, or route through a SOCKS5 proxy built for SMTP.
3. The v0.11.7 CLI does not accept the `--gmail-verif-method`, `--yahoo-verif-method`
   or `--hotmailb2c-verif-method` flags that the upstream README documents. Those
   exist only in the backend. Every CLI check is a plain SMTP probe, so consumer
   Gmail, Yahoo and Outlook addresses come back with lower confidence than they
   would from the backend.
4. Keep the pacing slow. Volume probing against one provider looks like
   reconnaissance to their abuse systems, and the penalty lands on the IP and the
   sending domain.
5. Verify lists we have a legitimate reason to hold. The tool is list hygiene for
   our own outbound, not a discovery mechanism.
6. AGPL-3.0 reaches service code exposed over a network. See `LICENSING.md`.
