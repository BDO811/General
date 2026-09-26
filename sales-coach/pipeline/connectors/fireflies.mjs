/**
 * Fireflies: list the calls and get at the audio.
 *
 * Step 1 of prompt 1. Fireflies exposes a single GraphQL endpoint. The only
 * fields that matter here are the transcript id, the date, who was on the
 * call, and the audio URL, because the transcription is redone with Gemini
 * so it comes back with tone tags on every line.
 */

import { createWriteStream } from 'node:fs';
import { mkdir, stat } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { Readable } from 'node:stream';
import { pipeline as streamPipeline } from 'node:stream/promises';

import { request, postJson } from './http.mjs';

const ENDPOINT = 'https://api.fireflies.ai/graphql';

const TRANSCRIPTS_QUERY = `
  query Transcripts($fromDate: DateTime, $toDate: DateTime, $limit: Int, $skip: Int, $hostEmail: String) {
    transcripts(fromDate: $fromDate, toDate: $toDate, limit: $limit, skip: $skip, host_email: $hostEmail) {
      id
      title
      date
      duration
      host_email
      organizer_email
      audio_url
      participants
      meeting_attendees {
        displayName
        email
      }
    }
  }
`;

function headers(apiKey) {
  return { authorization: `Bearer ${apiKey}`, 'content-type': 'application/json' };
}

/**
 * Every call hosted by `hostEmail` between two dates.
 *
 * Pages until Fireflies stops returning rows. The page size is capped at 50
 * because larger pages time out on accounts with long histories.
 *
 * @returns {Promise<Array<Object>>} raw transcript records
 */
export async function listCalls({ apiKey, hostEmail, fromDate, toDate, pageSize = 50, maxPages = 200 }) {
  const all = [];

  for (let page = 0; page < maxPages; page++) {
    const body = await postJson(
      ENDPOINT,
      {
        query: TRANSCRIPTS_QUERY,
        variables: {
          fromDate: toIso(fromDate),
          toDate: toIso(toDate),
          limit: pageSize,
          skip: page * pageSize,
          hostEmail: hostEmail ?? null,
        },
      },
      { headers: headers(apiKey) }
    );

    if (body.errors?.length) {
      throw new Error(`Fireflies: ${body.errors.map((e) => e.message).join('; ')}`);
    }

    const batch = body.data?.transcripts ?? [];
    all.push(...batch);
    if (batch.length < pageSize) break;
  }

  return all;
}

function toIso(d) {
  if (!d) return null;
  return d instanceof Date ? d.toISOString() : new Date(d).toISOString();
}

/**
 * Normalise a Fireflies transcript into the row `calls` expects, and work out
 * who the prospect is.
 *
 * The prospect is the attendee who is not the seller and not on the seller's
 * own domain. A call with no such attendee gets `prospectEmail: null` and will
 * end up in the no-matching-deal bucket, which is the honest answer.
 */
export function normalise(transcript, { sellerEmail }) {
  const sellerDomain = sellerEmail?.split('@')[1]?.toLowerCase() ?? null;

  const attendees = (transcript.meeting_attendees ?? [])
    .map((a) => ({
      name: a.displayName ?? null,
      email: (a.email ?? '').toLowerCase().trim(),
    }))
    .filter((a) => a.email);

  const outside = attendees.filter((a) => {
    if (a.email === sellerEmail?.toLowerCase()) return false;
    const domain = a.email.split('@')[1];
    return !sellerDomain || domain !== sellerDomain;
  });

  const prospect = outside[0] ?? null;

  return {
    id: transcript.id,
    title: transcript.title ?? null,
    date: new Date(Number(transcript.date) || transcript.date).toISOString().slice(0, 10),
    durationSec: transcript.duration ? Math.round(Number(transcript.duration) * 60) : null,
    audioUrl: transcript.audio_url ?? null,
    prospectEmail: prospect?.email ?? null,
    prospectName: prospect?.name ?? null,
    attendees,
  };
}

/**
 * Download a call's audio to `dir/[id].mp3`, named by its transcript id.
 *
 * Skips the download when the file is already on disk with a non-zero size,
 * so a re-run after a crash does not re-pull gigabytes of audio.
 *
 * @returns {Promise<string|null>} the path, or null when there is no audio URL
 */
export async function downloadAudio({ call, dir, apiKey }) {
  if (!call.audioUrl) return null;

  const path = join(dir, `${call.id}.mp3`);
  try {
    const existing = await stat(path);
    if (existing.size > 0) return path;
  } catch {
    // Not there yet, which is the normal case.
  }

  await mkdir(dirname(path), { recursive: true });

  // The audio URL is usually pre-signed. Send the key anyway: it is harmless
  // on a signed URL and required on the accounts that return an unsigned one.
  const res = await request(call.audioUrl, {
    headers: { authorization: `Bearer ${apiKey}` },
    timeoutMs: 600000,
  });

  await streamPipeline(Readable.fromWeb(res.body), createWriteStream(path));
  return path;
}
