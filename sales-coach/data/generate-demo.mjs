#!/usr/bin/env node
/**
 * Builds the demo dataset the workbench loads on first open.
 *
 * The numbers are not decorative. They are chosen so the engine, run over the
 * generated rows, reproduces every figure the reel puts on screen:
 *
 *   rapport before the pitch      71% won   29% lost
 *   matched their tone            64% won   41% lost
 *   held price on 1st objection   58% won   22% lost
 *   asked goal before price       82% won   77% lost   (no clear pattern)
 *   email length matched theirs   16% won   18% lost   (no clear pattern)
 *
 *   214 calls, 1,122 emails, 9 calls with no matching deal.
 *
 * The test suite asserts those numbers against the generated file, so if the
 * analysis ever drifts the build fails rather than the demo quietly lying.
 *
 * Run: node data/generate-demo.mjs
 */

import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, 'demo-dataset.json');

/** Reference date. Fixed so the file is byte-identical on every run. */
const AS_OF = new Date('2026-09-26T00:00:00Z');
const YEAR_MS = 365 * 86400000;

/* ------------------------------------------------------------------ */
/* Deterministic randomness                                            */
/* ------------------------------------------------------------------ */

/** mulberry32: small, fast, and identical across Node versions. */
function mulberry32(seed) {
  let a = seed >>> 0;
  return function rand() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = mulberry32(20260926);

const pick = (arr) => arr[Math.floor(rand() * arr.length)];
const between = (lo, hi) => lo + Math.floor(rand() * (hi - lo + 1));

/* ------------------------------------------------------------------ */
/* Shape of the book of business                                       */
/* ------------------------------------------------------------------ */

/**
 * Call and email counts per outcome bucket. These are the numbers that make
 * the reel's percentages come out exactly, so treat them as fixed.
 *
 *   calls  72 won + 133 lost + 9 with no deal = 214
 *   emails 394 won + 728 lost                 = 1,122 graded
 */
const PLAN = {
  won: { prospects: 48, singleCallProspects: 24, calls: 72, emails: 394 },
  lost: { prospects: 105, singleCallProspects: 77, calls: 133, emails: 728 },
  none: { prospects: 9, calls: 9, emails: 0 },
};

/** Exact yes counts per rubric question, per outcome. */
const YES = {
  // 51/72 = 70.8% -> 71 ; 39/133 = 29.3% -> 29
  rapport_first: { won: 51, lost: 39 },
  // 46/72 = 63.9% -> 64 ; 55/133 = 41.4% -> 41
  matched_tone: { won: 46, lost: 55 },
  // 59/72 = 81.9% -> 82 ; 102/133 = 76.7% -> 77
  asked_goal_before_price: { won: 59, lost: 102 },
  // 42/72 = 58.3% -> 58 ; 29/133 = 21.8% -> 22
  held_price_first_objection: { won: 42, lost: 29 },
  // 63/394 = 16.0% -> 16 ; 131/728 = 18.0% -> 18
  email_length_matched: { won: 63, lost: 131 },
  // 268/394 = 68.0% -> 68 ; 320/728 = 44.0% -> 44
  email_ends_with_question: { won: 268, lost: 320 },
};

/** How strongly each question tracks the latent "this was a good call" score. */
const CORRELATION = {
  rapport_first: 0.8,
  matched_tone: 0.7,
  asked_goal_before_price: 0.35,
  held_price_first_objection: 0.75,
  email_length_matched: 0.1,
  email_ends_with_question: 0.6,
};

/* ------------------------------------------------------------------ */
/* Names                                                               */
/* ------------------------------------------------------------------ */

const FIRST = [
  'Steve', 'Dana', 'Marcus', 'Priya', 'Tom', 'Elena', 'Ray', 'Nina', 'Curtis',
  'Joanne', 'Hector', 'Wendy', 'Sam', 'Brigid', 'Omar', 'Kate', 'Lonnie',
  'Rosa', 'Dale', 'Yvette', 'Glen', 'Shanice', 'Pete', 'Marta', 'Doug',
  'Alicia', 'Vern', 'Tessa', 'Russ', 'Camille', 'Neil', 'Bettina',
];

const LAST = [
  'Arden', 'Okafor', 'Delgado', 'Raman', 'Whitfield', 'Sorensen', 'Brandt',
  'Alvarez', 'Nakamura', 'Fontaine', 'Mbeki', 'Kowalski', 'Hargrove', 'Pham',
  'Castellanos', 'Odum', 'Lindqvist', 'Boateng', 'Merriweather', 'Tallis',
  'Vasquez', 'Petrov', 'Crenshaw', 'Ibrahim', 'Donnelly', 'Sato',
];

const COMPANY_A = [
  'Corvell', 'Northstar', 'Blue Ridge', 'Ironvale', 'Summit Line', 'Cedarbrook',
  'Halverson', 'Granite Bay', 'Mesa Point', 'Kingsley', 'Redpine', 'Fairmount',
  'Two Rivers', 'Copperfield', 'Whitehall', 'Stonebridge', 'Larkspur',
  'Eastgate', 'Foxglove', 'Meridian',
];

const COMPANY_B = [
  'Roofing', 'Exteriors', 'Home Services', 'Mechanical', 'Restoration',
  'Contracting', 'Builders', 'HVAC', 'Property Group', 'Construction',
];

const CITIES = [
  'Denver, Colorado', 'Aurora, Colorado', 'Boulder, Colorado',
  'Colorado Springs, Colorado', 'Fort Collins, Colorado', 'Lakewood, Colorado',
  'Westminster, Colorado', 'Golden, Colorado',
];

const TITLES = ['Owner', 'President', 'General Manager', 'VP Operations', 'Founder'];

function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '');
}

/** Short hex-ish id in the style the reel's screenshots use (01K7Q3, 01K7R8). */
function shortId(n) {
  return '01K' + n.toString(36).toUpperCase().padStart(3, '0');
}

/* ------------------------------------------------------------------ */
/* Build prospects                                                     */
/* ------------------------------------------------------------------ */

const usedNames = new Set();

function makeName() {
  for (let attempt = 0; attempt < 500; attempt++) {
    const name = `${pick(FIRST)} ${pick(LAST)}`;
    if (!usedNames.has(name)) {
      usedNames.add(name);
      return name;
    }
  }
  // Fall back to a numbered name rather than looping forever.
  const name = `${pick(FIRST)} ${pick(LAST)} ${usedNames.size}`;
  usedNames.add(name);
  return name;
}

const usedCompanies = new Set();

function makeCompany() {
  for (let attempt = 0; attempt < 500; attempt++) {
    const c = `${pick(COMPANY_A)} ${pick(COMPANY_B)}`;
    if (!usedCompanies.has(c)) {
      usedCompanies.add(c);
      return c;
    }
  }
  const c = `${pick(COMPANY_A)} ${pick(COMPANY_B)} ${usedCompanies.size}`;
  usedCompanies.add(c);
  return c;
}

const prospects = [];
let prospectSeq = 0;

function addProspects(outcome, count) {
  const made = [];
  for (let i = 0; i < count; i++) {
    prospectSeq += 1;
    const name = prospectSeq === 1 ? 'Steve Arden' : makeName();
    const company = prospectSeq === 1 ? 'Corvell Roofing' : makeCompany();
    const [first, last] = name.split(' ');
    const p = {
      id: `P${String(prospectSeq).padStart(4, '0')}`,
      name,
      company,
      title: prospectSeq === 1 ? 'Owner' : pick(TITLES),
      city: prospectSeq === 1 ? 'Denver, Colorado' : pick(CITIES),
      email: `${slug(first)}@${slug(company)}.com`,
      outcome,
      amount: outcome === 'none' ? null : between(4, 42) * 1000 + 800,
      closedAt:
        outcome === 'none'
          ? null
          : new Date(AS_OF.getTime() - Math.floor(rand() * YEAR_MS * 0.85)).toISOString().slice(0, 10),
    };
    prospects.push(p);
    made.push(p);
  }
  return made;
}

// Steve Arden lands first and is a closed won deal, so the prep demo in the
// web app has a real history to render against.
const wonProspects = addProspects('closed_won', PLAN.won.prospects);
const lostProspects = addProspects('closed_lost', PLAN.lost.prospects);
const noneProspects = addProspects('none', PLAN.none.prospects);

/* ------------------------------------------------------------------ */
/* Build calls                                                         */
/* ------------------------------------------------------------------ */

const calls = [];
let callSeq = 0;

/**
 * Hand out calls so the per-outcome totals land exactly. The first
 * `singleCallProspects` get one call, the rest get two.
 */
function addCalls(list, total, singleCallProspects) {
  const counts = list.map((_, i) => (i < singleCallProspects ? 1 : 2));
  const sum = counts.reduce((a, b) => a + b, 0);
  if (sum !== total) {
    throw new Error(`call plan does not balance: got ${sum}, want ${total}`);
  }

  list.forEach((p, i) => {
    for (let k = 0; k < counts[i]; k++) {
      callSeq += 1;
      const daysAgo = between(8, 360) - k * 7;
      calls.push({
        id: shortId(callSeq),
        prospectId: p.id,
        title: k === 0 ? `Discovery: ${p.company}` : `Follow up: ${p.company}`,
        date: new Date(AS_OF.getTime() - Math.max(1, daysAgo) * 86400000)
          .toISOString()
          .slice(0, 10),
        durationSec: between(11, 47) * 60,
        // Latent "how well did this call go" score. Every rubric answer is
        // drawn against it, which is what gives the demo realistic
        // co-occurrence instead of six independent coin flips.
        quality: rand(),
        tags: {},
      });
    }
  });
}

addCalls(wonProspects, PLAN.won.calls, PLAN.won.singleCallProspects);
addCalls(lostProspects, PLAN.lost.calls, PLAN.lost.singleCallProspects);
noneProspects.forEach((p) => {
  callSeq += 1;
  calls.push({
    id: shortId(callSeq),
    prospectId: p.id,
    title: `Inbound: ${p.company}`,
    date: new Date(AS_OF.getTime() - between(20, 300) * 86400000).toISOString().slice(0, 10),
    durationSec: between(6, 25) * 60,
    quality: rand(),
    tags: {},
  });
});

/* ------------------------------------------------------------------ */
/* Build emails                                                        */
/* ------------------------------------------------------------------ */

const emails = [];
let emailSeq = 0;

/** Spread `total` outbound emails across `list` as evenly as the count allows. */
function addEmails(list, total) {
  const per = Math.floor(total / list.length);
  let remainder = total - per * list.length;

  for (const p of list) {
    let n = per;
    if (remainder > 0) {
      n += 1;
      remainder -= 1;
    }
    for (let k = 0; k < n; k++) {
      emailSeq += 1;
      const date = new Date(AS_OF.getTime() - between(5, 355) * 86400000)
        .toISOString()
        .slice(0, 10);
      emails.push({
        id: `E${String(emailSeq).padStart(5, '0')}`,
        prospectId: p.id,
        direction: 'out',
        date,
        words: between(28, 260),
        quality: rand(),
        tags: {},
      });
      // Roughly six in ten outbound emails draw a reply. The replies are not
      // graded, but "a similar length to theirs" is unanswerable without them.
      if (rand() < 0.6) {
        emailSeq += 1;
        emails.push({
          id: `E${String(emailSeq).padStart(5, '0')}`,
          prospectId: p.id,
          direction: 'in',
          date,
          words: between(12, 140),
        });
      }
    }
  }
}

addEmails(wonProspects, PLAN.won.emails);
addEmails(lostProspects, PLAN.lost.emails);

/* ------------------------------------------------------------------ */
/* Apply Jev's answers, hitting the exact yes counts                   */
/* ------------------------------------------------------------------ */

const outcomeById = new Map(prospects.map((p) => [p.id, p.outcome]));

/**
 * Set `questionId` to true on exactly `count` of `artifacts` and false on the
 * rest, choosing which by a blend of the artifact's latent quality and noise.
 *
 * Sorting by a blended score rather than shuffling is what makes rapport and
 * tone tend to travel together the way they do in real call data, while still
 * landing on the exact totals the reel reports.
 */
function applyExact(artifacts, questionId, count, correlation) {
  if (count > artifacts.length) {
    throw new Error(
      `cannot set ${count} yes answers for ${questionId} across ${artifacts.length} records`
    );
  }
  const scored = artifacts
    .map((a) => ({
      a,
      score: correlation * a.quality + (1 - correlation) * rand(),
    }))
    .sort((x, y) => y.score - x.score);

  scored.forEach((entry, i) => {
    entry.a.tags[questionId] = i < count;
  });
}

const callsWon = calls.filter((c) => outcomeById.get(c.prospectId) === 'closed_won');
const callsLost = calls.filter((c) => outcomeById.get(c.prospectId) === 'closed_lost');
const callsNone = calls.filter((c) => outcomeById.get(c.prospectId) === 'none');

const outEmails = emails.filter((e) => e.direction === 'out');
const emailsWon = outEmails.filter((e) => outcomeById.get(e.prospectId) === 'closed_won');
const emailsLost = outEmails.filter((e) => outcomeById.get(e.prospectId) === 'closed_lost');

for (const [questionId, counts] of Object.entries(YES)) {
  const isEmail = questionId.startsWith('email_');
  const w = CORRELATION[questionId];
  applyExact(isEmail ? emailsWon : callsWon, questionId, counts.won, w);
  applyExact(isEmail ? emailsLost : callsLost, questionId, counts.lost, w);
}

// Calls with no matching deal still get graded. They are simply held out of
// every won against lost comparison, which is the behaviour being demonstrated.
for (const c of callsNone) {
  for (const questionId of ['rapport_first', 'matched_tone', 'asked_goal_before_price', 'held_price_first_objection']) {
    c.tags[questionId] = rand() < 0.5;
  }
}

/* ------------------------------------------------------------------ */
/* Emit                                                                */
/* ------------------------------------------------------------------ */

// `quality` is scaffolding for the generator, not part of the data contract.
for (const c of calls) delete c.quality;
for (const e of emails) delete e.quality;

const dataset = {
  meta: {
    name: 'Demo book of business',
    note:
      'Synthetic. Generated by data/generate-demo.mjs so the engine reproduces the ' +
      'figures shown in the source reel. No real prospect, call or email is in this file.',
    generatedFor: AS_OF.toISOString().slice(0, 10),
    seller: { name: 'You', email: 'you@example.com' },
  },
  prospects,
  calls,
  emails,
};

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(dataset, null, 0) + '\n');

const outCount = emails.filter((e) => e.direction === 'out').length;
console.log(
  `Wrote ${OUT}\n` +
    `  prospects ${prospects.length}\n` +
    `  calls     ${calls.length} (${callsWon.length} won, ${callsLost.length} lost, ${callsNone.length} no deal)\n` +
    `  emails    ${emails.length} total, ${outCount} graded`
);
