/**
 * Configuration and working directories.
 *
 * Everything lives under ~/sales-coach, the way the reel lays it out:
 *
 *   ~/sales-coach/calls/        downloaded audio, named by transcript id
 *   ~/sales-coach/calls/[id].json  tone-tagged transcripts
 *   ~/sales-coach/sales.db      the one database
 *   ~/sales-coach/findings.md   what prompt 2 writes
 *   ~/sales-coach/prep/         what prompt 3 writes, one file per prospect
 *   ~/sales-coach/dataset.json  the export the workbench reads
 *
 * Secrets come from the environment or from a .env file next to this one.
 * Nothing is read from, or written to, the repository.
 */

import { readFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));

/** Minimal .env reader. No dependency, no surprises about quoting. */
export function loadEnvFile(path = resolve(HERE, '.env')) {
  if (!existsSync(path)) return {};

  const out = {};
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    out[key] = value;
  }
  return out;
}

export function loadConfig(overrides = {}) {
  const fromFile = loadEnvFile();
  const env = { ...fromFile, ...process.env, ...overrides };

  const home = env.HOME ?? env.USERPROFILE ?? '.';
  const root = env.SALES_COACH_HOME ?? join(home, 'sales-coach');

  return {
    root,
    paths: {
      root,
      calls: join(root, 'calls'),
      prep: join(root, 'prep'),
      db: join(root, 'sales.db'),
      findings: join(root, 'findings.md'),
      dataset: join(root, 'dataset.json'),
    },

    seller: {
      email: (env.SELLER_EMAIL ?? '').toLowerCase() || null,
      name: env.SELLER_NAME ?? null,
    },

    /** How far back prompt 1 looks. The reel uses 12 months. */
    months: Number(env.LOOKBACK_MONTHS ?? 12),

    fireflies: { apiKey: env.FIREFLIES_API_KEY ?? null },

    gemini: {
      apiKey: env.GEMINI_API_KEY ?? env.GOOGLE_API_KEY ?? null,
      model: env.GEMINI_MODEL ?? 'gemini-3.8-flash',
      concurrency: Number(env.GEMINI_CONCURRENCY ?? 3),
    },

    gmail: { token: env.GMAIL_ACCESS_TOKEN ?? null },

    hubspot: { token: env.HUBSPOT_TOKEN ?? null },

    jev: {
      transport: env.JEV_TRANSPORT ?? 'mcp',
      tool: env.JEV_TOOL ?? 'jev_verify',
      url: env.JEV_URL ?? null,
      apiKey: env.TYPESAFE_API_KEY ?? null,
      concurrency: Number(env.JEV_CONCURRENCY ?? 8),
    },

    thresholds: {
      minSample: Number(env.MIN_SAMPLE ?? 10),
      minGapPp: Number(env.MIN_GAP_PP ?? 15),
      alpha: Number(env.ALPHA ?? 0.05),
    },
  };
}

/** Create the working directories. Safe to call every run. */
export function ensureDirs(config) {
  for (const dir of [config.paths.root, config.paths.calls, config.paths.prep]) {
    mkdirSync(dir, { recursive: true });
  }
}

/**
 * Stop before doing any work if a required credential is missing.
 *
 * Failing at the top with a list beats failing on call 140 of 214 with a 401.
 */
export function requireKeys(config, keys) {
  const missing = [];
  const check = {
    fireflies: () => config.fireflies.apiKey || missing.push('FIREFLIES_API_KEY'),
    gemini: () => config.gemini.apiKey || missing.push('GEMINI_API_KEY'),
    gmail: () => config.gmail.token || missing.push('GMAIL_ACCESS_TOKEN'),
    hubspot: () => config.hubspot.token || missing.push('HUBSPOT_TOKEN'),
    seller: () => config.seller.email || missing.push('SELLER_EMAIL'),
    jev: () => {
      if (config.jev.transport === 'http') {
        config.jev.url || missing.push('JEV_URL');
      } else if (!config.jev.apiKey) {
        missing.push('TYPESAFE_API_KEY');
      }
    },
  };

  for (const key of keys) check[key]?.();

  if (missing.length) {
    throw new Error(
      `Missing configuration: ${missing.join(', ')}.\n` +
        `Set them in the environment or in pipeline/.env. See pipeline/.env.example.`
    );
  }
}

/** The start of the lookback window. */
export function windowStart(config, asOf = new Date()) {
  const d = new Date(asOf);
  d.setMonth(d.getMonth() - config.months);
  return d;
}
