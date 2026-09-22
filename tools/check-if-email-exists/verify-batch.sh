#!/usr/bin/env bash
# Batch email verification with the Reacher CLI.
#
# Usage:
#   ./verify-batch.sh addresses.txt            # one address per line, or CSV with an email column
#   ./verify-batch.sh addresses.txt out_prefix
#
# Writes:
#   <prefix>.jsonl  full JSON per address
#   <prefix>.csv    email,is_reachable,valid_syntax,accepts_mail,is_disposable,is_role,error
#
# Addresses are shuffled so consecutive probes rarely hit the same provider.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "${HERE}/config.env" ] && . "${HERE}/config.env"

IN="${1:-}"
PREFIX="${2:-verify-$(date +%Y%m%d-%H%M%S)}"
[ -n "${IN}" ] && [ -f "${IN}" ] || { echo "usage: $0 <addresses-file> [output-prefix]" >&2; exit 2; }
command -v check_if_email_exists >/dev/null || { echo "check_if_email_exists not on PATH (run ./install.sh)" >&2; exit 1; }

FROM_EMAIL="${FROM_EMAIL:-}"
HELLO_NAME="${HELLO_NAME:-}"
[ -n "${FROM_EMAIL}" ] && [ -n "${HELLO_NAME}" ] || {
  echo "FROM_EMAIL and HELLO_NAME must be set in config.env. Running without them gets you greylisted." >&2
  exit 1
}

SLEEP_SECONDS="${SLEEP_SECONDS:-5}"
BATCH_PAUSE_EVERY="${BATCH_PAUSE_EVERY:-50}"
BATCH_PAUSE_SECONDS="${BATCH_PAUSE_SECONDS:-60}"

JSONL="${PREFIX}.jsonl"
CSV="${PREFIX}.csv"
: > "${JSONL}"
echo "email,is_reachable,valid_syntax,accepts_mail,is_disposable,is_role,error" > "${CSV}"

# Extract addresses from a plain list or a CSV, dedupe, shuffle.
ADDRS="$(python3 - "${IN}" <<'PY'
import re, sys, random
seen, out = set(), []
pat = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
with open(sys.argv[1], encoding='utf-8', errors='replace') as fh:
    for line in fh:
        for m in pat.findall(line):
            a = m.strip().lower()
            if a not in seen:
                seen.add(a); out.append(a)
random.shuffle(out)
print('\n'.join(out))
PY
)"

TOTAL="$(printf '%s\n' "${ADDRS}" | grep -c . || true)"
[ "${TOTAL}" -gt 0 ] || { echo "no addresses found in ${IN}" >&2; exit 1; }
echo "verifying ${TOTAL} addresses as ${FROM_EMAIL} (EHLO ${HELLO_NAME}), ${SLEEP_SECONDS}s apart"

N=0
while IFS= read -r ADDR; do
  [ -n "${ADDR}" ] || continue
  N=$((N+1))
  OUT="$(timeout 180 check_if_email_exists \
          --from-email "${FROM_EMAIL}" \
          --hello-name "${HELLO_NAME}" \
          ${SMTP_PORT:+--smtp-port "${SMTP_PORT}"} \
          ${PROXY_HOST:+--proxy-host "${PROXY_HOST}" --proxy-port "${PROXY_PORT:-1080}"} \
          ${PROXY_USERNAME:+--proxy-username "${PROXY_USERNAME}"} \
          ${PROXY_PASSWORD:+--proxy-password "${PROXY_PASSWORD}"} \
          "${ADDR}" 2>/dev/null)"

  printf '%s\n' "${OUT:-{\"input\":\"${ADDR}\",\"error\":\"timeout or no output\"}}" \
    | tr -d '\n' >> "${JSONL}"
  printf '\n' >> "${JSONL}"

  LINE="$(printf '%s' "${OUT}" | python3 -c '
import sys, json, csv
w = csv.writer(sys.stdout, lineterminator="")
try:
    d = json.load(sys.stdin)
except Exception:
    raise SystemExit
smtp = d.get("smtp") or {}
err = ""
if isinstance(smtp, dict) and isinstance(smtp.get("error"), dict):
    err = smtp["error"].get("message", "")[:120]
w.writerow([
    d.get("input",""),
    d.get("is_reachable",""),
    (d.get("syntax") or {}).get("is_valid_syntax",""),
    (d.get("mx") or {}).get("accepts_mail",""),
    (d.get("misc") or {}).get("is_disposable",""),
    (d.get("misc") or {}).get("is_role_account",""),
    err,
])' 2>/dev/null)"
  printf '%s\n' "${LINE:-${ADDR},error,,,,,no output}" >> "${CSV}"
  printf '  [%d/%d] %s\n' "${N}" "${TOTAL}" "${LINE:-${ADDR} (no output)}"

  if [ "${N}" -lt "${TOTAL}" ]; then
    if [ "${BATCH_PAUSE_EVERY}" -gt 0 ] && [ $((N % BATCH_PAUSE_EVERY)) -eq 0 ]; then
      echo "  ... pausing ${BATCH_PAUSE_SECONDS}s after ${N}"
      sleep "${BATCH_PAUSE_SECONDS}"
    else
      sleep "${SLEEP_SECONDS}"
    fi
  fi
done <<< "${ADDRS}"

echo
echo "wrote ${JSONL} and ${CSV}"
python3 - "${CSV}" <<'PY'
import csv, sys, collections
rows = list(csv.DictReader(open(sys.argv[1])))
c = collections.Counter(r["is_reachable"] for r in rows)
print("summary:", ", ".join(f"{k or 'blank'}={v}" for k, v in c.most_common()))
PY
