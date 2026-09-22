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

## Use the CLI

```bash
check_if_email_exists someone@gmail.com
```

Output is JSON with four blocks: `syntax`, `mx`, `smtp`, `misc`, plus a top level
`is_reachable` verdict of `safe`, `risky`, `invalid` or `unknown`.

Useful options:

```bash
check_if_email_exists --from-email you@yourdomain.com \
                      --hello-name yourdomain.com \
                      --proxy-host 1.2.3.4 --proxy-port 1080 \
                      target@example.com
```

## Use the HTTP backend

```bash
reacher_backend                      # listens on 0.0.0.0:8080
curl -X POST http://localhost:8080/v0/check_email \
  -H 'content-type: application/json' \
  -d '{"to_email":"someone@gmail.com"}'
```

Docker is the upstream default if a daemon is available:

```bash
docker run -p 8080:8080 reacherhq/backend:latest
```

## Operating notes

1. The SMTP stage needs outbound port 25. Most cloud providers (AWS, GCP, Azure) and
   most sandboxed containers block it. Without it you still get syntax, MX, disposable
   and role account signals, and `is_reachable` degrades to `unknown`.
2. To get port 25 in practice you either request an unblock from the provider, run on a
   host that allows it, or route through a SOCKS5 proxy built for SMTP.
3. Set `--from-email` and `--hello-name` to a domain you control with matching PTR, SPF
   and DKIM. Default values get you throttled or greylisted quickly.
4. Gmail, Yahoo and Hotmail B2C need special verification methods. Gmail defaults to
   SMTP, Yahoo and Hotmail B2C default to a headless browser, which requires a
   WebDriver endpoint running.
5. Volume verification against a provider looks like probing to their abuse systems.
   Keep rate limits low and verify only lists you have a legitimate relationship with.
6. AGPL-3.0: if you expose this over a network as a service, the license reaches your
   service code. Reacher sells a commercial license if that matters.
