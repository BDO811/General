/**
 * The analysis step from prompt 2.
 *
 * Jev has already answered every rubric question against every call and every
 * email. This module does the only part the reel insists a model must not do
 * by feel: for each question, compare how often the answer was yes in closed
 * won against closed lost, and only call it a pattern when the gap is wide and
 * the sample is not tiny. Everything else is reported as no clear pattern.
 *
 * Pure ES module. Same file runs in Node and in the browser.
 */

import { RUBRIC, questionById } from './rubric.js';
import { rate, pct, twoProportionZTest, wilsonInterval } from './stats.js';

/**
 * Defaults for the pattern guard.
 *
 * `minSample` and `minGapPp` are the two guards the reel names in words. The
 * significance test is the third, and it is the one that stops a 12 versus 11
 * split on small groups from being read out as advice.
 */
export const DEFAULT_THRESHOLDS = Object.freeze({
  /** Minimum closed won and closed lost records before a question is judged. */
  minSample: 10,
  /** Minimum absolute gap, in percentage points, before a gap counts. */
  minGapPp: 15,
  /** Two tailed significance level for the two-proportion z-test. */
  alpha: 0.05,
});

export const VERDICT = Object.freeze({
  PATTERN: 'pattern',
  NO_CLEAR_PATTERN: 'no_clear_pattern',
  INSUFFICIENT_DATA: 'insufficient_data',
});

/**
 * @typedef {Object} Dataset
 * @property {Array<Object>} prospects  {id, name, company, email, outcome, amount}
 * @property {Array<Object>} calls      {id, prospectId, date, tags}
 * @property {Array<Object>} emails     {id, prospectId, date, direction, words, tags}
 * @property {Object} [meta]
 */

/** Index prospects by id so call and email rows can be resolved in one pass. */
function indexProspects(dataset) {
  const byId = new Map();
  for (const p of dataset.prospects ?? []) byId.set(p.id, p);
  return byId;
}

/**
 * Resolve the deal outcome for an artifact.
 *
 * An artifact whose prospect is missing, or whose prospect has no deal, is
 * `none`. Those rows are counted in the totals and then held out of every
 * comparison, which is what "9 calls had no matching deal" means in practice.
 */
function outcomeOf(artifact, prospectsById) {
  const p = prospectsById.get(artifact.prospectId);
  if (!p) return 'none';
  return p.outcome ?? 'none';
}

/** True when the artifact carries a usable yes or no answer for `questionId`. */
function answered(artifact, questionId) {
  const v = artifact?.tags?.[questionId];
  return v === true || v === false;
}

/**
 * Tally one rubric question across closed won and closed lost.
 *
 * Artifacts with no answer for the question are skipped rather than counted
 * as no, so a Jev call that failed or timed out cannot quietly drag a rate
 * toward zero.
 */
function tally(artifacts, prospectsById, questionId) {
  const counts = {
    won: { yes: 0, n: 0 },
    lost: { yes: 0, n: 0 },
    skipped: 0,
  };

  for (const a of artifacts) {
    if (!answered(a, questionId)) {
      counts.skipped += 1;
      continue;
    }
    const outcome = outcomeOf(a, prospectsById);
    const bucket =
      outcome === 'closed_won' ? counts.won : outcome === 'closed_lost' ? counts.lost : null;
    if (!bucket) continue;
    bucket.n += 1;
    if (a.tags[questionId] === true) bucket.yes += 1;
  }

  return counts;
}

/** Build the reported side of a group: counts, rate, percent, confidence band. */
function describe(group) {
  const r = rate(group.yes, group.n);
  return {
    yes: group.yes,
    n: group.n,
    rate: r,
    pct: pct(r),
    interval: wilsonInterval(group.yes, group.n),
  };
}

/**
 * Decide whether a gap is a pattern, and say why when it is not.
 *
 * The order matters. Sample size is checked first because a gap computed from
 * four records is not a small gap, it is no answer at all, and labelling it
 * "no clear pattern" would overstate what the data supports.
 */
function judge(won, lost, thresholds) {
  const { minSample, minGapPp, alpha } = thresholds;

  if (won.n < minSample || lost.n < minSample) {
    return {
      verdict: VERDICT.INSUFFICIENT_DATA,
      reason:
        `Needs at least ${minSample} closed won and ${minSample} closed lost. ` +
        `Have ${won.n} and ${lost.n}.`,
      test: null,
    };
  }

  const gapPp = (won.rate - lost.rate) * 100;
  const test = twoProportionZTest(won.yes, won.n, lost.yes, lost.n);

  if (Math.abs(gapPp) < minGapPp) {
    return {
      verdict: VERDICT.NO_CLEAR_PATTERN,
      reason: `Gap is ${gapPp.toFixed(1)} points, under the ${minGapPp} point floor.`,
      test,
    };
  }

  if (!test || test.p >= alpha) {
    return {
      verdict: VERDICT.NO_CLEAR_PATTERN,
      reason: test
        ? `Gap is ${gapPp.toFixed(1)} points but p is ${test.p.toFixed(3)}, over ${alpha}.`
        : 'Not enough variation in the answers to test against.',
      test,
    };
  }

  return {
    verdict: VERDICT.PATTERN,
    reason: `Gap is ${gapPp.toFixed(1)} points, p is ${test.p < 0.001 ? '<0.001' : test.p.toFixed(3)}.`,
    test,
  };
}

/**
 * Run the full analysis.
 *
 * @param {Dataset} dataset
 * @param {Partial<typeof DEFAULT_THRESHOLDS>} [overrides]
 * @returns {Object} totals, per-question results, and the split into patterns
 *   and non-patterns, sorted strongest gap first.
 */
export function analyze(dataset, overrides = {}) {
  const thresholds = { ...DEFAULT_THRESHOLDS, ...overrides };
  const prospectsById = indexProspects(dataset);

  const calls = dataset.calls ?? [];
  const emails = dataset.emails ?? [];

  // Only the seller's own emails are graded. The prospect's replies are kept
  // in the dataset because "a similar length to theirs" cannot be answered
  // without them, but they are not the thing being judged.
  const sellerEmails = emails.filter((e) => e.direction === 'out');

  const results = RUBRIC.map((q) => {
    const artifacts = q.scope === 'call' ? calls : sellerEmails;
    const counts = tally(artifacts, prospectsById, q.id);
    const won = describe(counts.won);
    const lost = describe(counts.lost);

    const gapPp =
      won.rate != null && lost.rate != null ? (won.rate - lost.rate) * 100 : null;

    const { verdict, reason, test } = judge(won, lost, thresholds);

    return {
      id: q.id,
      scope: q.scope,
      label: q.label,
      question: q.question,
      heading: q.heading,
      advice: q.advice,
      won,
      lost,
      gapPp,
      gapPpRounded: gapPp == null ? null : Math.round(gapPp * 10) / 10,
      /** Gap as the table shows it: the difference of the two rounded percents. */
      displayGapPp: won.pct == null || lost.pct == null ? null : won.pct - lost.pct,
      direction: gapPp == null ? null : gapPp >= 0 ? 'helps' : 'hurts',
      verdict,
      reason,
      z: test?.z ?? null,
      p: test?.p ?? null,
      skipped: counts.skipped,
    };
  });

  const byGap = (a, b) => Math.abs(b.gapPp ?? 0) - Math.abs(a.gapPp ?? 0);
  const patterns = results.filter((r) => r.verdict === VERDICT.PATTERN).sort(byGap);
  const noClearPattern = results
    .filter((r) => r.verdict === VERDICT.NO_CLEAR_PATTERN)
    .sort(byGap);
  const insufficient = results.filter((r) => r.verdict === VERDICT.INSUFFICIENT_DATA);

  return {
    thresholds,
    totals: totals(dataset, prospectsById, calls, sellerEmails),
    results,
    patterns,
    noClearPattern,
    insufficient,
  };
}

/** Headline counts: what went in, and how much of it was usable. */
function totals(dataset, prospectsById, calls, sellerEmails) {
  const callOutcomes = { closed_won: 0, closed_lost: 0, open: 0, none: 0 };
  for (const c of calls) callOutcomes[outcomeOf(c, prospectsById)] += 1;

  const emailOutcomes = { closed_won: 0, closed_lost: 0, open: 0, none: 0 };
  for (const e of sellerEmails) emailOutcomes[outcomeOf(e, prospectsById)] += 1;

  return {
    prospects: (dataset.prospects ?? []).length,
    calls: calls.length,
    /** Emails Jev actually graded, which is the seller's own side of the thread. */
    taggedEmails: sellerEmails.length,
    allEmails: (dataset.emails ?? []).length,
    callsWithoutDeal: callOutcomes.none,
    callOutcomes,
    emailOutcomes,
  };
}

/**
 * Look one question up in a finished analysis. Used by the call-prep renderer,
 * which needs specific findings rather than the whole table.
 */
export function resultFor(analysis, questionId) {
  return analysis.results.find((r) => r.id === questionId) ?? null;
}

/** Re-export so callers only need one import to build a rubric-aware UI. */
export { RUBRIC, questionById };
