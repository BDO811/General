// Fidelity Quick Order Overlay
// Floating button on digital.fidelity.com. Click to open a panel:
//   1. Paste a screenshot (Cmd+V) OR a label/value text block
//   2. Extension extracts symbol, shares, price, amount, account
//   3. Action is hardcoded to SELL
//   4. Submit selects the matching account on Fidelity's trade ticket,
//      fills the form, and clicks Preview Order.

(function () {
  if (window.__fidelityQuickOrderInjected) return;
  window.__fidelityQuickOrderInjected = true;

  const HOST_ID = "fidelity-quick-order-host";
  const STATE_KEY = "fidelityQuickOrderLast";

  // ---------- styles ----------
  const css = `
    #${HOST_ID} { position: fixed; z-index: 2147483647; right: 20px; bottom: 20px;
      font-family: "Helvetica Neue", Arial, sans-serif; color: #111; }
    #${HOST_ID} .fqo-fab {
      width: 56px; height: 56px; border-radius: 50%; background: #050505;
      color: #f3eee4; font-weight: 900; letter-spacing: -0.5px;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; box-shadow: 0 6px 24px rgba(0,0,0,0.35);
      user-select: none; font-size: 14px; border: 0;
    }
    #${HOST_ID} .fqo-fab:hover { background: #1a1a1a; }
    #${HOST_ID} .fqo-panel {
      position: absolute; right: 0; bottom: 70px; width: 380px;
      background: #ffffff; border: 1px solid #d0d0d0; border-radius: 8px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.25); padding: 16px;
    }
    #${HOST_ID} .fqo-drop {
      width: 100%; box-sizing: border-box; border: 2px dashed #050505;
      border-radius: 6px; padding: 22px 10px; text-align: center;
      font-size: 13px; font-weight: 700; color: #050505; cursor: pointer;
      background: #f3eee4; min-height: 96px;
      display: flex; align-items: center; justify-content: center;
    }
    #${HOST_ID} .fqo-drop.fqo-active { border-color: #050505; background: #f0eee9; color: #111; }
    #${HOST_ID} .fqo-drop.fqo-has-image { padding: 6px; }
    #${HOST_ID} .fqo-drop img { max-width: 100%; max-height: 140px; border-radius: 4px; }
    #${HOST_ID} textarea.fqo-text {
      width: 100%; box-sizing: border-box; padding: 8px 10px;
      border: 1px solid #bbb; border-radius: 6px; font-size: 12px;
      font-family: ui-monospace, Menlo, monospace; min-height: 64px; resize: vertical;
      background: #fafafa; color: #111; margin-top: 8px;
    }
    #${HOST_ID} textarea.fqo-text:focus { outline: 2px solid #050505; }
    #${HOST_ID} .fqo-help { font-size: 11px; color: #888; margin: 4px 0 10px; }
    #${HOST_ID} .fqo-row { display: flex; gap: 8px; margin-bottom: 10px; }
    #${HOST_ID} .fqo-row > * { flex: 1; }
    #${HOST_ID} label { font-size: 11px; font-weight: 700; color: #444;
      display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
    #${HOST_ID} input {
      width: 100%; box-sizing: border-box; padding: 8px 10px;
      border: 1px solid #bbb; border-radius: 6px; font-size: 14px;
      font-family: inherit; background: #fff; color: #111;
    }
    #${HOST_ID} input:focus { outline: 2px solid #050505; }
    #${HOST_ID} .fqo-actions { display: flex; gap: 8px; margin-top: 6px; }
    #${HOST_ID} button.fqo-btn {
      flex: 1; padding: 10px; border-radius: 6px; border: 0;
      font-weight: 700; cursor: pointer; font-size: 13px;
    }
    #${HOST_ID} .fqo-primary { background: #050505; color: #f3eee4; }
    #${HOST_ID} .fqo-primary:hover { background: #1a1a1a; }
    #${HOST_ID} .fqo-ghost { background: #eee; color: #111; }
    #${HOST_ID} .fqo-ghost:hover { background: #ddd; }
    #${HOST_ID} .fqo-status {
      margin-top: 10px; font-size: 12px; color: #444;
      max-height: 90px; overflow: auto; white-space: pre-wrap;
      background: #f5f5f5; padding: 6px 8px; border-radius: 4px; display: none;
    }
    #${HOST_ID} .fqo-quote {
      font-size: 11px; color: #666; min-height: 14px; margin: -4px 0 10px;
    }
    #${HOST_ID} .fqo-quote b { color: #ff0000; }
    #${HOST_ID} .fqo-quote-use {
      margin-left: 6px; background: none; border: 0; padding: 0;
      font-size: 11px; font-weight: 700; color: #050505; text-decoration: underline;
      cursor: pointer;
    }
    #${HOST_ID} .fqo-title-row { display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 12px; }
    #${HOST_ID} .fqo-title { font-weight: 900; font-size: 14px; letter-spacing: -0.3px; }
    #${HOST_ID} .fqo-action-pill { font-size: 10px; font-weight: 900; background: #c00; color: #fff;
      padding: 3px 8px; border-radius: 999px; letter-spacing: 0.5px; }
    #${HOST_ID} .fqo-icon-btn { background: none; border: 0; cursor: pointer; color: #888;
      font-size: 14px; padding: 0 4px; }
    #${HOST_ID} .fqo-icon-btn:hover { color: #111; }
    #${HOST_ID} .fqo-close { background: none; border: 0; cursor: pointer; color: #888;
      font-weight: 700; font-size: 16px; }
    #${HOST_ID} .fqo-progress {
      display: flex; gap: 3px; margin: 0 0 12px 0;
    }
    #${HOST_ID} .fqo-step {
      flex: 1; height: 6px; background: #e5e5e5; border-radius: 2px;
      transition: background 0.15s ease;
    }
    #${HOST_ID} .fqo-step-done { background: #ff1a1a; }
    #${HOST_ID} .fqo-step-active {
      background: #ff1a1a;
      animation: fqoFlash 0.5s ease-in-out infinite alternate;
    }
    @keyframes fqoFlash {
      0%   { background: #ff1a1a; box-shadow: 0 0 0 #ff1a1a; }
      100% { background: #ff5555; box-shadow: 0 0 8px #ff1a1a; }
    }
  `;
  const style = document.createElement("style");
  style.textContent = css;
  document.documentElement.appendChild(style);

  // ---------- DOM ----------
  const host = document.createElement("div");
  host.id = HOST_ID;
  host.innerHTML = `
    <button class="fqo-fab" title="Quick Order">FID</button>
    <div class="fqo-panel" style="display:none">
      <div class="fqo-progress">
        <div class="fqo-step" data-step="0" title="Trade tab"></div>
        <div class="fqo-step" data-step="1" title="Account"></div>
        <div class="fqo-step" data-step="2" title="Symbol"></div>
        <div class="fqo-step" data-step="3" title="Sell"></div>
        <div class="fqo-step" data-step="4" title="Quantity"></div>
        <div class="fqo-step" data-step="5" title="Limit"></div>
        <div class="fqo-step" data-step="6" title="Limit Price"></div>
        <div class="fqo-step" data-step="7" title="GTC"></div>
        <div class="fqo-step" data-step="8" title="Preview"></div>
      </div>
      <div class="fqo-title-row">
        <div style="display:flex;align-items:center;gap:8px">
          <span class="fqo-title">Quick Sell</span>
          <span class="fqo-action-pill">SELL</span>
        </div>
        <div>
          <button class="fqo-icon-btn fqo-close" aria-label="Close">×</button>
        </div>
      </div>
      <label>Paste Screenshot</label>
      <div class="fqo-drop" tabindex="0">Press Cmd+V to paste a screenshot (read locally, on-device — no data leaves this machine)</div>
      <textarea class="fqo-text" placeholder="…or paste a label/value block here (Symbol&#10;CCIF&#10;Shares&#10;+2,018.629…)"></textarea>
      <div class="fqo-help">Action is locked to SELL. Account is auto-selected on Fidelity.</div>
      <div class="fqo-row">
        <div>
          <label>Account</label>
          <input class="fqo-account" placeholder="ROTH IRA ***8429" autocomplete="off"/>
        </div>
        <div>
          <label>Ticker</label>
          <input class="fqo-ticker" placeholder="CCIF" autocomplete="off"/>
        </div>
      </div>
      <div class="fqo-row">
        <div>
          <label>Shares</label>
          <input class="fqo-qty" type="number" min="0" step="any" placeholder="100"/>
        </div>
        <div>
          <label>Limit Price</label>
          <input class="fqo-price" type="number" min="0" step="0.01" placeholder="3.37"/>
        </div>
      </div>
      <div class="fqo-quote"></div>
      <div class="fqo-actions">
        <button class="fqo-btn fqo-ghost" data-act="cancel">Cancel</button>
        <button class="fqo-btn fqo-primary" data-act="submit">Enter SELL Order</button>
      </div>
      <div class="fqo-status"></div>
    </div>
  `;
  document.body.appendChild(host);

  const $ = (s) => host.querySelector(s);
  const fab = $(".fqo-fab");
  const panel = $(".fqo-panel");
  const dropEl = $(".fqo-drop");
  const textEl = $(".fqo-text");
  const accountEl = $(".fqo-account");
  const tickerEl = $(".fqo-ticker");
  const qtyEl = $(".fqo-qty");
  const priceEl = $(".fqo-price");
  const statusEl = $(".fqo-status");
  const quoteEl = $(".fqo-quote");

  function setStatus(msg, isError = false) {
    statusEl.style.display = "block";
    statusEl.style.color = isError ? "#a00" : "#444";
    statusEl.textContent = msg;
  }

  // ---------- live price lookup (internet quote via background) ----------
  let quoteReqId = 0;
  let quoteDebounce;
  async function fetchQuote(symbol) {
    const sym = (symbol || "").trim().toUpperCase();
    if (!sym) { quoteEl.textContent = ""; return; }
    const reqId = ++quoteReqId;
    quoteEl.textContent = `Looking up ${sym}…`;
    const resp = await new Promise((resolve) =>
      chrome.runtime.sendMessage({ action: "getQuote", symbol: sym }, resolve)
    );
    if (reqId !== quoteReqId) return; // ticker changed since this request went out
    if (!resp?.ok) {
      quoteEl.textContent = `Live price unavailable (${resp?.error || "error"})`;
      return;
    }
    quoteEl.innerHTML = `Live: <b>$${Number(resp.price).toFixed(2)}</b>${resp.asOf ? ` · ${resp.asOf}` : ""}`;
    const useBtn = document.createElement("button");
    useBtn.type = "button";
    useBtn.className = "fqo-quote-use";
    useBtn.textContent = "Use as limit";
    useBtn.addEventListener("click", () => { priceEl.value = resp.price; });
    quoteEl.appendChild(useBtn);
  }
  function scheduleQuote(symbol) {
    clearTimeout(quoteDebounce);
    quoteDebounce = setTimeout(() => fetchQuote(symbol), 400);
  }
  tickerEl.addEventListener("input", () => scheduleQuote(tickerEl.value));
  tickerEl.addEventListener("blur", () => fetchQuote(tickerEl.value));

  // Progress bar: 9 steps. Index becomes "active" (flashing red); all prior become "done" (solid red).
  const stepEls = host.querySelectorAll(".fqo-step");
  function setStep(index) {
    stepEls.forEach((el, i) => {
      el.classList.remove("fqo-step-active", "fqo-step-done");
      if (i < index) el.classList.add("fqo-step-done");
      else if (i === index) el.classList.add("fqo-step-active");
    });
  }
  function resetSteps() {
    stepEls.forEach((el) => el.classList.remove("fqo-step-active", "fqo-step-done"));
  }
  function finishSteps() {
    stepEls.forEach((el) => {
      el.classList.remove("fqo-step-active");
      el.classList.add("fqo-step-done");
    });
  }

  function togglePanel(show) {
    panel.style.display = show ? "block" : "none";
    if (show) {
      dropEl.focus();
      // Try modern Clipboard API to auto-pick up an image already on the clipboard.
      if (navigator.clipboard?.read) {
        navigator.clipboard.read().then(async (items) => {
          for (const item of items) {
            const imgType = item.types.find((t) => t.startsWith("image/"));
            if (imgType) {
              const blob = await item.getType(imgType);
              const reader = new FileReader();
              reader.onload = async () => {
                const dataUrl = reader.result;
                showImagePreview(dataUrl);
                await runOcr(dataUrl);
              };
              reader.readAsDataURL(blob);
              return;
            }
          }
        }).catch(() => {});
      }
    }
  }

  fab.addEventListener("click", () => togglePanel(panel.style.display === "none"));
  $(".fqo-close").addEventListener("click", () => togglePanel(false));
  panel.addEventListener("click", async (e) => {
    const act = e.target?.dataset?.act;
    if (act === "cancel") return togglePanel(false);
    if (act === "submit") return submit();
  });

  // ---------- text-block parser (fallback for non-image paste) ----------
  const KEY_RE = /^(symbol|symbol description|description|type|account type|account|shares|quantity|qty|price|last price|limit price|amount|action|side)$/i;
  function parsePasteBlock(text) {
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    const map = {};
    for (let i = 0; i < lines.length - 1; i++) {
      // See parseTextBlocks below: a label immediately preceded by another
      // label is the tail of a label-block, not a standalone pair — don't
      // mispair it with the first line of the value block that follows.
      if (i > 0 && KEY_RE.test(lines[i - 1])) continue;
      if (KEY_RE.test(lines[i]) && !KEY_RE.test(lines[i + 1])) {
        map[lines[i].toLowerCase()] = lines[i + 1];
        i++;
      }
    }
    return map;
  }

  // Same "all labels, then all values" OCR/paste ordering that background.js
  // guards against — a pasted text block copied from a two-column layout can
  // land the same way (every label first, every value after). Pair a run of
  // >=2 consecutive label lines positionally against the values that follow.
  function parseTextBlocks(text) {
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

  function parseSignedNumber(raw) {
    if (raw == null) return { value: NaN, sign: 0 };
    const s = String(raw).trim();
    const sign = s.startsWith("-") || s.startsWith("−") ? -1 : s.startsWith("+") ? 1 : 0;
    const cleaned = s.replace(/[+\-−,\s$]/g, "");
    const value = parseFloat(cleaned);
    return { value, sign };
  }

  function applyFields({ symbol, shares, price, account_last4, account_type }) {
    if (symbol) {
      const sym = String(symbol).toUpperCase().replace(/[^A-Z0-9.\-]/g, "");
      if (sym) tickerEl.value = sym;
    }
    if (shares != null && !isNaN(parseFloat(shares))) {
      // Floor to whole shares — Fidelity rejects GTC on fractional shares
      qtyEl.value = Math.floor(Math.abs(parseFloat(shares)));
    }
    if (price != null && !isNaN(parseFloat(price))) {
      priceEl.value = parseFloat(price);
    }
    if (account_last4 || account_type) {
      const parts = [];
      if (account_type) parts.push(String(account_type).toUpperCase());
      if (account_last4) parts.push(`***${String(account_last4).replace(/\D/g, "").slice(-4)}`);
      accountEl.value = parts.join(" ");
    }
    if (tickerEl.value) fetchQuote(tickerEl.value);
  }

  function applyTextParsed(text) {
    // Block pairing goes first (weaker signal, positional), adjacent-line
    // pairing second so it overrides on any key both passes agree exists.
    const map = { ...parseTextBlocks(text), ...parsePasteBlock(text) };
    if (!Object.keys(map).length) return false;
    const sym = map["symbol"];
    const sharesRaw = map["shares"] || map["quantity"] || map["qty"];
    const priceRaw = map["price"] || map["limit price"] || map["last price"];
    const accountRaw = map["account"] || map["account type"];
    const fields = {};
    if (sym) fields.symbol = sym;
    if (sharesRaw) fields.shares = parseSignedNumber(sharesRaw).value;
    if (priceRaw) fields.price = parseSignedNumber(priceRaw).value;
    if (accountRaw) {
      const last4Match = accountRaw.match(/(\d{4})\s*$/);
      if (last4Match) fields.account_last4 = last4Match[1];
      fields.account_type = accountRaw.replace(/\*+\s*\d+\s*$/, "").trim();
    }
    applyFields(fields);
    return true;
  }

  // ---------- screenshot OCR via background ----------
  // sendMessage wrapper that surfaces chrome.runtime.lastError instead of a
  // silent undefined response (the cause of the bare "OCR failed." message).
  function bgMessage(msg) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(msg, (resp) => {
          const le = chrome.runtime.lastError;
          if (le) resolve({ ok: false, error: `Extension error: ${le.message}. Reload the extension at chrome://extensions, then refresh this page.` });
          else resolve(resp);
        });
      } catch (e) {
        resolve({ ok: false, error: `Extension error: ${e.message}. Refresh this page and try again.` });
      }
    });
  }

  // Guards against two OCR calls racing: the paste event fires on the drop zone
  // AND bubbles to the panel, and the clipboard auto-read can land on top of a
  // manual Cmd+V. Concurrent calls used to double-bill and let a loser's error
  // overwrite the winner's parsed fields.
  let ocrInFlight = false;

  async function runOcr(dataUrl) {
    if (ocrInFlight) return;
    ocrInFlight = true;
    try {
      await runOcrInner(dataUrl);
    } finally {
      ocrInFlight = false;
    }
  }

  async function runOcrInner(dataUrl) {
    // First read of a screenshot spins up the offscreen OCR document and loads
    // the language model — noticeably slower than subsequent reads.
    setStatus("Reading screenshot locally (on-device OCR)…");
    const resp = await bgMessage({ action: "ocrExtract", imageDataUrl: dataUrl });
    if (!resp?.ok) {
      setStatus(resp?.error || "OCR failed: no response from the extension background worker. Reload the extension at chrome://extensions, then refresh this page.", true);
      return;
    }
    const d = resp.data || {};
    // Each screenshot is a standalone transaction record. Clear every field
    // before applying the new parse so a field this screenshot fails to
    // produce (e.g. an account nickname OCR can't read) shows up as an
    // obvious blank, not a stale value carried over from the last paste —
    // that stale value is exactly what feeds account auto-select on submit.
    tickerEl.value = "";
    qtyEl.value = "";
    priceEl.value = "";
    accountEl.value = "";
    applyFields(d);
    const summary = [
      d.symbol && `Symbol: ${d.symbol}`,
      d.shares != null && `Shares: ${d.shares}`,
      d.price != null && `Price: $${d.price}`,
      d.amount != null && `Amount: $${d.amount}`,
      d.account_type && `${d.account_type}${d.account_last4 ? ` ***${d.account_last4}` : ""}`
    ].filter(Boolean).join(" · ");
    // Account parsing keeps missing in ways that don't match what the parser
    // logic should produce against clean text — meaning the actual Tesseract
    // output for these screenshots has never actually been seen, only
    // guessed at. Surface it directly (console + status box) so a real
    // failure can be diagnosed from real data instead of another guess.
    console.log("[FQO] raw OCR text:\n" + (resp.rawText || "(none)"));
    const rawPreview = (resp.rawText || "").trim();
    setStatus(
      `Parsed: ${summary || "(no fields)"}\nReview and click Enter SELL Order.` +
      (rawPreview ? `\n\n[Raw OCR — copy this back if account is still wrong]\n${rawPreview}` : "")
    );
  }

  function showImagePreview(dataUrl) {
    dropEl.innerHTML = "";
    dropEl.classList.add("fqo-has-image");
    const img = document.createElement("img");
    img.src = dataUrl;
    dropEl.appendChild(img);
  }

  // Handle a clipboard paste — image or text
  async function handlePasteEvent(e) {
    const items = e.clipboardData?.items || [];
    for (const item of items) {
      if (item.kind === "file" && item.type.startsWith("image/")) {
        e.preventDefault();
        const blob = item.getAsFile();
        if (!blob) continue;
        const reader = new FileReader();
        reader.onload = async () => {
          const dataUrl = reader.result;
          showImagePreview(dataUrl);
          await runOcr(dataUrl);
        };
        reader.readAsDataURL(blob);
        return true;
      }
    }
    // No image — try text from clipboard
    const txt = e.clipboardData?.getData("text") || "";
    if (txt && /symbol|shares|price|amount|account/i.test(txt)) {
      e.preventDefault();
      textEl.value = txt;
      const ok = applyTextParsed(txt);
      setStatus(ok ? "Parsed text. Review and submit." : "Could not parse text block.", !ok);
      return true;
    }
    return false;
  }

  // Panel-wide paste: catches Cmd+V anywhere in the panel, including the drop
  // zone (the event bubbles up from it). Deliberately the ONLY paste listener —
  // a second one on dropEl meant every screenshot ran OCR twice.
  panel.addEventListener("paste", (e) => {
    // Skip if user is intentionally pasting into the manual-edit inputs
    const tag = e.target?.tagName;
    if (tag === "INPUT" && !e.target.classList.contains("fqo-text")) return;
    handlePasteEvent(e);
  });

  // Chrome only dispatches paste to an editable or focused element. The drop zone
  // is a plain div, so a Cmd+V with focus elsewhere on the page lands on document
  // and never reaches the panel listener above.
  document.addEventListener("paste", (e) => {
    if (panel.style.display === "none") return;
    if (panel.contains(e.target)) return; // already handled by the panel listener
    handlePasteEvent(e);
  });

  dropEl.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropEl.classList.add("fqo-active");
  });
  dropEl.addEventListener("dragleave", () => dropEl.classList.remove("fqo-active"));
  dropEl.addEventListener("drop", async (e) => {
    e.preventDefault();
    dropEl.classList.remove("fqo-active");
    const file = e.dataTransfer?.files?.[0];
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = async () => {
        const dataUrl = reader.result;
        showImagePreview(dataUrl);
        await runOcr(dataUrl);
      };
      reader.readAsDataURL(file);
    }
  });

  textEl.addEventListener("input", () => {
    if (!textEl.value.trim()) return;
    applyTextParsed(textEl.value);
  });

  // restore last
  try {
    const last = JSON.parse(localStorage.getItem(STATE_KEY) || "{}");
    if (last.ticker) tickerEl.value = last.ticker;
    if (last.account) accountEl.value = last.account;
  } catch {}

  // ---------- Fidelity automation (faithful port of Ten Talons executeSellOrder) ----------
  // Source: /Users/amitmehta/Desktop/ten-talons-ext/background.js, function executeSellOrder.
  // Reads {account, symbol, quantity, limitPrice} from the overlay input boxes.
  // Always: action=SELL, orderType=Limit, timeInForce=Good 'Til Canceled.

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function simulateTyping(inputElement, newValue, delay = 1) {
    if (!inputElement) return Promise.reject("Input element not found");
    return new Promise((typeResolve) => {
      inputElement.value = "";
      inputElement.focus();
      const text = String(newValue);
      let index = 0;
      function typeCharacter() {
        if (index < text.length) {
          inputElement.value += text.charAt(index);
          inputElement.dispatchEvent(new Event("input", { bubbles: true }));
          inputElement.dispatchEvent(new KeyboardEvent("keydown", {
            key: text.charAt(index),
            keyCode: text.charCodeAt(index),
            bubbles: true
          }));
          index++;
          setTimeout(typeCharacter, delay);
        } else {
          inputElement.dispatchEvent(new Event("change", { bubbles: true }));
          inputElement.dispatchEvent(new Event("blur", { bubbles: true }));
          typeResolve();
        }
      }
      typeCharacter();
    });
  }

  function selectAccountFromDropdown(targetAccountName, onComplete) {
    const accountDropdown = document.querySelector("#dest-acct-dropdown");
    if (!accountDropdown) {
      console.error("[FQO] #dest-acct-dropdown not found");
      onComplete(false);
      return;
    }
    accountDropdown.click();

    function normalize(name) {
      const m = name.match(/(?:[A-Z]\d{8}|\d{9})/i);
      return { full: name.trim().toLowerCase(), number: m ? m[0].toLowerCase() : null };
    }
    const target = normalize(targetAccountName);
    const targetLast4 = (targetAccountName.match(/(\d{4})(?!.*\d)/) || [])[1];

    function tryOnce() {
      if (!document.querySelector("#ett-acct-sel-list")) return false;
      let buttons = document.querySelectorAll("#ett-acct-sel-list > ul > li > button");
      if (!buttons.length) buttons = document.querySelectorAll("#ett-acct-sel-list button");
      if (!buttons.length) buttons = document.querySelectorAll('[id*="acct-sel"] button, [id*="account-sel"] button');
      if (!buttons.length) buttons = document.querySelectorAll('button[role="option"]');
      if (!buttons.length) return false;

      let found = false;
      buttons.forEach((node) => {
        if (found) return;
        const cur = normalize(node.innerText || "");
        const last4Match = targetLast4 && (node.innerText || "").includes(targetLast4);
        if (cur.full === target.full ||
            (target.number && cur.number === target.number) ||
            last4Match ||
            cur.full.includes(target.full) ||
            target.full.includes(cur.full)) {
          node.click();
          node.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true }));
          node.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true }));
          node.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
          node.focus();
          node.dispatchEvent(new Event("focus", { bubbles: true }));
          node.dispatchEvent(new Event("blur", { bubbles: true }));
          node.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true }));
          node.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, cancelable: true }));
          found = true;
          setTimeout(() => {
            document.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", keyCode: 27, bubbles: true }));
          }, 300);
        }
      });
      return true;
    }

    let attempts = 0;
    const interval = setInterval(() => {
      attempts++;
      if (tryOnce()) {
        clearInterval(interval);
        onComplete(true);
      } else if (attempts >= 10) {
        clearInterval(interval);
        onComplete(false);
      }
    }, 200);
  }

  // Parse "$3.37" / "3.37" / "1,234.56" into a float
  function parsePrice(text) {
    if (text == null) return null;
    const m = String(text).match(/\$?\s*([\d,]+\.\d+)/);
    if (!m) return null;
    const v = parseFloat(m[1].replace(/,/g, ""));
    return isNaN(v) ? null : v;
  }

  // Read the current market price from the Fidelity trade ticket quote panel.
  // For a SELL order we want the BID (what buyers are paying right now);
  // fall back to LAST trade if BID isn't visible.
  function getMarketPrice() {
    const directSelectors = [
      "#dest-bid", "#bid", "[data-testid='bid']", "[data-testid='bid-price']",
      ".bid", ".bid-price", ".eq-ticket-bid",
      "#dest-last-trade-price", "#dest-last-price", "#last-price",
      "[data-testid='last-price']", "[data-testid='last-trade-price']",
      ".last-price", ".last-trade-price", ".eq-ticket-last"
    ];
    for (const sel of directSelectors) {
      const el = document.querySelector(sel);
      const p = parsePrice(el?.textContent);
      if (p != null) return { price: p, source: sel };
    }
    // Label-based search: "Bid" then "Last" then "Ask"
    const labelOrder = [/^bid$/i, /^last(\s*(price|trade))?$/i, /^ask$/i];
    for (const re of labelOrder) {
      const all = document.querySelectorAll("span, div, label");
      for (const el of all) {
        if (el.offsetParent === null) continue;
        if (!re.test((el.textContent || "").trim())) continue;
        const candidates = [
          el.nextElementSibling,
          el.parentElement?.nextElementSibling,
          el.parentElement?.querySelector("[class*='value']"),
          el.parentElement?.querySelector("[class*='price']"),
          ...(el.parentElement ? Array.from(el.parentElement.children) : [])
        ];
        for (const c of candidates) {
          const p = parsePrice(c?.textContent);
          if (p != null && p > 0 && p < 1e6) {
            return { price: p, source: `label:${(el.textContent || "").trim()}` };
          }
        }
      }
    }
    return null;
  }

  function executeSellOrder(orderData) {
    return new Promise((resolve) => {
      console.log("[FQO] executeSellOrder", orderData);

      // Click the Trade tab (Ten Talons exact selector)
      const tradeTabSelector =
        "#action-bar--container > action-bar-menu-fds > div.action-bar--wrapper.action-bar--group-container.action-bar--collapsed > div.action-bar--group.action-bar--left > ul > li.action-bar--item.action-bar--item-submenu.action-bar--item-trade > apex-kit-web-button > s-root > button";
      let tradeTab = document.querySelector(tradeTabSelector);
      if (!tradeTab) tradeTab = document.querySelector("li.action-bar--item-trade button");
      if (!tradeTab && !document.querySelector("#eq-ticket-dest-symbol")) {
        // Fallback: any visible button/link with text "Trade"
        const all = document.querySelectorAll("button, a, [role='button']");
        for (const el of all) {
          if ((el.textContent || "").trim().toLowerCase() === "trade" && el.offsetParent !== null) {
            tradeTab = el;
            break;
          }
        }
      }
      setStep(0); // Trade tab
      if (tradeTab) {
        tradeTab.click();
        console.log("[FQO] Trade tab clicked");
      }

      setTimeout(() => {
        const targetAccount = orderData.account || orderData.accountNumber || "";

        const continueAfterAccount = () => setTimeout(() => {
          const symbolInput = document.querySelector("#eq-ticket-dest-symbol");
          if (!symbolInput) {
            console.warn("[FQO] symbol input not found");
            return resolve({ success: false, error: "Symbol input not found" });
          }
          setStep(2); // Symbol
          simulateTyping(symbolInput, String(orderData.symbol)).then(() => {
            console.log("[FQO] symbol entered");
            setTimeout(() => {
              setStep(3); // Sell
              // ── Action: SELL ──
              // Try button-style UI: look for the sell radio/label by id or by text
              const isSellEl = (el) => /^\s*sell\s*$/i.test(el.textContent || "");
              let sellButton =
                document.querySelector("#action-sell > s-root > div > label > s-slot > s-assigned-wrapper") ||
                document.querySelector("#action-sell > s-root > div > label") ||
                document.querySelector("#action-sell");
              // If the id-based selector matched something, double-check it's not "Recurring Investment"
              if (sellButton && /recurring/i.test(sellButton.textContent || "")) sellButton = null;
              // Fallback: find any visible radio label whose text is exactly "Sell"
              if (!sellButton) {
                const allLabels = document.querySelectorAll("label, [role='radio'], s-root div label");
                for (const el of allLabels) {
                  if (el.offsetParent !== null && isSellEl(el)) { sellButton = el; break; }
                }
              }
              if (sellButton) {
                sellButton.click();
                console.log("[FQO] Sell button clicked (button UI):", sellButton.id || sellButton.textContent.trim());
              } else {
                const actionDropdown = document.querySelector("#dest-dropdownlist-button-action");
                if (actionDropdown) {
                  actionDropdown.click();
                  setTimeout(() => {
                    // Find option by text "Sell" — never trust positional IDs like #Action1
                    let sellOption = null;
                    const candidates = document.querySelectorAll(
                      '[role="option"], [role="listbox"] li, [id^="Action"], li button, option'
                    );
                    for (const el of candidates) {
                      if (el.offsetParent === null) continue;
                      if (/^\s*sell\s*$/i.test(el.textContent || "")) { sellOption = el; break; }
                    }
                    if (sellOption) {
                      sellOption.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
                      sellOption.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
                      sellOption.dispatchEvent(new MouseEvent("click", { bubbles: true }));
                      console.log("[FQO] Sell selected (dropdown UI):", sellOption.textContent.trim());
                    } else {
                      console.warn("[FQO] Sell option not found in action dropdown");
                    }
                  }, 300);
                } else {
                  console.warn("[FQO] No Sell button or Action dropdown");
                }
              }

              // ── Quantity ──
              setTimeout(() => {
                const quantityInput = document.querySelector("#eqt-shared-quantity");
                if (!quantityInput) {
                  console.warn("[FQO] #eqt-shared-quantity not found");
                  return resolve({ success: false, error: "Quantity input not found" });
                }
                setStep(4); // Quantity
                simulateTyping(quantityInput, String(orderData.quantity)).then(() => {
                  console.log("[FQO] quantity entered");

                  // ── Order type: Limit ──
                  setTimeout(() => {
                    setStep(5); // Limit
                    const limitButton =
                      document.querySelector("#market-no > s-root > div > label") ||
                      document.querySelector("#market-no");
                    if (limitButton) {
                      limitButton.click();
                      console.log("[FQO] Limit button clicked (button UI)");
                    } else {
                      const orderTypeDropdown = document.querySelector("#dest-dropdownlist-button-ordertype");
                      if (orderTypeDropdown) {
                        orderTypeDropdown.click();
                        setTimeout(() => {
                          let limitOption =
                            document.querySelector("#OrderType1") ||
                            document.querySelector("#Ordertype1") ||
                            document.querySelector("#ordertype1");
                          if (!limitOption) {
                            document.querySelectorAll('[role="option"]').forEach((o) => {
                              if (o.textContent.trim() === "Limit") limitOption = o;
                            });
                          }
                          if (limitOption) {
                            limitOption.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
                            limitOption.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
                            limitOption.dispatchEvent(new MouseEvent("click", { bubbles: true }));
                            console.log("[FQO] Limit selected (dropdown UI)");
                          }
                        }, 300);
                      } else {
                        console.warn("[FQO] No Limit button or Order type dropdown");
                      }
                    }

                    // ── Limit price (smart-adjust against live market) ──
                    setTimeout(() => {
                      setStep(6); // Limit Price
                      const limitPriceInput = document.querySelector(
                        'input[id*="limit-price"], input[aria-label*="Limit price"]'
                      );
                      if (!limitPriceInput) {
                        console.warn("[FQO] limit-price input not found");
                        return resolve({ success: false, error: "Limit price input not found" });
                      }
                      const screenshotPrice = parseFloat(orderData.limitPrice);
                      const market = getMarketPrice();
                      let effectivePrice = screenshotPrice;
                      if (market && market.price > screenshotPrice) {
                        // Market has moved up — sit 1 cent above current to capture more upside
                        effectivePrice = Math.round((market.price + 0.01) * 100) / 100;
                        console.log(`[FQO] Market $${market.price} (${market.source}) > screenshot $${screenshotPrice} → using $${effectivePrice}`);
                        setStatus(`Market $${market.price} > screenshot $${screenshotPrice}; submitting at $${effectivePrice}`);
                      } else if (market) {
                        console.log(`[FQO] Market $${market.price} ≤ screenshot $${screenshotPrice} → using $${screenshotPrice}`);
                      } else {
                        console.warn(`[FQO] Could not read market price; using screenshot $${screenshotPrice}`);
                      }
                      // Direct value set — char-by-char typing breaks decimals on number inputs
                      limitPriceInput.value = String(effectivePrice);
                      limitPriceInput.dispatchEvent(new Event("input", { bubbles: true }));
                      limitPriceInput.dispatchEvent(new Event("change", { bubbles: true }));
                      limitPriceInput.dispatchEvent(new Event("blur", { bubbles: true }));
                      console.log("[FQO] limit price set:", effectivePrice);

                      // ── Time in Force: Good 'Til Canceled ──
                      setTimeout(() => {
                        setStep(7); // GTC
                        const tifDropdown = document.querySelector("#dest-dropdownlist-button-timeinforce");
                        if (!tifDropdown) {
                          console.warn("[FQO] tif dropdown not found");
                          return resolve({ success: false, error: "Time in Force dropdown not found" });
                        }
                        tifDropdown.click();
                        setTimeout(() => {
                          // Find the GTC option by text rather than trusting #Time-in-force1
                          // (option ordering varies across Fidelity UI variants)
                          const isGtc = (txt) =>
                            /\bgtc\b/i.test(txt) ||
                            /good\s*[-']?\s*('?til|till)\s*[-]?\s*can/i.test(txt);
                          let gtcOption = null;
                          // 1) Search any visible option/li/button under an open listbox
                          const candidates = document.querySelectorAll(
                            '[role="listbox"] [role="option"], [role="option"], li button, [id^="Time-in-force"], [id^="TimeInForce"], [id^="Tif"]'
                          );
                          for (const el of candidates) {
                            if (el.offsetParent === null) continue;
                            if (isGtc(el.textContent || "")) { gtcOption = el; break; }
                          }
                          // 2) Fall back to the literal Ten Talons id if no text match
                          if (!gtcOption) gtcOption = document.querySelector("#Time-in-force1");
                          if (gtcOption) {
                            gtcOption.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
                            gtcOption.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
                            gtcOption.dispatchEvent(new MouseEvent("click", { bubbles: true }));
                            gtcOption.click();
                            console.log("[FQO] GTC selected:", gtcOption.id || gtcOption.textContent.trim());
                          } else {
                            console.warn("[FQO] GTC option not found in TIF list");
                          }
                          // Click Preview Order
                          setTimeout(() => {
                            setStep(8); // Preview
                            const previewBtn =
                              document.querySelector("#previewOrderBtn") ||
                              [...document.querySelectorAll("button")].find(
                                (b) => /preview\s*order/i.test(b.textContent || "") && !b.disabled && b.offsetParent !== null
                              );
                            if (previewBtn) {
                              previewBtn.click();
                              console.log("[FQO] Preview Order clicked");
                              finishSteps();
                              resolve({ success: true });
                            } else {
                              console.warn("[FQO] Preview Order button not found");
                              resolve({ success: false, error: "Preview Order button not found" });
                            }
                          }, 600);
                        }, 500);
                      }, 500);
                    }, 500);
                  }, 500);
                }).catch((err) => {
                  console.warn("[FQO] qty error", err);
                  resolve({ success: false, error: "Failed to enter quantity" });
                });
              }, 500);
            }, 500);
          }).catch((err) => {
            console.warn("[FQO] symbol error", err);
            resolve({ success: false, error: "Failed to enter symbol" });
          });
        }, 500);

        if (targetAccount) {
          setStep(1); // Account
          selectAccountFromDropdown(targetAccount, () => continueAfterAccount());
        } else {
          continueAfterAccount();
        }
      }, 2000);
    });
  }


  async function submit() {
    const account = (accountEl.value || "").trim();
    const ticker = (tickerEl.value || "").trim().toUpperCase();
    // Floor shares to whole integer — GTC only works with whole shares on Fidelity
    const qty = Math.floor(Math.abs(parseFloat(qtyEl.value)));
    const price = parseFloat(priceEl.value);

    if (!ticker) return setStatus("Ticker required.", true);
    if (!qty || qty < 1) return setStatus("Shares must be ≥ 1 whole share for GTC.", true);
    if (!price || price <= 0) return setStatus("Limit price must be > 0.", true);

    // Reflect the floored value in the input box so user sees what's being submitted
    qtyEl.value = qty;

    try {
      localStorage.setItem(STATE_KEY, JSON.stringify({ ticker, account }));
    } catch {}

    setStatus(`Placing SELL ${qty} ${ticker} @ ${price} GTC${account ? ` from ${account}` : ""}…`);
    resetSteps();
    // Close the overlay so Fidelity's trade ticket is visible while automation runs
    togglePanel(false);
    try {
      const result = await executeSellOrder({
        account,
        symbol: ticker,
        quantity: qty,
        limitPrice: price
      });
      if (result.success) {
        setStatus(`✓ Preview opened: SELL ${qty} ${ticker} @ ${price} GTC. Review and place the order.`);
      } else {
        setStatus(`Failed: ${result.error || "unknown"} (see DevTools console)`, true);
      }
    } catch (e) {
      console.error("[FidelityQuickOrder]", e);
      setStatus(e.message || String(e), true);
    }
  }

  panel.addEventListener("keydown", (e) => {
    if (e.key === "Escape") togglePanel(false);
  });

  console.log("[FidelityQuickOrder] overlay ready");
})();
