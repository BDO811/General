#!/usr/bin/env bash
# Create or update every DNS record the probe identity needs, on Cloudflare.
#
# Idempotent: existing records with the same name and type are updated in place,
# nothing else in the zone is read or written.
#
# Usage:
#   CF_API_TOKEN=... ./setup-dns-cloudflare.sh <probe-domain> <probe-ip> [--dry-run]
#
# The token needs Zone.DNS Edit on this one zone and nothing else.

set -uo pipefail

DOMAIN="${1:-}"
PROBE_IP="${2:-}"
DRY=0
[ "${3:-}" = "--dry-run" ] && DRY=1

[ -n "${DOMAIN}" ] && [ -n "${PROBE_IP}" ] || {
  echo "usage: CF_API_TOKEN=... $0 <probe-domain> <probe-ip> [--dry-run]" >&2; exit 2; }
printf '%s' "${PROBE_IP}" | grep -qE '^[0-9]{1,3}(\.[0-9]{1,3}){3}$' || {
  echo "probe IP '${PROBE_IP}' is not an IPv4 address" >&2; exit 2; }

REPORT_TO="${DMARC_RUA:-amit@amplifierhealth.com}"
API="https://api.cloudflare.com/client/v4"

# name type content priority
RECORDS=(
  "${DOMAIN}|A|${PROBE_IP}|"
  "mail.${DOMAIN}|A|${PROBE_IP}|"
  "${DOMAIN}|MX|mail.${DOMAIN}|10"
  "${DOMAIN}|TXT|v=spf1 ip4:${PROBE_IP} -all|"
  "_dmarc.${DOMAIN}|TXT|v=DMARC1; p=reject; rua=mailto:${REPORT_TO}|"
)

if [ "${DRY}" = "1" ]; then
  echo "dry run, zone ${DOMAIN}, probe ${PROBE_IP}"
  printf '%s\n' "${RECORDS[@]}" | python3 -c 'import json, sys
out = []
for line in sys.stdin.read().splitlines():
    if not line.strip():
        continue
    name, typ, content, prio = line.split("|", 3)
    body = {"type": typ, "name": name, "content": content, "ttl": 300}
    if prio:
        body["priority"] = int(prio)
    out.append("  PUT/POST " + json.dumps(body))
sys.stdout.write("\n".join(out) + "\n")'
  echo "  (no requests sent)"
  exit 0
fi

[ -n "${CF_API_TOKEN:-}" ] || { echo "CF_API_TOKEN is not set" >&2; exit 1; }
AUTH=(-H "Authorization: Bearer ${CF_API_TOKEN}" -H "Content-Type: application/json")

jqp() { python3 -c "import sys,json
try: d=json.load(sys.stdin)
except Exception: print(''); raise SystemExit
sys.stdout.write(str(eval(sys.argv[1], {'d': d, 'json': json}) or ''))" "$1" 2>/dev/null; }

echo "== resolving zone ${DOMAIN}"
ZRESP="$(curl -s --max-time 20 "${AUTH[@]}" "${API}/zones?name=${DOMAIN}")"
if [ "$(printf '%s' "${ZRESP}" | jqp "d.get('success')")" != "True" ]; then
  echo "  cloudflare rejected the request:" >&2
  printf '%s' "${ZRESP}" | jqp "json.dumps(d.get('errors'))" >&2; echo >&2
  exit 1
fi
ZONE_ID="$(printf '%s' "${ZRESP}" | jqp "(d.get('result') or [{}])[0].get('id')")"
[ -n "${ZONE_ID}" ] || { echo "  zone ${DOMAIN} not found on this account" >&2; exit 1; }
echo "  zone id ${ZONE_ID}"

FAILED=0
for R in "${RECORDS[@]}"; do
  IFS='|' read -r NAME TYPE CONTENT PRIO <<< "${R}"

  BODY="$(python3 -c 'import json,sys
name,typ,content,prio = sys.argv[1:5]
b = {"type": typ, "name": name, "content": content, "ttl": 300}
if prio: b["priority"] = int(prio)
print(json.dumps(b))' "${NAME}" "${TYPE}" "${CONTENT}" "${PRIO}")"

  # Find an existing record of the same name and type. For TXT, match on the
  # record prefix so the SPF record is replaced rather than duplicated.
  LIST="$(curl -s --max-time 20 "${AUTH[@]}" \
    --get "${API}/zones/${ZONE_ID}/dns_records" \
    --data-urlencode "name=${NAME}" --data-urlencode "type=${TYPE}")"
  EXISTING="$(printf '%s' "${LIST}" | python3 -c '
import sys, json
want = sys.argv[1]
try: d = json.load(sys.stdin)
except Exception: raise SystemExit
prefix = want.split("=")[0] + "=" if want.startswith(("v=spf1", "v=DMARC1")) else None
for r in d.get("result", []):
    c = (r.get("content") or "").strip(chr(34))
    if prefix is None or c.startswith(prefix):
        print(r["id"]); break' "${CONTENT}")"

  if [ -n "${EXISTING}" ]; then
    RESP="$(curl -s --max-time 20 -X PUT "${AUTH[@]}" \
      "${API}/zones/${ZONE_ID}/dns_records/${EXISTING}" --data "${BODY}")"
    ACTION="updated"
  else
    RESP="$(curl -s --max-time 20 -X POST "${AUTH[@]}" \
      "${API}/zones/${ZONE_ID}/dns_records" --data "${BODY}")"
    ACTION="created"
  fi

  if [ "$(printf '%s' "${RESP}" | jqp "d.get('success')")" = "True" ]; then
    printf '  %-9s %-6s %-28s %s\n' "${ACTION}" "${TYPE}" "${NAME}" "${CONTENT}"
  else
    printf '  FAILED    %-6s %-28s %s\n' "${TYPE}" "${NAME}" \
      "$(printf '%s' "${RESP}" | jqp "json.dumps(d.get('errors'))")"
    FAILED=$((FAILED+1))
  fi
done

echo
if [ "${FAILED}" -eq 0 ]; then
  echo "done. Now set reverse DNS on ${PROBE_IP} to mail.${DOMAIN} at your hosting"
  echo "provider, then run: ./check-dns.sh probe ${DOMAIN} ${PROBE_IP}"
else
  echo "${FAILED} record(s) failed" >&2; exit 1
fi
