/**
 * The one HTTP helper every connector uses.
 *
 * Retries on the failures that are worth retrying (429 and 5xx) and gives up
 * immediately on the ones that are not (401, 403, 404), because a pipeline
 * that quietly retries a bad API key for two minutes is worse than one that
 * stops and says the key is bad.
 */

const RETRYABLE = new Set([408, 425, 429, 500, 502, 503, 504]);

export class HttpError extends Error {
  constructor(status, url, body) {
    super(`${status} from ${url}: ${String(body).slice(0, 400)}`);
    this.name = 'HttpError';
    this.status = status;
    this.url = url;
    this.body = body;
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * @param {string} url
 * @param {RequestInit & {retries?:number, timeoutMs?:number}} [init]
 * @returns {Promise<Response>}
 */
export async function request(url, init = {}) {
  const { retries = 4, timeoutMs = 120000, ...rest } = init;

  let lastError;
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...rest, signal: controller.signal });
      clearTimeout(timer);

      if (res.ok) return res;

      const body = await res.text().catch(() => '');
      if (!RETRYABLE.has(res.status) || attempt === retries) {
        throw new HttpError(res.status, url, body);
      }

      // Honour Retry-After when the server sends one, otherwise back off.
      const retryAfter = Number(res.headers.get('retry-after'));
      const waitMs = Number.isFinite(retryAfter) && retryAfter > 0
        ? retryAfter * 1000
        : Math.min(30000, 2 ** attempt * 1000) + Math.floor(Math.random() * 400);
      lastError = new HttpError(res.status, url, body);
      await sleep(waitMs);
    } catch (err) {
      clearTimeout(timer);
      if (err instanceof HttpError) throw err;
      // Network error or timeout. Worth one more go.
      if (attempt === retries) throw err;
      lastError = err;
      await sleep(Math.min(30000, 2 ** attempt * 1000));
    }
  }
  throw lastError;
}

export async function getJson(url, init) {
  const res = await request(url, init);
  return res.json();
}

export async function postJson(url, body, init = {}) {
  const res = await request(url, {
    ...init,
    method: 'POST',
    headers: { 'content-type': 'application/json', ...(init.headers ?? {}) },
    body: JSON.stringify(body),
  });
  return res.json();
}

/** Run `worker` over `items` with at most `limit` in flight at once. */
export async function pool(items, limit, worker) {
  const results = new Array(items.length);
  let cursor = 0;

  async function run() {
    while (cursor < items.length) {
      const i = cursor++;
      results[i] = await worker(items[i], i);
    }
  }

  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, run));
  return results;
}
