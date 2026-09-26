/**
 * Gemini: turn call audio into a tone-tagged transcript.
 *
 * Step 2 of prompt 1, and the step the whole thing hangs on. Fireflies already
 * has a transcript, but it is words only. The rubric asks questions like "did
 * I match their tone", which cannot be answered from words. So every call is
 * re-transcribed with a tone tag on every line.
 *
 * The tags are constrained by a response schema rather than asked for in
 * prose, so a line can only come back with a tag the rubric knows about.
 */

import { readFile, stat } from 'node:fs/promises';
import { basename } from 'node:path';

import { request, postJson, getJson } from './http.mjs';
import { TONE_TAGS } from '../../engine/rubric.js';

const BASE = 'https://generativelanguage.googleapis.com/v1beta';

/** The model named in the reel. Override with GEMINI_MODEL when it moves. */
export const DEFAULT_MODEL = 'gemini-3.8-flash';

const TRANSCRIPT_SCHEMA = {
  type: 'OBJECT',
  properties: {
    call_id: { type: 'STRING' },
    prospect: { type: 'STRING', description: 'Name of the non-seller speaker, if it can be told' },
    lines: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          t: { type: 'STRING', description: 'Timestamp as mm:ss from the start of the call' },
          speaker: { type: 'STRING', description: "'me' for the seller, otherwise the other speaker's name" },
          text: { type: 'STRING' },
          tone: { type: 'STRING', enum: TONE_TAGS },
        },
        required: ['t', 'speaker', 'text', 'tone'],
      },
    },
  },
  required: ['call_id', 'lines'],
};

function instruction({ callId, sellerName }) {
  return [
    'You are transcribing a recorded sales call.',
    '',
    'Return every spoken line in order. On each line give:',
    '  t       the timestamp as mm:ss from the start of the call',
    `  speaker "me" for the seller${sellerName ? ` (${sellerName})` : ''}, otherwise the other speaker's name`,
    '  text    what was said, verbatim',
    `  tone    exactly one of: ${TONE_TAGS.join(', ')}`,
    '',
    'The tone tag describes how the line was delivered, not what it says. Judge it',
    'from pitch, pace, pauses and volume. "matching their energy" means the speaker',
    'moved toward the other speaker\'s pace and volume on that line.',
    '',
    'Do not summarise. Do not merge speakers. Do not skip small talk: the opening',
    'few minutes are the part being measured.',
    '',
    `Use "${callId}" as call_id.`,
  ].join('\n');
}

/**
 * Upload a local audio file through the Files API.
 *
 * Files over a few megabytes cannot be sent inline, and sales calls are always
 * over a few megabytes, so everything goes through the resumable endpoint.
 *
 * @returns {Promise<{uri:string, mimeType:string, name:string}>}
 */
export async function uploadAudio({ apiKey, path, mimeType = 'audio/mpeg' }) {
  const { size } = await stat(path);

  const startRes = await request(`${BASE}/files?key=${encodeURIComponent(apiKey)}`, {
    method: 'POST',
    headers: {
      'X-Goog-Upload-Protocol': 'resumable',
      'X-Goog-Upload-Command': 'start',
      'X-Goog-Upload-Header-Content-Length': String(size),
      'X-Goog-Upload-Header-Content-Type': mimeType,
      'content-type': 'application/json',
    },
    body: JSON.stringify({ file: { display_name: basename(path) } }),
  });

  const uploadUrl = startRes.headers.get('x-goog-upload-url');
  if (!uploadUrl) throw new Error('Gemini did not return an upload URL');

  const bytes = await readFile(path);
  const finish = await request(uploadUrl, {
    method: 'POST',
    headers: {
      'content-length': String(size),
      'X-Goog-Upload-Offset': '0',
      'X-Goog-Upload-Command': 'upload, finalize',
    },
    body: bytes,
    timeoutMs: 600000,
  });

  const body = await finish.json();
  const file = body.file ?? body;
  if (!file?.uri) throw new Error('Gemini upload returned no file URI');

  return { uri: file.uri, mimeType: file.mimeType ?? mimeType, name: file.name };
}

/**
 * Wait for an uploaded file to leave PROCESSING.
 *
 * Audio is not usable the instant the upload finishes. Sending it too early
 * comes back as a 400 that reads like a malformed request, so poll first.
 */
export async function waitForFile({ apiKey, name, timeoutMs = 300000, intervalMs = 2000 }) {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const file = await getJson(`${BASE}/${name}?key=${encodeURIComponent(apiKey)}`);
    if (file.state === 'ACTIVE') return file;
    if (file.state === 'FAILED') throw new Error(`Gemini could not process ${name}`);
    if (Date.now() > deadline) throw new Error(`Gemini still processing ${name} after ${timeoutMs}ms`);
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}

/**
 * Transcribe one call.
 *
 * @returns {Promise<{call_id:string, prospect?:string, lines:Array<{t,speaker,text,tone}>}>}
 */
export async function transcribe({ apiKey, path, callId, sellerName, model = DEFAULT_MODEL }) {
  const file = await uploadAudio({ apiKey, path });
  await waitForFile({ apiKey, name: file.name });

  const body = await postJson(
    `${BASE}/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`,
    {
      contents: [
        {
          role: 'user',
          parts: [
            { text: instruction({ callId, sellerName }) },
            { file_data: { mime_type: file.mimeType, file_uri: file.uri } },
          ],
        },
      ],
      generationConfig: {
        temperature: 0,
        response_mime_type: 'application/json',
        response_schema: TRANSCRIPT_SCHEMA,
      },
    },
    { timeoutMs: 900000 }
  );

  const text = body.candidates?.[0]?.content?.parts?.map((p) => p.text).join('') ?? '';
  if (!text) {
    const reason = body.candidates?.[0]?.finishReason ?? body.promptFeedback?.blockReason ?? 'unknown';
    throw new Error(`Gemini returned no transcript for ${callId} (${reason})`);
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error(`Gemini returned unparseable JSON for ${callId}`);
  }

  if (!Array.isArray(parsed.lines)) {
    throw new Error(`Gemini returned no lines for ${callId}`);
  }

  // The schema constrains the enum, but a model can still surprise you.
  // Anything unexpected is dropped to null rather than stored as a tag the
  // rubric will later read as meaningful.
  const allowed = new Set(TONE_TAGS);
  parsed.lines = parsed.lines.map((l) => ({
    ...l,
    tone: allowed.has(l.tone) ? l.tone : null,
  }));

  return parsed;
}

/** Delete an uploaded file. Worth doing: these are recordings of real people. */
export async function deleteFile({ apiKey, name }) {
  await request(`${BASE}/${name}?key=${encodeURIComponent(apiKey)}`, { method: 'DELETE', retries: 1 });
}
