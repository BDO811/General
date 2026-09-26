import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

import { analyze } from '../engine/analysis.js';
import { renderPrep, prepSources, historyFor } from '../engine/prep.js';
import { renderFindings } from '../engine/findings.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const dataset = JSON.parse(readFileSync(resolve(HERE, '../data/demo-dataset.json'), 'utf8'));
const analysis = analyze(dataset);
const steve = dataset.prospects.find((p) => p.name === 'Steve Arden');

const RESEARCH = {
  linkedin: 'Owner at Corvell Roofing in Denver, 500+ connections, runs the sales side himself.',
  company: 'Family owned since 2009. Free roof inspections anywhere in the Denver metro.',
  news: ['Hail season claims are running long in the metro.'],
  hooks: ['Ask how the hail backlog is running against his crew size.'],
};

test('historyFor pulls only this prospect and sorts oldest first', () => {
  const h = historyFor(dataset, steve.id);
  assert.ok(h.calls.length > 0);
  for (const c of h.calls) assert.equal(c.prospectId, steve.id);
  for (const e of h.emails) assert.equal(e.prospectId, steve.id);
  const dates = h.calls.map((c) => c.date);
  assert.deepEqual(dates, [...dates].sort());
});

test('the call plan names the prospect and the company in the heading', () => {
  const md = renderPrep({ prospect: steve, analysis, dataset, research: RESEARCH, asOf: '2026-09-26' });
  assert.match(md, /^# Call prep: Steve Arden at Corvell Roofing$/m);
});

test('the call plan carries the findings through as concrete numbers', () => {
  const md = renderPrep({ prospect: steve, analysis, dataset, research: RESEARCH, asOf: '2026-09-26' });
  assert.match(md, /71% of your wins and 29% of your losses/, 'rapport figure is quoted');
  assert.match(md, /58% of wins and 22% of losses/, 'price-holding figure is quoted');
  assert.match(md, /## What actually closes for you/);
  assert.match(md, /## Objections they will likely raise/);
});

test('the call plan reports what is not worth worrying about', () => {
  const md = renderPrep({ prospect: steve, analysis, dataset, research: RESEARCH, asOf: '2026-09-26' });
  assert.match(md, /## Stop worrying about/);
  assert.match(md, /email length matched theirs \(16% vs 18%\)/);
});

test('research is used when supplied and called out when it is not', () => {
  const withResearch = renderPrep({ prospect: steve, analysis, dataset, research: RESEARCH, asOf: '2026-09-26' });
  assert.match(withResearch, /Family owned since 2009/);
  assert.match(withResearch, /hail backlog/);

  const without = renderPrep({ prospect: steve, analysis, dataset, asOf: '2026-09-26' });
  assert.match(without, /No research supplied\. Run the research step before the call\./);
});

test('the call plan degrades to something usable when there are no findings', () => {
  const empty = analyze({ prospects: [], calls: [], emails: [] });
  const md = renderPrep({
    prospect: { id: 'PX', name: 'New Name', company: 'New Co' },
    analysis: empty,
    dataset: { prospects: [], calls: [], emails: [] },
    asOf: '2026-09-26',
  });
  assert.match(md, /# Call prep: New Name at New Co/);
  assert.match(md, /Open warm and let them set the pace\./);
  assert.match(md, /0 calls · 0 emails/);
  assert.ok(!md.includes('undefined'), 'no undefined leaks into the page');
  assert.ok(!md.includes('NaN'), 'no NaN leaks into the page');
});

test('a prospect with no deal record says so rather than inventing one', () => {
  const noDeal = dataset.prospects.find((p) => p.outcome === 'none');
  const md = renderPrep({ prospect: noDeal, analysis, dataset, asOf: '2026-09-26' });
  assert.match(md, /no deal record in the CRM/);
});

test('renderPrep refuses to run without a prospect', () => {
  assert.throws(
    () => renderPrep({ prospect: null, analysis, dataset }),
    /renderPrep needs a prospect/
  );
});

test('the call plan contains no em dash, en dash or ellipsis', () => {
  const md = renderPrep({ prospect: steve, analysis, dataset, research: RESEARCH, asOf: '2026-09-26' });
  assert.ok(!/[\u2013\u2014\u2026]/.test(md));
});

test('prepSources bundles the plan and the research for the notebook', () => {
  const md = renderPrep({ prospect: steve, analysis, dataset, research: RESEARCH, asOf: '2026-09-26' });
  const sources = prepSources({ prospect: steve, prepMarkdown: md, research: RESEARCH });
  assert.equal(sources[0].title, 'Call plan: Steve Arden');
  assert.equal(sources[0].content, md);
  const titles = sources.map((s) => s.title);
  assert.ok(titles.some((t) => /LinkedIn/.test(t)));
  assert.ok(titles.some((t) => /Corvell Roofing overview/.test(t)));
  assert.ok(titles.some((t) => /recent news/.test(t)));
});

test('prepSources drops sections that have no research behind them', () => {
  const sources = prepSources({ prospect: steve, prepMarkdown: '# x', research: {} });
  assert.equal(sources.length, 1, 'only the call plan survives');
});

test('findings.md and the call plan agree on the pattern count', () => {
  const md = renderFindings(analysis);
  const headings = md.match(/^### \d+\. /gm) ?? [];
  assert.equal(headings.length, analysis.patterns.length);
});

test('the last-contact line reads correctly for both a call and an email', () => {
  const base = {
    prospects: [{ id: 'P1', name: 'Pat Lee', company: 'Lee Co', outcome: 'closed_won' }],
    emails: [],
  };
  const analysisLocal = analyze(base);

  const callLast = renderPrep({
    prospect: base.prospects[0],
    analysis: analysisLocal,
    dataset: { ...base, calls: [{ id: 'C1', prospectId: 'P1', date: '2026-09-01', tags: {} }] },
    asOf: '2026-09-26',
  });
  assert.match(callLast, /Last contact 2026-09-01, 25 days ago, a call\./);

  const emailLast = renderPrep({
    prospect: base.prospects[0],
    analysis: analysisLocal,
    dataset: {
      ...base,
      calls: [{ id: 'C1', prospectId: 'P1', date: '2026-09-01', tags: {} }],
      emails: [{ id: 'E1', prospectId: 'P1', direction: 'out', date: '2026-09-05', words: 20, tags: {} }],
    },
    asOf: '2026-09-26',
  });
  assert.match(emailLast, /Last contact 2026-09-05, 21 days ago, an email\./);
});
