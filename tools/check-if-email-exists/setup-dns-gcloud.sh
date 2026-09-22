#!/usr/bin/env bash
# Create or update every DNS record the probe identity needs, in Google Cloud DNS.
#
# Same contract as setup-dns-cloudflare.sh, for an existing GCP account.
# Idempotent: an existing record of the same name and type is replaced.
#
# Usage:
#   ./setup-dns-gcloud.sh <probe-domain> <probe-ip> <gcp-project> <zone-name> [--dry-run]
#
# Auth: an already authenticated gcloud, or a service account key with
# roles/dns.admin on this project only:
#   gcloud auth activate-service-account --key-file=key.json
#
# The zone must exist and the registrar's nameservers must point at it:
#   gcloud dns managed-zones create <zone-name> --dns-name=<probe-domain>. \
#     --description="email verification probe" --project=<gcp-project>
#   gcloud dns managed-zones describe <zone-name> --project=<gcp-project> \
#     --format='value(nameServers)'

set -uo pipefail

DOMAIN="${1:-}"; PROBE_IP="${2:-}"; PROJECT="${3:-}"; ZONE="${4:-}"
DRY=0; [ "${5:-}" = "--dry-run" ] && DRY=1

[ -n "${DOMAIN}" ] && [ -n "${PROBE_IP}" ] && [ -n "${PROJECT}" ] && [ -n "${ZONE}" ] || {
  echo "usage: $0 <probe-domain> <probe-ip> <gcp-project> <zone-name> [--dry-run]" >&2; exit 2; }
printf '%s' "${PROBE_IP}" | grep -qE '^[0-9]{1,3}(\.[0-9]{1,3}){3}$' || {
  echo "probe IP '${PROBE_IP}' is not an IPv4 address" >&2; exit 2; }

REPORT_TO="${DMARC_RUA:-amit@amplifierhealth.com}"

# Cloud DNS wants fully qualified names with a trailing dot, and TXT values quoted.
RECORDS=(
  "${DOMAIN}.|A|300|${PROBE_IP}"
  "mail.${DOMAIN}.|A|300|${PROBE_IP}"
  "${DOMAIN}.|MX|300|10 mail.${DOMAIN}."
  "${DOMAIN}.|TXT|300|\"v=spf1 ip4:${PROBE_IP} -all\""
  "_dmarc.${DOMAIN}.|TXT|300|\"v=DMARC1; p=reject; rua=mailto:${REPORT_TO}\""
)

if [ "${DRY}" = "1" ]; then
  echo "dry run, project ${PROJECT}, zone ${ZONE}, domain ${DOMAIN}, probe ${PROBE_IP}"
  for R in "${RECORDS[@]}"; do
    IFS='|' read -r NAME TYPE TTL DATA <<< "${R}"
    printf '  %-6s %-30s ttl=%s  %s\n' "${TYPE}" "${NAME}" "${TTL}" "${DATA}"
  done
  echo "  (no requests sent)"
  exit 0
fi

command -v gcloud >/dev/null || { echo "gcloud CLI not found" >&2; exit 1; }

if ! gcloud dns managed-zones describe "${ZONE}" --project="${PROJECT}" >/dev/null 2>&1; then
  echo "managed zone '${ZONE}' not found in project '${PROJECT}'." >&2
  echo "Create it first, see the header of this script." >&2
  exit 1
fi

FAILED=0
for R in "${RECORDS[@]}"; do
  IFS='|' read -r NAME TYPE TTL DATA <<< "${R}"

  EXISTING="$(gcloud dns record-sets list --zone="${ZONE}" --project="${PROJECT}" \
    --name="${NAME}" --type="${TYPE}" --format='value(name)' 2>/dev/null | head -1)"

  if [ -n "${EXISTING}" ]; then
    ACTION="updated"
    OUT="$(gcloud dns record-sets update "${NAME}" --zone="${ZONE}" --project="${PROJECT}" \
      --type="${TYPE}" --ttl="${TTL}" --rrdatas="${DATA}" 2>&1)"
    RC=$?
  else
    ACTION="created"
    OUT="$(gcloud dns record-sets create "${NAME}" --zone="${ZONE}" --project="${PROJECT}" \
      --type="${TYPE}" --ttl="${TTL}" --rrdatas="${DATA}" 2>&1)"
    RC=$?
  fi

  if [ "${RC}" -eq 0 ]; then
    printf '  %-9s %-6s %-30s %s\n' "${ACTION}" "${TYPE}" "${NAME}" "${DATA}"
  else
    printf '  FAILED    %-6s %-30s %s\n' "${TYPE}" "${NAME}" "$(printf '%s' "${OUT}" | head -1)"
    FAILED=$((FAILED+1))
  fi
done

echo
if [ "${FAILED}" -eq 0 ]; then
  echo "done. Set reverse DNS on ${PROBE_IP} to mail.${DOMAIN} at whoever hosts the"
  echo "probe, then run: ./check-dns.sh probe ${DOMAIN} ${PROBE_IP}"
else
  echo "${FAILED} record(s) failed" >&2; exit 1
fi
