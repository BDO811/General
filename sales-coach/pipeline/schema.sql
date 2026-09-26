-- sales.db
--
-- The single file prompt 1 builds and prompts 2 and 3 read. Everything the
-- coach needs lives here: the calls with tone-tagged transcripts, the email
-- threads, the deal outcomes, and Jev's answers.
--
-- Deliberately one file with no server. It gets read on a laptop before a
-- call, and it holds real customer conversations, so it should be as easy to
-- delete as it was to build.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- A person on the other side of the deal, joined to their CRM record.
CREATE TABLE IF NOT EXISTS prospects (
  id          TEXT PRIMARY KEY,           -- our key: normalised email
  name        TEXT,
  company     TEXT,
  title       TEXT,
  email       TEXT UNIQUE,
  -- closed_won | closed_lost | open | none
  -- 'none' means no deal was found in the CRM for this person at all.
  outcome     TEXT NOT NULL DEFAULT 'none',
  amount      REAL,
  closed_at   TEXT,
  hubspot_deal_id     TEXT,
  hubspot_contact_id  TEXT,
  updated_at  TEXT NOT NULL
);

-- One row per Fireflies recording.
CREATE TABLE IF NOT EXISTS calls (
  id            TEXT PRIMARY KEY,         -- Fireflies transcript id
  prospect_id   TEXT REFERENCES prospects(id) ON DELETE SET NULL,
  title         TEXT,
  date          TEXT NOT NULL,            -- ISO date
  duration_sec  INTEGER,
  audio_path    TEXT,                     -- where the downloaded audio landed
  transcript_path TEXT,                   -- calls/[id].json
  -- Non-null once Gemini has returned a tone-tagged transcript for this call.
  transcribed_at TEXT
);

CREATE INDEX IF NOT EXISTS calls_prospect ON calls(prospect_id);
CREATE INDEX IF NOT EXISTS calls_date ON calls(date);

-- One row per transcript line, so a rubric question can be answered against
-- a slice of a call rather than the whole thing.
CREATE TABLE IF NOT EXISTS call_lines (
  call_id   TEXT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
  seq       INTEGER NOT NULL,
  t         TEXT,                         -- mm:ss as Gemini returned it
  t_sec     INTEGER,                      -- parsed, so "first five minutes" is a WHERE
  speaker   TEXT,                         -- 'me' or the prospect's name
  text      TEXT NOT NULL,
  tone      TEXT,                         -- hesitant | rushed | confident | laughing | flat | warm | matching their energy
  PRIMARY KEY (call_id, seq)
);

CREATE INDEX IF NOT EXISTS call_lines_tone ON call_lines(tone);

-- Both sides of the email thread. The seller's own messages are the ones
-- graded; the prospect's replies are what "a similar length to theirs" is
-- measured against.
CREATE TABLE IF NOT EXISTS emails (
  id          TEXT PRIMARY KEY,           -- Gmail message id
  thread_id   TEXT,
  prospect_id TEXT REFERENCES prospects(id) ON DELETE SET NULL,
  direction   TEXT NOT NULL CHECK (direction IN ('out', 'in')),
  date        TEXT NOT NULL,
  subject     TEXT,
  words       INTEGER,
  body        TEXT
);

CREATE INDEX IF NOT EXISTS emails_prospect ON emails(prospect_id);
CREATE INDEX IF NOT EXISTS emails_thread ON emails(thread_id);

-- Jev's answers. One row per (artifact, question).
--
-- `answer` is the typed verdict, stored as 0 or 1. `probability` and
-- `confidence` come back from Jev alongside it and are kept so a borderline
-- judgment can be found later rather than being flattened into a bare yes.
CREATE TABLE IF NOT EXISTS tags (
  artifact_kind TEXT NOT NULL CHECK (artifact_kind IN ('call', 'email')),
  artifact_id   TEXT NOT NULL,
  question_id   TEXT NOT NULL,
  answer        INTEGER,                  -- 1 yes, 0 no, NULL if Jev could not answer
  probability   REAL,
  confidence    REAL,
  model         TEXT,
  judged_at     TEXT NOT NULL,
  PRIMARY KEY (artifact_kind, artifact_id, question_id)
);

CREATE INDEX IF NOT EXISTS tags_question ON tags(question_id);

-- Bookkeeping so a re-run can pick up where the last one stopped instead of
-- re-paying for every Gemini and Jev call.
CREATE TABLE IF NOT EXISTS runs (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  step       TEXT NOT NULL,               -- prompt1 | prompt2 | prompt3
  started_at TEXT NOT NULL,
  ended_at   TEXT,
  ok         INTEGER,
  note       TEXT
);

-- The view prompt 2 reads: every graded artifact with its outcome attached.
CREATE VIEW IF NOT EXISTS graded AS
  SELECT
    'call'   AS artifact_kind,
    c.id     AS artifact_id,
    c.prospect_id,
    COALESCE(p.outcome, 'none') AS outcome,
    t.question_id,
    t.answer
  FROM calls c
  LEFT JOIN prospects p ON p.id = c.prospect_id
  JOIN tags t ON t.artifact_kind = 'call' AND t.artifact_id = c.id
UNION ALL
  SELECT
    'email'  AS artifact_kind,
    e.id     AS artifact_id,
    e.prospect_id,
    COALESCE(p.outcome, 'none') AS outcome,
    t.question_id,
    t.answer
  FROM emails e
  LEFT JOIN prospects p ON p.id = e.prospect_id
  JOIN tags t ON t.artifact_kind = 'email' AND t.artifact_id = e.id
  WHERE e.direction = 'out';
