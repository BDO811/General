#!/usr/bin/env bash
# Verify DNS for the verification probe, or audit a corporate domain read-only.
#
#   ./check-dns.sh probe <probe-domain> [PROBE_IP]
#   ./check-dns.sh audit <corporate-domain>
#
# Uses DNS over HTTPS, so it needs nothing installed but curl and python3.

set -uo pipefail

MODE="${1:-}"
DOMAIN="${2:-}"
PROBE_IP="${3:-}"

usage() { echo "usage: $0 probe <probe-domain> [PROBE_IP] | $0 audit <corporate-domain>" >&2; exit 2; }
[ -n "${MODE}" ] && [ -n "${DOMAIN}" ] || usage

PASS=0; FAIL=0; NOTE=0
ok()   { printf '  PASS  %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); }
note() { printf '  NOTE  %s\n' "$1"; NOTE=$((NOTE+1)); }

dns() {
  curl -s --max-time 10 "https://dns.google/resolve?name=$1&type=$2" \
    | python3 -c 'import sys,json
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
for a in d.get("Answer",[]):
    print(a.get("data","").strip(chr(34)))' 2>/dev/null
}

case "${MODE}" in

probe)
  HOSTNAME_="mail.${DOMAIN}"
  echo "== probe domain: ${DOMAIN}"

  NS="$(dns "${DOMAIN}" NS | head -2 | tr '\n' ' ')"
  if [ -n "${NS}" ]; then ok "delegated: ${NS}"; else bad "${DOMAIN} has no nameservers, is it registered?"; fi

  A="$(dns "${DOMAIN}" A | head -1)"
  HA="$(dns "${HOSTNAME_}" A | head -1)"
  MX="$(dns "${DOMAIN}" MX | head -1)"
  SPF="$(dns "${DOMAIN}" TXT | grep -i '^v=spf1' | head -1)"
  DMARC="$(dns "_dmarc.${DOMAIN}" TXT | grep -i '^v=DMARC1' | head -1)"

  if [ -z "${PROBE_IP}" ]; then
    [ -n "${A}" ]  && note "apex A -> ${A} (pass the probe IP to verify)" || bad "no apex A record"
    [ -n "${HA}" ] && note "${HOSTNAME_} A -> ${HA}"                      || bad "no A record for ${HOSTNAME_}"
  else
    [ "${A}"  = "${PROBE_IP}" ] && ok "apex A -> ${PROBE_IP}"        || bad "apex A is '${A:-missing}', expected ${PROBE_IP}"
    [ "${HA}" = "${PROBE_IP}" ] && ok "${HOSTNAME_} A -> ${PROBE_IP}" || bad "${HOSTNAME_} A is '${HA:-missing}', expected ${PROBE_IP}"
  fi

  [ -n "${MX}" ] && ok "MX -> ${MX}" || bad "no MX record, bounces cannot route and receivers reject unroutable senders"

  if [ -z "${SPF}" ]; then
    bad "no SPF record. Needs: v=spf1 ip4:${PROBE_IP:-PROBE_IP} -all"
  elif [ -n "${PROBE_IP}" ] && printf '%s' "${SPF}" | grep -qF "ip4:${PROBE_IP}"; then
    ok "SPF covers ${PROBE_IP}"
  elif [ -z "${PROBE_IP}" ]; then
    note "SPF: ${SPF}"
  else
    bad "SPF does not list ${PROBE_IP}: ${SPF}"
  fi

  if [ -z "${DMARC}" ]; then
    bad "no DMARC record on the probe domain"
  else
    case "${DMARC}" in
      *p=reject*) ok "DMARC p=reject" ;;
      *)          note "DMARC is '${DMARC}', p=reject is preferred on a domain that never sends real mail" ;;
    esac
  fi

  if [ -n "${PROBE_IP}" ]; then
    REV="$(printf '%s' "${PROBE_IP}" | awk -F. '{print $4"."$3"."$2"."$1".in-addr.arpa"}')"
    PTR="$(dns "${REV}" PTR | head -1)"; PTR="${PTR%.}"
    if [ "${PTR}" = "${HOSTNAME_}" ]; then
      ok "PTR ${PROBE_IP} -> ${PTR}"
    else
      bad "PTR is '${PTR:-missing}', expected ${HOSTNAME_}. Set this at the hosting provider, not in DNS."
    fi
  else
    note "skipped PTR, no probe IP given"
  fi
  ;;

audit)
  echo "== read-only audit: ${DOMAIN} (this script never changes anything)"
  SPF="$(dns "${DOMAIN}" TXT | grep -i '^v=spf1' | head -1)"
  [ -n "${SPF}" ] && ok "SPF: ${SPF}" || bad "no SPF record"

  DKIM="$(dns "google._domainkey.${DOMAIN}" TXT | head -1)"
  [ -n "${DKIM}" ] && ok "Workspace DKIM present" || note "no google._domainkey record"

  DMARC="$(dns "_dmarc.${DOMAIN}" TXT | grep -i '^v=DMARC1' | head -1)"
  if [ -z "${DMARC}" ]; then
    bad "no DMARC record"
  else
    RUA="$(printf '%s' "${DMARC}" | grep -oE 'rua=mailto:[^;[:space:]]+' | sed 's/rua=mailto://')"
    POLICY="$(printf '%s' "${DMARC}" | grep -oE 'p=[a-z]+' | head -1 | cut -d= -f2)"
    if [ -z "${RUA}" ]; then
      bad "DMARC has no rua address, no reports are collected"
    elif [ "${RUA##*@}" = "${DOMAIN}" ]; then
      ok "DMARC reports go to ${RUA}"
    else
      AUTH="$(dns "${DOMAIN}._report._dmarc.${RUA##*@}" TXT | head -1)"
      if [ -n "${AUTH}" ]; then
        bad "DMARC reports go to third party ${RUA}"
      else
        bad "DMARC reports go to ${RUA}, and ${RUA##*@} publishes no authorization record: every receiver DROPS them"
      fi
    fi
    case "${POLICY}" in
      reject)     ok "policy p=reject" ;;
      quarantine) ok "policy p=quarantine" ;;
      none)       bad "policy p=none, nothing enforced, the domain is spoofable" ;;
      *)          bad "policy unreadable: ${DMARC}" ;;
    esac
  fi
  echo
  echo "  Findings here belong to whoever owns this domain's DNS. Nothing in this"
  echo "  toolchain touches it."
  ;;

*) usage ;;
esac

echo
printf '%s: %d pass, %d note, %d fail\n' "${MODE}" "${PASS}" "${NOTE}" "${FAIL}"
[ "${FAIL}" -eq 0 ] || exit 1
