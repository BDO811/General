/**
 * Jev: the judge.
 *
 * Prompt 2 is emphatic that the agent must not grade calls itself. It asks
 * Jev, TypeSafe's small typed-judgment model, one yes or no question at a
 * time. That is the whole trick. A frontier model asked to grade 214 calls
 * against six criteria is slow, expensive, and drifts between call 1 and call
 * 200. Jev returns a typed verdict with a probability in a few hundred
 * milliseconds for a fraction of a cent, and answers question 200 the same
 * way it answered question 1.
 *
 * Two transports:
 *
 *   mcp   spawns `npx -y @jkudish/jev-mcp` and speaks MCP over stdio. This is
 *         the path the reel uses, and the default here.
 *   http  posts to an endpoint that returns {answer, probability, confidence}.
 *         For running the pipeline on a box where spawning npx is not an
 *         option, or against a self-hosted Jev.
 *
 * The MCP client discovers the tool's input schema at connect time and maps
 * the claim and evidence onto whatever it actually names its parameters, so a
 * rename upstream does not silently produce garbage judgments.
 */

import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';

import { postJson } from './http.mjs';

/** Candidate parameter names, most likely first. */
const CLAIM_KEYS = ['claim', 'statement', 'question', 'hypothesis', 'assertion'];
const EVIDENCE_KEYS = ['text', 'evidence', 'context', 'source', 'document', 'content'];

/* ------------------------------------------------------------------ */
/* MCP over stdio                                                      */
/* ------------------------------------------------------------------ */

class McpStdioClient {
  constructor({ command = 'npx', args = ['-y', '@jkudish/jev-mcp'], env = {} } = {}) {
    this.command = command;
    this.args = args;
    this.env = env;
    this.nextId = 1;
    this.pending = new Map();
    this.proc = null;
  }

  async start() {
    this.proc = spawn(this.command, this.args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, ...this.env },
    });

    this.proc.on('error', (err) => {
      for (const { reject } of this.pending.values()) reject(err);
      this.pending.clear();
    });

    // The server's own logging goes to stderr. Surface it, because a missing
    // TYPESAFE_API_KEY shows up there and nowhere else.
    this.stderr = '';
    this.proc.stderr.on('data', (chunk) => {
      this.stderr += String(chunk);
      if (this.stderr.length > 8192) this.stderr = this.stderr.slice(-8192);
    });

    // MCP stdio framing is one JSON object per line.
    this.rl = createInterface({ input: this.proc.stdout });
    this.rl.on('line', (line) => {
      const trimmed = line.trim();
      if (!trimmed) return;
      let msg;
      try {
        msg = JSON.parse(trimmed);
      } catch {
        return; // Not a protocol message. Ignore it.
      }
      const entry = this.pending.get(msg.id);
      if (!entry) return;
      this.pending.delete(msg.id);
      if (msg.error) entry.reject(new Error(`jev-mcp: ${msg.error.message ?? JSON.stringify(msg.error)}`));
      else entry.resolve(msg.result);
    });

    await this.call('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'sales-coach', version: '1.0.0' },
    });
    this.notify('notifications/initialized', {});
  }

  call(method, params, timeoutMs = 60000) {
    const id = this.nextId++;
    const payload = JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n';

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`jev-mcp: ${method} timed out after ${timeoutMs}ms. stderr: ${this.stderr.slice(-500)}`));
      }, timeoutMs);

      this.pending.set(id, {
        resolve: (r) => {
          clearTimeout(timer);
          resolve(r);
        },
        reject: (e) => {
          clearTimeout(timer);
          reject(e);
        },
      });

      this.proc.stdin.write(payload);
    });
  }

  notify(method, params) {
    this.proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n');
  }

  async listTools() {
    const result = await this.call('tools/list', {});
    return result.tools ?? [];
  }

  async callTool(name, args) {
    return this.call('tools/call', { name, arguments: args }, 120000);
  }

  stop() {
    this.rl?.close();
    this.proc?.stdin.end();
    this.proc?.kill();
  }
}

/** Pick the first candidate key the schema actually declares. */
function pickKey(schema, candidates, fallback) {
  const props = schema?.properties ?? {};
  for (const key of candidates) if (key in props) return key;
  // Nothing matched. Prefer a required string parameter over guessing.
  const required = (schema?.required ?? []).filter((k) => props[k]?.type === 'string');
  return required[0] ?? fallback;
}

/**
 * Read a verdict out of whatever shape came back.
 *
 * MCP tool results carry content blocks. Jev's payload is JSON in a text
 * block on every provider seen so far, but the field naming varies, so this
 * looks for the meaning rather than one exact key.
 */
export function parseVerdict(result) {
  let payload = result;

  if (Array.isArray(result?.content)) {
    const text = result.content
      .filter((c) => c.type === 'text')
      .map((c) => c.text)
      .join('');
    try {
      payload = JSON.parse(text);
    } catch {
      // Not JSON. Fall back to reading the words.
      const t = text.trim().toLowerCase();
      if (/^(true|yes|supported|pass)\b/.test(t)) return { answer: true, probability: null, confidence: null };
      if (/^(false|no|unsupported|fail)\b/.test(t)) return { answer: false, probability: null, confidence: null };
      return { answer: null, probability: null, confidence: null };
    }
  }

  const raw =
    payload?.verdict ?? payload?.answer ?? payload?.result ?? payload?.supported ?? payload?.decision;

  let answer = null;
  if (typeof raw === 'boolean') answer = raw;
  else if (typeof raw === 'string') {
    const v = raw.trim().toLowerCase();
    if (['true', 'yes', 'supported', 'pass', 'y'].includes(v)) answer = true;
    else if (['false', 'no', 'unsupported', 'fail', 'n'].includes(v)) answer = false;
  }

  const probability =
    num(payload?.probability) ??
    num(payload?.probabilities?.true) ??
    num(payload?.probabilities?.yes) ??
    num(payload?.score);

  // When no explicit verdict came back but a probability did, read the
  // probability. A judgment sitting exactly on 0.5 stays unanswered rather
  // than being rounded into a yes.
  if (answer === null && probability != null && probability !== 0.5) {
    answer = probability > 0.5;
  }

  return {
    answer,
    probability: probability ?? null,
    confidence: num(payload?.confidence) ?? null,
    model: payload?.model ?? null,
  };
}

function num(v) {
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
}

/* ------------------------------------------------------------------ */
/* Public surface                                                      */
/* ------------------------------------------------------------------ */

/**
 * Open a Jev judge.
 *
 * @param {Object} options
 * @param {'mcp'|'http'} [options.transport]
 * @param {string} [options.tool]     MCP tool name, default jev_verify
 * @param {string} [options.url]      HTTP endpoint, required for transport http
 * @param {string} [options.apiKey]   TYPESAFE_API_KEY, passed to the MCP server
 * @returns {Promise<{judge:(claim:string, evidence:string)=>Promise<Object>, close:()=>void}>}
 */
export async function openJudge(options = {}) {
  const transport = options.transport ?? 'mcp';

  if (transport === 'http') {
    if (!options.url) throw new Error('Jev http transport needs a url');
    return {
      async judge(claim, evidence) {
        const body = await postJson(
          options.url,
          { claim, text: evidence },
          {
            headers: options.apiKey ? { authorization: `Bearer ${options.apiKey}` } : {},
            timeoutMs: 60000,
          }
        );
        return parseVerdict(body);
      },
      close() {},
    };
  }

  const client = new McpStdioClient({
    command: options.command,
    args: options.args,
    env: options.apiKey ? { TYPESAFE_API_KEY: options.apiKey } : {},
  });
  await client.start();

  const toolName = options.tool ?? 'jev_verify';
  const tools = await client.listTools();
  const tool = tools.find((t) => t.name === toolName);

  if (!tool) {
    client.stop();
    throw new Error(
      `jev-mcp does not expose ${toolName}. It offers: ${tools.map((t) => t.name).join(', ') || 'nothing'}`
    );
  }

  const claimKey = options.claimKey ?? pickKey(tool.inputSchema, CLAIM_KEYS, 'claim');
  const evidenceKey = options.evidenceKey ?? pickKey(tool.inputSchema, EVIDENCE_KEYS, 'text');

  return {
    tool: toolName,
    claimKey,
    evidenceKey,
    async judge(claim, evidence) {
      const result = await client.callTool(toolName, {
        [claimKey]: claim,
        [evidenceKey]: evidence,
      });
      return parseVerdict(result);
    },
    close() {
      client.stop();
    },
  };
}

/* ------------------------------------------------------------------ */
/* Turning artifacts into evidence                                     */
/* ------------------------------------------------------------------ */

/**
 * Render a call as the text Jev reads.
 *
 * Tone tags are inline on every line, because half the rubric is unanswerable
 * without them. Timestamps stay in so "the first five minutes" is a fact on
 * the page rather than something the judge has to infer.
 */
export function callEvidence(call) {
  const head = `Call ${call.id}${call.title ? `: ${call.title}` : ''} on ${call.date}.`;
  const lines = (call.lines ?? []).map(
    (l) => `[${l.t ?? '--:--'}] ${l.speaker ?? 'unknown'} (${l.tone ?? 'untagged'}): ${l.text}`
  );
  return [head, '', ...lines].join('\n');
}

/**
 * Render a seller email plus the prospect's replies.
 *
 * Word counts are stated rather than left to be counted, since one rubric
 * question is a length comparison and a judge should not be doing arithmetic.
 */
export function emailEvidence(email) {
  const theirWords = (email.theirs ?? []).map((t) => t.words).filter((n) => Number.isFinite(n));
  const theirAverage = theirWords.length
    ? Math.round(theirWords.reduce((a, b) => a + b, 0) / theirWords.length)
    : null;

  return [
    `Email from the seller on ${email.date}${email.subject ? `, subject: ${email.subject}` : ''}.`,
    `Length: ${email.words} words.`,
    theirAverage == null
      ? 'The prospect has not replied in this thread.'
      : `The prospect's messages in this thread average ${theirAverage} words (${theirWords.join(', ')}).`,
    '',
    email.body ?? '',
  ].join('\n');
}
