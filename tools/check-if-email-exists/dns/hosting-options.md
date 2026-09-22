# Where the probe host can and cannot live

The verification probe opens a TCP connection to the recipient's MX server on
port 25 and stops at `RCPT TO`. That single requirement rules out most of the
places you would naturally reach for.

## Google Cloud and Firebase: DNS yes, probe host no

**Cloud DNS works.** It is a full API-managed zone and `setup-dns-gcloud.sh`
drives it with the same contract as the Cloudflare version. A service account
key with `roles/dns.admin` scoped to one project is the equivalent of a scoped
Cloudflare token.

**Reverse DNS works too.** Compute Engine supports configurable PTR records on a
VM's external IP through `--public-ptr` and `--public-ptr-domain`, after you
verify domain ownership. This is a genuine capability that many clouds lack.

**Port 25 does not work, and that is fatal.** Google's own documentation:

> Due to the risk of abuse, connections to destination TCP Port 25 are blocked
> when the destination is external to your VPC network. This includes using SMTP
> relay with Google Workspace.

There is no documented unblock process. The docs note only that "some projects
do not have this restriction," with no way to request it. Ports 587 and 465 are
explicitly unrestricted, which does not help: those are submission ports for
authenticated sending, and no receiving MX server accepts anonymous `RCPT TO`
probes on them. Port 25 is the only port that answers this question.

So a GCE instance gives you every prerequisite except the one the tool actually
needs.

**Firebase, Cloud Run and Cloud Functions are further out of reach.** They carry
the same port 25 block, have no stable outbound IP without Cloud NAT, and cannot
hold a PTR record at all. A request-scoped serverless runtime is also the wrong
shape for a probe that can block for two minutes on a slow MX server.

## What works

| Provider | Port 25 | Custom PTR | Notes |
| --- | --- | --- | --- |
| Hetzner | yes, after a one line request | yes | cheapest, grants routinely |
| Vultr | yes, on request | yes | fast to provision |
| OVH | yes | yes | |
| DigitalOcean | blocked by default, opened on request | yes | support ticket, often declined for new accounts |
| Google Cloud | no | yes | no unblock path |
| AWS | blocked, removable by request | via Route 53 support request | slow, requires justification |
| Azure | blocked on most subscriptions | limited | effectively no |

## The split that makes sense given what you already have

Keep DNS in Google Cloud, where you already have an account and billing. Put the
probe host on Hetzner or Vultr for a few dollars a month. The two do not need to
know about each other: Cloud DNS holds the records, the VPS holds the IP and its
PTR, and `check-dns.sh probe` verifies that they agree.

```bash
# once, to create the zone
gcloud dns managed-zones create probe-zone --dns-name=<probe-domain>. \
  --description="email verification probe" --project=<gcp-project>
gcloud dns managed-zones describe probe-zone --project=<gcp-project> \
  --format='value(nameServers)'
# point the registrar's nameservers at those four values

# then, every time
./setup-dns-gcloud.sh <probe-domain> <probe-ip> <gcp-project> probe-zone
./check-dns.sh probe <probe-domain> <probe-ip>
```

## Sources

- https://docs.cloud.google.com/compute/docs/tutorials/sending-mail
- https://docs.cloud.google.com/compute/docs/instances/create-ptr-record
