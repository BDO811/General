/**
 * Renders the one-page call plan from prompt 3.
 *
 * The plan is built from three things: what the analysis says actually closes
 * for this seller, the full history with this prospect, and whatever research
 * the agent gathered. Anything the analysis could not establish is left out
 * rather than padded, because a call plan that hedges is a call plan nobody
 * reads in the car.
 */

import { VERDICT } from './analysis.js';

const DAY_MS = 86400000;

function fmtDate(value) {
  if (!value) return 'unknown date';
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toISOString().slice(0, 10);
}

function daysBetween(a, b) {
  const t1 = new Date(a).getTime();
  const t2 = new Date(b).getTime();
  if (Number.isNaN(t1) || Number.isNaN(t2)) return null;
  return Math.round(Math.abs(t2 - t1) / DAY_MS);
}

function money(amount) {
  if (amount == null || !Number.isFinite(amount)) return null;
  return '$' + Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/** Pull every call and email tied to a prospect, newest last. */
export function historyFor(dataset, prospectId) {
  const byDate = (a, b) => new Date(a.date) - new Date(b.date);
  return {
    calls: (dataset.calls ?? []).filter((c) => c.prospectId === prospectId).sort(byDate),
    emails: (dataset.emails ?? []).filter((e) => e.prospectId === prospectId).sort(byDate),
  };
}

/**
 * Turn the analysis into the two lists a call plan needs: what to do, and
 * what the evidence says costs you the deal.
 */
function playbookFrom(analysis) {
  const doThis = [];
  const dont = [];

  for (const r of analysis.patterns) {
    if (r.direction === 'helps') {
      doThis.push({
        heading: r.heading,
        line: r.advice ?? r.question,
        evidence: `${r.won.pct}% of wins against ${r.lost.pct}% of losses`,
        scope: r.scope,
      });
    } else {
      dont.push({
        heading: r.heading,
        line: r.advice ?? r.question,
        evidence: `${r.won.pct}% of wins against ${r.lost.pct}% of losses`,
        scope: r.scope,
      });
    }
  }

  return { doThis, dont };
}

/**
 * @typedef {Object} Research
 * @property {string} [linkedin]   one paragraph on the person
 * @property {string} [company]    one paragraph on the company and its site
 * @property {string[]} [news]     recent items, newest first
 * @property {string[]} [hooks]    concrete openers drawn from the research
 */

/**
 * Render the call plan.
 *
 * @param {Object} args
 * @param {Object} args.prospect          {id, name, company, email, outcome, amount}
 * @param {ReturnType<import('./analysis.js').analyze>} args.analysis
 * @param {Object} args.dataset
 * @param {Research} [args.research]
 * @param {string|Date} [args.asOf]       date the plan is written for
 * @returns {string} markdown
 */
export function renderPrep({ prospect, analysis, dataset, research = {}, asOf = new Date() }) {
  if (!prospect) throw new Error('renderPrep needs a prospect');

  const { calls, emails } = historyFor(dataset, prospect.id);
  const { doThis, dont } = playbookFrom(analysis);
  const lastTouch = [...calls, ...emails].sort((a, b) => new Date(b.date) - new Date(a.date))[0];

  const out = [];
  out.push(`# Call prep: ${prospect.name}${prospect.company ? ` at ${prospect.company}` : ''}`);
  out.push('');
  out.push(`_Generated ${fmtDate(asOf)} from findings.md and ${calls.length} prior call${calls.length === 1 ? '' : 's'}._`);
  out.push('');

  // 1. Who you are walking into.
  out.push('## Who you are walking into');
  if (research.linkedin) out.push(research.linkedin);
  if (research.company) {
    if (research.linkedin) out.push('');
    out.push(research.company);
  }
  if (Array.isArray(research.news) && research.news.length) {
    out.push('');
    out.push('Recent:');
    for (const item of research.news.slice(0, 4)) out.push(`- ${item}`);
  }
  if (!research.linkedin && !research.company && !research.news?.length) {
    out.push('No research supplied. Run the research step before the call.');
  }
  out.push('');

  // 2. Where the relationship stands.
  out.push('## Where this stands');
  const bits = [];
  bits.push(`${calls.length} call${calls.length === 1 ? '' : 's'}`);
  bits.push(`${emails.length} email${emails.length === 1 ? '' : 's'}`);
  if (prospect.outcome && prospect.outcome !== 'none') {
    bits.push(`deal is ${prospect.outcome.replace('_', ' ')}`);
  } else {
    bits.push('no deal record in the CRM');
  }
  const amt = money(prospect.amount);
  if (amt) bits.push(`${amt} on the table`);
  out.push(bits.join(' · ') + '.');

  if (lastTouch) {
    const gap = daysBetween(lastTouch.date, asOf);
    // Emails carry a direction, calls do not. That is what tells the two apart
    // once both lists have been merged and sorted together.
    const kind = lastTouch.direction ? 'an email' : 'a call';
    out.push('');
    out.push(
      `Last contact ${fmtDate(lastTouch.date)}` +
        (gap != null ? `, ${gap} day${gap === 1 ? '' : 's'} ago` : '') +
        `, ${kind}.`
    );
  }
  out.push('');

  // 3. The plan itself, ordered the way the call runs.
  out.push('## Open with');
  const rapport = analysis.results.find((r) => r.id === 'rapport_first');
  if (rapport?.verdict === VERDICT.PATTERN && rapport.direction === 'helps') {
    out.push(
      `Five minutes before anything about the product. You do this in ` +
        `${rapport.won.pct}% of your wins and ${rapport.lost.pct}% of your losses.`
    );
  } else {
    out.push('Open warm and let them set the pace.');
  }
  if (Array.isArray(research.hooks) && research.hooks.length) {
    out.push('');
    for (const hook of research.hooks.slice(0, 3)) out.push(`- ${hook}`);
  } else if (prospect.company) {
    out.push('');
    out.push(`- Something specific and recent about ${prospect.company}, not the weather.`);
  }
  out.push('');

  out.push('## Discovery');
  const goal = analysis.results.find((r) => r.id === 'asked_goal_before_price');
  out.push('- What are you actually trying to get to this year?');
  out.push('- What happens if this stays the way it is?');
  out.push('- Who else has to say yes?');
  if (goal && goal.verdict === VERDICT.PATTERN && goal.direction === 'helps') {
    out.push('');
    out.push(
      `Get all three answered before any number. ${goal.won.pct}% of wins against ` +
        `${goal.lost.pct}% of losses.`
    );
  }
  out.push('');

  // 4. Objections, grounded in what has actually worked.
  out.push('## Objections they will likely raise');
  const hold = analysis.results.find((r) => r.id === 'held_price_first_objection');
  out.push('- **Price.** Expect it on the first number.');
  if (hold?.verdict === VERDICT.PATTERN && hold.direction === 'helps') {
    out.push(
      `  Hold it. You held on the first objection in ${hold.won.pct}% of wins and ` +
        `${hold.lost.pct}% of losses. The discount is what loses these, not the number.`
    );
  }
  out.push('- **Timing.** Ask what changes between now and then.');
  out.push('- **Internal buy-in.** Ask who else is in the room and what they care about.');
  out.push('');

  // 5. The distilled playbook.
  if (doThis.length) {
    out.push('## What actually closes for you');
    for (const d of doThis) out.push(`- **${d.heading}.** ${d.line} (${d.evidence})`);
    out.push('');
  }

  if (dont.length) {
    out.push('## Do not');
    for (const d of dont) out.push(`- **${d.heading}.** ${d.evidence}, so it is costing you.`);
    out.push('');
  }

  if (analysis.noClearPattern.length) {
    out.push('## Stop worrying about');
    out.push(
      analysis.noClearPattern
        .map((r) => `${r.label} (${r.won.pct}% vs ${r.lost.pct}%)`)
        .join(', ') + '.'
    );
    out.push('');
  }

  return out.join('\n');
}

/**
 * The source list for the NotebookLM notebook in prompt 3, step 4. The audio
 * overview is generated from exactly these, so the call plan and the research
 * stay the only things the podcast can talk about.
 */
export function prepSources({ prospect, prepMarkdown, research = {} }) {
  const sources = [
    { title: `Call plan: ${prospect.name}`, type: 'text', content: prepMarkdown },
  ];
  if (research.linkedin) {
    sources.push({ title: `${prospect.name} on LinkedIn`, type: 'text', content: research.linkedin });
  }
  if (research.company) {
    sources.push({ title: `${prospect.company ?? 'Company'} overview`, type: 'text', content: research.company });
  }
  if (Array.isArray(research.news) && research.news.length) {
    sources.push({
      title: `${prospect.company ?? prospect.name}: recent news`,
      type: 'text',
      content: research.news.map((n) => `- ${n}`).join('\n'),
    });
  }
  return sources;
}
