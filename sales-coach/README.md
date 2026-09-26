# Sales Coach

Grade every sales call and every email against a fixed rubric, then keep only
the differences that actually separate closed won from closed lost.

Live: **[athemventures.com/sales-coach/](https://athemventures.com/sales-coach/)**

Built from a 60 second reel that walks through the whole thing on screen. The
three prompts, the file layout, the tone tag vocabulary and the rubric are
taken from that video. See [PRD.md](PRD.md) for the full specification and
[PLAYBOOK.md](PLAYBOOK.md) for how this repository was produced.

---

## What it does

```
Fireflies ─┐
Gemini   ──┼──► sales.db ──► Jev ──► findings.md ──► prep/[prospect].md
Gmail    ──┤                  │
HubSpot  ──┘                  └──► the workbench (browser)
```

1. **Build the database.** Every call from the last twelve months, re-transcribed
   by Gemini with a tone tag on every line. Every email thread. Every deal
   outcome. One SQLite file.
2. **Grade it.** Jev answers six yes or no questions about every call and every
   email. Compare the yes rate in wins against the yes rate in losses. Report
   only what clears the guard.
3. **Use it.** One page before a specific call, built from what actually closes
   for you plus the whole history with that person.

## The part that matters

A question is reported as a pattern only when all three hold:

- at least 10 closed won and 10 closed lost carry an answer
- the gap between the two rates is at least 15 percentage points
- a two-proportion z-test comes in under p = 0.05

Everything else is reported by name as "no clear pattern", never dropped
silently. Transcription and grading are commodities. Refusing to turn a coin
flip into advice is the product.

---

## Try it without installing anything

Open the [workbench](https://athemventures.com/sales-coach/). It loads a demo
book of business and runs the analysis in the page. Drag the three guard
sliders to see what the guard is holding back.

## Run it on your own calls

```bash
cp pipeline/.env.example pipeline/.env   # then fill it in

node pipeline/run-prompt1.mjs            # build sales.db
node pipeline/run-prompt2.mjs            # grade it, write findings.md
node pipeline/run-prompt3.mjs --prospect steve@example.com
```

Needs Node 22.5 or later (for `node:sqlite`) and five credentials: Fireflies,
Gemini, a Gmail OAuth token with read scope, a HubSpot private app token, and a
TypeSafe key for Jev. Every one is documented in `pipeline/.env.example`.

Every step is resumable. Audio already on disk is not downloaded twice, calls
already transcribed are not sent to Gemini twice, and an artifact that already
has an answer is not sent to Jev twice.

## Run it with an agent instead

`prompts/` holds the three prompts as plain markdown, ready to paste into an
agent with Fireflies, Gmail, HubSpot and the Jev MCP connected. That is how the
source does it.

---

## Layout

| Path | What is in it |
| --- | --- |
| `engine/` | The analysis. Pure ES modules, no dependencies, runs in Node and the browser. |
| `pipeline/` | Connectors, SQLite schema, and the three runnable stages. |
| `prompts/` | The three prompts, copy-paste ready. |
| `web/` | The workbench source. |
| `data/` | The demo dataset and its generator. |
| `test/` | 89 tests, run with `npm test`. |

## Development

```bash
npm test                  # 89 tests, no dependencies, no network
npm run build             # assemble dist/
npm run demo              # regenerate the demo dataset
npm run serve             # build, then serve dist/ on :8899
```

The demo dataset is generated, not hand-written. It is built so the engine
reproduces every figure the source video shows: 71/29 on rapport, 64/41 on
tone, 58/22 on holding price, 82/77 and 16/18 as non-patterns, across 214 calls
and 1,122 emails with 9 calls carrying no matching deal. Those figures are
pinned as test assertions, so if the analysis ever drifts the build fails
rather than the demo quietly showing different numbers.

No prospect, call or email in `data/demo-dataset.json` is real.

## Credits

The build is [@jkudish/jev-mcp](https://github.com/jkudish/jev-mcp) (Jev as MCP
tools), the Gemini Files API, Fireflies, HubSpot, and NotebookLM for the audio
overview. Source reel:
[instagram.com/reel/DdmnpY8hmnE](https://www.instagram.com/reel/DdmnpY8hmnE/).
