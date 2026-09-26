/**
 * HubSpot: the outcome column.
 *
 * Step 4 of prompt 1, and the one that makes the whole thing work. Without a
 * won or lost label on every prospect there is nothing to compare, and the
 * analysis has no ground truth at all.
 *
 * Needs a private app token with crm.objects.contacts.read and
 * crm.objects.deals.read.
 */

import { getJson, postJson, pool } from './http.mjs';

const BASE = 'https://api.hubapi.com';

function auth(token) {
  return { authorization: `Bearer ${token}` };
}

/** Find the contact record for an email address. Returns null when there is none. */
export async function findContact({ token, email }) {
  const body = await postJson(
    `${BASE}/crm/v3/objects/contacts/search`,
    {
      filterGroups: [
        { filters: [{ propertyName: 'email', operator: 'EQ', value: email.toLowerCase() }] },
      ],
      properties: ['email', 'firstname', 'lastname', 'company', 'jobtitle'],
      limit: 1,
    },
    { headers: auth(token) }
  );

  return body.results?.[0] ?? null;
}

/** Every deal associated with a contact, with the properties the analysis needs. */
export async function dealsForContact({ token, contactId }) {
  const assoc = await getJson(
    `${BASE}/crm/v4/objects/contacts/${contactId}/associations/deals?limit=100`,
    { headers: auth(token) }
  );

  const ids = (assoc.results ?? []).map((r) => r.toObjectId ?? r.id).filter(Boolean);
  if (ids.length === 0) return [];

  const body = await postJson(
    `${BASE}/crm/v3/objects/deals/batch/read`,
    {
      properties: ['dealname', 'dealstage', 'amount', 'closedate', 'pipeline'],
      inputs: ids.map((id) => ({ id: String(id) })),
    },
    { headers: auth(token) }
  );

  return body.results ?? [];
}

/**
 * Map a HubSpot deal stage onto the three buckets the analysis understands.
 *
 * Stage ids are per-pipeline and customisable, so this checks the built-in
 * ids first and then falls back to matching the words. Anything it cannot
 * place is `open`, never `closed_lost`: guessing lost would quietly inflate
 * every loss rate in the findings.
 */
export function outcomeFromStage(stage) {
  if (!stage) return 'open';
  const s = String(stage).toLowerCase();
  if (s === 'closedwon' || /closed[\s_-]*won/.test(s) || s === 'won') return 'closed_won';
  if (s === 'closedlost' || /closed[\s_-]*lost/.test(s) || s === 'lost') return 'closed_lost';
  return 'open';
}

/**
 * Pick the deal that should label this prospect.
 *
 * A prospect can have several. A closed deal beats an open one, because the
 * point of the exercise is learning from finished deals. Among closed deals
 * the most recent one wins.
 */
export function pickDeal(deals) {
  if (!deals?.length) return null;

  const scored = deals.map((d) => {
    const outcome = outcomeFromStage(d.properties?.dealstage);
    return {
      deal: d,
      outcome,
      closed: outcome !== 'open',
      when: Date.parse(d.properties?.closedate ?? '') || 0,
    };
  });

  scored.sort((a, b) => {
    if (a.closed !== b.closed) return a.closed ? -1 : 1;
    return b.when - a.when;
  });

  return scored[0];
}

/**
 * Resolve one email address to {outcome, amount, closedAt, ids}.
 *
 * A contact with no CRM record, or a contact with no deals, comes back as
 * `none`. Those are the calls the reel counts separately as having no
 * matching deal.
 */
export async function resolveProspect({ token, email }) {
  const contact = await findContact({ token, email });
  if (!contact) {
    return { email, outcome: 'none', amount: null, closedAt: null, contactId: null, dealId: null };
  }

  const deals = await dealsForContact({ token, contactId: contact.id });
  const best = pickDeal(deals);

  const props = contact.properties ?? {};
  const name = [props.firstname, props.lastname].filter(Boolean).join(' ') || null;

  if (!best) {
    return {
      email,
      name,
      company: props.company ?? null,
      title: props.jobtitle ?? null,
      outcome: 'none',
      amount: null,
      closedAt: null,
      contactId: contact.id,
      dealId: null,
    };
  }

  const amount = Number(best.deal.properties?.amount);

  return {
    email,
    name,
    company: props.company ?? null,
    title: props.jobtitle ?? null,
    outcome: best.outcome,
    amount: Number.isFinite(amount) ? amount : null,
    closedAt: best.deal.properties?.closedate?.slice(0, 10) ?? null,
    contactId: contact.id,
    dealId: best.deal.id,
  };
}

/** Resolve a list of addresses, a few at a time so HubSpot's rate limit holds. */
export async function resolveAll({ token, emails, concurrency = 4 }) {
  return pool(emails, concurrency, (email) => resolveProspect({ token, email }));
}
