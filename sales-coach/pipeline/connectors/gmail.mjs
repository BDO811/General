/**
 * Gmail: pull the email thread with each prospect.
 *
 * Step 3 of prompt 1. Both directions are stored. The seller's own messages
 * are what get graded; the prospect's replies are what "a similar length to
 * theirs" is measured against, so pulling only one side makes that rubric
 * question unanswerable.
 *
 * Needs an OAuth access token with gmail.readonly. There is no API-key path
 * for Gmail.
 */

import { getJson, pool } from './http.mjs';

const BASE = 'https://gmail.googleapis.com/gmail/v1/users/me';

function auth(token) {
  return { authorization: `Bearer ${token}` };
}

/** Every message id matching a Gmail search query. Pages through all of them. */
export async function search({ token, query, maxResults = 500 }) {
  const ids = [];
  let pageToken;

  do {
    const url = new URL(`${BASE}/messages`);
    url.searchParams.set('q', query);
    url.searchParams.set('maxResults', String(Math.min(500, maxResults - ids.length)));
    if (pageToken) url.searchParams.set('pageToken', pageToken);

    const body = await getJson(url.toString(), { headers: auth(token) });
    for (const m of body.messages ?? []) ids.push(m.id);
    pageToken = body.nextPageToken;
  } while (pageToken && ids.length < maxResults);

  return ids;
}

/** Fetch and flatten one message. */
export async function getMessage({ token, id }) {
  const body = await getJson(`${BASE}/messages/${id}?format=full`, { headers: auth(token) });
  return flatten(body);
}

function header(payload, name) {
  const h = (payload?.headers ?? []).find((x) => x.name.toLowerCase() === name.toLowerCase());
  return h?.value ?? null;
}

/** Walk the MIME tree and pull out the plain-text body. */
function extractText(payload) {
  if (!payload) return '';

  if (payload.mimeType === 'text/plain' && payload.body?.data) {
    return decode(payload.body.data);
  }

  for (const part of payload.parts ?? []) {
    const text = extractText(part);
    if (text) return text;
  }

  // Nothing but HTML. Strip the tags rather than storing markup, since word
  // count and "ends with a question" are both computed off this string.
  if (payload.mimeType === 'text/html' && payload.body?.data) {
    return decode(payload.body.data)
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>/gi, '\n')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/[ \t]+/g, ' ');
  }

  return '';
}

function decode(data) {
  return Buffer.from(data.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8');
}

/**
 * Drop quoted history and signatures.
 *
 * Without this every reply in a long thread counts as hundreds of words and
 * the length comparison becomes meaningless.
 */
export function stripQuoted(text) {
  const lines = text.split('\n');
  const out = [];

  for (const line of lines) {
    const t = line.trim();
    if (/^On .+ wrote:$/.test(t)) break;
    if (/^-{2,}\s*Original Message\s*-{2,}$/i.test(t)) break;
    if (/^From:\s/.test(t) && out.length > 0) break;
    if (t === '--' || t === '__') break;
    if (t.startsWith('>')) continue;
    out.push(line);
  }

  return out.join('\n').trim();
}

export function wordCount(text) {
  const clean = stripQuoted(text);
  if (!clean) return 0;
  return clean.split(/\s+/).filter(Boolean).length;
}

function flatten(message) {
  const raw = extractText(message.payload);
  const body = stripQuoted(raw);
  const dateHeader = header(message.payload, 'Date');
  const ms = Number(message.internalDate);

  return {
    id: message.id,
    threadId: message.threadId,
    date: new Date(Number.isFinite(ms) && ms > 0 ? ms : dateHeader).toISOString().slice(0, 10),
    from: header(message.payload, 'From'),
    to: header(message.payload, 'To'),
    subject: header(message.payload, 'Subject'),
    body,
    words: wordCount(raw),
    labelIds: message.labelIds ?? [],
  };
}

/** Pull the address out of `Name <addr@example.com>`. */
export function addressOf(headerValue) {
  if (!headerValue) return null;
  const angle = headerValue.match(/<([^>]+)>/);
  const raw = angle ? angle[1] : headerValue;
  const trimmed = raw.trim().toLowerCase();
  return /\S+@\S+/.test(trimmed) ? trimmed : null;
}

/**
 * Every message either way with one prospect, in both directions.
 *
 * @returns {Promise<Array<Object>>} messages with `direction` set
 */
export async function threadWith({ token, prospectEmail, sellerEmail, concurrency = 6 }) {
  const query = `{from:${prospectEmail} to:${prospectEmail}} -in:chats`;
  const ids = await search({ token, query });

  const messages = await pool(ids, concurrency, (id) => getMessage({ token, id }));

  return messages
    .filter(Boolean)
    .map((m) => {
      const from = addressOf(m.from);
      const direction = from === sellerEmail?.toLowerCase() ? 'out' : 'in';
      return { ...m, direction };
    })
    // A thread can pick up stray messages that mention the address without
    // actually involving the prospect. Keep only the ones they are on.
    .filter((m) => {
      const from = addressOf(m.from);
      const to = (m.to ?? '').toLowerCase();
      return from === prospectEmail.toLowerCase() || to.includes(prospectEmail.toLowerCase());
    });
}
