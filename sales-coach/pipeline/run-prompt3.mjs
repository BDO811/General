#!/usr/bin/env node
/**
 * Prompt 3: prep me for a call.
 *
 *   1. Research the prospect: their LinkedIn, the company site and recent
 *      news, plus every call and email with them in sales.db.
 *   2. Read ~/sales-coach/findings.md and build a one-page call plan that
 *      follows what actually closes for this seller: the opening rapport
 *      questions, the discovery questions, and the objections they will
 *      likely raise with how they have been won before.
 *   3. Save it as ~/sales-coach/prep/[prospect].md.
 *   4. Create a NotebookLM notebook with the call plan and the research as
 *      sources, and generate an audio overview called "Call prep: [prospect]".
 *   5. Send the link so it can be listened to on the way to the call.
 *
 * Steps 1 and 4 are the two the agent does, not this script. The research is
 * a browsing task and NotebookLM has no public API for notebook creation, so
 * this script does steps 2 and 3 and then prints exactly what the agent needs
 * to do for 1, 4 and 5, with the sources already assembled.
 *
 * Research can be handed in with --research so the plan is built from it:
 *   node pipeline/run-prompt3.mjs --prospect steve@corvellroofing.com \
 *     --research research.json
 *
 * research.json is {linkedin, company, news: [...], hooks: [...]}.
 *
 * Usage:
 *   node pipeline/run-prompt3.mjs --prospect <email or name> [--research f.json]
 *   node pipeline/run-prompt3.mjs --list
 */

import { writeFile, readFile } from 'node:fs/promises';
import { join } from 'node:path';

import { loadConfig, ensureDirs } from './config.mjs';
import * as db from './db.mjs';

import { analyze } from '../engine/analysis.js';
import { renderPrep, prepSources } from '../engine/prep.js';

const args = parseArgs(process.argv.slice(2));
const config = loadConfig();

function parseArgs(argv) {
  const out = { prospect: null, research: null, list: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--prospect') out.prospect = argv[++i];
    else if (argv[i] === '--research') out.research = argv[++i];
    else if (argv[i] === '--list') out.list = true;
  }
  return out;
}

const log = (...a) => console.log(...a);

/** File-safe name for prep/[prospect].md. */
function slug(s) {
  return String(s)
    .toLowerCase()
    .replace(/@.*$/, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

async function main() {
  ensureDirs(config);
  const database = db.open(config.paths.db);

  try {
    const dataset = db.toDataset(database, { source: 'prompt3' });

    if (args.list) {
      const rows = dataset.prospects
        .slice()
        .sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''));
      log(`${rows.length} prospects in sales.db:\n`);
      for (const p of rows) {
        log(`  ${(p.email ?? p.id).padEnd(40)} ${(p.name ?? '').padEnd(24)} ${p.outcome}`);
      }
      return;
    }

    if (!args.prospect) {
      throw new Error('Pass --prospect <email or name>, or --list to see who is in the database.');
    }

    const needle = args.prospect.toLowerCase();
    const prospect =
      dataset.prospects.find((p) => (p.email ?? '').toLowerCase() === needle) ??
      dataset.prospects.find((p) => (p.id ?? '').toLowerCase() === needle) ??
      dataset.prospects.find((p) => (p.name ?? '').toLowerCase().includes(needle));

    if (!prospect) {
      throw new Error(`No prospect matching "${args.prospect}". Run with --list to see who is there.`);
    }

    let research = {};
    if (args.research) {
      research = JSON.parse(await readFile(args.research, 'utf8'));
    }

    const analysis = analyze(dataset, config.thresholds);
    if (analysis.patterns.length === 0) {
      log('Warning: findings.md has no patterns yet, so the plan is generic. Run prompt 2 first.\n');
    }

    const markdown = renderPrep({ prospect, analysis, dataset, research });
    const outPath = join(config.paths.prep, `${slug(prospect.email ?? prospect.name)}.md`);
    await writeFile(outPath, markdown);

    log(markdown);
    log('');
    log(`Wrote ${outPath}`);

    /* Steps 1, 4 and 5: what the agent still has to do ---------------- */

    const sources = prepSources({ prospect, prepMarkdown: markdown, research });

    if (!args.research) {
      log('');
      log('Still to do, step 1. Research and re-run with --research:');
      log(`  ${prospect.name}${prospect.title ? `, ${prospect.title}` : ''} at ${prospect.company ?? 'unknown company'}`);
      log(`  LinkedIn, the company site, and anything in the news in the last quarter.`);
      log(`  Save it as {"linkedin": "...", "company": "...", "news": [], "hooks": []}`);
    }

    log('');
    log('Still to do, steps 4 and 5. In NotebookLM:');
    log(`  Create a notebook called "Call prep: ${prospect.name}"`);
    log(`  Add ${sources.length} source${sources.length === 1 ? '' : 's'}:`);
    for (const s of sources) log(`    ${s.title}`);
    log(`  Generate the audio overview, then send the link.`);

    const sourcesPath = join(config.paths.prep, `${slug(prospect.email ?? prospect.name)}.sources.json`);
    await writeFile(sourcesPath, JSON.stringify(sources, null, 2));
    log('');
    log(`Sources ready to paste: ${sourcesPath}`);
  } finally {
    database.close();
  }
}

main().catch((err) => {
  console.error(`\nprompt 3 failed: ${err.message}`);
  process.exitCode = 1;
});
