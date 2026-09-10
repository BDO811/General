// Background service worker.
// - On toolbar click: re-inject overlay (in case page loaded before extension)
// - On runtime message "ocrExtract": OCR a screenshot fully locally (Tesseract.js,
//   run in an offscreen document) and parse the recognized text into
//   {symbol, shares, price, amount, account_last4, account_type}.
//
// No external API, no API key, no network request for OCR — everything Tesseract
// needs is bundled under vendor/tesseract/.

const OFFSCREEN_URL = "offscreen.html";

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab?.id) return;
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["fidelity-overlay.js"]
    });
  } catch (e) {
    console.error("[FidelityQuickOrder] inject failed:", e);
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.action === "ocrExtract") {
    handleOcr(msg.imageDataUrl).then(sendResponse).catch((e) =>
      sendResponse({ ok: false, error: e?.message || String(e) })
    );
    return true; // async response
  }
  if (msg?.action === "getQuote") {
    handleQuote(msg.symbol).then(sendResponse).catch((e) =>
      sendResponse({ ok: false, error: e?.message || String(e) })
    );
    return true;
  }
});

// Live price lookup via Yahoo Finance's public chart endpoint (no key required).
async function handleQuote(symbol) {
  const sym = (symbol || "").trim().toUpperCase();
  if (!sym) return { ok: false, error: "No symbol." };
  const hosts = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"];
  let lastErr = "";
  for (const host of hosts) {
    try {
      const resp = await fetch(
        `${host}/v8/finance/chart/${encodeURIComponent(sym)}?interval=1d&range=1d`,
        { headers: { accept: "application/json" } }
      );
      if (!resp.ok) { lastErr = `HTTP ${resp.status}`; continue; }
      const json = await resp.json();
      const meta = json?.chart?.result?.[0]?.meta;
      const price = meta?.regularMarketPrice;
      if (price == null) { lastErr = "No price returned."; continue; }
      const asOf = meta?.regularMarketTime
        ? new Date(meta.regularMarketTime * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : null;
      return { ok: true, symbol: meta?.symbol || sym, price, currency: meta?.currency || null, asOf };
    } catch (e) {
      lastErr = e?.message || String(e);
    }
  }
  return { ok: false, error: lastErr || "Quote lookup failed." };
}

// ---------- offscreen document (hosts Tesseract, isolated from Fidelity's CSP) ----------

let creatingOffscreen = null; // dedupe concurrent createDocument calls

async function ensureOffscreenDocument() {
  const existing = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
    documentUrls: [chrome.runtime.getURL(OFFSCREEN_URL)]
  });
  if (existing.length > 0) return;

  if (creatingOffscreen) {
    await creatingOffscreen;
    return;
  }
  creatingOffscreen = chrome.offscreen.createDocument({
    url: OFFSCREEN_URL,
    reasons: ["WORKERS"],
    justification: "Run Tesseract.js OCR on a pasted screenshot in a Worker, fully local."
  });
  try {
    await creatingOffscreen;
  } finally {
    creatingOffscreen = null;
  }
}

async function runOcrInOffscreen(imageDataUrl) {
  await ensureOffscreenDocument();
  const resp = await chrome.runtime.sendMessage({ target: "offscreen", type: "ocr", imageDataUrl });
  if (!resp) throw new Error("No response from offscreen OCR document.");
  if (!resp.ok) throw new Error(resp.error || "OCR failed.");
  return resp.text;
}

async function handleOcr(dataUrl) {
  if (!dataUrl?.startsWith("data:image/")) {
    return { ok: false, error: "No image data." };
  }

  let text;
  try {
    text = await runOcrInOffscreen(dataUrl);
  } catch (e) {
    return { ok: false, error: `OCR failed: ${e?.message || e}` };
  }
  if (!text || !text.trim()) {
    return { ok: false, error: "OCR found no readable text in this screenshot. Try a clearer crop, or paste the values as text instead." };
  }

  const data = parseOcrText(text);
  return { ok: true, data, rawText: text };
}

// ---------- local field extraction from raw OCR text ----------
// No model to lean on for this anymore — Tesseract returns plain text, not
// structured fields. Passes, most confident first:
//   1. Label-on-its-own-line, value-on-the-next-line (matches how Fidelity
//      actually lays out its ticket/position rows, and how OCR usually
//      preserves that when it reads cleanly).
//   2. Label-block / value-block: Tesseract frequently reads a two-column
//      label|value layout as two separate runs — every label top-to-bottom,
//      then every value top-to-bottom — rather than interleaved lines. Pass 1
//      finds nothing in that case (the line right after a label is just the
//      next label), so pair a run of >=2 consecutive label lines positionally
//      against the run of value lines that follows it.
//   3. Keyword-proximity fallback: scan the whole blob for a label keyword and
//      take the nearest value-shaped token after it, for when OCR runs labels
//      and values together on one line or drops a line break.
// Anything not found stays null — the UI always requires reviewing fields
// before Enter SELL Order, so a partial result is fine, a wrong guess isn't.

const KEY_RE = /^(symbol|symbol description|description|type|account type|account|shares|quantity|qty|price|last price|limit price|amount|action|side)$/i;

function parseSignedNumber(raw) {
  if (raw == null) return { value: NaN, sign: 0 };
  const s = String(raw).trim();
  const sign = s.startsWith("-") || s.startsWith("−") ? -1 : s.startsWith("+") ? 1 : 0;
  const cleaned = s.replace(/[+\-−,\s$]/g, "");
  const value = parseFloat(cleaned);
  return { value, sign };
}

function parseLabelValueLines(text) {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const map = {};
  for (let i = 0; i < lines.length - 1; i++) {
    // A label immediately preceded by another label is the tail of a
    // label-then-value-block run (see parseLabelValueBlocks below), not a
    // standalone pair — the non-label line right after it is the START of
    // the value block, not necessarily THIS label's value. Skipping it here
    // avoids mispairing e.g. the last of five stacked labels with the first
    // of five stacked values that follow.
    if (i > 0 && KEY_RE.test(lines[i - 1])) continue;
    if (KEY_RE.test(lines[i]) && !KEY_RE.test(lines[i + 1])) {
      map[lines[i].toLowerCase()] = lines[i + 1];
      i++;
    }
  }
  return map;
}

// Handles the "all labels, then all values" OCR ordering (common for card/grid
// UIs like Fidelity's ticket panel, where columns get read as separate blocks
// instead of interleaved rows). Find a run of >=2 consecutive label lines and
// zip it positionally against the run of non-label lines right after it —
// label[0]<->value[0], label[1]<->value[1], etc. A lone label (no run) is left
// alone here; parseLabelValueLines already handles that case via adjacency.
function parseLabelValueBlocks(text) {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const map = {};
  let i = 0;
  while (i < lines.length) {
    if (!KEY_RE.test(lines[i])) { i++; continue; }
    const labelStart = i;
    while (i < lines.length && KEY_RE.test(lines[i])) i++;
    const labels = lines.slice(labelStart, i);
    if (labels.length < 2) continue;
    const values = [];
    while (i < lines.length && values.length < labels.length && !KEY_RE.test(lines[i])) {
      values.push(lines[i]);
      i++;
    }
    for (let k = 0; k < values.length; k++) {
      map[labels[k].toLowerCase()] = values[k];
    }
  }
  return map;
}

// Find the value-shaped token nearest (and after) a keyword, searching within a
// short window of characters so an unrelated later number doesn't get grabbed.
function findNear(text, keywordRe, valueRe, windowChars = 60) {
  const km = keywordRe.exec(text);
  if (!km) return null;
  const start = km.index + km[0].length;
  const window = text.slice(start, start + windowChars);
  const vm = valueRe.exec(window);
  return vm ? vm[0] : null;
}

const TICKER_RE = /\b[A-Z]{1,5}(?:\.[A-Z])?\b/;
const MONEY_RE = /[+-]?\$?\s?[\d,]+\.\d{2,4}/;
const SHARES_RE = /[+-]?[\d,]+(?:\.\d+)?/;
const ACCOUNT_TYPE_RE = /\b(ROTH IRA|TRADITIONAL IRA|SEP IRA|SIMPLE IRA|INDIVIDUAL|JOINT|BROKERAGE|401K|CUSTODIAL)\b/i;
const LAST4_RE = /(?:\*{2,}\s*)(\d{4})\b|(\d{4})\s*$/m;
const MASKED_ACCT_RE = /\*{3,}\s*(\d{4})\b/;
const DATE_TOKEN_RE = /^[A-Za-z]{3}-\d{1,2}-\d{4}$/;
const MONEY_LINE_RE = /^[+-]?\$?[\d,]+\.\d{2,4}$/;
const NOISE_LINE_RE = /^\(?cash\)?$|^reinvestment\b|^dividend\b|^interest\b/i;

// Fidelity account "names" aren't a fixed set — they're whatever nickname the
// user gave the account ("Main Retirement Taxable Account", "ROTH IRA - Ria",
// etc.), printed as free text above a masked account number ("*****NNNN"),
// sometimes wrapped across 2-3 lines. Matching a keyword whitelist (IRA/
// INDIVIDUAL/JOINT/...) misses any custom nickname entirely. Instead, find the
// masked-number line and walk backward through the raw OCR lines to assemble
// whatever label precedes it, stopping at the previous row's date or dollar
// amount so we don't run past the account cell.
function extractAccountFromRawText(text) {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);

  // Fidelity often shows a sliver of the adjacent row above/below the one the
  // user actually expanded, so more than one masked-account line can appear
  // in the OCR text. The row that matches THIS detail panel is always the one
  // immediately before the panel's own "Date" / <date value> echo — so bound
  // the scan to lines before that echo, and keep the LAST masked-account
  // match found (closest to the panel), not the first one in the text.
  let boundary = lines.length;
  for (let i = 0; i < lines.length - 1; i++) {
    if (/^date$/i.test(lines[i]) && DATE_TOKEN_RE.test(lines[i + 1])) {
      boundary = i;
      break;
    }
  }

  let lastFound = null;
  for (let i = 0; i < boundary; i++) {
    const m = MASKED_ACCT_RE.exec(lines[i]);
    if (!m) continue;
    const last4 = m[1];
    const labelParts = [];
    const sameLine = lines[i].slice(0, m.index).trim();
    if (sameLine) labelParts.unshift(sameLine);
    for (let j = i - 1; j >= 0 && labelParts.length < 4; j--) {
      const l = lines[j];
      if (DATE_TOKEN_RE.test(l) || MONEY_LINE_RE.test(l) || NOISE_LINE_RE.test(l)) break;
      labelParts.unshift(l);
    }
    const label = labelParts
      .join(" ")
      .replace(/^[A-Za-z]{3}-\d{1,2}-\d{4}\s*/, "")
      .replace(/\s{2,}/g, " ")
      .trim();
    lastFound = { accountType: label || null, accountLast4: last4 };
  }
  return lastFound || { accountType: null, accountLast4: null };
}

// Asterisks are a small, fragile glyph — Tesseract can misread or drop
// "*****" entirely, which breaks the mask-anchored extraction above even
// though the account label around it read fine. Fall back to a pair of
// anchors OCR handles far more reliably: the transaction's date token (e.g.
// "Jul-31-2026") and the all-caps verb that starts the boxed description
// (REINVESTMENT, DIVIDEND RECEIVED, ...). The account label is whatever sits
// between them, with any trailing digit run (whatever survived of the masked
// number) split off as the last-4 — no requirement that the mask characters
// themselves were legible at all.
const TXN_VERB_RE = /\b(REINVESTMENT|DIVIDEND RECEIVED|QUALIFIED DIVIDEND|DIVIDEND|INTEREST EARNED|INTEREST|DISTRIBUTION|RETURN OF CAPITAL|YOU BOUGHT|YOU SOLD|TRANSFERRED|JOURNALED|MERGER|REORGANIZATION|CONTRIBUTION|WITHDRAWAL|DEPOSIT|CHECK|ASSIGNED|EXERCISED|EXPIRED|ELECTRONIC FUNDS TRANSFER|FEE CHARGED|NAME CHANGE|STOCK SPLIT|CASH MOVEMENT|ADJUSTMENT)\b/gi;
const DATE_ANYWHERE_RE = /[A-Za-z]{3}-\d{1,2}-\d{4}/g;
// The detail panel echoes its own date right after the literal word "Date" —
// e.g. "Date Jul-14-2026" — a pattern the summary rows above it never
// produce. Use it to find where the detail panel starts.
const DATE_LABEL_ECHO_RE = /\bDate\s+([A-Za-z]{3}-\d{1,2}-\d{4})\b/i;

function extractAccountByDateVerbSpan(text) {
  const flat = text.replace(/\r?\n/g, " ").replace(/\s{2,}/g, " ");

  // Fidelity often shows a sliver of the adjacent row above/below the one the
  // user actually expanded (visible as a partial row peeking into the crop).
  // The OCR text then contains multiple "<date> <account> <verb>..." groups,
  // and the FIRST one isn't necessarily the row this detail panel describes —
  // it's whichever row sits closest to the literal "Date"-labeled echo below.
  // So: bound the search to everything before that echo, and take the LAST
  // date/verb group in that bounded region, not the first in the whole text.
  const echoMatch = DATE_LABEL_ECHO_RE.exec(flat);
  const region = echoMatch ? flat.slice(0, echoMatch.index) : flat;

  const dateMatches = [...region.matchAll(DATE_ANYWHERE_RE)];
  if (!dateMatches.length) return { accountType: null, accountLast4: null };
  const dateMatch = dateMatches[dateMatches.length - 1];

  const afterDate = region.slice(dateMatch.index + dateMatch[0].length);
  TXN_VERB_RE.lastIndex = 0;
  const verbMatch = TXN_VERB_RE.exec(afterDate);
  if (!verbMatch) return { accountType: null, accountLast4: null };
  let span = afterDate.slice(0, verbMatch.index).trim();
  let last4 = null;
  const last4Match = /(\d{4})\D*$/.exec(span);
  if (last4Match) {
    last4 = last4Match[1];
    span = span.slice(0, last4Match.index).trim();
  }
  span = span.replace(/[*_\-.\s]+$/, "").trim();
  return { accountType: span || null, accountLast4: last4 };
}

function parseOcrText(text) {
  // Block pairing goes first (weaker signal, positional), adjacent-line
  // pairing second so it overrides on any key both passes agree exists.
  const map = { ...parseLabelValueBlocks(text), ...parseLabelValueLines(text) };
  const symRaw = map["symbol"] || map["symbol description"];
  const sharesRaw = map["shares"] || map["quantity"] || map["qty"];
  const priceRaw = map["price"] || map["limit price"] || map["last price"];
  const amountRaw = map["amount"];
  const accountRaw = map["account"] || map["account type"];

  let symbol = symRaw ? String(symRaw).toUpperCase().match(TICKER_RE)?.[0] || null : null;
  let shares = sharesRaw != null ? parseSignedNumber(sharesRaw).value : null;
  let price = priceRaw != null ? parseSignedNumber(priceRaw).value : null;
  let amount = amountRaw != null ? parseSignedNumber(amountRaw).value : null;
  let accountLast4 = null;
  let accountType = null;
  if (accountRaw) {
    const last4Match = String(accountRaw).match(/(\d{4})\s*$/);
    if (last4Match) accountLast4 = last4Match[1];
    accountType = String(accountRaw).replace(/\*+\s*\d+\s*$/, "").trim() || null;
  }

  // Fallback pass: fill in anything the label/value scans above missed.
  if (!symbol) {
    const m = findNear(text, /symbol/i, TICKER_RE, 40);
    if (m) symbol = m.toUpperCase();
  }
  if (shares == null || isNaN(shares)) {
    const m = findNear(text, /\b(shares|quantity|qty)\b/i, SHARES_RE, 40);
    if (m) shares = parseSignedNumber(m).value;
  }
  if (price == null || isNaN(price)) {
    const m = findNear(text, /\b(limit price|last price|price)\b/i, MONEY_RE, 40);
    if (m) price = parseSignedNumber(m).value;
  }
  if (amount == null || isNaN(amount)) {
    const m = findNear(text, /\bamount\b/i, MONEY_RE, 40);
    if (m) amount = parseSignedNumber(m).value;
  }
  if (!accountType || !accountLast4) {
    const found = extractAccountFromRawText(text);
    if (!accountType && found.accountType) accountType = found.accountType.toUpperCase();
    if (!accountLast4 && found.accountLast4) accountLast4 = found.accountLast4;
  }
  // Mask-anchored extraction depends on Tesseract having read the "*****"
  // cleanly — it often doesn't. This anchor never needs the mask itself to be
  // legible at all, so it catches cases the pass above misses.
  if (!accountType || !accountLast4) {
    const found = extractAccountByDateVerbSpan(text);
    if (!accountType && found.accountType) accountType = found.accountType.toUpperCase();
    if (!accountLast4 && found.accountLast4) accountLast4 = found.accountLast4;
  }
  if (!accountType) {
    const m = ACCOUNT_TYPE_RE.exec(text);
    if (m) accountType = m[0].toUpperCase();
  }
  if (!accountLast4) {
    const m = LAST4_RE.exec(text);
    if (m) accountLast4 = m[1] || m[2] || null;
  }

  return {
    symbol: symbol || null,
    shares: shares != null && !isNaN(shares) ? shares : null,
    price: price != null && !isNaN(price) ? price : null,
    amount: amount != null && !isNaN(amount) ? amount : null,
    account_last4: accountLast4,
    account_type: accountType
  };
}
