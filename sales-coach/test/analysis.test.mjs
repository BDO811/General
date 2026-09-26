import { test } from 'node:test';
import assert from 'node:assert/strict';
import { analyze, resultFor, VERDICT, DEFAULT_THRESHOLDS } from '../engine/analysis.js';

/**
 * Build a small dataset by hand.
 *
 * `spec` is {won: [yes, n], lost: [yes, n]} per question id. Every artifact
 * gets its own prospect so the outcome bucketing is unambiguous.
 */
function build(spec, scope = 'call') {
  const prospects = [];
  const calls = [];
  const emails = [];
  let seq = 0;

  const push = (outcome, count, yesCount, questionId) => {
    for (let i = 0; i < count; i++) {
      seq += 1;
      const id = `P${seq}`;
      prospects.push({ id, name: `Prospect ${seq}`, outcome });
      const artifact = {
        id: `A${seq}`,
        prospectId: id,
        date: '2026-01-01',
        tags: { [questionId]: i < yesCount },
      };
      if (scope === 'call') calls.push(artifact);
      else emails.push({ ...artifact, direction: 'out' });
    }
  };

  for (const [questionId, groups] of Object.entries(spec)) {
    push('closed_won', groups.won[1], groups.won[0], questionId);
    push('closed_lost', groups.lost[1], groups.lost[0], questionId);
  }

  return { prospects, calls, emails };
}

test('a wide gap on a healthy sample is a pattern', () => {
  const ds = build({ rapport_first: { won: [40, 50], lost: [10, 50] } });
  const r = resultFor(analyze(ds), 'rapport_first');
  assert.equal(r.verdict, VERDICT.PATTERN);
  assert.equal(r.won.pct, 80);
  assert.equal(r.lost.pct, 20);
  assert.equal(r.direction, 'helps');
  assert.ok(r.p < 0.001);
});

test('a narrow gap is reported as no clear pattern, not as advice', () => {
  const ds = build({ asked_goal_before_price: { won: [41, 50], lost: [38, 50] } });
  const r = resultFor(analyze(ds), 'asked_goal_before_price');
  assert.equal(r.verdict, VERDICT.NO_CLEAR_PATTERN);
  assert.match(r.reason, /under the 15 point floor/);
});

test('a wide gap on a tiny sample is insufficient data, not a pattern', () => {
  const ds = build({ matched_tone: { won: [4, 4], lost: [0, 4] } });
  const r = resultFor(analyze(ds), 'matched_tone');
  assert.equal(r.verdict, VERDICT.INSUFFICIENT_DATA);
  assert.match(r.reason, /at least 10 closed won/);
});

test('sample size is checked before the gap, so 4 against 4 never reads as flat', () => {
  const ds = build({ matched_tone: { won: [2, 4], lost: [2, 4] } });
  const r = resultFor(analyze(ds), 'matched_tone');
  assert.equal(r.verdict, VERDICT.INSUFFICIENT_DATA);
});

test('a wide gap that fails the significance test is not a pattern', () => {
  // 8/11 against 4/11 is a 36 point gap, but the sample is too thin to trust.
  const ds = build({ held_price_first_objection: { won: [8, 11], lost: [4, 11] } });
  const r = resultFor(analyze(ds), 'held_price_first_objection');
  assert.ok(Math.abs(r.gapPp) > DEFAULT_THRESHOLDS.minGapPp, 'the gap really is wide');
  assert.equal(r.verdict, VERDICT.NO_CLEAR_PATTERN);
  assert.match(r.reason, /p is/);
});

test('a gap running the other way is flagged as hurting', () => {
  const ds = build({ rapport_first: { won: [10, 50], lost: [40, 50] } });
  const r = resultFor(analyze(ds), 'rapport_first');
  assert.equal(r.verdict, VERDICT.PATTERN);
  assert.equal(r.direction, 'hurts');
  assert.ok(r.gapPp < 0);
});

test('calls with no matching deal are counted but held out of the comparison', () => {
  const ds = build({ rapport_first: { won: [40, 50], lost: [10, 50] } });
  ds.prospects.push({ id: 'PX', name: 'No deal', outcome: 'none' });
  for (let i = 0; i < 9; i++) {
    ds.calls.push({ id: `NX${i}`, prospectId: 'PX', date: '2026-02-02', tags: { rapport_first: true } });
  }

  const a = analyze(ds);
  assert.equal(a.totals.callsWithoutDeal, 9);
  const r = resultFor(a, 'rapport_first');
  assert.equal(r.won.n, 50, 'the 9 did not leak into won');
  assert.equal(r.lost.n, 50, 'the 9 did not leak into lost');
});

test('open deals are counted and held out the same way', () => {
  const ds = build({ rapport_first: { won: [40, 50], lost: [10, 50] } });
  ds.prospects.push({ id: 'PO', name: 'Still open', outcome: 'open' });
  ds.calls.push({ id: 'OC1', prospectId: 'PO', date: '2026-03-03', tags: { rapport_first: true } });

  const a = analyze(ds);
  assert.equal(a.totals.callOutcomes.open, 1);
  const r = resultFor(a, 'rapport_first');
  assert.equal(r.won.n + r.lost.n, 100);
});

test('an unanswered question is skipped, not scored as no', () => {
  const ds = build({ rapport_first: { won: [40, 50], lost: [10, 50] } });
  // Two more won calls where Jev returned nothing.
  ds.prospects.push({ id: 'PU', name: 'Unanswered', outcome: 'closed_won' });
  ds.calls.push({ id: 'U1', prospectId: 'PU', date: '2026-04-04', tags: { rapport_first: null } });
  ds.calls.push({ id: 'U2', prospectId: 'PU', date: '2026-04-05', tags: {} });

  const r = resultFor(analyze(ds), 'rapport_first');
  assert.equal(r.won.n, 50, 'denominator is unchanged');
  assert.equal(r.won.pct, 80, 'rate is not dragged down');
  assert.equal(r.skipped, 2);
});

test('inbound emails are never graded', () => {
  const ds = build({ email_ends_with_question: { won: [40, 50], lost: [10, 50] } }, 'email');
  const before = resultFor(analyze(ds), 'email_ends_with_question');

  ds.prospects.push({ id: 'PR', name: 'Replier', outcome: 'closed_won' });
  for (let i = 0; i < 30; i++) {
    ds.emails.push({
      id: `IN${i}`,
      prospectId: 'PR',
      direction: 'in',
      date: '2026-05-05',
      words: 20,
      tags: { email_ends_with_question: false },
    });
  }

  const after = analyze(ds);
  const r = resultFor(after, 'email_ends_with_question');
  assert.equal(r.won.n, before.won.n, 'replies did not enter the denominator');
  assert.equal(after.totals.taggedEmails, 100, 'only the seller side is counted as graded');
  assert.equal(after.totals.allEmails, 130);
});

test('thresholds can be tightened and the verdict follows', () => {
  const ds = build({ matched_tone: { won: [35, 50], lost: [15, 50] } });
  assert.equal(resultFor(analyze(ds), 'matched_tone').verdict, VERDICT.PATTERN);
  const strict = analyze(ds, { minGapPp: 50 });
  assert.equal(resultFor(strict, 'matched_tone').verdict, VERDICT.NO_CLEAR_PATTERN);
  assert.equal(strict.thresholds.minGapPp, 50);
  assert.equal(strict.thresholds.minSample, DEFAULT_THRESHOLDS.minSample, 'other guards untouched');
});

test('patterns come back sorted by the width of the gap', () => {
  const ds = build({
    rapport_first: { won: [45, 50], lost: [5, 50] },
    matched_tone: { won: [35, 50], lost: [15, 50] },
  });
  const a = analyze(ds);
  assert.equal(a.patterns.length, 2);
  assert.equal(a.patterns[0].id, 'rapport_first');
  assert.ok(Math.abs(a.patterns[0].gapPp) > Math.abs(a.patterns[1].gapPp));
});

test('an empty dataset produces no findings and does not throw', () => {
  const a = analyze({ prospects: [], calls: [], emails: [] });
  assert.equal(a.patterns.length, 0);
  assert.equal(a.noClearPattern.length, 0);
  assert.equal(a.insufficient.length, a.results.length);
  assert.equal(a.totals.calls, 0);
});

test('a dataset missing whole collections does not throw', () => {
  const a = analyze({});
  assert.equal(a.totals.calls, 0);
  assert.equal(a.totals.taggedEmails, 0);
  assert.equal(a.results.length, 6);
});

test('an artifact pointing at a prospect that does not exist is treated as no deal', () => {
  const a = analyze({
    prospects: [],
    calls: [{ id: 'X', prospectId: 'ghost', date: '2026-01-01', tags: { rapport_first: true } }],
    emails: [],
  });
  assert.equal(a.totals.callsWithoutDeal, 1);
  assert.equal(resultFor(a, 'rapport_first').won.n, 0);
});

test('resultFor returns null for an unknown question', () => {
  assert.equal(resultFor(analyze({}), 'not_a_question'), null);
});
