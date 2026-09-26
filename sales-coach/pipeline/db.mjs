/**
 * sales.db access.
 *
 * Uses node:sqlite, which ships with Node 22.5 and later, so the pipeline has
 * no install step and no native build. The whole database is one file under
 * ~/sales-coach, which is also how you delete it.
 */

import { DatabaseSync } from 'node:sqlite';
import { readFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SCHEMA = resolve(HERE, 'schema.sql');

/** Open sales.db, creating the file and the schema if they are not there. */
export function open(dbPath) {
  mkdirSync(dirname(dbPath), { recursive: true });
  const db = new DatabaseSync(dbPath);
  db.exec(readFileSync(SCHEMA, 'utf8'));
  return db;
}

const now = () => new Date().toISOString();

/* ------------------------------------------------------------------ */
/* Writes                                                              */
/* ------------------------------------------------------------------ */

export function upsertProspect(db, p) {
  db.prepare(
    `INSERT INTO prospects
       (id, name, company, title, email, outcome, amount, closed_at,
        hubspot_deal_id, hubspot_contact_id, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       name = COALESCE(excluded.name, prospects.name),
       company = COALESCE(excluded.company, prospects.company),
       title = COALESCE(excluded.title, prospects.title),
       outcome = excluded.outcome,
       amount = COALESCE(excluded.amount, prospects.amount),
       closed_at = COALESCE(excluded.closed_at, prospects.closed_at),
       hubspot_deal_id = COALESCE(excluded.hubspot_deal_id, prospects.hubspot_deal_id),
       hubspot_contact_id = COALESCE(excluded.hubspot_contact_id, prospects.hubspot_contact_id),
       updated_at = excluded.updated_at`
  ).run(
    p.id,
    p.name ?? null,
    p.company ?? null,
    p.title ?? null,
    p.email ?? null,
    p.outcome ?? 'none',
    p.amount ?? null,
    p.closedAt ?? null,
    p.hubspotDealId ?? null,
    p.hubspotContactId ?? null,
    now()
  );
}

export function upsertCall(db, c) {
  db.prepare(
    `INSERT INTO calls
       (id, prospect_id, title, date, duration_sec, audio_path, transcript_path, transcribed_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       prospect_id = COALESCE(excluded.prospect_id, calls.prospect_id),
       title = COALESCE(excluded.title, calls.title),
       duration_sec = COALESCE(excluded.duration_sec, calls.duration_sec),
       audio_path = COALESCE(excluded.audio_path, calls.audio_path),
       transcript_path = COALESCE(excluded.transcript_path, calls.transcript_path),
       transcribed_at = COALESCE(excluded.transcribed_at, calls.transcribed_at)`
  ).run(
    c.id,
    c.prospectId ?? null,
    c.title ?? null,
    c.date,
    c.durationSec ?? null,
    c.audioPath ?? null,
    c.transcriptPath ?? null,
    c.transcribedAt ?? null
  );
}

/** Replace a call's transcript lines wholesale. Re-transcribing is idempotent. */
export function replaceCallLines(db, callId, lines) {
  db.prepare('DELETE FROM call_lines WHERE call_id = ?').run(callId);
  const insert = db.prepare(
    'INSERT INTO call_lines (call_id, seq, t, t_sec, speaker, text, tone) VALUES (?, ?, ?, ?, ?, ?, ?)'
  );
  lines.forEach((line, i) => {
    insert.run(callId, i, line.t ?? null, toSeconds(line.t), line.speaker ?? null, line.text ?? '', line.tone ?? null);
  });
}

/** "14:52" becomes 892. Returns null for anything it cannot parse. */
export function toSeconds(t) {
  if (typeof t !== 'string') return null;
  const parts = t.split(':').map(Number);
  if (parts.some((n) => !Number.isFinite(n))) return null;
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return null;
}

export function upsertEmail(db, e) {
  db.prepare(
    `INSERT INTO emails (id, thread_id, prospect_id, direction, date, subject, words, body)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       prospect_id = COALESCE(excluded.prospect_id, emails.prospect_id),
       words = COALESCE(excluded.words, emails.words),
       body = COALESCE(excluded.body, emails.body)`
  ).run(
    e.id,
    e.threadId ?? null,
    e.prospectId ?? null,
    e.direction,
    e.date,
    e.subject ?? null,
    e.words ?? null,
    e.body ?? null
  );
}

export function saveTag(db, { kind, artifactId, questionId, answer, probability, confidence, model }) {
  db.prepare(
    `INSERT INTO tags
       (artifact_kind, artifact_id, question_id, answer, probability, confidence, model, judged_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(artifact_kind, artifact_id, question_id) DO UPDATE SET
       answer = excluded.answer,
       probability = excluded.probability,
       confidence = excluded.confidence,
       model = excluded.model,
       judged_at = excluded.judged_at`
  ).run(
    kind,
    artifactId,
    questionId,
    answer === null || answer === undefined ? null : answer ? 1 : 0,
    probability ?? null,
    confidence ?? null,
    model ?? null,
    now()
  );
}

export function startRun(db, step) {
  const r = db.prepare('INSERT INTO runs (step, started_at) VALUES (?, ?)').run(step, now());
  return Number(r.lastInsertRowid);
}

export function endRun(db, id, ok, note) {
  db.prepare('UPDATE runs SET ended_at = ?, ok = ?, note = ? WHERE id = ?').run(
    now(),
    ok ? 1 : 0,
    note ?? null,
    id
  );
}

/* ------------------------------------------------------------------ */
/* Reads                                                               */
/* ------------------------------------------------------------------ */

/** Calls that still need a Gemini transcript. */
export function callsNeedingTranscript(db) {
  return db.prepare('SELECT * FROM calls WHERE transcribed_at IS NULL ORDER BY date').all();
}

/** One artifact plus everything Jev needs to judge it. */
export function callForJudging(db, callId) {
  const call = db.prepare('SELECT * FROM calls WHERE id = ?').get(callId);
  if (!call) return null;
  const lines = db
    .prepare('SELECT seq, t, t_sec, speaker, text, tone FROM call_lines WHERE call_id = ? ORDER BY seq')
    .all(callId);
  return { ...call, lines };
}

/** A seller email plus the prospect's own messages in the same thread. */
export function emailForJudging(db, emailId) {
  const email = db.prepare('SELECT * FROM emails WHERE id = ?').get(emailId);
  if (!email) return null;
  const theirs = db
    .prepare("SELECT date, subject, words, body FROM emails WHERE thread_id = ? AND direction = 'in' ORDER BY date")
    .all(email.thread_id);
  return { ...email, theirs };
}

/** Artifacts that still need an answer for a given question. */
export function untagged(db, kind, questionId) {
  const table = kind === 'call' ? 'calls' : 'emails';
  const extra = kind === 'email' ? "AND a.direction = 'out'" : '';
  return db
    .prepare(
      `SELECT a.id FROM ${table} a
       LEFT JOIN tags t
         ON t.artifact_kind = ? AND t.artifact_id = a.id AND t.question_id = ?
       WHERE t.artifact_id IS NULL ${extra}
       ORDER BY a.date`
    )
    .all(kind, questionId)
    .map((r) => r.id);
}

/**
 * Export sales.db into the plain-object shape the engine and the web app read.
 *
 * This is the seam between the pipeline and the analysis: the engine never
 * touches SQL, and the workbench can load a file produced here without any
 * server in between.
 */
export function toDataset(db, meta = {}) {
  const prospects = db
    .prepare('SELECT id, name, company, title, email, outcome, amount, closed_at FROM prospects')
    .all()
    .map((p) => ({
      id: p.id,
      name: p.name,
      company: p.company,
      title: p.title,
      email: p.email,
      outcome: p.outcome,
      amount: p.amount,
      closedAt: p.closed_at,
    }));

  const tagsFor = (kind) => {
    const map = new Map();
    for (const row of db
      .prepare('SELECT artifact_id, question_id, answer FROM tags WHERE artifact_kind = ?')
      .all(kind)) {
      if (!map.has(row.artifact_id)) map.set(row.artifact_id, {});
      map.get(row.artifact_id)[row.question_id] = row.answer === null ? null : row.answer === 1;
    }
    return map;
  };

  const callTags = tagsFor('call');
  const emailTags = tagsFor('email');

  const calls = db
    .prepare('SELECT id, prospect_id, title, date, duration_sec FROM calls')
    .all()
    .map((c) => ({
      id: c.id,
      prospectId: c.prospect_id,
      title: c.title,
      date: c.date,
      durationSec: c.duration_sec,
      tags: callTags.get(c.id) ?? {},
    }));

  const emails = db
    .prepare('SELECT id, prospect_id, direction, date, words FROM emails')
    .all()
    .map((e) => {
      const row = {
        id: e.id,
        prospectId: e.prospect_id,
        direction: e.direction,
        date: e.date,
        words: e.words,
      };
      if (e.direction === 'out') row.tags = emailTags.get(e.id) ?? {};
      return row;
    });

  return { meta: { generatedAt: now(), ...meta }, prospects, calls, emails };
}

/** Default location of the working directory the reel uses. */
export function defaultRoot() {
  const home = process.env.HOME ?? process.env.USERPROFILE ?? '.';
  return process.env.SALES_COACH_HOME ?? join(home, 'sales-coach');
}
