/**
 * The demo dataset exists to prove the engine, so it is pinned to the exact
 * figures the source reel puts on screen. If a change to the analysis moves
 * any of these, the build fails here rather than the demo quietly showing
 * different numbers from the ones it claims to reproduce.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

import { analyze, VERDICT, resultFor } from '../engine/analysis.js';
import { renderFindings, renderTable } from '../engine/findings.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const dataset = JSON.parse(
  readFileSync(resolve(HERE, '../data/demo-dataset.json'), 'utf8')
);
const analysis = analyze(dataset);

/** Every figure the reel shows, as a single table. */
const REEL = [
  { id: 'rapport_first', won: 71, lost: 29, verdict: VERDICT.PATTERN },
  { id: 'matched_tone', won: 64, lost: 41, verdict: VERDICT.PATTERN },
  { id: 'held_price_first_objection', won: 58, lost: 22, verdict: VERDICT.PATTERN },
  { id: 'asked_goal_before_price', won: 82, lost: 77, verdict: VERDICT.NO_CLEAR_PATTERN },
  { id: 'email_length_matched', won: 16, lost: 18, verdict: VERDICT.NO_CLEAR_PATTERN },
];

test('headline totals match the reel', () => {
  assert.equal(analysis.totals.calls, 214, '214 calls');
  assert.equal(analysis.totals.taggedEmails, 1122, '1,122 emails');
  assert.equal(analysis.totals.callsWithoutDeal, 9, '9 calls had no matching deal');
});

for (const expected of REEL) {
  test(`${expected.id} reads ${expected.won}% won against ${expected.lost}% lost`, () => {
    const r = resultFor(analysis, expected.id);
    assert.ok(r, `${expected.id} is in the rubric`);
    assert.equal(r.won.pct, expected.won);
    assert.equal(r.lost.pct, expected.lost);
    assert.equal(r.verdict, expected.verdict);
  });
}

test('the three call patterns come out in the order the reel lists them', () => {
  const callPatterns = analysis.patterns.filter((p) => p.scope === 'call').map((p) => p.id);
  assert.deepEqual(callPatterns, [
    'rapport_first',
    'held_price_first_objection',
    'matched_tone',
  ]);
});

test('findings.md carries the headline line and every pattern', () => {
  const md = renderFindings(analysis);
  assert.match(md, /214 calls · 1,122 emails · tagged by Jev/);
  assert.match(md, /### 1\. Rapport first/);
  assert.match(md, /Yes on 71% of wins, 29% of losses\./);
  assert.match(md, /### No clear pattern/);
  assert.match(md, /asked goal before price \(82% vs 77%\)/);
  assert.match(md, /email length matched theirs \(16% vs 18%\)/);
  assert.match(md, /> Read this before every call prep\./);
});

test('findings.md contains no em dash, en dash or ellipsis', () => {
  const md = renderFindings(analysis, { includeStats: true });
  assert.ok(!/[\u2013\u2014\u2026]/.test(md), 'no dash or ellipsis characters');
});

test('the rendered table matches the on-screen grid', () => {
  const table = renderTable(analysis);
  assert.deepEqual(table.headers, ['JEV QUESTION', 'WON', 'LOST']);
  const byId = Object.fromEntries(table.rows.map((r) => [r.id, r]));
  assert.equal(byId.rapport_first.won, '71%');
  assert.equal(byId.rapport_first.lost, '29%');
  assert.equal(byId.rapport_first.isPattern, true);
  assert.equal(byId.email_length_matched.isPattern, false);
});

test('the dataset is internally consistent', () => {
  const ids = new Set(dataset.prospects.map((p) => p.id));
  for (const c of dataset.calls) {
    assert.ok(ids.has(c.prospectId), `call ${c.id} points at a real prospect`);
  }
  for (const e of dataset.emails) {
    assert.ok(ids.has(e.prospectId), `email ${e.id} points at a real prospect`);
  }
  const callIds = new Set(dataset.calls.map((c) => c.id));
  assert.equal(callIds.size, dataset.calls.length, 'call ids are unique');
  const emailIds = new Set(dataset.emails.map((e) => e.id));
  assert.equal(emailIds.size, dataset.emails.length, 'email ids are unique');
});

test('every graded email is the seller side and carries a full tag set', () => {
  const graded = dataset.emails.filter((e) => e.direction === 'out');
  assert.equal(graded.length, 1122);
  for (const e of graded) {
    assert.equal(typeof e.tags.email_length_matched, 'boolean');
    assert.equal(typeof e.tags.email_ends_with_question, 'boolean');
  }
  const replies = dataset.emails.filter((e) => e.direction === 'in');
  assert.ok(replies.length > 0, 'replies are present so length can be compared');
  for (const e of replies) assert.equal(e.tags, undefined, 'replies are not graded');
});

test('the demo prospect from the reel is present and closed won', () => {
  const steve = dataset.prospects.find((p) => p.name === 'Steve Arden');
  assert.ok(steve, 'Steve Arden is in the book');
  assert.equal(steve.company, 'Corvell Roofing');
  assert.equal(steve.outcome, 'closed_won');
});

test('the dataset says in the file itself that it is synthetic', () => {
  assert.match(dataset.meta.note, /[Ss]ynthetic/);
  assert.match(dataset.meta.note, /No real prospect/);
});
