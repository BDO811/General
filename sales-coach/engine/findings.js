/**
 * Renders `findings.md`, the artifact prompt 2 ends on.
 *
 * This is the file the reel tells you to read before every call prep, so it
 * is deliberately short. Patterns first, in order of how wide the gap is,
 * then one block listing everything the guard rejected, so a question that
 * came back flat is visibly answered rather than quietly dropped.
 */

import { VERDICT } from './analysis.js';

/** 1122 becomes "1,122". */
function commas(n) {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/** "71% of wins, 29% of losses" */
function split(result) {
  return `${result.won.pct}% of wins, ${result.lost.pct}% of losses`;
}

/**
 * Render findings.md.
 *
 * @param {ReturnType<import('./analysis.js').analyze>} analysis
 * @param {{title?:string, includeStats?:boolean}} [options]
 *   `includeStats` appends the sample sizes and p-values under each pattern.
 *   Off by default: the reel's version is a coaching note, not a stats report,
 *   and a wall of p-values is not something anyone reads in a car.
 * @returns {string} markdown
 */
export function renderFindings(analysis, options = {}) {
  const { title = 'findings.md', includeStats = false } = options;
  const { totals, patterns, noClearPattern, insufficient, thresholds } = analysis;

  const out = [];
  out.push(`# ${title}`);
  out.push('');
  out.push('## What actually closes for you');
  out.push(
    `${commas(totals.calls)} calls · ${commas(totals.taggedEmails)} emails · tagged by Jev`
  );
  out.push('');

  if (patterns.length === 0) {
    out.push('Nothing cleared the bar this time.');
    out.push('');
    out.push(
      `A question becomes a pattern at a gap of ${thresholds.minGapPp} points or more, ` +
        `with at least ${thresholds.minSample} closed won and ${thresholds.minSample} ` +
        `closed lost behind it, and p under ${thresholds.alpha}.`
    );
    out.push('');
  }

  patterns.forEach((r, i) => {
    out.push(`### ${i + 1}. ${r.heading}`);
    if (r.direction === 'helps') {
      out.push(`Yes on ${split(r)}.`);
    } else {
      out.push(`Yes on ${split(r)}. It runs against you, so stop doing it.`);
    }
    if (r.advice) out.push(r.advice);
    if (includeStats) {
      out.push(
        `_${r.won.yes}/${r.won.n} won, ${r.lost.yes}/${r.lost.n} lost. ` +
          `Gap ${r.gapPpRounded} points, p ${r.p < 0.001 ? '<0.001' : r.p.toFixed(3)}._`
      );
    }
    out.push('');
  });

  if (noClearPattern.length > 0) {
    out.push('### No clear pattern');
    for (const r of noClearPattern) {
      out.push(`${r.label} (${r.won.pct}% vs ${r.lost.pct}%).`);
    }
    out.push('');
  }

  if (insufficient.length > 0) {
    out.push('### Not enough data yet');
    for (const r of insufficient) {
      out.push(`${r.label}: ${r.won.n} won and ${r.lost.n} lost answered.`);
    }
    out.push('');
  }

  out.push('> Read this before every call prep.');
  out.push('');

  return out.join('\n');
}

/**
 * The same analysis as a flat table, which is what the workbench renders and
 * what the reel puts on screen as the JEV QUESTION / WON / LOST grid.
 *
 * @returns {{headers:string[], rows:Array<{label:string, won:string, lost:string, verdict:string}>}}
 */
export function renderTable(analysis) {
  return {
    headers: ['JEV QUESTION', 'WON', 'LOST'],
    rows: analysis.results
      .slice()
      .sort((a, b) => Math.abs(b.gapPp ?? 0) - Math.abs(a.gapPp ?? 0))
      .map((r) => ({
        id: r.id,
        label: r.label,
        won: r.won.pct == null ? 'n/a' : `${r.won.pct}%`,
        lost: r.lost.pct == null ? 'n/a' : `${r.lost.pct}%`,
        verdict: r.verdict,
        isPattern: r.verdict === VERDICT.PATTERN,
      })),
  };
}
