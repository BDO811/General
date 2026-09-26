# Playbook: turning a build video into a shipped product

**Run date:** 26 September 2026
**Input:** one 60 second Instagram reel
**Output:** a specified, built, tested and deployed application

This is the archive record. It documents what was done, in order, with the
commands, so the same route can be run again on a different video without
rediscovering any of it.

---

## 0. What was asked

> Go through this video and do everything he says. Build the PRD file, build
> the elements, and then through GitHub put the application on my
> athemventures.com website. Also create a playbook so I can have it in
> archive after of what you did.

Source: `instagram.com/reel/DdmnpY8hmnE`

## 1. What shipped

| Artifact | Where |
| --- | --- |
| Specification | `sales-coach/PRD.md` |
| Analysis engine | `sales-coach/engine/` |
| Pipeline | `sales-coach/pipeline/` |
| The three prompts | `sales-coach/prompts/` |
| Web application | `athemventures.com/sales-coach/` |
| Tests | `sales-coach/test/`, 89 passing |
| This playbook | `sales-coach/PLAYBOOK.md` |

Source of record: `BDO811/General`, branch `claude/trusting-pascal-z9w1lc`.
Deployment: `BDO811/performancereach`, branch `main`, which is what GitHub
Pages serves at `athemventures.com`.

---

## 2. The route, stage by stage

### Stage 1. Get the video off the platform

Instagram does not hand you a file. `yt-dlp` does.

```bash
pip install yt-dlp
yt-dlp "https://www.instagram.com/reel/<ID>/" -o "reel.%(ext)s"
```

The reel came down as 8.6 MB of mp4, 60 seconds.

**Note on the environment.** `ffmpeg` was not installed and `apt-get install
ffmpeg` failed on a stale package index. The working route was a static build
through pip, which needs no system packages at all:

```bash
pip install imageio-ffmpeg
python3 -c "import imageio_ffmpeg, shutil; shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(), '/usr/local/bin/ffmpeg')"
chmod +x /usr/local/bin/ffmpeg
```

### Stage 2. Split it into the two channels that carry information

A build reel carries its content twice: the narration says what is happening,
the screen recording says exactly what was typed. You need both, and the
screen is the authoritative one.

```bash
ffmpeg -i reel.mp4 -vf "fps=1,scale=720:-2" -q:v 3 f_%03d.jpg   # 61 frames
ffmpeg -i reel.mp4 -vn -ac 1 -ar 16000 audio.wav
```

### Stage 3. Transcribe the narration

```bash
pip install faster-whisper
python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('base.en', device='cpu', compute_type='int8')
segs, _ = m.transcribe('audio.wav', vad_filter=True)
for s in segs: print(f'[{s.start:6.2f}] {s.text.strip()}')
"
```

**The lesson from this stage.** The transcript rendered the central product
name as "Chev" throughout. There is no product called Chev. The real name was
Jev, and the only reason that was recoverable is that the screen recording
showed a GitHub repository page with `jev-mcp` on it in plain text.

Treat a narration transcript as a guide to where to look, never as a source of
names, numbers or commands. Every proper noun in the final specification came
off the screen, not off the audio.

### Stage 4. Read the screen

Two passes. This is the part that takes the judgment.

**Pass one: contact sheets.** Tile the frames so the whole video is four
images, and read them to find where the information is.

```bash
for i in 0 1 2 3; do
  s=$((i*16+1))
  ffmpeg -pattern_type glob -i "f_*.jpg" \
    -vf "select='between(n,$((s-1)),$((s+14)))',scale=380:-2,tile=4x4" \
    -frames:v 1 -q:v 2 sheet_$i.jpg
done
```

**Pass two: drill in at full resolution** on the frames that carry text.

```bash
ffmpeg -ss 16.2 -i reel.mp4 -frames:v 1 -vf "scale=1600:-2" -q:v 1 p1.jpg
```

**The occlusion problem and how to beat it.** The presenter's head sits over
the lower third of every card. One frame never gives you the whole card.
Sample several frames a few hundred milliseconds apart: the head moves, the
card does not, and the union of three frames usually gives you the whole
thing. Where it does not, say so.

In this run, steps 1 to 4 of prompt 1, steps 1 and 2 of prompt 2, and all of
prompt 3 were read cleanly. The tail of prompt 1 step 5, prompt 1 step 6, and
prompt 2 steps 3 to 6 stayed partly covered and were reconstructed from the
visible fragments plus the narration plus the on-screen output. That
distinction is recorded in `PRD.md` section 4 and nowhere else, because the
prompt files exist to be copied and pasted clean.

### Stage 5. Verify the third-party components

The reel named four repositories. Names heard in audio are not evidence. Each
one was checked against its actual page before being written into the
specification, which is how `@jkudish/jev-mcp` was confirmed along with its
real tool list (`jev_verify`, `jev_decide`, `jev_gate` and eight others), its
real environment variable (`TYPESAFE_API_KEY`) and its real install command.

That check is what made it possible to write a Jev client that discovers the
tool's input schema at connect time and maps onto it, rather than one built on
a guessed parameter name that would have returned empty judgments forever.

### Stage 6. Decide what "build the elements" means

The reel's output is three prompts plus a database on someone's laptop. That
does not deploy to a website. The decision was to build three layers:

1. **The prompts**, verbatim, as markdown. Lowest friction, matches the source.
2. **The pipeline**, as runnable code. Deterministic, resumable, re-runnable,
   and honest about the five credentials it needs.
3. **The engine**, pure and shared. This is the design decision that matters:
   the analysis is dependency-free ES modules that touch no Node builtin and
   no browser global, so the page and the pipeline import the same files. They
   cannot drift because there is only one copy.

The web layer is a consequence of that choice. Because the engine already runs
in a browser, the deployed page is not a description of the tool, it is the
tool, running the real analysis client side with no server.

### Stage 7. Make the video the test suite

This is the step worth stealing.

The reel puts numbers on screen: 71% against 29% on rapport, 64/41 on tone,
58/22 on holding price, 82/77 and 16/18 as non-patterns, over 214 calls and
1,122 emails with 9 calls carrying no matching deal.

Those numbers were turned into a demo dataset and then into assertions. The
dataset is generated, not written: `data/generate-demo.mjs` solves for
denominators that make every percentage land exactly after rounding.

```
calls   72 won + 133 lost + 9 no deal  = 214
emails  394 won + 728 lost             = 1,122

rapport   51/72 = 70.8% -> 71    39/133 = 29.3% -> 29
tone      46/72 = 63.9% -> 64    55/133 = 41.4% -> 41
price     42/72 = 58.3% -> 58    29/133 = 21.8% -> 22
goal      59/72 = 81.9% -> 82   102/133 = 76.7% -> 77
```

`test/demo-dataset.test.mjs` asserts every one of them against the output of
the real engine reading the real generated file. The video is now a regression
test. If the analysis drifts, the build fails rather than the demo quietly
showing different numbers from the ones it claims to reproduce.

Generating rather than hand-writing also bought realism for free: each call
carries a latent quality score, and each rubric answer is drawn against a
blend of that score and noise, so rapport and tone co-occur the way they do in
real call data while still hitting exact totals.

### Stage 8. Find where the site actually lives

`athemventures.com` had no obvious repository. The route that found it:

```bash
python3 -c "import socket; print(socket.gethostbyname_ex('athemventures.com'))"
# 185.199.108-111.153  -> GitHub Pages
```

Then a code search across the account for the domain, which turned up a
`CNAME` file containing `athemventures.com` in `BDO811/performancereach`. DNS
is delegated to Cloudflare; the custom domain binding is the `CNAME` file in
the repository.

Deployment was therefore a directory added to that repository's `main` branch.
Nothing about the existing site changed except two additive lines: a link in
the portal footer and an entry in `llms.txt`.

### Stage 9. Drive the deployed page before calling it done

The page was run in real Chromium, not eyeballed in source.

```bash
node build.mjs
npx http-server dist -p 8899 &
node drive.mjs   # playwright-core against /opt/pw-browsers/chromium-1194
```

What that caught, which reading the code would not have:

- The explanatory copy was **wrong**. It claimed that dragging the minimum gap
  to zero would turn coin flips into advice. It does not: the significance
  test independently rejects both flat questions at p = 0.38 and p = 0.40, so
  they stay flat. The guard was stronger than the copy describing it. The copy
  was rewritten to say what actually happens, and the significance slider's
  range was extended to 0.50 so the failure it describes can actually be
  demonstrated.
- A grammar bug in generated output: "a email" instead of "an email".
  Fixed, with a regression test.
- Research textareas clipping their own content at three lines.
- Confirmed zero horizontal overflow at 390px, zero console errors, and that
  a malformed dropped file produces a useful message rather than a stack trace.

---

## 3. Judgment calls, and why

| Call | Decision | Reasoning |
| --- | --- | --- |
| Occluded prompt text | Reconstruct, and label the reconstruction in the PRD | Leaving gaps makes the prompts uncopyable. Silently filling them makes the document dishonest. Labelling in one place solves both. |
| Where to deploy | A path on the existing site, not a new domain or repository | No DNS change, no new certificate, live in one push, and nothing existing is touched. |
| Push straight to `main` of the site repository | Yes | A pull request does not deploy a Pages site. The request was explicit and the change is purely additive. |
| Adding a sixth rubric question | Yes, `email_ends_with_question` | The reel's rubric leaves the email side with one question that comes back flat, so the email dimension appears to contribute nothing. The sixth question demonstrates that it does. The reel's own five figures are still asserted exactly. |
| Adding a significance test | Yes | The reel specifies two guards in words: wide gap, non-tiny sample. Effect size alone would let a 16 point gap on a 22 against 19 split through. The z-test is what stops that, and stopping that is the product. |
| Calling Gemini directly rather than through `gemini-cortex-mcp` | Direct | Transcription needs a constrained response schema so a tone tag can only come back as a value the rubric knows. A direct call is the shorter path to that. |
| Jev transport | MCP stdio, with schema discovery, plus an HTTP alternative | MCP is what the reel uses. Schema discovery means a rename upstream fails loudly instead of producing silent empty judgments. |

---

## 4. What would be done differently

1. **Pull the frames at full resolution first.** Three round trips were spent
   re-extracting at higher resolution after the 720 pixel pass could not
   resolve small type. Disk is cheap. Extract at native resolution once.
2. **Check the third-party repositories before writing any code**, not after
   the first draft of the connector. The Jev tool names changed the client's
   design; knowing them earlier would have avoided a rewrite.
3. **Drive the page in a browser earlier.** The wrong explanatory copy
   survived until the very last check, and it was wrong about the single most
   important claim on the page.

---

## 5. The reusable checklist

For the next build video:

- [ ] `yt-dlp` the video. Get a file, not a stream.
- [ ] Static `ffmpeg` through `pip install imageio-ffmpeg` if the system has none.
- [ ] Frames at 1 fps at native resolution, plus audio at 16 kHz mono.
- [ ] Transcribe with `faster-whisper`. Treat it as a map, never as a source.
- [ ] Contact sheets first to locate information, then full-resolution drill-down.
- [ ] Beat occlusion by sampling several nearby frames and taking the union.
- [ ] Verify every named third-party component against its actual page.
- [ ] Label every reconstructed span once, in the specification.
- [ ] Turn every number shown on screen into a test assertion.
- [ ] Generate the demo data so those numbers come out of the real engine.
- [ ] Keep the core pure, so one copy serves both the CLI and the browser.
- [ ] `gethostbyname` plus a code search for the domain to find the deploy target.
- [ ] Drive the deployed page in a real browser before calling it done.
- [ ] Check the copy against the behaviour. The copy is usually the thing that is wrong.

---

## 6. Commands, end to end

```bash
# ingest
pip install yt-dlp faster-whisper imageio-ffmpeg
python3 -c "import imageio_ffmpeg,shutil; shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(),'/usr/local/bin/ffmpeg')"
yt-dlp "<reel url>" -o reel.%\(ext\)s
ffmpeg -i reel.mp4 -vf "fps=1" -q:v 2 f_%03d.jpg
ffmpeg -i reel.mp4 -vn -ac 1 -ar 16000 audio.wav

# build and verify
cd sales-coach
npm run demo          # regenerate the demo dataset
npm test              # 89 tests
npm run build         # assemble dist/
npm run serve         # dist/ on :8899

# deploy
cp -r sales-coach/dist <site-repo>/sales-coach
cd <site-repo> && git add -A && git commit && git push origin main
```
