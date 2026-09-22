#!/usr/bin/env bash
# Verify the DNS records this tool depends on, from anywhere.
#
# Usage:
#   ./check-dns.sh                        # check amplifierhealth.com
#   ./check-dns.sh amplifierhealth.com 1.2.3.4   # also check the probe identity
#
# Uses DNS over HTTPS so it needs nothing installed but curl and python3.

set -uo pipefail

DOMAIN="${1:-amplifierhealth.com}"
PROBE_IP="${2:-}"
SUB="verify.${DOMAIN}"
HOSTNAME_="mail.${SUB}"

PASS=0; FAIL=0
ok()  { printf '  PASS  %s\n' "$1"; PASS=$((PASS+1)); }
bad() { printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); }

dns() {
  curl -s --max-time 10 "https://dns.google/resolve?name=$1&type=$2" \
    | python3 -c 'import sys,json
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
for a in d.get("Answer",[]):
    print(a.get("data","").strip(chr(34)))' 2>/dev/null
}

echo "== corporate domain: ${DOMAIN}"

SPF="$(dns "${DOMAIN}" TXT | grep -i '^v=spf1' | head -1)"
if [ -n "${SPF}" ]; then ok "SPF present: ${SPF}"; else bad "no SPF record"; fi

DKIM="$(dns "google._domainkey.${DOMAIN}" TXT | head -1)"
if [ -n "${DKIM}" ]; then ok "Workspace DKIM present"; else bad "no google._domainkey record"; fi

DMARC="$(dns "_dmarc.${DOMAIN}" TXT | grep -i '^v=DMARC1' | head -1)"
if [ -z "${DMARC}" ]; then
  bad "no DMARC record"
else
  RUA="$(printf '%s' "${DMARC}" | grep -oE 'rua=mailto:[^;[:space:]]+' | sed 's/rua=mailto://')"
  POLICY="$(printf '%s' "${DMARC}" | grep -oE 'p=[a-z]+' | head -1 | cut -d= -f2)"
  if [ -z "${RUA}" ]; then
    bad "DMARC has no rua address, no reports are collected"
  else
    RUA_DOMAIN="${RUA##*@}"
    if [ "${RUA_DOMAIN}" = "${DOMAIN}" ]; then
      ok "DMARC reports go to ${RUA}, a domain we control"
    else
      AUTH="$(dns "${DOMAIN}._report._dmarc.${RUA_DOMAIN}" TXT | head -1)"
      if [ -n "${AUTH}" ]; then
        bad "DMARC reports go to third party ${RUA} (authorized, but we see nothing)"
      else
        bad "DMARC reports go to ${RUA} and ${RUA_DOMAIN} has no authorization record: reports are DROPPED by every receiver"
      fi
    fi
  fi
  case "${POLICY}" in
    reject)     ok "DMARC policy p=reject" ;;
    quarantine) ok "DMARC policy p=quarantine (tighten to reject once clean)" ;;
    none)       bad "DMARC policy p=none, nothing is enforced, the domain is spoofable" ;;
    *)          bad "DMARC policy unreadable: ${DMARC}" ;;
  esac
fi

echo "== verification identity: ${SUB}"

VA="$(dns "${SUB}" A | head -1)"
HA="$(dns "${HOSTNAME_}" A | head -1)"
VMX="$(dns "${SUB}" MX | head -1)"
VSPF="$(dns "${SUB}" TXT | grep -i '^v=spf1' | head -1)"

if [ -z "${PROBE_IP}" ]; then
  if [ -z "${VA}${HA}${VMX}${VSPF}" ]; then
    echo "  SKIP  not configured yet. Re-run with the probe host IP once you have one:"
    echo "        ./check-dns.sh ${DOMAIN} PROBE_IP"
  else
    ok "records exist: A=${VA:-none} mail=${HA:-none} MX=${VMX:-none}"
    echo "  NOTE  pass the probe IP to verify they point at the right host"
  fi
else
  [ "${VA}" = "${PROBE_IP}" ] && ok "${SUB} A -> ${PROBE_IP}" || bad "${SUB} A is '${VA:-missing}', expected ${PROBE_IP}"
  [ "${HA}" = "${PROBE_IP}" ] && ok "${HOSTNAME_} A -> ${PROBE_IP}" || bad "${HOSTNAME_} A is '${HA:-missing}', expected ${PROBE_IP}"
  [ -n "${VMX}" ] && ok "${SUB} MX -> ${VMX}" || bad "${SUB} has no MX record, bounces cannot route"
  if printf '%s' "${VSPF}" | grep -qF "ip4:${PROBE_IP}"; then
    ok "${SUB} SPF covers ${PROBE_IP}"
  else
    bad "${SUB} SPF is '${VSPF:-missing}', must contain ip4:${PROBE_IP}"
  fi
  REV="$(printf '%s' "${PROBE_IP}" | awk -F. '{print $4"."$3"."$2"."$1".in-addr.arpa"}')"
  PTR="$(dns "${REV}" PTR | head -1)"; PTR="${PTR%.}"
  if [ "${PTR}" = "${HOSTNAME_}" ]; then
    ok "PTR ${PROBE_IP} -> ${PTR}"
  else
    bad "PTR is '${PTR:-missing}', expected ${HOSTNAME_} (set this at the hosting provider, not in DNS)"
  fi
fi

echo
printf 'dns check: %d pass, %d fail\n' "${PASS}" "${FAIL}"
[ "${FAIL}" -eq 0 ] || exit 1
