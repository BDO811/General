#!/usr/bin/env node
/**
 * Prompt 1: build the database.
 *
 *   1. List every call hosted in the last N months from Fireflies and
 *      download each one's audio into ~/sales-coach/calls/.
 *   2. Send each audio file to Gemini and transcribe it with speaker labels,
 *      timestamps and a tone tag on every line. Save as calls/[id].json.
 *   3. For every prospect on those calls, pull every email sent to them and
 *      every reply from Gmail, with the date and word count.
 *   4. Look up each prospect's deal in HubSpot and record closed won, closed
 *      lost or open, plus the amount.
 *   5. Put it all in one SQLite file, ~/sales-coach/sales.db.
 *   6. Report the row counts and any call that could not be matched.
 *
 * Every step is resumable. Audio already on disk is not re-downloaded, calls
 * already transcribed are not re-sent, and every write is an upsert. Killing
 * this halfway and running it again costs nothing but the step it was on.
 *
 * Usage:
 *   node pipeline/run-prompt1.mjs [--months 12] [--limit 20] [--dry-run]
 */

import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';

import { loadConfig, ensureDirs, requireKeys, windowStart } from './config.mjs';
import * as db from './db.mjs';
import * as fireflies from './connectors/fireflies.mjs';
import * as gemini from './connectors/gemini.mjs';
import * as gmail from './connectors/gmail.mjs';
import * as hubspot from './connectors/hubspot.mjs';
import { pool } from './connectors/http.mjs';

const args = parseArgs(process.argv.slice(2));
const config = loadConfig(args.months ? { LOOKBACK_MONTHS: String(args.months) } : {});

function parseArgs(argv) {
  const out = { dryRun: false, limit: null, months: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--dry-run') out.dryRun = true;
    else if (argv[i] === '--limit') out.limit = Number(argv[++i]);
    else if (argv[i] === '--months') out.months = Number(argv[++i]);
  }
  return out;
}

const log = (...a) => console.log(...a);
const warn = (...a) => console.warn(...a);

async function main() {
  requireKeys(config, ['seller', 'fireflies', 'gemini', 'gmail', 'hubspot']);
  ensureDirs(config);

  const database = db.open(config.paths.db);
  const runId = db.startRun(database, 'prompt1');
  const problems = [];

  try {
    /* 1. Calls and audio -------------------------------------------- */

    const from = windowStart(config);
    log(`Listing calls since ${from.toISOString().slice(0, 10)} for ${config.seller.email}`);

    const raw = await fireflies.listCalls({
      apiKey: config.fireflies.apiKey,
      hostEmail: config.seller.email,
      fromDate: from,
      toDate: new Date(),
    });

    let calls = raw.map((t) => fireflies.normalise(t, { sellerEmail: config.seller.email }));
    if (args.limit) calls = calls.slice(0, args.limit);
    log(`Found ${calls.length} calls`);

    if (args.dryRun) {
      log('Dry run. Stopping before anything is downloaded or written.');
      db.endRun(database, runId, true, 'dry run');
      return;
    }

    await pool(calls, 4, async (call) => {
      try {
        call.audioPath = await fireflies.downloadAudio({
          call,
          dir: config.paths.calls,
          apiKey: config.fireflies.apiKey,
        });
        if (!call.audioPath) problems.push(`${call.id}: no audio URL`);
      } catch (err) {
        problems.push(`${call.id}: audio download failed, ${err.message}`);
      }
    });

    /* 2. Prospects from the CRM ------------------------------------- */
    // Done before transcription so a call whose prospect cannot be resolved
    // is visible before paying Gemini to transcribe it.

    const prospectEmails = [...new Set(calls.map((c) => c.prospectEmail).filter(Boolean))];
    log(`Resolving ${prospectEmails.length} prospects in HubSpot`);

    const resolved = await hubspot.resolveAll({
      token: config.hubspot.token,
      emails: prospectEmails,
    });

    const prospectByEmail = new Map();
    for (const r of resolved) {
      const fromCall = calls.find((c) => c.prospectEmail === r.email);
      const record = {
        id: r.email,
        email: r.email,
        name: r.name ?? fromCall?.prospectName ?? null,
        company: r.company ?? null,
        title: r.title ?? null,
        outcome: r.outcome,
        amount: r.amount,
        closedAt: r.closedAt,
        hubspotContactId: r.contactId,
        hubspotDealId: r.dealId,
      };
      db.upsertProspect(database, record);
      prospectByEmail.set(r.email, record);
      if (r.outcome === 'none') problems.push(`${r.email}: no matching deal in HubSpot`);
    }

    for (const call of calls) {
      db.upsertCall(database, {
        id: call.id,
        prospectId: call.prospectEmail ?? null,
        title: call.title,
        date: call.date,
        durationSec: call.durationSec,
        audioPath: call.audioPath ?? null,
      });
      if (!call.prospectEmail) problems.push(`${call.id}: no outside attendee on the invite`);
    }

    /* 3. Transcription ---------------------------------------------- */

    const pending = db.callsNeedingTranscript(database).filter((c) => c.audio_path);
    log(`Transcribing ${pending.length} calls with ${config.gemini.model}`);

    let done = 0;
    await pool(pending, config.gemini.concurrency, async (row) => {
      try {
        const transcript = await gemini.transcribe({
          apiKey: config.gemini.apiKey,
          path: row.audio_path,
          callId: row.id,
          sellerName: config.seller.name,
          model: config.gemini.model,
        });

        const jsonPath = join(config.paths.calls, `${row.id}.json`);
        await writeFile(jsonPath, JSON.stringify(transcript, null, 2));

        db.replaceCallLines(database, row.id, transcript.lines);
        db.upsertCall(database, {
          id: row.id,
          date: row.date,
          transcriptPath: jsonPath,
          transcribedAt: new Date().toISOString(),
        });

        done += 1;
        if (done % 10 === 0) log(`  ${done}/${pending.length}`);
      } catch (err) {
        problems.push(`${row.id}: transcription failed, ${err.message}`);
      }
    });

    /* 4. Email threads ---------------------------------------------- */

    log(`Pulling email threads for ${prospectEmails.length} prospects`);
    let emailCount = 0;

    await pool(prospectEmails, 3, async (email) => {
      try {
        const messages = await gmail.threadWith({
          token: config.gmail.token,
          prospectEmail: email,
          sellerEmail: config.seller.email,
        });
        for (const m of messages) {
          db.upsertEmail(database, {
            id: m.id,
            threadId: m.threadId,
            prospectId: email,
            direction: m.direction,
            date: m.date,
            subject: m.subject,
            words: m.words,
            body: m.body,
          });
          emailCount += 1;
        }
      } catch (err) {
        problems.push(`${email}: email pull failed, ${err.message}`);
      }
    });

    /* 5 and 6. Report ------------------------------------------------ */

    const counts = {
      prospects: database.prepare('SELECT COUNT(*) n FROM prospects').get().n,
      calls: database.prepare('SELECT COUNT(*) n FROM calls').get().n,
      transcribed: database.prepare('SELECT COUNT(*) n FROM calls WHERE transcribed_at IS NOT NULL').get().n,
      lines: database.prepare('SELECT COUNT(*) n FROM call_lines').get().n,
      emails: database.prepare('SELECT COUNT(*) n FROM emails').get().n,
      sent: database.prepare("SELECT COUNT(*) n FROM emails WHERE direction = 'out'").get().n,
      noDeal: database
        .prepare("SELECT COUNT(*) n FROM calls c LEFT JOIN prospects p ON p.id = c.prospect_id WHERE COALESCE(p.outcome,'none') = 'none'")
        .get().n,
    };

    const dataset = db.toDataset(database, { source: 'prompt1' });
    await writeFile(config.paths.dataset, JSON.stringify(dataset));

    log('');
    log(`Done. ${config.paths.db}`);
    log(`  prospects        ${counts.prospects}`);
    log(`  calls            ${counts.calls} (${counts.transcribed} transcribed, ${counts.lines} lines)`);
    log(`  emails           ${counts.emails} (${counts.sent} sent by you)`);
    log(`  calls with no matching deal  ${counts.noDeal}`);
    log(`  workbench export ${config.paths.dataset}`);

    if (problems.length) {
      log('');
      warn(`${problems.length} thing${problems.length === 1 ? '' : 's'} could not be matched:`);
      for (const p of problems.slice(0, 40)) warn(`  ${p}`);
      if (problems.length > 40) warn(`  and ${problems.length - 40} more`);
    }

    db.endRun(database, runId, true, `${counts.calls} calls, ${counts.emails} emails, ${problems.length} problems`);
  } catch (err) {
    db.endRun(database, runId, false, err.message);
    throw err;
  } finally {
    database.close();
  }
}

main().catch((err) => {
  console.error(`\nprompt 1 failed: ${err.message}`);
  process.exitCode = 1;
});
