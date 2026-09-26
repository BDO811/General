#!/usr/bin/env node
/**
 * Prompt 2: coach me with Jev.
 *
 *   1. Read ~/sales-coach/sales.db. Use Jev for every judgment about a call
 *      or an email. Never judge them here.
 *   2. For every call, ask Jev the yes or no rubric questions against its
 *      tone-tagged transcript.
 *   3. For every email the seller sent, ask Jev the email questions.
 *   4. Save every answer and its probability in the tags table.
 *   5. For each question, compare how often the answer was yes in closed won
 *      against closed lost. Only call it a pattern when the gap is wide and
 *      the sample is not tiny. Otherwise say no clear pattern.
 *   6. Write it up as a direct call review at ~/sales-coach/findings.md.
 *
 * Step 5 is the only step this script does itself, and it does it with
 * arithmetic rather than judgment: see engine/analysis.js. Every actual
 * opinion about a call comes from Jev.
 *
 * Resumable. An artifact that already has an answer for a question is not
 * re-judged, so a second run costs only what is new.
 *
 * Usage:
 *   node pipeline/run-prompt2.mjs [--requery] [--limit 50]
 */

import { writeFile } from 'node:fs/promises';

import { loadConfig, ensureDirs, requireKeys } from './config.mjs';
import * as db from './db.mjs';
import { openJudge, callEvidence, emailEvidence } from './connectors/jev.mjs';
import { pool } from './connectors/http.mjs';

import { RUBRIC } from '../engine/rubric.js';
import { analyze } from '../engine/analysis.js';
import { renderFindings, renderTable } from '../engine/findings.js';

const args = parseArgs(process.argv.slice(2));
const config = loadConfig();

function parseArgs(argv) {
  const out = { requery: false, limit: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--requery') out.requery = true;
    else if (argv[i] === '--limit') out.limit = Number(argv[++i]);
  }
  return out;
}

const log = (...a) => console.log(...a);

async function main() {
  requireKeys(config, ['jev']);
  ensureDirs(config);

  const database = db.open(config.paths.db);
  const runId = db.startRun(database, 'prompt2');

  const totalCalls = database.prepare('SELECT COUNT(*) n FROM calls WHERE transcribed_at IS NOT NULL').get().n;
  if (totalCalls === 0) {
    database.close();
    throw new Error('No transcribed calls in sales.db. Run prompt 1 first.');
  }

  log(`Opening Jev over ${config.jev.transport}`);
  const judge = await openJudge({
    transport: config.jev.transport,
    tool: config.jev.tool,
    url: config.jev.url,
    apiKey: config.jev.apiKey,
  });
  if (judge.tool) {
    log(`  tool ${judge.tool}, parameters ${judge.claimKey} and ${judge.evidenceKey}`);
  }

  let judged = 0;
  let failed = 0;

  try {
    for (const question of RUBRIC) {
      const kind = question.scope;

      let ids = args.requery
        ? database
            .prepare(
              kind === 'call'
                ? 'SELECT id FROM calls WHERE transcribed_at IS NOT NULL ORDER BY date'
                : "SELECT id FROM emails WHERE direction = 'out' ORDER BY date"
            )
            .all()
            .map((r) => r.id)
        : db.untagged(database, kind, question.id);

      // Calls with no transcript cannot be judged, so leave them unanswered
      // rather than sending Jev an empty page and storing the result.
      if (kind === 'call' && !args.requery) {
        const transcribed = new Set(
          database.prepare('SELECT id FROM calls WHERE transcribed_at IS NOT NULL').all().map((r) => r.id)
        );
        ids = ids.filter((id) => transcribed.has(id));
      }

      if (args.limit) ids = ids.slice(0, args.limit);
      if (ids.length === 0) {
        log(`${question.id}: nothing to do`);
        continue;
      }

      log(`${question.id}: asking Jev about ${ids.length} ${kind}${ids.length === 1 ? '' : 's'}`);

      await pool(ids, config.jev.concurrency, async (id) => {
        const artifact =
          kind === 'call' ? db.callForJudging(database, id) : db.emailForJudging(database, id);
        if (!artifact) return;

        const evidence = kind === 'call' ? callEvidence(artifact) : emailEvidence(artifact);

        try {
          const verdict = await judge.judge(question.claim, evidence);
          db.saveTag(database, {
            kind,
            artifactId: id,
            questionId: question.id,
            answer: verdict.answer,
            probability: verdict.probability,
            confidence: verdict.confidence,
            model: verdict.model,
          });
          judged += 1;
        } catch (err) {
          // Record the failure as an unanswered tag. An unanswered question is
          // skipped by the analysis; an absent row would be retried forever.
          db.saveTag(database, {
            kind,
            artifactId: id,
            questionId: question.id,
            answer: null,
            probability: null,
            confidence: null,
            model: `error: ${err.message.slice(0, 120)}`,
          });
          failed += 1;
        }
      });
    }
  } finally {
    judge.close();
  }

  log(`\nJev answered ${judged} question${judged === 1 ? '' : 's'}${failed ? `, ${failed} failed` : ''}`);

  /* 5 and 6. Compare, then write it up ------------------------------ */

  const dataset = db.toDataset(database, { source: 'prompt2' });
  const analysis = analyze(dataset, config.thresholds);

  await writeFile(config.paths.findings, renderFindings(analysis));
  await writeFile(config.paths.dataset, JSON.stringify(dataset));

  const table = renderTable(analysis);
  const width = Math.max(...table.rows.map((r) => r.label.length), table.headers[0].length);

  log('');
  log(`${table.headers[0].padEnd(width)}   ${'WON'.padStart(4)}  ${'LOST'.padStart(4)}`);
  for (const row of table.rows) {
    const flag = row.isPattern ? '  <- pattern' : '';
    log(`${row.label.padEnd(width)}   ${row.won.padStart(4)}  ${row.lost.padStart(4)}${flag}`);
  }

  log('');
  log(`Wrote ${config.paths.findings}`);
  log(`Wrote ${config.paths.dataset}`);

  db.endRun(database, runId, true, `${judged} judgments, ${analysis.patterns.length} patterns`);
  database.close();
}

main().catch((err) => {
  console.error(`\nprompt 2 failed: ${err.message}`);
  process.exitCode = 1;
});
