#!/usr/bin/env python3
"""
Stage two: mailbox verification through a paid API.

Run this on what survives prefilter.py, never on a raw list. Stage one costs
nothing and removes a large share of the addresses; every one it catches is a
credit you do not spend here.

    ./prefilter.py prospects.csv
    ./verify-api.py prospects.pass.txt

Providers (set VERIFY_PROVIDER and VERIFY_API_KEY, or use config.env):
    abstract          emailvalidation.abstractapi.com, 100 free credits a month
    millionverifier   api.millionverifier.com, cheap bulk

Credits are money, so this script:
  - never verifies the same address twice, it resumes from the output file
  - prints the count and estimated cost and stops unless you pass --yes
  - stops immediately if the provider reports credits exhausted
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Rough published rates, for the cost estimate only. Update as needed.
RATE_PER_1000 = {"abstract": 0.0, "millionverifier": 3.70}
# Free plans are rate limited hard. Seconds between requests.
MIN_INTERVAL = {"abstract": 1.1, "millionverifier": 0.1}


def load_config():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "config.env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "list-hygiene/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def check_abstract(email, key):
    url = "https://emailvalidation.abstractapi.com/v1/?" + urllib.parse.urlencode(
        {"api_key": key, "email": email})
    return get(url)


def check_millionverifier(email, key):
    url = "https://api.millionverifier.com/api/v3/?" + urllib.parse.urlencode(
        {"api": key, "email": email, "timeout": 20})
    return get(url)


def norm_abstract(d):
    """Map Abstract's response onto safe / risky / invalid / unknown.

    Handles the documented v1 flat shape, and defensively the nested shape their
    marketing pages show, in case the account is provisioned on a newer schema.
    """
    flat = d
    if "email_deliverability" in d and isinstance(d["email_deliverability"], dict):
        flat = {}
        for block in d.values():
            if isinstance(block, dict):
                flat.update(block)
        flat.setdefault("deliverability", (d["email_deliverability"] or {}).get("status"))

    def flag(name):
        v = flat.get(name)
        if isinstance(v, dict):
            return v.get("value")
        return v if isinstance(v, bool) else None

    deliver = (flat.get("deliverability") or "").upper()
    if flag("is_disposable_email"):
        return "invalid", "disposable"
    if deliver == "UNDELIVERABLE":
        return "invalid", "undeliverable"
    if deliver == "DELIVERABLE":
        if flag("is_catchall_email"):
            return "risky", "catch-all domain, cannot confirm the mailbox"
        if flag("is_role_email"):
            return "risky", "role account"
        return "safe", "deliverable"
    return "unknown", f"deliverability {deliver or 'missing'}"


def norm_millionverifier(d):
    r = (d.get("result") or "").lower()
    if r == "ok":
        return ("risky", "role account") if d.get("role") else ("safe", "deliverable")
    if r == "invalid":
        return "invalid", d.get("subresult") or "invalid"
    if r == "disposable":
        return "invalid", "disposable"
    if r == "catch_all":
        return "risky", "catch-all domain, cannot confirm the mailbox"
    if r in ("unknown", "unverified"):
        return "unknown", d.get("subresult") or r
    return "unknown", d.get("error") or r or "unrecognised response"


PROVIDERS = {
    "abstract": (check_abstract, norm_abstract),
    "millionverifier": (check_millionverifier, norm_millionverifier),
}

EXHAUSTED = ("insufficient", "credit", "quota", "limit reached", "no credits")


def fatal_abstract(d):
    err = d.get("error")
    if isinstance(err, dict):
        msg = (err.get("message") or "").lower()
        if "key" in msg or "unauthor" in msg:
            return "auth", err.get("message")
        if any(t in msg for t in EXHAUSTED):
            return "credits", err.get("message")
    return None


def fatal_millionverifier(d):
    """MillionVerifier answers HTTP 200 even for a bad key, so read the body."""
    if (d.get("result") or "").lower() != "error":
        return None
    msg = (d.get("error") or "").strip()
    low = msg.lower()
    if "apikey" in low or "api key" in low or "not found" in low:
        return "auth", msg
    if any(t in low for t in EXHAUSTED):
        return "credits", msg
    return "auth", msg or "provider returned an unspecified error"


FATAL = {"abstract": fatal_abstract, "millionverifier": fatal_millionverifier}



def self_test(email):
    """Confirm the key works, using exactly one credit."""
    provider = os.environ.get("VERIFY_PROVIDER", "").lower()
    key = os.environ.get("VERIFY_API_KEY", "")
    if provider not in PROVIDERS:
        print(f"VERIFY_PROVIDER is '{provider or 'unset'}', expected one of: "
              f"{', '.join(PROVIDERS)}", file=sys.stderr)
        return 2
    if not key:
        print("VERIFY_API_KEY is not set. Put it in config.env.", file=sys.stderr)
        return 2

    check, norm = PROVIDERS[provider]
    print(f"provider   {provider}")
    print(f"key        ...{key[-6:]}  ({len(key)} chars)")
    print(f"test       {email}   this uses one credit")
    try:
        raw = check(email, key)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        print(f"\n  HTTP {e.code}: {body or e}", file=sys.stderr)
        if e.code in (401, 403):
            print("  The key was rejected. Check you copied the Email Validation key,"
                  "\n  not a key for one of Abstract's other APIs. Each API has its own.",
                  file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n  request failed: {e}", file=sys.stderr)
        return 1

    bad = FATAL.get(provider, lambda _d: None)(raw)
    if bad:
        kind, msg = bad
        print(f"\n  {'key rejected' if kind == 'auth' else 'credits exhausted'}: {msg}",
              file=sys.stderr)
        if kind == "auth":
            print("  Check the key is for this provider and the account is active.",
                  file=sys.stderr)
        return 1

    verdict, reason = norm(raw)
    print(f"\n  verdict  {verdict}  ({reason})")
    left = raw.get("credits") if isinstance(raw, dict) else None
    if isinstance(left, int):
        print(f"  credits  {left} remaining")
    print(f"  raw      {json.dumps(raw)[:400]}")
    if verdict in ("safe", "risky", "invalid"):
        print("\n  Key works. You are ready to run a real list.")
        return 0
    print("\n  Key works but the verdict came back unknown. That can be normal for"
          "\n  this address. Try --test with a different one before concluding.")
    return 0


def main(argv):
    load_config()
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}

    if "--test" in flags:
        return self_test(args[0] if args else "support@github.com")

    if not args:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    path = args[0]
    prefix = args[1] if len(args) > 1 else os.path.splitext(path)[0] + ".verified"
    limit = None
    for f in flags:
        if f.startswith("--limit="):
            limit = int(f.split("=", 1)[1])

    provider = os.environ.get("VERIFY_PROVIDER", "").lower()
    key = os.environ.get("VERIFY_API_KEY", "")
    if provider not in PROVIDERS:
        print(f"set VERIFY_PROVIDER to one of: {', '.join(PROVIDERS)}", file=sys.stderr)
        return 2
    check, norm = PROVIDERS[provider]

    with open(path, encoding="utf-8", errors="replace") as fh:
        addrs, seen = [], set()
        for line in fh:
            a = line.strip().lower()
            if a and "@" in a and a not in seen:
                seen.add(a)
                addrs.append(a)

    jsonl, out_csv = f"{prefix}.jsonl", f"{prefix}.csv"

    # Resume: never spend a credit on an address already verified.
    done = set()
    if os.path.exists(jsonl):
        with open(jsonl, encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["email"])
                except Exception:
                    continue
    todo = [a for a in addrs if a not in done]
    if limit:
        todo = todo[:limit]

    est = len(todo) * RATE_PER_1000.get(provider, 0) / 1000
    print(f"provider   {provider}")
    print(f"input      {len(addrs)} addresses")
    if done:
        print(f"already    {len(done)} verified previously, skipping")
    print(f"to verify  {len(todo)}")
    print(f"estimated  ${est:.2f}" + ("  (free tier credits)" if est == 0 else ""))

    if not todo:
        print("nothing to do")
        return 0
    if "--dry-run" in flags:
        print("dry run, nothing sent")
        return 0
    if "--yes" not in flags:
        print("\nthis spends credits. Re-run with --yes to proceed.")
        return 1
    if not key:
        print("VERIFY_API_KEY is not set", file=sys.stderr)
        return 2

    interval = MIN_INTERVAL.get(provider, 1.0)
    counts, failures, last = {}, 0, 0.0

    with open(jsonl, "a", encoding="utf-8") as jf:
        for i, addr in enumerate(todo, 1):
            wait = interval - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.time()

            try:
                raw = check(addr, key)
                bad = FATAL.get(provider, lambda _d: None)(raw)
                if bad:
                    kind, msg = bad
                    label = ("key rejected by" if kind == "auth"
                             else "credits exhausted at")
                    print(f"\n  {label} {provider}: {msg}", file=sys.stderr)
                    print(f"  stopping with {len(todo) - i + 1} unverified",
                          file=sys.stderr)
                    break
                verdict, reason = norm(raw)
            except urllib.error.HTTPError as e:
                body = ""
                try:
                    body = e.read().decode("utf-8", "replace")[:300]
                except Exception:
                    pass
                if e.code in (401, 403):
                    print(f"\n  auth rejected by {provider}: {body or e}", file=sys.stderr)
                    return 1
                if e.code == 422 or any(t in body.lower() for t in EXHAUSTED):
                    print(f"\n  credits exhausted at {provider}, stopping with "
                          f"{len(todo) - i + 1} unverified", file=sys.stderr)
                    break
                raw, verdict, reason = {"http_error": e.code, "body": body}, "error", f"HTTP {e.code}"
                failures += 1
            except Exception as e:
                raw, verdict, reason = {"error": str(e)}, "error", str(e)[:120]
                failures += 1

            jf.write(json.dumps({"email": addr, "verdict": verdict,
                                 "reason": reason, "raw": raw}) + "\n")
            jf.flush()
            counts[verdict] = counts.get(verdict, 0) + 1
            left = raw.get("credits") if isinstance(raw, dict) else None
            tail = f"   [{left} credits left]" if isinstance(left, int) and left else ""
            print(f"  [{i}/{len(todo)}] {addr:<42} {verdict:<8} {reason}{tail}")

            if failures >= 5 and failures == i:
                print("\n  every request has failed, stopping rather than burning credits",
                      file=sys.stderr)
                break

    # Rebuild the CSV from the full jsonl so it always reflects everything done.
    rows = []
    with open(jsonl, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            rows.append([d["email"], d.get("verdict", ""), d.get("reason", "")])
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["email", "verdict", "reason"])
        w.writerows(rows)

    print()
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:6d}  {k}")
    safe = sum(1 for r in rows if r[1] == "safe")
    print(f"\n  {safe} of {len(rows)} confirmed safe to send")
    print(f"  wrote {jsonl} and {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
