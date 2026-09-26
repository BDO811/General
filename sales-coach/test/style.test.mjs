/**
 * House style, enforced.
 *
 * Em dashes, en dashes and ellipsis characters are not used anywhere in this
 * project, in prose or in generated output. This is a standing rule rather
 * than a preference, so it is a test rather than a note in a contributing
 * guide.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve, relative, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const SKIP_DIRS = new Set(['node_modules', 'dist', '.git']);
const CHECK_EXT = ['.md', '.js', '.mjs', '.html', '.css', '.sql', '.txt'];

/** Generated data. Its content is names and ids, and it is 300 KB of one line. */
const SKIP_FILES = new Set(['demo-dataset.json']);

/** This file necessarily contains the characters it is looking for. */
const SELF = basename(fileURLToPath(import.meta.url));

const FORBIDDEN = {
  '–': 'en dash',
  '—': 'em dash',
  '…': 'ellipsis',
  '‒': 'figure dash',
  '―': 'horizontal bar',
};

function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      walk(join(dir, entry.name), out);
    } else {
      out.push(join(dir, entry.name));
    }
  }
  return out;
}

test('no em dash, en dash or ellipsis anywhere in the project', () => {
  const offences = [];

  for (const path of walk(ROOT)) {
    const name = basename(path);
    if (name === SELF || SKIP_FILES.has(name)) continue;
    if (name !== '.env.example' && !CHECK_EXT.some((e) => name.endsWith(e))) continue;

    let text;
    try {
      text = readFileSync(path, 'utf8');
    } catch {
      continue;
    }

    text.split('\n').forEach((line, i) => {
      for (const [char, label] of Object.entries(FORBIDDEN)) {
        if (line.includes(char)) {
          offences.push(`${relative(ROOT, path)}:${i + 1} ${label}: ${line.trim().slice(0, 90)}`);
        }
      }
    });
  }

  assert.deepEqual(offences, [], `\n${offences.join('\n')}\n`);
});

test('no credential file is committed', () => {
  const leaked = walk(ROOT).filter((p) => {
    const name = basename(p);
    return name === '.env' || name.endsWith('.pem');
  });
  assert.deepEqual(leaked.map((p) => relative(ROOT, p)), [], 'a credential file is present');
});

test('.env.example documents every key the config reads', async () => {
  const example = readFileSync(join(ROOT, 'pipeline/.env.example'), 'utf8');
  const config = readFileSync(join(ROOT, 'pipeline/config.mjs'), 'utf8');

  // Every SCREAMING_SNAKE env key config.mjs reads off `env`.
  const used = new Set([...config.matchAll(/env\.([A-Z][A-Z0-9_]+)/g)].map((m) => m[1]));
  // Set by the shell, not by the user.
  for (const builtin of ['HOME', 'USERPROFILE', 'GOOGLE_API_KEY']) used.delete(builtin);

  const missing = [...used].filter((key) => !new RegExp(`^#?\\s*${key}=`, 'm').test(example));
  assert.deepEqual(missing, [], `keys read by config.mjs but absent from .env.example: ${missing.join(', ')}`);
});

test('the demo dataset stays checked in and loadable', () => {
  const path = join(ROOT, 'data/demo-dataset.json');
  assert.ok(statSync(path).size > 1000, 'the workbench cannot load without it');
});
