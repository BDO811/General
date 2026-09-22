#!/usr/bin/env python3
"""
Find and confirm an executive's email address empirically.

Replaces guessing a pattern and hoping. Generates the likely addresses for a
person at a domain, tests each against MillionVerifier, and stops at the first
one the receiving mail server accepts.

    ./verify_email.py --first Sarah --last Chen --domain acme.com
    ./verify_email.py --email sarah@acme.com          # check one broker-supplied address

Needs only Python 3 and a MillionVerifier key in MV_API_KEY, or in
~/.millionverifier_key.

Exit codes:  0 confirmed   2 catch-all, cannot discriminate   3 none found   1 error
"""

import argparse
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.millionverifier.com/api/v3/"
CREDITS = "https://api.millionverifier.com/api/v3/credits"


def load_key():
    key = os.environ.get("MV_API_KEY", "").strip()
    if key:
        return key
    path = os.path.expanduser("~/.millionverifier_key")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    return ""


def slug(s):
    """Strip accents and punctuation: O'Brien -> obrien, Muller -> muller."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum())


def candidates(first, last, domain):
    """Likely patterns, most common at venture-backed companies first."""
    f, l = slug(first), slug(last)
    if not domain or not (f or l):
        return []

    if f and l:
        pats = [f, f"{f}.{l}", f"{f[0]}{l}", f"{f}{l[0]}", f"{f}_{l}",
                f"{f[0]}.{l}", l, f"{f}{l}"]
    else:
        # Only one name known. Nothing else can be constructed honestly.
        pats = [f or l]

    out, seen = [], set()
    for p in pats:
        addr = f"{p}@{domain}"
        if addr not in seen:
            seen.add(addr)
            out.append(addr)
    return out


def verify(email, key, timeout=30):
    url = API + "?" + urllib.parse.urlencode({"api": key, "email": email, "timeout": 20})
    req = urllib.request.Request(url, headers={"User-Agent": "amplifier-outbound/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def balance(key):
    try:
        url = CREDITS + "?" + urllib.parse.urlencode({"api": key})
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.load(r).get("credits")
    except Exception:
        return None


def fatal(d):
    """MillionVerifier answers a bad key or a blocked account with HTTP 200."""
    if (d.get("result") or "").lower() != "error":
        return None
    msg = (d.get("error") or "").strip() or "unspecified provider error"
    return msg


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--first", default="")
    ap.add_argument("--last", default="")
    ap.add_argument("--domain", default="")
    ap.add_argument("--email", default="", help="verify one specific address instead")
    ap.add_argument("--max", type=int, default=6, help="most candidates to try")
    ap.add_argument("--json", action="store_true", help="machine readable output only")
    a = ap.parse_args()

    key = load_key()
    if not key:
        print("No API key. Set MV_API_KEY or write it to ~/.millionverifier_key",
              file=sys.stderr)
        return 1

    if a.email:
        tries = [a.email.strip().lower()]
    elif a.domain and (a.first or a.last):
        tries = candidates(a.first, a.last, a.domain.strip().lower())[:a.max]
    else:
        print("Give --email, or --domain with --first and --last", file=sys.stderr)
        return 1
    if not tries:
        print("No candidates could be built from those inputs", file=sys.stderr)
        return 1

    results, confirmed, catchall = [], None, False

    for i, email in enumerate(tries):
        if i:
            time.sleep(0.5)
        try:
            raw = verify(email, key)
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code} from MillionVerifier", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"request failed: {e}", file=sys.stderr)
            return 1

        err = fatal(raw)
        if err:
            print(f"provider error: {err}", file=sys.stderr)
            if "abuse" in err.lower():
                print("  The account is flagged. Check the MillionVerifier dashboard;"
                      "\n  free credits may not permit API use on this plan.", file=sys.stderr)
            elif "apikey" in err.lower() or "not found" in err.lower():
                print("  The API key was rejected.", file=sys.stderr)
            return 1

        result = (raw.get("result") or "").lower()
        results.append({"email": email, "result": result,
                        "subresult": raw.get("subresult", ""),
                        "role": bool(raw.get("role"))})

        if result == "catch_all":
            # Every address at this domain is accepted, so testing more tells us
            # nothing and only spends credits.
            catchall = True
            break
        if result == "ok":
            confirmed = email
            break

    left = balance(key)

    if a.json:
        print(json.dumps({"confirmed": confirmed, "catch_all": catchall,
                          "tried": results, "credits_left": left}))
    else:
        for r in results:
            mark = {"ok": "CONFIRMED", "catch_all": "catch-all",
                    "invalid": "rejected"}.get(r["result"], r["result"])
            note = "  (role account)" if r["role"] else ""
            print(f"  {r['email']:<40} {mark}{note}")
        print()
        if confirmed:
            print(f"USE: {confirmed}")
            print("Confirmed by the receiving mail server. No further sourcing needed.")
        elif catchall:
            print("CATCH-ALL DOMAIN. This domain accepts mail for any address, so")
            print("verification cannot tell a real mailbox from a typo.")
            print("Fall back to the 3-source method for this company.")
        else:
            print("NO CANDIDATE CONFIRMED. Every pattern was rejected.")
            print("Either the domain is wrong or the person uses an unusual format.")
            print("Fall back to the 3-source method for this company.")
        if left is not None:
            print(f"\n{left} credits remaining")

    return 0 if confirmed else (2 if catchall else 3)


if __name__ == "__main__":
    sys.exit(main())
