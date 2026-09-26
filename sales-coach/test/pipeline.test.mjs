/**
 * Pipeline tests.
 *
 * Nothing here touches the network. The connectors are exercised through the
 * pure parts that decide what gets stored: outcome mapping, deal selection,
 * email cleanup, verdict parsing, evidence rendering, and the sales.db round
 * trip into the shape the engine reads.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import * as db from '../pipeline/db.mjs';
import { outcomeFromStage, pickDeal } from '../pipeline/connectors/hubspot.mjs';
import { stripQuoted, wordCount, addressOf } from '../pipeline/connectors/gmail.mjs';
import { parseVerdict, callEvidence, emailEvidence } from '../pipeline/connectors/jev.mjs';
import { normalise } from '../pipeline/connectors/fireflies.mjs';
import { analyze, resultFor } from '../engine/analysis.js';
import { loadEnvFile } from '../pipeline/config.mjs';
import { writeFileSync } from 'node:fs';

function tempDb() {
  const dir = mkdtempSync(join(tmpdir(), 'sales-coach-'));
  const path = join(dir, 'sales.db');
  return { dir, path, database: db.open(path) };
}

/* ------------------------------------------------------------------ */
/* HubSpot outcome mapping                                             */
/* ------------------------------------------------------------------ */

test('built-in HubSpot stage ids map to the right bucket', () => {
  assert.equal(outcomeFromStage('closedwon'), 'closed_won');
  assert.equal(outcomeFromStage('closedlost'), 'closed_lost');
  assert.equal(outcomeFromStage('appointmentscheduled'), 'open');
  assert.equal(outcomeFromStage('qualifiedtobuy'), 'open');
});

test('custom stage labels are matched on the words', () => {
  assert.equal(outcomeFromStage('Closed Won'), 'closed_won');
  assert.equal(outcomeFromStage('closed-lost'), 'closed_lost');
  assert.equal(outcomeFromStage('CLOSED_WON'), 'closed_won');
  assert.equal(outcomeFromStage('won'), 'closed_won');
});

test('an unrecognised stage is open, never lost', () => {
  // Guessing lost would inflate every loss rate in the findings.
  assert.equal(outcomeFromStage('negotiation phase 2'), 'open');
  assert.equal(outcomeFromStage(''), 'open');
  assert.equal(outcomeFromStage(null), 'open');
  assert.equal(outcomeFromStage(undefined), 'open');
});

test('a closed deal beats an open one when a prospect has several', () => {
  const best = pickDeal([
    { id: '1', properties: { dealstage: 'appointmentscheduled', closedate: '2026-09-01' } },
    { id: '2', properties: { dealstage: 'closedlost', closedate: '2026-03-01' } },
  ]);
  assert.equal(best.deal.id, '2');
  assert.equal(best.outcome, 'closed_lost');
});

test('among closed deals the most recent wins', () => {
  const best = pickDeal([
    { id: 'old', properties: { dealstage: 'closedlost', closedate: '2025-01-01' } },
    { id: 'new', properties: { dealstage: 'closedwon', closedate: '2026-06-01' } },
  ]);
  assert.equal(best.deal.id, 'new');
  assert.equal(best.outcome, 'closed_won');
});

test('no deals means no pick', () => {
  assert.equal(pickDeal([]), null);
  assert.equal(pickDeal(null), null);
});

/* ------------------------------------------------------------------ */
/* Gmail cleanup                                                       */
/* ------------------------------------------------------------------ */

test('quoted history is stripped so length comparisons mean something', () => {
  const raw = [
    'Sounds good, Tuesday works.',
    '',
    'On Mon, Sep 1, 2026 at 9:14 AM Steve Arden wrote:',
    '> Can we push to Tuesday?',
    '> Thanks',
  ].join('\n');
  assert.equal(stripQuoted(raw), 'Sounds good, Tuesday works.');
  assert.equal(wordCount(raw), 4);
});

test('signature blocks are cut at the delimiter', () => {
  const raw = 'Here is the quote.\n\n--\nJane Doe\nVP Sales\n555 1234';
  assert.equal(stripQuoted(raw), 'Here is the quote.');
});

test('a forwarded header ends the body', () => {
  const raw = 'Passing this along.\n\nFrom: someone@else.com\nSubject: old thread';
  assert.equal(stripQuoted(raw), 'Passing this along.');
});

test('an email with no quoting survives unchanged', () => {
  const raw = 'Short one. Does Thursday work for you?';
  assert.equal(stripQuoted(raw), raw);
  assert.equal(wordCount(raw), 7);
});

test('word count of an empty body is zero, not NaN', () => {
  assert.equal(wordCount(''), 0);
  assert.equal(wordCount('   \n  '), 0);
});

test('addresses are pulled out of display-name headers', () => {
  assert.equal(addressOf('Steve Arden <steve@corvellroofing.com>'), 'steve@corvellroofing.com');
  assert.equal(addressOf('steve@corvellroofing.com'), 'steve@corvellroofing.com');
  assert.equal(addressOf('"Arden, Steve" <Steve@Corvell.com>'), 'steve@corvell.com');
  assert.equal(addressOf(null), null);
  assert.equal(addressOf('no address here'), null);
});

/* ------------------------------------------------------------------ */
/* Fireflies normalisation                                             */
/* ------------------------------------------------------------------ */

test('the prospect is the attendee outside the seller domain', () => {
  const call = normalise(
    {
      id: 'T1',
      title: 'Discovery',
      date: '2026-05-04T15:00:00.000Z',
      duration: 32,
      audio_url: 'https://example.com/a.mp3',
      meeting_attendees: [
        { displayName: 'You', email: 'you@yourco.com' },
        { displayName: 'Colleague', email: 'sam@yourco.com' },
        { displayName: 'Steve Arden', email: 'steve@corvellroofing.com' },
      ],
    },
    { sellerEmail: 'you@yourco.com' }
  );

  assert.equal(call.prospectEmail, 'steve@corvellroofing.com');
  assert.equal(call.prospectName, 'Steve Arden');
  assert.equal(call.date, '2026-05-04');
  assert.equal(call.durationSec, 1920);
});

test('an internal-only call gets no prospect rather than a wrong one', () => {
  const call = normalise(
    {
      id: 'T2',
      date: '2026-05-04T15:00:00.000Z',
      meeting_attendees: [
        { displayName: 'You', email: 'you@yourco.com' },
        { displayName: 'Colleague', email: 'sam@yourco.com' },
      ],
    },
    { sellerEmail: 'you@yourco.com' }
  );
  assert.equal(call.prospectEmail, null);
});

/* ------------------------------------------------------------------ */
/* Jev verdict parsing                                                 */
/* ------------------------------------------------------------------ */

test('a JSON verdict in an MCP text block is read', () => {
  const v = parseVerdict({
    content: [{ type: 'text', text: JSON.stringify({ verdict: true, probability: 0.93, confidence: 0.88 }) }],
  });
  assert.equal(v.answer, true);
  assert.equal(v.probability, 0.93);
  assert.equal(v.confidence, 0.88);
});

test('alternative field names are understood', () => {
  assert.equal(parseVerdict({ answer: false }).answer, false);
  assert.equal(parseVerdict({ supported: 'yes' }).answer, true);
  assert.equal(parseVerdict({ decision: 'NO' }).answer, false);
  assert.equal(parseVerdict({ result: 'unsupported' }).answer, false);
});

test('a bare probability is read as the verdict', () => {
  assert.equal(parseVerdict({ probability: 0.79 }).answer, true);
  assert.equal(parseVerdict({ probabilities: { true: 0.12 } }).answer, false);
});

test('a probability sitting exactly on the fence stays unanswered', () => {
  const v = parseVerdict({ probability: 0.5 });
  assert.equal(v.answer, null);
  assert.equal(v.probability, 0.5);
});

test('plain text verdicts are read, and anything else is unanswered', () => {
  assert.equal(parseVerdict({ content: [{ type: 'text', text: 'yes, clearly' }] }).answer, true);
  assert.equal(parseVerdict({ content: [{ type: 'text', text: 'No.' }] }).answer, false);
  assert.equal(parseVerdict({ content: [{ type: 'text', text: 'it depends' }] }).answer, null);
  assert.equal(parseVerdict({}).answer, null);
});

/* ------------------------------------------------------------------ */
/* Evidence rendering                                                  */
/* ------------------------------------------------------------------ */

test('call evidence keeps timestamps and tone on every line', () => {
  const text = callEvidence({
    id: '01K7Q3',
    title: 'Discovery',
    date: '2026-05-04',
    lines: [
      { t: '00:04', speaker: 'me', text: "Hey Steve, how's your week?", tone: 'warm' },
      { t: '00:07', speaker: 'Steve', text: 'Honestly? Slammed.', tone: 'flat' },
    ],
  });
  assert.match(text, /Call 01K7Q3: Discovery on 2026-05-04/);
  assert.match(text, /\[00:04\] me \(warm\): Hey Steve/);
  assert.match(text, /\[00:07\] Steve \(flat\): Honestly\? Slammed\./);
});

test('an untagged line says untagged rather than dropping the tag silently', () => {
  const text = callEvidence({ id: 'X', date: '2026-01-01', lines: [{ t: '00:01', speaker: 'me', text: 'Hi', tone: null }] });
  assert.match(text, /\(untagged\)/);
});

test('email evidence states both sides of the length comparison', () => {
  const text = emailEvidence({
    date: '2026-05-05',
    subject: 'Quote',
    words: 120,
    body: 'Here is the quote. Does Thursday work?',
    theirs: [{ words: 40 }, { words: 60 }],
  });
  assert.match(text, /Length: 120 words/);
  assert.match(text, /average 50 words \(40, 60\)/);
  assert.match(text, /Does Thursday work\?/);
});

test('email evidence says so when there is nothing to compare against', () => {
  const text = emailEvidence({ date: '2026-05-05', words: 90, body: 'Hello.', theirs: [] });
  assert.match(text, /The prospect has not replied in this thread\./);
  assert.ok(!text.includes('NaN'));
});

/* ------------------------------------------------------------------ */
/* sales.db round trip                                                 */
/* ------------------------------------------------------------------ */

test('timestamps parse into seconds, and refuse to guess', () => {
  assert.equal(db.toSeconds('14:52'), 892);
  assert.equal(db.toSeconds('01:14:52'), 4492);
  assert.equal(db.toSeconds('00:04'), 4);
  assert.equal(db.toSeconds('nonsense'), null);
  assert.equal(db.toSeconds(null), null);
});

test('sales.db round trips into the shape the engine reads', () => {
  const { dir, database } = tempDb();
  try {
    db.upsertProspect(database, {
      id: 'steve@corvellroofing.com',
      email: 'steve@corvellroofing.com',
      name: 'Steve Arden',
      company: 'Corvell Roofing',
      outcome: 'closed_won',
      amount: 18400,
    });
    db.upsertProspect(database, {
      id: 'dana@northstar.com',
      email: 'dana@northstar.com',
      name: 'Dana Okafor',
      outcome: 'closed_lost',
    });

    db.upsertCall(database, { id: 'C1', prospectId: 'steve@corvellroofing.com', date: '2026-05-04', durationSec: 1920 });
    db.upsertCall(database, { id: 'C2', prospectId: 'dana@northstar.com', date: '2026-05-06' });

    db.replaceCallLines(database, 'C1', [
      { t: '00:04', speaker: 'me', text: 'Hey Steve', tone: 'warm' },
      { t: '14:52', speaker: 'me', text: 'So the investment is 4,800.', tone: 'confident' },
    ]);

    db.upsertEmail(database, { id: 'E1', threadId: 'T1', prospectId: 'steve@corvellroofing.com', direction: 'out', date: '2026-05-05', words: 60 });
    db.upsertEmail(database, { id: 'E2', threadId: 'T1', prospectId: 'steve@corvellroofing.com', direction: 'in', date: '2026-05-05', words: 40 });

    db.saveTag(database, { kind: 'call', artifactId: 'C1', questionId: 'rapport_first', answer: true, probability: 0.93 });
    db.saveTag(database, { kind: 'call', artifactId: 'C2', questionId: 'rapport_first', answer: false, probability: 0.12 });
    db.saveTag(database, { kind: 'email', artifactId: 'E1', questionId: 'email_ends_with_question', answer: true });

    const dataset = db.toDataset(database);

    assert.equal(dataset.prospects.length, 2);
    assert.equal(dataset.calls.length, 2);
    assert.equal(dataset.emails.length, 2);

    const c1 = dataset.calls.find((c) => c.id === 'C1');
    assert.equal(c1.prospectId, 'steve@corvellroofing.com');
    assert.equal(c1.tags.rapport_first, true);

    const inbound = dataset.emails.find((e) => e.id === 'E2');
    assert.equal(inbound.tags, undefined, 'replies carry no tag object');

    // The engine reads it without any adaptation in between.
    const a = analyze(dataset);
    assert.equal(a.totals.calls, 2);
    assert.equal(a.totals.taggedEmails, 1);
    assert.equal(resultFor(a, 'rapport_first').won.yes, 1);
    assert.equal(resultFor(a, 'rapport_first').lost.yes, 0);

    // Transcript lines are queryable by time, which is what "the first five
    // minutes" needs to be a WHERE clause rather than a guess.
    const early = database
      .prepare('SELECT COUNT(*) n FROM call_lines WHERE call_id = ? AND t_sec < 300')
      .get('C1').n;
    assert.equal(early, 1);
  } finally {
    database.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

test('re-running a step upserts rather than duplicating', () => {
  const { dir, database } = tempDb();
  try {
    for (let i = 0; i < 3; i++) {
      db.upsertProspect(database, { id: 'p@x.com', email: 'p@x.com', name: 'P', outcome: 'closed_won' });
      db.upsertCall(database, { id: 'C1', prospectId: 'p@x.com', date: '2026-01-01' });
      db.upsertEmail(database, { id: 'E1', prospectId: 'p@x.com', direction: 'out', date: '2026-01-01', words: 10 });
      db.saveTag(database, { kind: 'call', artifactId: 'C1', questionId: 'rapport_first', answer: i === 2 });
      db.replaceCallLines(database, 'C1', [{ t: '00:01', speaker: 'me', text: 'Hi', tone: 'warm' }]);
    }

    assert.equal(database.prepare('SELECT COUNT(*) n FROM prospects').get().n, 1);
    assert.equal(database.prepare('SELECT COUNT(*) n FROM calls').get().n, 1);
    assert.equal(database.prepare('SELECT COUNT(*) n FROM emails').get().n, 1);
    assert.equal(database.prepare('SELECT COUNT(*) n FROM tags').get().n, 1);
    assert.equal(database.prepare('SELECT COUNT(*) n FROM call_lines').get().n, 1, 'lines are replaced, not appended');
    assert.equal(database.prepare('SELECT answer FROM tags').get().answer, 1, 'the newest answer wins');
  } finally {
    database.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

test('untagged finds exactly the work still outstanding', () => {
  const { dir, database } = tempDb();
  try {
    db.upsertProspect(database, { id: 'p@x.com', email: 'p@x.com', outcome: 'closed_won' });
    db.upsertCall(database, { id: 'C1', prospectId: 'p@x.com', date: '2026-01-01' });
    db.upsertCall(database, { id: 'C2', prospectId: 'p@x.com', date: '2026-01-02' });
    db.upsertEmail(database, { id: 'E1', prospectId: 'p@x.com', direction: 'out', date: '2026-01-01', words: 10 });
    db.upsertEmail(database, { id: 'E2', prospectId: 'p@x.com', direction: 'in', date: '2026-01-01', words: 10 });

    assert.deepEqual(db.untagged(database, 'call', 'rapport_first'), ['C1', 'C2']);
    assert.deepEqual(db.untagged(database, 'email', 'email_ends_with_question'), ['E1'], 'replies are never queued');

    db.saveTag(database, { kind: 'call', artifactId: 'C1', questionId: 'rapport_first', answer: true });
    assert.deepEqual(db.untagged(database, 'call', 'rapport_first'), ['C2']);

    // An answer Jev could not give still counts as done, so it is not retried
    // on every run forever.
    db.saveTag(database, { kind: 'call', artifactId: 'C2', questionId: 'rapport_first', answer: null });
    assert.deepEqual(db.untagged(database, 'call', 'rapport_first'), []);
  } finally {
    database.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

test('the graded view excludes replies and carries the outcome through', () => {
  const { dir, database } = tempDb();
  try {
    db.upsertProspect(database, { id: 'w@x.com', email: 'w@x.com', outcome: 'closed_won' });
    db.upsertEmail(database, { id: 'E1', prospectId: 'w@x.com', direction: 'out', date: '2026-01-01', words: 10 });
    db.upsertEmail(database, { id: 'E2', prospectId: 'w@x.com', direction: 'in', date: '2026-01-01', words: 10 });
    db.saveTag(database, { kind: 'email', artifactId: 'E1', questionId: 'email_length_matched', answer: true });
    db.saveTag(database, { kind: 'email', artifactId: 'E2', questionId: 'email_length_matched', answer: true });

    const rows = database.prepare('SELECT * FROM graded').all();
    assert.equal(rows.length, 1);
    assert.equal(rows[0].artifact_id, 'E1');
    assert.equal(rows[0].outcome, 'closed_won');
  } finally {
    database.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

test('a call whose prospect is unknown reads as no deal through the view', () => {
  const { dir, database } = tempDb();
  try {
    db.upsertCall(database, { id: 'C9', prospectId: null, date: '2026-01-01' });
    db.saveTag(database, { kind: 'call', artifactId: 'C9', questionId: 'rapport_first', answer: true });
    const row = database.prepare('SELECT * FROM graded').get();
    assert.equal(row.outcome, 'none');
  } finally {
    database.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

/* ------------------------------------------------------------------ */
/* Config                                                              */
/* ------------------------------------------------------------------ */

test('the env reader handles comments, blanks and quoting', () => {
  const dir = mkdtempSync(join(tmpdir(), 'sales-coach-env-'));
  const path = join(dir, '.env');
  writeFileSync(
    path,
    ['# a comment', '', 'PLAIN=value', 'QUOTED="with spaces"', "SINGLE='also'", 'EQUALS=a=b', 'NOEQUALS'].join('\n')
  );
  try {
    const env = loadEnvFile(path);
    assert.equal(env.PLAIN, 'value');
    assert.equal(env.QUOTED, 'with spaces');
    assert.equal(env.SINGLE, 'also');
    assert.equal(env.EQUALS, 'a=b', 'only the first equals splits');
    assert.equal('NOEQUALS' in env, false);
    assert.equal('# a comment' in env, false);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('a missing env file is empty rather than an error', () => {
  assert.deepEqual(loadEnvFile('/definitely/not/a/path/.env'), {});
});
