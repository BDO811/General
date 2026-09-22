#!/usr/bin/env python3
"""
Stage one list hygiene. Free, runs anywhere, no port 25 and no probe host.

Checks syntax, MX, disposable domains and role accounts. These are the cheap
signals, and on a scraped or purchased list they remove a large share of the
addresses before anything paid or rate limited touches them.

What it cannot tell you is whether a specific mailbox exists. That needs the
SMTP probe in verify-batch.sh, or a paid API. Feed it only the survivors.

Usage:
    ./prefilter.py prospects.csv                 # writes prospects.stage1.csv and .pass.txt
    ./prefilter.py prospects.csv out_prefix
"""

import csv
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ADDR = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

ROLE_PREFIXES = {
    "abuse", "admin", "administrator", "all", "billing", "career", "careers",
    "compliance", "contact", "customerservice", "dev", "enquiries", "enquiry",
    "feedback", "finance", "ftp", "help", "hello", "hi", "hr", "info", "inquiries",
    "inquiry", "investors", "it", "jobs", "legal", "mail", "marketing", "media",
    "news", "newsletter", "noreply", "no-reply", "office", "orders", "postmaster",
    "press", "privacy", "recruiting", "sales", "security", "服务", "service",
    "signup", "subscribe", "support", "team", "webmaster", "welcome",
}

DISPOSABLE_URL = (
    "https://raw.githubusercontent.com/disposable-email-domains/"
    "disposable-email-domains/master/disposable_email_blocklist.conf"
)
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".disposable-domains.txt")


def load_disposable():
    """Fetch the public disposable domain list, cached on disk."""
    if os.path.exists(CACHE) and os.path.getsize(CACHE) > 1000:
        with open(CACHE, encoding="utf-8") as fh:
            return {l.strip().lower() for l in fh if l.strip()}
    try:
        with urllib.request.urlopen(DISPOSABLE_URL, timeout=30) as r:
            text = r.read().decode("utf-8", "replace")
        with open(CACHE, "w", encoding="utf-8") as fh:
            fh.write(text)
        return {l.strip().lower() for l in text.splitlines() if l.strip()}
    except Exception as exc:
        print(f"  warning: could not fetch disposable list ({exc}), skipping that check",
              file=sys.stderr)
        return set()


_mx_cache = {}


def has_mx(domain):
    """Resolve MX over DNS over HTTPS. Falls back to A, which accepts mail per RFC 5321."""
    if domain in _mx_cache:
        return _mx_cache[domain]
    result = None
    for rtype in ("MX", "A"):
        try:
            url = f"https://dns.google/resolve?name={urllib.parse.quote(domain)}&type={rtype}"
            with urllib.request.urlopen(url, timeout=10) as r:
                d = json.load(r)
            if d.get("Answer"):
                result = rtype
                break
            if d.get("Status") == 3:  # NXDOMAIN
                result = None
                break
        except Exception:
            continue
    _mx_cache[domain] = result
    return result


def classify(addr, disposable):
    local, _, domain = addr.rpartition("@")
    domain = domain.lower()

    if not ADDR.fullmatch(addr) or ".." in addr or addr.startswith("."):
        return "invalid", "bad syntax"
    if domain in disposable:
        return "invalid", "disposable domain"
    mx = has_mx(domain)
    if mx is None:
        return "invalid", "domain does not accept mail"

    # Role accounts are NOT dropped. For B2B outreach press@, sales@, bd@ and
    # partnerships@ are often the intended contact. They are labelled so you can
    # decide, and excluded only with --no-role.
    if local.lower() in ROLE_PREFIXES:
        return "role", "role account, deliverable but not a person"
    if mx == "A":
        return "risky", "no MX, A record fallback only"
    return "unknown", "passed stage one, mailbox not yet verified"


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not argv:
        print("usage: prefilter.py <addresses-file> [output-prefix] [--no-role]",
              file=sys.stderr)
        return 2
    path = argv[0]
    prefix = argv[1] if len(argv) > 1 else os.path.splitext(path)[0]
    keep_role = "--no-role" not in flags

    seen, addrs = set(), []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            for m in ADDR.findall(line):
                a = m.strip().lower()
                if a not in seen:
                    seen.add(a)
                    addrs.append(a)
    if not addrs:
        print(f"no addresses found in {path}", file=sys.stderr)
        return 1

    print(f"stage one on {len(addrs)} unique addresses")
    disposable = load_disposable()
    if disposable:
        print(f"  disposable list: {len(disposable)} domains")

    # Warm the MX cache one domain at a time, in parallel.
    domains = sorted({a.rpartition('@')[2].lower() for a in addrs})
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(has_mx, domains))
    print(f"  resolved {len(domains)} domains")

    rows = [(a, *classify(a, disposable)) for a in addrs]

    out_csv = f"{prefix}.stage1.csv"
    out_pass = f"{prefix}.pass.txt"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["email", "stage1", "reason"])
        w.writerows(rows)
    carry = {"unknown", "risky"} | ({"role"} if keep_role else set())
    survivors = [r[0] for r in rows if r[1] in carry]
    with open(out_pass, "w", encoding="utf-8") as fh:
        fh.write("\n".join(survivors) + ("\n" if survivors else ""))

    counts = {}
    for _, verdict, reason in rows:
        counts[f"{verdict}: {reason}"] = counts.get(f"{verdict}: {reason}", 0) + 1
    print()
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:6d}  {k}")
    dropped = sum(1 for r in rows if r[1] == "invalid")
    roles = sum(1 for r in rows if r[1] == "role")
    print()
    print(f"  {dropped} of {len(addrs)} ({100*dropped/len(addrs):.0f}%) "
          f"dropped as invalid, at zero cost")
    if roles and keep_role:
        print(f"  {roles} role accounts kept for stage two, pass --no-role to exclude them")
    elif roles:
        print(f"  {roles} role accounts excluded by --no-role")
    print(f"  wrote {out_csv} and {out_pass}")
    print(f"  {len(survivors)} addresses remain for stage two")
    return 0


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main())
