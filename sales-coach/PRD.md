# Sales Coach

**Product Requirements Document**
Version 1.0 · 26 September 2026 · Athem Ventures

---

## 1. Bottom line up front

Every sales call a team has ever run is already recorded. Every email is already in Gmail. Every outcome is already sitting in the CRM. Nobody joins the three together, so a rep repeats the same losing behaviour for a year and pays someone six thousand dollars to tell them to build rapport.

Sales Coach joins them together. It pulls the calls, re-transcribes them with a tone tag on every line, pulls the email threads, attaches the deal outcome, then grades every artifact against a fixed rubric using a small typed-judgment model. It reports only the behaviours where the closed-won rate and the closed-lost rate genuinely diverge, and it says "no clear pattern" for everything else.

The product is not the transcription and it is not the grading. Both are commodities. The product is the discipline in the last step: a statistical guard that refuses to turn a coin flip into advice. That is the only part of this pipeline that a competitor cannot buy off the shelf, and it is the only part that determines whether a rep trusts the output on week three.

Shipped in this version: the full runnable pipeline, the analysis engine with 89 tests, and a browser workbench live at `athemventures.com/sales-coach/`.

---

## 2. The problem

A sales rep has three data sources and no way to reason across them.

| Source | What it holds | Why it is useless alone |
| --- | --- | --- |
| Call recorder | Every conversation, transcribed | No outcome attached. No behavioural labels. Searching it tells you what was said, never what worked. |
| Email | Every written exchange | Same problem, plus nobody reads a year of their own sent folder. |
| CRM | Won, lost, amount, date | Knows the result and nothing about the behaviour that produced it. |

The gap is the join. Without it, coaching falls back on generic advice sold at a premium, and the rep has no way to tell whether that advice applies to their book, their market, or their price point.

The failure mode of naive automation is worse than the gap. Point a frontier model at a year of calls and ask what closes, and it will produce a confident, fluent, well-structured answer built on eleven data points and no significance test. A rep who acts on that and loses will not come back.

---

## 3. What this is

A three-stage pipeline with one artifact between each stage.

```
Fireflies ─┐
Gemini   ──┼──► sales.db ──► Jev ──► findings.md ──► prep/[prospect].md
Gmail    ──┤                  │
HubSpot  ──┘                  └──► the workbench (browser)
```

**Stage 1, build the database.** List every call hosted in the last twelve months. Download each recording. Send each one to Gemini and get back a transcript with speaker labels, timestamps, and a tone tag on every line: hesitant, rushed, confident, laughing, flat, warm, or matching their energy. For every prospect on those calls, pull every email sent and every reply with the date and word count. Look up each prospect's deal and record closed won, closed lost, or open, plus the amount. Put all of it in one SQLite file.

**Stage 2, grade it.** Ask Jev a fixed set of yes or no questions against every call and every email. Save every answer and its probability. For each question, compare the yes rate in closed won against the yes rate in closed lost. Report only what clears the guard.

**Stage 3, use it.** Before a specific call, combine the findings with the full history with that prospect and fresh research into a one-page plan. Optionally turn that plan into an audio overview to listen to on the way.

### 3.1 Why the tone tags matter

Fireflies already has a transcript, so re-transcribing looks redundant. It is not. Half the rubric is unanswerable from words alone. "Did I match their tone" cannot be decided from a text transcript at any model size. The tone tag on every line is the thing that makes the acoustic half of the rubric answerable, and it is the reason stage 1 pays for transcription twice.

This is the same observation Amplifier Health's thesis rests on, arrived at from the opposite direction: how something is said carries signal that what was said does not. Sales Coach is a commercial instance of that claim in a domain with a hard ground truth attached, which makes it unusually good evidence. See section 15.

### 3.2 Why a small model does the grading

Jev is TypeSafe's typed-judgment model, exposed over MCP by `@jkudish/jev-mcp`. It returns a typed verdict with a probability in a few hundred milliseconds for a fraction of a cent.

Three reasons it does the grading instead of the orchestrating model:

1. **Cost.** Six questions across 214 calls and 1,122 emails is roughly 8,000 judgments. At frontier prices with a full transcript in context each time, that is a meaningful bill for one report. At Jev prices it rounds to nothing.
2. **Consistency.** A long-context model asked to grade 214 calls in sequence does not answer call 200 the way it answered call 1. A per-artifact typed call does, because every call is a fresh, identical, narrow question.
3. **Separation of duties.** The orchestrating agent never forms an opinion about a call. It moves data and does arithmetic. Every judgment in the system is attributable to a specific model call with a stored probability, which is what makes the output auditable rather than merely plausible.

Prompt 2 states this as a hard instruction: use Jev for every judgment about a call or an email, never judge them yourself.

---

## 4. Source and provenance

This specification is derived from a 60 second Instagram reel (`instagram.com/reel/DdmnpY8hmnE`) that walks through the build on screen. The three prompt cards, the file layout, the tone tag vocabulary, the rubric questions, and the reported figures are all taken from frames in that video rather than invented.

Figures shown on screen, all of which the shipped engine reproduces:

| Jev question | Won | Lost | Verdict |
| --- | --- | --- | --- |
| rapport before the pitch | 71% | 29% | pattern |
| matched their tone | 64% | 41% | pattern |
| held price on 1st objection | 58% | 22% | pattern |
| asked goal before price | 82% | 77% | no clear pattern |
| email length matched theirs | 16% | 18% | no clear pattern |

Totals: 214 calls, 1,122 emails, 9 calls with no matching deal.

**Reconstruction note.** The presenter's head occludes part of every prompt card. Steps 1 to 4 of prompt 1, steps 1 and 2 of prompt 2, and all of prompt 3 were read cleanly across multiple frames. The tail of prompt 1 step 5, prompt 1 step 6, and prompt 2 steps 3 to 6 were partially occluded and reconstructed from the visible fragments plus the narration and the on-screen output. The reconstructed spans are consistent with everything visible, but they are reconstruction, not transcription. They are marked as such here and nowhere else, because the prompt files are meant to be copied and pasted clean.

**Third-party components named in the source.** `@jkudish/jev-mcp` (Jev as MCP tools), `atknony/gemini-cortex-mcp` (Gemini delegation as MCP tools), `Ying-Kai-Liao/jev-browser`, and NotebookLM for the audio overview. This implementation calls Gemini directly rather than through `gemini-cortex-mcp`, because the pipeline needs a constrained response schema on the transcription call and a direct call is the shorter path to that.

---

## 5. Users

**Primary: the individual rep or founder who sells.** One person, one book of business, a laptop, no data team. They want to know what to do differently on Thursday. They will not read a statistics appendix and they will not run anything that takes an afternoon to set up.

**Secondary: the sales leader.** Same pipeline pointed at several reps. Wants to know whether the thing the team is being coached on is the thing that is actually costing deals. Out of scope for version 1 but the data model does not prevent it.

**Non-user: the enterprise revenue intelligence buyer.** Gong and Clari already serve them, with seat pricing and an implementation. This is deliberately the opposite shape: one directory, one SQLite file, five API keys, and a delete that is `rm -rf`.

---

## 6. The rubric

Six questions. Each has to be answerable yes or no from a single artifact, because that is the only shape of question Jev is fast and cheap at. Anything requiring a paragraph of reasoning does not belong in the rubric.

| id | Scope | Question |
| --- | --- | --- |
| `rapport_first` | call | Did I build rapport for five minutes before pitching? |
| `matched_tone` | call | Did I match their tone? |
| `asked_goal_before_price` | call | Did I ask their goal before naming a price? |
| `held_price_first_objection` | call | Did I hold price on the first objection? |
| `email_length_matched` | email | Is my email a similar length to theirs? |
| `email_ends_with_question` | email | Does it end with a question? |

Each question ships with a `claim`: the statement Jev actually verifies against the artifact, phrased as an assertion rather than a question because `jev_verify` takes a claim and evidence. The question is what a human reads; the claim is what the model sees. Keeping them separate means the rubric can be reworded for readability without silently changing what is being measured.

Only the seller's own emails are graded. The prospect's replies are stored because "a similar length to theirs" is unanswerable without them, but they are never the artifact under judgment.

The rubric is a configuration file, not a schema. Adding a question is one entry in `engine/rubric.js` and a re-run of stage 2.

---

## 7. The pattern guard

This is the part that matters.

For each question, compute the yes rate among closed-won artifacts and among closed-lost artifacts. A question is reported as a pattern only when all three of the following hold:

1. **Sample.** At least 10 closed won and at least 10 closed lost carry an answer.
2. **Effect size.** The gap between the two rates is at least 15 percentage points.
3. **Significance.** A two tailed two-proportion z-test comes in under p = 0.05.

Otherwise the question is reported as "no clear pattern", by name, with its two rates. It is never dropped silently. A rep needs to know that email length was checked and came back flat, otherwise they will wonder.

The order of the checks is load bearing. Sample size is tested first, because a gap computed from four records is not a small gap, it is no answer at all, and labelling it "no clear pattern" would overstate what the data supports. Those questions are reported separately as "not enough data yet".

### 7.1 Why three guards and not one

The reel specifies two of these in words: the gap has to be wide and the sample cannot be tiny. The significance test is the addition, and it earns its place on the demo data.

`asked_goal_before_price` reads 82% against 77%. `email_length_matched` reads 16% against 18%. Both clear a sample floor comfortably. Drag the minimum gap all the way to zero in the workbench and both still refuse to become patterns, because at p = 0.38 and p = 0.40 the z-test rejects them. They only flip once significance is pushed past 0.40, which is the point at which nothing is being tested.

Effect size alone would have let a 16 percentage point gap on a 22 versus 19 split through. The z-test is what stops that, and stopping that is the product.

### 7.2 What the guard is not

It is not a causal claim. A behaviour that correlates with winning may be a consequence of an easy deal rather than a cause of it: a prospect who is already sold is easier to build rapport with. The findings are written as "this is what separates your wins from your losses", never as "do this and you will win". Version 2 should look at ordering within a call to get closer to causality. Version 1 does not pretend to have it.

---

## 8. Data model

One SQLite file at `~/sales-coach/sales.db`.

| Table | Holds |
| --- | --- |
| `prospects` | One per person, keyed by normalised email. Carries the CRM outcome and amount. |
| `calls` | One per recording. Points at the audio and the transcript on disk. |
| `call_lines` | One per transcript line. Speaker, text, tone tag, and timestamp in seconds. |
| `emails` | Both directions. Direction, date, word count, cleaned body. |
| `tags` | One per (artifact, question). Jev's answer, probability, confidence, model. |
| `runs` | Bookkeeping so a re-run resumes rather than re-paying. |
| `graded` (view) | Every graded artifact joined to its outcome. What stage 2 reads. |

Design decisions worth stating:

- **`call_lines` is a table, not a blob.** Storing the transcript as JSON would make "the first five minutes" a thing a model has to infer. As rows with `t_sec`, it is a `WHERE` clause.
- **An unanswered question is stored as a null answer, not as an absent row.** An absent row would be retried on every run forever. A null answer is skipped by the analysis and never counted as a no, so a failed Jev call cannot quietly drag a rate toward zero.
- **An unrecognised CRM stage maps to `open`, never to `closed_lost`.** Deal stages are per-pipeline and customisable. Guessing lost would inflate every loss rate in the findings, which is the direction that produces confident wrong advice.
- **Every write is an upsert.** Killing the pipeline halfway and running it again costs only the step it was on.

The engine never touches SQL. It reads a plain object, which is what lets the same analysis run in Node and in the browser with no adaptation layer.

---

## 9. Interfaces

### 9.1 The three prompts

Shipped as `prompts/*.md`, copy-paste ready, for the reader who wants to run this through an agent rather than install anything. This is the lowest-friction entry point and the one the source uses.

### 9.2 The pipeline

`node pipeline/run-prompt1.mjs`, `run-prompt2.mjs`, `run-prompt3.mjs`. For the reader who wants it deterministic, resumable, and re-runnable on a schedule. Five credentials, all read from `pipeline/.env`, none ever written to the repository.

### 9.3 The workbench

A static page at `athemventures.com/sales-coach/`. It carries the three prompt cards, and it runs stage 2's comparison live in the browser against a demo book of business or against a `dataset.json` the reader drops in. Nothing is uploaded; a dropped file is read with `FileReader` and stays in the tab.

The three guard thresholds are sliders. This is the central design decision of the page. The guard is the product, and an abstract claim about statistical discipline persuades nobody. Letting a reader drag significance to 0.50 and watch two flat questions turn into confident advice is the fastest honest way to explain why the guard exists.

---

## 10. What ships in version 1

- [x] Analysis engine: rubric, statistics, pattern guard, findings renderer, call-plan renderer. Pure ES modules, no dependencies, runs unchanged in Node and the browser.
- [x] 89 tests, including every figure in the source video pinned as an assertion.
- [x] Pipeline: Fireflies, Gemini, Gmail, HubSpot and Jev connectors, SQLite schema, three runnable stages, resumable throughout.
- [x] Jev over MCP stdio with input-schema discovery, plus an HTTP transport.
- [x] Demo dataset, generated to reproduce the source figures exactly.
- [x] Browser workbench, deployed.
- [x] Dataset importer, so the pipeline can be exercised end to end with no API keys.

## 11. Non-goals

- No hosted service, no accounts, no server. Recordings of customer conversations should not transit a third party to be counted.
- No CRM writes. Read only, in every direction.
- No real-time coaching during a call.
- No multi-rep leaderboard. The data model allows it; version 1 deliberately does not ship it, because a rubric this small becomes a management weapon the moment it is ranked.

---

## 12. Privacy and security

The pipeline downloads recordings of real customer conversations to a laptop and sends them to Gemini. That is a real exposure and the product should say so rather than bury it.

| Decision | Rationale |
| --- | --- |
| Everything lives under `~/sales-coach/` | One directory to audit, one directory to delete. |
| Uploaded Gemini files are deletable and the helper is provided | The recordings should not sit in a Files API bucket after the transcript is back. |
| Credentials in `pipeline/.env`, gitignored, never in the repository | `.env.example` documents every key and holds none. |
| The workbench never uploads | A dropped dataset stays in the tab. No analytics, no telemetry, no third-party script beyond a webfont. |
| Read-only scopes throughout | Gmail `readonly`, HubSpot read scopes only. |

**Open item.** Two-party consent recording law varies by state and country. Fireflies is already recording, so this product does not change the consent position, but a team rolling it out should confirm that position holds before pointing it at a year of history. This is flagged, not resolved.

---

## 13. Cost

Per full twelve-month run, roughly 200 calls:

| Line | Driver | Order of magnitude |
| --- | --- | --- |
| Gemini transcription | ~200 calls at ~25 minutes of audio | Single-digit dollars on a flash-tier model |
| Jev judgments | ~8,000 typed calls | Cents |
| Fireflies, Gmail, HubSpot | Reads within existing plans | Zero marginal |

The economics are the point. A full analysis of a year of selling costs less than lunch, against six thousand dollars for the course it replaces. Re-runs are cheaper still because every step is resumable.

---

## 14. Success metrics

| Metric | Target | Why this one |
| --- | --- | --- |
| Findings a rep says match their experience | 3 of 4 patterns | If the output does not ring true, nothing downstream matters. |
| Prep documents opened before a call | 60% of booked calls in month 1 | Stage 3 is where value is realised. Stages 1 and 2 are cost. |
| Questions reported as "no clear pattern" | Non-zero, always | A run that finds a pattern in everything has a broken guard. This is the canary. |
| Re-runs per user per quarter | 2 or more | A one-time report is a novelty. A re-run is a habit. |

That third metric is the one to watch. Its failure mode is silent and it is the failure mode that destroys trust.

---

## 15. Strategic note for Amplifier Health

Not a build instruction. A read on what this demonstrates.

The tone tag is the weakest link in the pipeline and the most valuable one. Sales Coach asks a general-purpose multimodal model to label prosody from raw audio with a seven-value vocabulary, and then hangs half its rubric on those labels. It works well enough for a coaching product. It is not calibrated, it is not validated against anything, and the labels have no confidence attached.

That is precisely the gap a purpose-built large acoustic model closes. Three observations follow:

1. **This is an adjacent commercial use of the same core claim.** Acoustics carry signal that linguistics do not. Here the proof is unusually clean, because the domain has a hard ground truth attached: the deal closed or it did not. Most voice-biomarker validation has no label that crisp.
2. **The dataset shape is familiar.** Real-world conversational audio, labelled by outcome, at volume, is the same shape as the asset that anchors our valuation. A sales organisation generates it continuously and considers it exhaust.
3. **It is a distribution question, not a science question.** Whether that adjacency is worth anything to us depends entirely on whether it competes for the same engineering and regulatory attention as the clinical roadmap. At this stage it almost certainly does, which is the argument for treating this as a demonstration rather than a product line.

The one thing worth extracting now: the pattern guard in section 7 is the same discipline a clinical validation study demands, implemented in 60 lines. It is reusable as-is.

---

## 16. Risks

| Risk | Severity | Response |
| --- | --- | --- |
| Tone tags are not calibrated | High | Version 1 ships call-only and email-only patterns side by side. If the acoustic questions behave erratically against the text-only ones, that shows up immediately in the table. |
| A rep acts on correlation as causation | High | Findings are worded as separation, never as instruction. Section 7.2 is stated in the product, not just the PRD. |
| `gemini-3.8-flash` is named in the source and may move | Medium | Model id is configurable. Default matches the source. |
| Jev's tool surface changes | Medium | The MCP client discovers the input schema at connect time and maps onto it, and fails loudly when the tool is absent rather than producing empty judgments. |
| Small books produce no findings at all | Medium | Correct behaviour, but it reads as a broken product. "Not enough data yet" is reported as its own category with the counts, so the reason is visible. |
| Gmail OAuth tokens are short lived | Low | Documented. Generate immediately before a run. |

---

## 17. What version 2 should do

1. **Ordering within a call.** "Rapport before the pitch" is currently one bit. The transcript is already stored line by line with timestamps, so the real question, how many minutes elapsed before the first price mention, is already answerable and is a far stronger signal than a boolean.
2. **Per-segment rubrics.** What closes a 5,000 dollar deal is not what closes a 50,000 dollar deal. The amount is already in the database and the analysis is already parameterised.
3. **Confidence-weighted answers.** Jev returns a probability and it is already stored. Weighting by it, or excluding judgments below a confidence floor, costs nothing and should sharpen every rate.
4. **A calibration set.** Fifty calls graded by hand against the same rubric, to measure what Jev and the tone tags are actually worth. Without this, every number in `findings.md` rests on an unvalidated labeller. This is the single highest-value item on the list.

---

## 18. Open questions

- What is the minimum book size at which this produces anything useful? The guard implies roughly 20 closed deals with a reasonable win rate, but that is derived, not measured.
- Does re-transcribing beat using the Fireflies transcript plus a separate prosody pass? Cheaper, and it would isolate the acoustic contribution, which matters for question 1 in section 17.
- Is `email_ends_with_question` real or an artifact of deal stage? Late-stage threads are shorter and more transactional. The demo data cannot distinguish these. Real data might.
