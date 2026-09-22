# check-if-email-exists (Reacher)

Open source email verification: syntax, MX, disposable/role detection, and an SMTP
probe that checks deliverability without sending mail.

Upstream: https://github.com/reacherhq/check-if-email-exists (AGPL-3.0)

## Install

```bash
./install.sh            # builds and installs the CLI into ~/.local/bin
./install.sh --backend  # also builds the reacher_backend HTTP server
```

Requires a Rust toolchain plus perl, cc, make and pkg-config. The release build uses
LTO and compiles roughly 500 crates, so budget 10 to 20 minutes on a small machine.

## Configure the identity (do this before any real run)

```bash
cp config.env.example config.env   # gitignored
```

Set `FROM_EMAIL` and `HELLO_NAME` to the verification subdomain, not to
amplifierhealth.com. See `dns/squarespace-records.md` for the exact DNS records
and for why the identity is separated.

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
check_if_email_exists --from-email probe@verify.amplifierhealth.com \
                      --hello-name mail.verify.amplifierhealth.com \
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
