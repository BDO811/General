#!/usr/bin/env node
/**
 * Load a dataset JSON file into sales.db.
 *
 * Two uses. It seeds a working sales.db from the demo dataset so prompts 2
 * and 3 can be run end to end without any API keys, and it takes a dataset
 * exported from somewhere else (another machine, a colleague's run) and puts
 * it back into a database the pipeline can carry on with.
 *
 * Usage:
 *   node pipeline/import-dataset.mjs data/demo-dataset.json
 *   node pipeline/import-dataset.mjs data/demo-dataset.json --db /tmp/sales.db
 */

import { readFileSync } from 'node:fs';

import { loadConfig, ensureDirs } from './config.mjs';
import * as db from './db.mjs';

const argv = process.argv.slice(2);
const file = argv.find((a) => !a.startsWith('--'));
const dbFlag = argv.indexOf('--db');
const config = loadConfig();
const dbPath = dbFlag !== -1 ? argv[dbFlag + 1] : config.paths.db;

if (!file) {
  console.error('Usage: node pipeline/import-dataset.mjs <dataset.json> [--db path]');
  process.exit(1);
}

ensureDirs(config);
const dataset = JSON.parse(readFileSync(file, 'utf8'));
const database = db.open(dbPath);

try {
  for (const p of dataset.prospects ?? []) {
    db.upsertProspect(database, { ...p, id: p.id, email: p.email ?? p.id });
  }

  for (const c of dataset.calls ?? []) {
    db.upsertCall(database, {
      id: c.id,
      prospectId: c.prospectId,
      title: c.title,
      date: c.date,
      durationSec: c.durationSec,
      // The demo dataset carries answers but no transcript text. Mark it as
      // transcribed so prompt 2 does not queue it for Gemini, and leave the
      // lines empty rather than inventing a conversation.
      transcribedAt: c.tags && Object.keys(c.tags).length ? new Date().toISOString() : null,
    });
    for (const [questionId, answer] of Object.entries(c.tags ?? {})) {
      db.saveTag(database, { kind: 'call', artifactId: c.id, questionId, answer, model: 'imported' });
    }
  }

  for (const e of dataset.emails ?? []) {
    db.upsertEmail(database, {
      id: e.id,
      threadId: e.threadId ?? e.id,
      prospectId: e.prospectId,
      direction: e.direction,
      date: e.date,
      subject: e.subject,
      words: e.words,
      body: e.body,
    });
    for (const [questionId, answer] of Object.entries(e.tags ?? {})) {
      db.saveTag(database, { kind: 'email', artifactId: e.id, questionId, answer, model: 'imported' });
    }
  }

  const n = (sql) => database.prepare(sql).get().n;
  console.log(`Imported into ${dbPath}`);
  console.log(`  prospects ${n('SELECT COUNT(*) n FROM prospects')}`);
  console.log(`  calls     ${n('SELECT COUNT(*) n FROM calls')}`);
  console.log(`  emails    ${n('SELECT COUNT(*) n FROM emails')}`);
  console.log(`  tags      ${n('SELECT COUNT(*) n FROM tags')}`);
} finally {
  database.close();
}
