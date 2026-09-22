#!/usr/bin/env bash
# Preflight for the email verification probe host.
#
# Run this ON the host that will do the verifying, before any batch. It checks
# the seven things that decide whether an SMTP probe gets an honest answer or a
# greylist, then does one live check to prove the path end to end.
#
# Usage: ./preflight.sh [test-address]

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "${HERE}/config.env" ] && . "${HERE}/config.env"

FROM_EMAIL="${FROM_EMAIL:-}"
HELLO_NAME="${HELLO_NAME:-}"
TEST_EMAIL="${1:-support@github.com}"

PASS=0; FAIL=0; WARN=0
ok()   { printf '  PASS  %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); }
warn() { printf '  WARN  %s\n' "$1"; WARN=$((WARN+1)); }

# DNS over HTTPS so this works without dig installed.
dns() { # dns <name> <type> -> one record per line
  curl -s --max-time 10 "https://dns.google/resolve?name=$1&type=$2" \
    | python3 -c 'import sys,json
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
for a in d.get("Answer",[]):
    print(a.get("data","").strip(chr(34)))' 2>/dev/null
}

echo "== 1. config"
if [ -z "${FROM_EMAIL}" ] || [ -z "${HELLO_NAME}" ]; then
  bad "FROM_EMAIL and HELLO_NAME must be set (copy config.env.example to config.env)"
  echo; echo "Cannot continue without a configured identity."; exit 1
fi
ok "FROM_EMAIL=${FROM_EMAIL}  HELLO_NAME=${HELLO_NAME}"
MAIL_FROM_DOMAIN="${FROM_EMAIL##*@}"

echo "== 2. binary"
if command -v check_if_email_exists >/dev/null; then
  ok "check_if_email_exists $(check_if_email_exists --version 2>&1 | awk '{print $2}')"
else
  bad "check_if_email_exists not on PATH (run ./install.sh)"
fi

echo "== 3. public IP"
PUBIP="$(curl -s --max-time 10 https://api.ipify.org)"
if [ -n "${PUBIP}" ]; then ok "public IP ${PUBIP}"; else bad "could not determine public IP"; fi

echo "== 4. outbound port 25"
if timeout 12 bash -c 'exec 3<>/dev/tcp/gmail-smtp-in.l.google.com/25 && head -1 <&3' >/dev/null 2>&1; then
  ok "port 25 egress open"
else
  if [ -n "${PROXY_HOST:-}" ]; then
    warn "port 25 blocked, but PROXY_HOST is set. Verification will route through the proxy."
  else
    bad "port 25 egress blocked and no PROXY_HOST configured. SMTP stage cannot run."
  fi
fi

echo "== 5. reverse DNS (PTR)"
if [ -n "${PUBIP}" ]; then
  REV="$(printf '%s' "${PUBIP}" | awk -F. '{print $4"."$3"."$2"."$1".in-addr.arpa"}')"
  PTR="$(dns "${REV}" PTR | head -1)"; PTR="${PTR%.}"
  if [ -z "${PTR}" ]; then
    bad "no PTR record for ${PUBIP}. Set it at your hosting provider to ${HELLO_NAME}"
  elif [ "${PTR}" = "${HELLO_NAME}" ]; then
    ok "PTR ${PUBIP} -> ${PTR}, matches HELLO_NAME"
  else
    bad "PTR is ${PTR} but HELLO_NAME is ${HELLO_NAME}. They must match."
  fi
fi

echo "== 6. forward-confirmed reverse DNS"
FWD="$(dns "${HELLO_NAME}" A | head -1)"
if [ -z "${FWD}" ]; then
  bad "${HELLO_NAME} has no A record. Add one pointing to ${PUBIP:-the probe host}."
elif [ "${FWD}" = "${PUBIP}" ]; then
  ok "${HELLO_NAME} A -> ${FWD}, matches public IP"
else
  bad "${HELLO_NAME} A -> ${FWD} but public IP is ${PUBIP}"
fi

echo "== 7. MAIL FROM domain is routable"
MFA="$(dns "${MAIL_FROM_DOMAIN}" MX | head -1)"
[ -z "${MFA}" ] && MFA="$(dns "${MAIL_FROM_DOMAIN}" A | head -1)"
if [ -n "${MFA}" ]; then
  ok "${MAIL_FROM_DOMAIN} resolves (${MFA}), bounces can route"
else
  bad "${MAIL_FROM_DOMAIN} has no MX or A record. Receivers reject unroutable senders."
fi

echo "== 8. SPF covers the probe host"
SPF="$(dns "${MAIL_FROM_DOMAIN}" TXT | grep -i '^v=spf1' | head -1)"
if [ -z "${SPF}" ]; then
  bad "no SPF record on ${MAIL_FROM_DOMAIN}. Add: v=spf1 ip4:${PUBIP:-YOUR_IP} -all"
elif [ -n "${PUBIP}" ] && printf '%s' "${SPF}" | grep -qF "ip4:${PUBIP}"; then
  ok "SPF lists ${PUBIP}"
else
  bad "SPF on ${MAIL_FROM_DOMAIN} does not list ${PUBIP:-the probe host}: ${SPF}"
fi

echo "== 9. live check against ${TEST_EMAIL}"
if command -v check_if_email_exists >/dev/null; then
  OUT="$(timeout 120 check_if_email_exists \
          --from-email "${FROM_EMAIL}" \
          --hello-name "${HELLO_NAME}" \
          ${SMTP_PORT:+--smtp-port "${SMTP_PORT}"} \
          ${PROXY_HOST:+--proxy-host "${PROXY_HOST}" --proxy-port "${PROXY_PORT:-1080}"} \
          "${TEST_EMAIL}" 2>/dev/null)"
  VERDICT="$(printf '%s' "${OUT}" | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    print("no-output"); raise SystemExit
print(d.get("is_reachable","?"), "| smtp:", json.dumps(d.get("smtp",{}))[:120])' 2>/dev/null)"
  case "${VERDICT}" in
    safe*|risky*|invalid*) ok "live check returned: ${VERDICT}" ;;
    *)                     bad "live check returned: ${VERDICT:-nothing}" ;;
  esac
else
  warn "skipped, binary missing"
fi

echo
printf 'preflight: %d pass, %d warn, %d fail\n' "${PASS}" "${WARN}" "${FAIL}"
[ "${FAIL}" -eq 0 ] || { echo "Fix the failures above before running a batch."; exit 1; }
