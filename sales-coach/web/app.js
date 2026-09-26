/**
 * Sales Coach workbench.
 *
 * Everything here runs in the page. The analysis is the same engine the
 * pipeline uses, imported unchanged, so what this shows and what
 * `node pipeline/run-prompt2.mjs` writes cannot drift apart.
 *
 * No dataset is ever uploaded. A file dropped here is read with FileReader
 * and stays in this tab.
 */

import { analyze } from './engine/analysis.js';
import { renderFindings, renderTable } from './engine/findings.js';
import { renderPrep } from './engine/prep.js';

const $ = (id) => document.getElementById(id);

const PROMPT_FILES = [
  { n: 1, title: 'Build the database', file: 'prompts/prompt-1-build-the-database.md' },
  { n: 2, title: 'Coach me with Jev', file: 'prompts/prompt-2-coach-me-with-jev.md' },
  { n: 3, title: 'Prep me for a call', file: 'prompts/prompt-3-prep-me-for-a-call.md' },
];

/**
 * The prompts, preferring the module `build.mjs` generates from prompts/*.md.
 *
 * The generated module is what ships. Fetching the markdown is the fallback
 * for serving web/ straight off disk without a build, and it is also what
 * keeps the two paths honest: both read the same files.
 */
async function loadPrompts() {
  try {
    const mod = await import('./prompts.generated.js');
    if (Array.isArray(mod.PROMPTS) && mod.PROMPTS.length) return mod.PROMPTS;
  } catch {
    // No build present. Fall through and read the markdown directly.
  }

  return Promise.all(
    PROMPT_FILES.map(async (p) => {
      try {
        const res = await fetch(p.file);
        if (!res.ok) throw new Error(String(res.status));
        return { ...p, text: (await res.text()).trim() };
      } catch {
        return { ...p, text: null };
      }
    })
  );
}

const state = {
  dataset: null,
  sourceName: 'demo book of business',
  analysis: null,
  showStats: false,
  prepMarkdown: '',
  prepName: 'prep',
};

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

function commas(n) {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/** Flash a button so a copy or download is visibly acknowledged. */
function flash(button, label = 'Copied') {
  const original = button.dataset.label ?? button.textContent;
  button.dataset.label = original;
  button.textContent = label;
  button.classList.add('copied');
  clearTimeout(button._t);
  button._t = setTimeout(() => {
    button.textContent = button.dataset.label;
    button.classList.remove('copied');
  }, 1400);
}

async function copy(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    flash(button);
  } catch {
    // Clipboard API is blocked in some embedded contexts. Fall back to a
    // selection the reader can copy by hand rather than failing silently.
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try {
      ok = document.execCommand('copy');
    } catch {
      ok = false;
    }
    document.body.removeChild(ta);
    flash(button, ok ? 'Copied' : 'Press ctrl C');
  }
}

function download(filename, text) {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Light markdown colouring. Headings, bold, quotes, percentages. */
function highlight(md) {
  return esc(md)
    .replace(/^(#{1,6} .*)$/gm, '<span class="h">$1</span>')
    .replace(/^(&gt; .*)$/gm, '<span class="q">$1</span>')
    .replace(/\*\*(.+?)\*\*/g, '<span class="b">$1</span>')
    .replace(/(\d+(?:\.\d+)?%)/g, '<span class="n">$1</span>');
}

/* ------------------------------------------------------------------ */
/* Prompt cards                                                        */
/* ------------------------------------------------------------------ */

async function renderPrompts() {
  const host = $('promptCards');
  const prompts = await loadPrompts();
  host.innerHTML = '';

  for (const p of prompts) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-head">
        <div class="card-title"><span class="dot"></span> Prompt ${p.n} · ${esc(p.title)}</div>
        <div class="btn-row"><button type="button">Copy</button></div>
      </div>
      <pre class="prompt-body"></pre>`;
    host.appendChild(card);

    const body = card.querySelector('.prompt-body');
    const button = card.querySelector('button');

    if (!p.text) {
      body.textContent = `Could not load ${p.file}`;
      button.disabled = true;
      continue;
    }

    // Highlight the [bracketed] spans the reader is meant to replace.
    body.innerHTML = esc(p.text).replace(/\[([^\]]+)\]/g, '<span class="ph">[$1]</span>');
    button.addEventListener('click', () => copy(p.text, button));
  }
}

/* ------------------------------------------------------------------ */
/* Data loading                                                        */
/* ------------------------------------------------------------------ */

function showError(message) {
  $('dataError').innerHTML = message ? `<div class="err">${esc(message)}</div>` : '';
}

/** Reject anything that is not shaped like a dataset before it reaches the engine. */
function validate(data) {
  if (!data || typeof data !== 'object') throw new Error('That file is not a JSON object.');
  for (const key of ['prospects', 'calls', 'emails']) {
    if (!Array.isArray(data[key])) {
      throw new Error(`That file has no "${key}" array. Export one with node pipeline/run-prompt1.mjs.`);
    }
  }
  if (data.prospects.length === 0 && data.calls.length === 0) {
    throw new Error('That dataset is empty.');
  }
  return data;
}

async function loadDemo() {
  showError('');
  try {
    const res = await fetch('data/demo-dataset.json');
    if (!res.ok) throw new Error(`demo dataset returned ${res.status}`);
    setDataset(validate(await res.json()), 'demo book of business');
  } catch (err) {
    showError(`Could not load the demo dataset. ${err.message}`);
    $('sourceLabel').textContent = 'No data loaded';
  }
}

function setDataset(dataset, sourceName) {
  state.dataset = dataset;
  state.sourceName = sourceName;
  $('sourceLabel').innerHTML =
    `Source: <b>${esc(sourceName)}</b> · ${commas(dataset.calls.length)} calls · ` +
    `${commas(dataset.emails.filter((e) => e.direction === 'out').length)} emails graded`;
  renderProspects();
  recompute();
}

function readFile(file) {
  showError('');
  const reader = new FileReader();
  reader.onload = () => {
    try {
      setDataset(validate(JSON.parse(String(reader.result))), file.name);
    } catch (err) {
      showError(err instanceof SyntaxError ? `${file.name} is not valid JSON.` : err.message);
    }
  };
  reader.onerror = () => showError(`Could not read ${file.name}.`);
  reader.readAsText(file);
}

/* ------------------------------------------------------------------ */
/* Analysis rendering                                                  */
/* ------------------------------------------------------------------ */

function thresholds() {
  return {
    minGapPp: Number($('minGap').value),
    minSample: Number($('minSample').value),
    alpha: Number($('alpha').value) / 100,
  };
}

function recompute() {
  if (!state.dataset) return;

  const t = thresholds();
  $('minGapVal').textContent = `${t.minGapPp} pts`;
  $('minSampleVal').textContent = String(t.minSample);
  $('alphaVal').textContent = t.alpha.toFixed(2);

  state.analysis = analyze(state.dataset, t);
  renderStats();
  renderJevTable();
  renderFindingsPane();
}

function renderStats() {
  const { totals, patterns, noClearPattern } = state.analysis;
  const cells = [
    { k: 'Calls', v: commas(totals.calls) },
    { k: 'Emails graded', v: commas(totals.taggedEmails) },
    { k: 'Closed won', v: commas(totals.callOutcomes.closed_won) },
    { k: 'Closed lost', v: commas(totals.callOutcomes.closed_lost) },
    { k: 'No matching deal', v: commas(totals.callsWithoutDeal) },
    { k: 'Patterns', v: String(patterns.length), accent: true },
    { k: 'No clear pattern', v: String(noClearPattern.length) },
  ];

  $('stats').innerHTML = cells
    .map(
      (c) =>
        `<div class="stat"><span class="k">${esc(c.k)}</span>` +
        `<span class="v${c.accent ? ' accent' : ''}">${esc(c.v)}</span></div>`
    )
    .join('');
}

function renderJevTable() {
  const rows = state.analysis.results
    .slice()
    .sort((a, b) => Math.abs(b.gapPp ?? 0) - Math.abs(a.gapPp ?? 0));

  $('tableBody').innerHTML = rows
    .map((r) => {
      const isPattern = r.verdict === 'pattern';
      const won = r.won.pct == null ? 'n/a' : `${r.won.pct}%`;
      const lost = r.lost.pct == null ? 'n/a' : `${r.lost.pct}%`;
      const gap = r.displayGapPp == null ? 'n/a' : `${r.displayGapPp > 0 ? '+' : ''}${r.displayGapPp}`;

      const verdictLabel =
        r.verdict === 'pattern'
          ? r.direction === 'helps'
            ? 'pattern'
            : 'pattern · costs you'
          : r.verdict === 'insufficient_data'
            ? 'not enough data'
            : 'no clear pattern';

      return `
        <tr class="${isPattern ? 'is-pattern' : ''}">
          <td class="q-cell">
            <span class="q">${esc(r.label)}</span>
            <span class="scope">${esc(r.scope)} · ${esc(r.question)}</span>
          </td>
          <td class="num won">${esc(won)}</td>
          <td class="num lost">${esc(lost)}</td>
          <td>
            <div class="bars">
              <span class="bar w"><i style="width:${(r.won.rate ?? 0) * 100}%"></i></span>
              <span class="bar l"><i style="width:${(r.lost.rate ?? 0) * 100}%"></i></span>
            </div>
          </td>
          <td class="num">${esc(gap)}</td>
          <td>
            <span class="verdict ${isPattern ? 'pattern' : ''}">${esc(verdictLabel)}</span>
            <div class="why">${esc(r.reason)}</div>
          </td>
        </tr>`;
    })
    .join('');
}

function renderFindingsPane() {
  const md = renderFindings(state.analysis, { includeStats: state.showStats });
  $('findings').innerHTML = highlight(md);
  state.findingsMarkdown = md;
}

/* ------------------------------------------------------------------ */
/* Call prep                                                           */
/* ------------------------------------------------------------------ */

function renderProspects() {
  const select = $('prospect');
  const rank = { closed_won: 0, closed_lost: 1, open: 2, none: 3 };

  const options = state.dataset.prospects
    .slice()
    .sort((a, b) => (rank[a.outcome] ?? 9) - (rank[b.outcome] ?? 9) || (a.name ?? '').localeCompare(b.name ?? ''))
    .map((p) => {
      const label = `${p.name ?? p.id}${p.company ? ` · ${p.company}` : ''} · ${String(p.outcome ?? 'none').replace('_', ' ')}`;
      return `<option value="${esc(p.id)}">${esc(label)}</option>`;
    });

  select.innerHTML = options.join('');

  // Open on the prospect the reel uses, when the demo book is loaded, so the
  // first plan anyone builds is the one they just watched being built.
  const steve = state.dataset.prospects.find((p) => p.name === 'Steve Arden');
  if (steve) select.value = steve.id;
}

function lines(value) {
  return String(value ?? '')
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean);
}

function buildPrep() {
  if (!state.analysis) return;

  const id = $('prospect').value;
  const prospect = state.dataset.prospects.find((p) => p.id === id);
  if (!prospect) return;

  const research = {
    linkedin: $('rLinkedin').value.trim() || undefined,
    company: $('rCompany').value.trim() || undefined,
    news: lines($('rNews').value),
    hooks: lines($('rHooks').value),
  };

  const md = renderPrep({ prospect, analysis: state.analysis, dataset: state.dataset, research });
  state.prepMarkdown = md;
  state.prepName = String(prospect.name ?? prospect.id)
    .toLowerCase()
    .replace(/@.*$/, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

  $('prepName').textContent = `prep/${state.prepName}.md`;
  $('prepOut').innerHTML = highlight(md);
}

/* ------------------------------------------------------------------ */
/* Wiring                                                              */
/* ------------------------------------------------------------------ */

function wire() {
  for (const id of ['minGap', 'minSample', 'alpha']) {
    $(id).addEventListener('input', recompute);
  }

  $('loadDemo').addEventListener('click', loadDemo);
  $('pickFile').addEventListener('click', () => $('fileInput').click());
  $('fileInput').addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (file) readFile(file);
    e.target.value = '';
  });

  // Drag and drop anywhere on the page.
  let depth = 0;
  document.addEventListener('dragenter', (e) => {
    e.preventDefault();
    depth += 1;
    document.body.classList.add('dragging');
  });
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('dragleave', () => {
    depth = Math.max(0, depth - 1);
    if (depth === 0) document.body.classList.remove('dragging');
  });
  document.addEventListener('drop', (e) => {
    e.preventDefault();
    depth = 0;
    document.body.classList.remove('dragging');
    const file = e.dataTransfer?.files?.[0];
    if (file) readFile(file);
  });

  $('toggleStats').addEventListener('click', (e) => {
    state.showStats = !state.showStats;
    e.currentTarget.textContent = state.showStats ? 'Hide the working' : 'Show the working';
    renderFindingsPane();
  });

  $('copyFindings').addEventListener('click', (e) => copy(state.findingsMarkdown ?? '', e.currentTarget));
  $('downloadFindings').addEventListener('click', () => download('findings.md', state.findingsMarkdown ?? ''));

  $('copyTable').addEventListener('click', (e) => {
    const table = renderTable(state.analysis);
    const tsv = [
      table.headers.join('\t'),
      ...table.rows.map((r) => [r.label, r.won, r.lost, r.verdict].join('\t')),
    ].join('\n');
    copy(tsv, e.currentTarget);
  });

  $('buildPrep').addEventListener('click', buildPrep);
  $('prospect').addEventListener('change', () => {
    if (state.prepMarkdown) buildPrep();
  });

  $('copyPrep').addEventListener('click', (e) => {
    if (!state.prepMarkdown) return flash(e.currentTarget, 'Build it first');
    copy(state.prepMarkdown, e.currentTarget);
  });
  $('downloadPrep').addEventListener('click', () => {
    if (state.prepMarkdown) download(`${state.prepName}.md`, state.prepMarkdown);
  });

  $('prepOut').innerHTML =
    '<span style="color:rgba(255,255,255,0.28)">Pick a prospect and build the plan.</span>';
}

wire();
renderPrompts();
loadDemo();
