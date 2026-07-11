# Secretary Protocol — the `.omp/secretary/` file contract (SSOT)

This card is the single source of truth for the **secretary axis** — the time axis
(progress tracking, session journal, todo/RAID, decisions, briefing) that sits alongside
omp's existing space axis (folder structure/naming governance). Every skill or agent that
reads or writes `.omp/secretary/**` MUST obey this card — `omp-log`, `omp-brief`,
`omp-review`, the `chronicler` agent, and the `omp_session_brief.py` / `omp_session_capture.py`
hooks.

> **Origin.** Design doc `docs/design/2026-07-11-omp-secretary-upgrade-plan.md` §4.1
> (layout), §5 (lifecycle), §3 (tag grammar), §1 D1–D9 (locked decisions) is the authored
> source for everything in this card. Where this card and the design doc ever appear to
> disagree, the design doc's D-table wins and this card should be corrected to match.

The path contract for where `.omp/` (governance) lives is `references/output-layout.md`.
This card is that same kind of contract, scoped to `.omp/secretary/`.

---

## Layout

```
<project>/.omp/secretary/
├── BRIEF.md              # ≤30 lines AND ≤2000 chars, regenerated, omp-managed marker+hash
├── todo.txt              # todo.txt schema, one line = one task (done moves to done.txt at review)
├── done.txt              # completed-task archive (todo.txt convention)
├── raid.md               # Risks/Assumptions/Issues/Dependencies — closed by a human only
├── ledger.jsonl           # append-only event log (machine, the SSOT for derived metrics)
├── journal/
│   └── YYYY-MM-DD.md     # daybook — append-only, failure is first-class content, session stub + narrative
└── decisions/
    └── NNNN-slug.md       # ADR, 5 fields, superseded_by tracking, [[wikilink]] allowed
```

This is SSOT-layer content, not the regenerable `work/` layer — with one exception:
`BRIEF.md` is a "regenerated SSOT". Its source of truth is `ledger.jsonl` / `todo.txt` /
`raid.md` / `journal/` — BRIEF is a derived view over them, which is why it alone carries
the omp-managed marker (below): a wholesale regeneration must never silently clobber a
human's hand-edit to that file.

---

## `todo.txt` line grammar

One line = one task, following the [todo.txt spec](https://github.com/todotxt/todo.txt/blob/master/README.md):

```
(A) 2026-07-11 본문 +project @context key:value
```

- `(A)` — optional priority letter, uppercase, in parentheses, first token.
- `2026-07-11` — optional creation date, ISO `YYYY-MM-DD`.
- `본문` — free-text task description.
- `+project` — zero or more project tags (any token prefixed `+`).
- `@context` — zero or more context tags (any token prefixed `@`).
- `key:value` — zero or more custom key:value fields, space-separated. omp's custom keys:
  - `due:` — ISO date the task is due.
  - `blocked-by:` — a `raid.md` id or another task reference this task waits on.
  - `id:` — a stable identifier for cross-referencing from `ledger.jsonl` events.

Completed line (moved to `done.txt` at review time):

```
x 2026-07-12 2026-07-11 본문
```

- `x` — literal completion marker, first token.
- `2026-07-12` — completion date.
- `2026-07-11` — original creation date (both dates present once a task is marked done,
  per the todo.txt spec).
- `본문` — same task text (tags/keys carried over unchanged).

---

## `ledger.jsonl` event schema

Append-only. One line = one complete JSON object (no multi-line records — POSIX line-append
is atomic, a partial line is never a valid record):

```json
{"ts":"<ISO8601>","event":"<task_added|task_done|blocker_opened|blocker_closed|decision_recorded|gate_passed|session_start|session_end>","stage":"<init|codify|organize|dataset|env|doc|null>", ...}
```

- `ts` — **required.** ISO 8601 timestamp.
- `event` — **required.** One of exactly: `task_added`, `task_done`, `blocker_opened`,
  `blocker_closed`, `decision_recorded`, `gate_passed`, `session_start`, `session_end`.
- `stage` — optional. One of `init`, `codify`, `organize`, `dataset`, `env`, `doc`, or
  `null`. Present when the event correlates with a governance-axis stage (e.g.
  `gate_passed{stage: "organize", decision: ...}`).
- All other fields are free-form **but flat** (no nested objects/arrays required by the
  schema) — a reader must be able to `json.loads` a line and treat it as a flat dict.

A malformed line (JSON parse failure) is skipped with a one-line stderr warning by any
reader (`derive_status`, `scan_stale`, …) — one corrupt line must never crash the derived
metrics for the whole file.

---

## `journal/` tag grammar

Journal entries are free-form narrative by default (D6 — failure is first-class content,
nothing is forced into a schema). Inline tags are an **optional** grep hook layered on top,
never a requirement to write a journal entry. Extraction regex (paired with the grammar,
per the OMC evidence-tag convention — grammar and extractor live in the same document):

```
\[(BLOCKER|LESSON|DECISION):([A-Za-z0-9_-]+)\]
```

- Group 1 — tag kind: `BLOCKER`, `LESSON`, or `DECISION`.
- Group 2 — a slug/id (e.g. a `raid.md` id for `BLOCKER`, an ADR number for `DECISION`, a
  free slug for `LESSON`).
- Example: `[BLOCKER:R-0003]`, `[DECISION:0002]`, `[LESSON:icloud-eviction]`.

`scan_journal_tags` greps this pattern across `journal/*.md` to surface repeated-failure
tags as candidates `omp-review` *presents* for wiki promotion — tagging never auto-promotes
(D9: closing/promoting is a human's call).

---

## Registered sources (`rules.json` `secretary.sources[]`)

Release 2 (design Part II §10.2). Existing state surfaces the user already keeps —
`Kanban.md`, daily-note task lists, README status tables — are registered as **read**
targets in `rules.json`:

```json
{"secretary": {"sources": [
  {"path": "Kanban.md", "kind": "todo", "convention": "unchecked boxes = open milestones"}
]}}
```

- Registration happens **only via the omp-codify human gate** (D14 read-don't-replace;
  never auto-registered — surfaces are *proposed*, a human approves).
- `kind` ∈ `todo | journal | status | schedule`. `todo`/`schedule` are parsed for open-item
  counts (`*.txt` → todo.txt grammar; otherwise markdown `- [ ]` checkboxes) and aggregate
  into `derive_status` open-task counts and the traffic light. `journal`/`status` contribute
  no numbers — they are read-map pointers: BRIEF tells the reader *where to look*.
- Fail-open: a missing file or corrupt `rules.json` never crashes status derivation.
- BRIEF may render the read-map as `읽을 곳: <path> (<kind>) — <convention>` lines (≤4).
  When over the BRIEF cap, read-map lines are dropped **before** the existing truncation
  priority list (they are pointers, reconstructible from rules.json).

---

## BRIEF contract

- **Double cap: ≤30 lines AND ≤2000 characters.** Both bounds apply — line count alone
  lets any single line grow unbounded and defeat the budget. This mirrors the OMC Zod
  hard-cap / `priorityMaxChars` soft-cap precedent for a context payload injected every
  SessionStart.
- **Truncation priority when over cap** (no author discretion at truncation time — apply
  in this order until back under both caps):
  1. top-5 task list → top-3.
  2. open-blocker list → count only (no per-item detail).
  3. decisions summary → path references only (no inline summary text).
- **Never truncated (inviolable, always present, 3 lines minimum):** the omp-managed
  marker line, the traffic-light line + its one-line rationale, and the one-line
  State-of-play line.
- **omp-managed marker format** (one fixed line, HTML comment, at the top of the file):

  ```
  <!-- omp-managed: sha256:<64hex> -->
  ```

  Before `omp-brief` regenerates `BRIEF.md`, it hashes the current on-disk file and
  compares against the marker's recorded hash (`brief_hash_check`). Mismatch means a human
  hand-edited the file since the last regeneration — regeneration STOPs and surfaces the
  conflict instead of silently overwriting.

---

## ADR format

`.omp/secretary/decisions/NNNN-slug.md`, zero-padded 4-digit sequence number + slug.
5 fields (Nygard 2011 form), created once and never edited except via a new superseding
ADR:

- **Title**
- **Status** — one of `proposed`, `accepted`, `deprecated`, `superseded`.
- **Context**
- **Decision**
- **Consequences**

Optional frontmatter field: `superseded_by:` — set on an older ADR once a newer one
replaces it, so "was this decision reversed?" is a single grep, never a directory
crawl-and-read.

---

## Lifecycle

Summarized from design §5 (the table there is authoritative; this is the operational
digest):

| File | Write discipline | Retirement / migration | Promotion |
|:---|:---|:---|:---|
| `journal/` | append-only, truncation permanently forbidden | none — a daybook is never deleted; BRIEF only reads the last 7 days | a recurring failure pattern is **rewritten** into `learned.md` (a copy is not enough — it travels the heavy channel like any other observation) |
| `todo.txt` | whole-file rewrite allowed (it's a snapshot) — but only via atomic write | done items move to `done.txt` at `omp-review` time | none |
| `raid.md` | append + status updates | closed only by a human (D9); stale >14 days surfaces in `BRIEF.md` | a recurring issue becomes a `wiki/` note |
| `decisions/` | write-once, reversals are a new ADR + `superseded_by` | never deleted | none — an ADR is already the terminal form |
| `ledger.jsonl` | append-only, machine-only writer | none (event volume is daily-dozens scale; no cap for now, revisit if observed otherwise) | none |
| `BRIEF.md` | regenerated wholesale only by `omp-brief`, gated by the managed-hash check | every regeneration *is* the update | none (it's a derived view, not a source) |

---

## Writer ownership

Per D7: the secretary axis has **two disjoint writers**, split at line granularity, never
by file:

- **`chronicler`** (the only LLM writer, scope `.omp/secretary/**`) owns narrative/judgment
  content: journal prose, `decisions/`, `todo.txt`, `raid.md`, `BRIEF.md`.
- **Hooks** (`omp_session_brief.py`, `omp_session_capture.py` — no LLM call) own machine
  append: `ledger.jsonl` in full, and the session-stub lines appended to
  `journal/YYYY-MM-DD.md`.

The two writers are **disjoint at the line level, not the file level** — `journal/*.md` is
the one file both touch: the hook appends only its own stub lines (never edits an existing
line), and `chronicler` appends only narrative blocks (never truncates or rewrites an
existing line, hook stub or its own). Neither writer ever truncates a line the other
wrote.

---

## See also

- `references/output-layout.md` — the `.omp/` SSOT vs work-layer boundary; this card's
  `secretary/` entry there is the pointer back to this document.
- `references/learning-protocol.md` — the heavy/light channel boundary; secretary files
  are **not** a third learning channel — a promoted journal lesson or raid pattern still
  travels through `learned.md` (heavy) or `wiki/` (light) exactly as before.
- `references/safe-fileops.md` — move/delete protocol; secretary files are never moved by
  `organizer`, only appended/regenerated in place by `chronicler`/hooks.
