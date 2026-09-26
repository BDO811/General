#!/usr/bin/env node
/**
 * Assemble the deployable site into dist/.
 *
 * There is no bundler and no transpile step. The page imports the engine as
 * plain ES modules, so "building" is copying four directories into one that
 * can be served from any static host at any path.
 *
 * The engine files are copied rather than duplicated by hand, which is the
 * point: the page and the pipeline run the same analysis, and there is no
 * second copy to drift.
 *
 * Usage:
 *   node build.mjs                 assemble into dist/
 *   node build.mjs --out ../site   assemble somewhere else
 */

import { cp, rm, mkdir, readdir, stat } from 'node:fs/promises';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));

const argv = process.argv.slice(2);
const outFlag = argv.indexOf('--out');
const OUT = resolve(HERE, outFlag === -1 ? 'dist' : argv[outFlag + 1]);
const clean = !argv.includes('--no-clean');

/** What goes where, relative to the project root and to dist. */
const COPY = [
  { from: 'web', to: '.' },
  { from: 'engine', to: 'engine' },
  { from: 'prompts', to: 'prompts' },
  { from: 'data/demo-dataset.json', to: 'data/demo-dataset.json' },
];

async function dirSize(path) {
  let bytes = 0;
  let files = 0;
  for (const entry of await readdir(path, { withFileTypes: true })) {
    const full = join(path, entry.name);
    if (entry.isDirectory()) {
      const inner = await dirSize(full);
      bytes += inner.bytes;
      files += inner.files;
    } else {
      bytes += (await stat(full)).size;
      files += 1;
    }
  }
  return { bytes, files };
}

async function main() {
  if (clean) await rm(OUT, { recursive: true, force: true });
  await mkdir(OUT, { recursive: true });

  for (const item of COPY) {
    const from = resolve(HERE, item.from);
    const to = resolve(OUT, item.to);
    await mkdir(dirname(to), { recursive: true });
    await cp(from, to, { recursive: true });
  }

  const { bytes, files } = await dirSize(OUT);
  console.log(`Built ${OUT}`);
  console.log(`  ${files} files, ${(bytes / 1024).toFixed(0)} KB`);
  console.log(`  serve it from any path: it uses no absolute URLs`);
}

main().catch((err) => {
  console.error(`build failed: ${err.message}`);
  process.exitCode = 1;
});
