# Learning Protocol — omp's generic→specialized self-evolution (SSOT)

This card is the single source of truth for **how omp gets smarter about *your* project
the more you use it**. It is the heart of omp's identity: shipped generic, specialized in
place. Every skill or agent that reads, writes, or promotes project knowledge MUST obey
this card — `omp-learn`, `omp-codify`, `omp-init`, the `rule-architect` agent, and the
`wiki/` accumulation behavior.

> **Identity in one line.** omp ships as a *generic* harness (same logic for everyone) and
> becomes *specialized* purely through the contents of `<project>/.omp/`. Specialization is
> data, not code. This card defines exactly how that data accumulates — safely, with the
> right friction in the right place.

The path contract for where this data lives is `references/output-layout.md`. The machine
shape of the rules is `references/schemas/rules.schema.json`. This card governs the
*dynamics* — what flows into those files, when, and under whose approval.

---

## 1. The two channels (asymmetric on purpose)

omp learns through **two channels with deliberately different friction**. The asymmetry is
the whole design: rule changes can move files, so they pay a human gate; patterns and
decisions are cheap memory, so they accumulate freely.

```
                          OBSERVATION (something omp noticed about your project)
                                              │
                ┌─────────────────────────────┴──────────────────────────────┐
                │                                                             │
        is it a candidate RULE                                  is it a PATTERN / DECISION
        (could change files / drive audit)?                     (a note worth recalling later)?
                │                                                             │
        ── HEAVY CHANNEL (gated) ──                              ── LIGHT CHANNEL (no gate) ──
                │                                                             │
   learned.md  ──>  omp-learn  ──>  rule-architect              wiki/<topic>.md  (auto-append)
   (observation     (promotion       (promotion judgment)               │
    accrues)         skill)               │                      next session: deterministic
                │                          ▼                      grep recall (no model search)
                │                  HUMAN APPROVAL GATE                     │
                │                          │                               ▼
                │                          ▼                      injected as context,
                └────────────────> rules.json  (specificity bump)  never auto-applied as a rule
```

### Heavy channel — RULES (`learned.md` → `omp-learn` → human gate → `rules.json`)

A **rule** is anything `omp-audit` could enforce or `omp-organize` could act on: a folder
role, a naming pattern, an ignore glob. Because a promoted rule can ultimately cause files
to be flagged or *moved*, it is a heavy, consequential decision. It therefore travels the
gated path:

1. Observations accrue in `.omp/learned.md` (any read-only stage may append; see §2).
2. `omp-learn` dispatches `rule-architect` (opus, read-only) to judge which observations
   are ripe (§3) and to draft the rule edit + the specificity recompute (§4).
3. **A human approves the promotion.** This is the single most important gate in omp.
4. On approval, the rule is written into `rules.json`, `specificity` is recomputed, the
   observation's id is recorded in `rules.json.learned_refs[]` (provenance), and the
   paired `STRUCTURE.md` / `NAMING.md` are regenerated in the same pass so .md ↔ .json
   never drift (per `output-layout.md`).

`rule-architect` **proposes only** — it never writes `rules.json` itself in the learn flow;
the human gate plus `omp-codify` perform the write. (Design §3: "규칙은 제안만, 강제는 사람.")

### Light channel — PATTERNS / DECISIONS (`wiki/*.md` auto-append, grep recall, no gate)

A **pattern or decision** is a note about the project that is useful to *remember* but is
not an enforceable rule: "we decided to keep raw dumps even after cleaning", "the figures
script expects PNG not SVG", "exp-2026-05 used the 80/20 split". These are cheap. They
auto-append to `.omp/wiki/<topic>.md` during any stage, with **no approval gate**, and are
recalled next session by **deterministic grep** over `wiki/` (§5). A wiki note is *context*,
never an enforced rule — it can inform a future rule proposal, but it cannot itself cause a
file to be flagged or moved. That promotion (wiki insight → candidate rule) only happens by
re-entering the heavy channel through `learned.md`.

### Channel routing rule (which channel does an observation take?)

| The observation… | Channel | Why |
|:---|:---|:---|
| could be enforced by audit or acted on by organize (folder role, naming regex, ignore glob) | **Heavy** (`learned.md`) | can move/flag files → needs the gate |
| is a fact, rationale, or decision worth remembering but not enforcing | **Light** (`wiki/`) | cheap memory → no gate |
| is ambiguous | **default to Light**, and let a human or a later `omp-learn` pass escalate it into `learned.md` | safer to remember-without-enforcing than to enforce-without-asking |

---

## 2. The `learned.md` observation format (heavy-channel staging)

`.omp/learned.md` is an append-only ledger of candidate rules awaiting promotion. It is
human-readable Markdown with a fixed per-observation block. Stages append; only `omp-learn`
(via the human gate) consumes/retires entries.

Each observation is one fenced block:

```
## OBS-<NNNN>  <one-line summary>
- id: OBS-<NNNN>
- channel: rule                      # always 'rule' in learned.md (light-channel notes go to wiki/)
- status: candidate | promoted | rejected | superseded
- pattern: <precise, testable statement of the regularity>
- candidate_rule:                    # the exact rules.json edit this would become, if promoted
    target: structure.directories[] | naming.patterns[] | ignore[]
    value: <the concrete dir-role / regex / glob being proposed>
- evidence_count: <integer ≥ 1>      # how many distinct files/events support it
- evidence:                          # the actual support — paths/events, NOT a vibe
    - <relative/path/or/event #1>
    - <relative/path/or/event #2>
- counter_examples: <integer>        # files/events that VIOLATE the pattern (kills promotion if > 0)
- first_seen: <ISO date>
- last_seen: <ISO date>
- user_overridden: false             # set true if the user has ever rejected/contradicted this
- source_stage: <init|audit|organize|dataset|doc>   # which stage logged it
```

Worked example:

```
## OBS-0007  .pkl files always live under data/processed/
- id: OBS-0007
- channel: rule
- status: candidate
- pattern: Every committed *.pkl in this repo sits under data/processed/.
- candidate_rule:
    target: naming.patterns[]
    # A pure *location* rule (no basename-shape constraint), so `regex` is omitted and
    # `path_constraint.must_be_under` carries the intent. Validates against
    # rules.schema.json naming.patterns[] (applies_to + description required; regex optional).
    value:
      applies_to: "**/*.pkl"
      path_constraint: { must_be_under: "data/processed" }
      description: ".pkl 파일은 data/processed/ 아래에만 둔다 (관찰 4회 → 승격)"
      origin: learned
      severity: warn
- evidence_count: 4
- evidence:
    - data/processed/train.pkl
    - data/processed/val.pkl
    - data/processed/scaler.pkl
    - data/processed/encoder.pkl
- counter_examples: 0
- first_seen: 2026-05-12
- last_seen: 2026-05-30
- user_overridden: false
- source_stage: audit
```

Rules for the ledger:
- **Append-only by stages.** A scanning stage that re-observes an existing pattern bumps
  `evidence_count`, appends to `evidence[]`, and updates `last_seen` — it does not create a
  duplicate block.
- **Evidence is concrete.** `evidence[]` lists real paths/events. An observation with no
  enumerable evidence is not an observation — it is a guess, and guesses do not enter
  `learned.md` (Constraints: "추측 금지, 실제 트리만").
- **Counter-examples are tracked honestly.** The moment a file violating the pattern is
  seen, `counter_examples` increments. This is what makes promotion safe (§3).
- **Status is a lifecycle, not a delete.** Promoted/rejected/superseded entries stay in the
  ledger for provenance; they are filtered out of the candidate set, not erased.

---

## 3. Promotion criteria (the test `rule-architect` applies)

When `omp-learn` runs, `rule-architect` evaluates each `status: candidate` observation
against **all** of the following. A candidate is promotable to the human gate **only if
every condition holds** — this is an AND, not a score:

1. **Repetition.** `evidence_count ≥ 3` across **distinct** files/events. Three is the
   minimum that distinguishes a convention from a coincidence. (Design §4: "관찰 3회 반복".)
2. **No counter-examples.** `counter_examples == 0`. A single file that breaks the pattern
   means it is not yet a rule — it is a tendency. Counter-examples block promotion outright;
   they are not outweighed by a high evidence count.
3. **Not user-overridden.** `user_overridden == false`. If the user has ever rejected or
   contradicted this pattern, omp does not keep re-proposing it. The user's "no" is durable.
4. **Stability over time.** `first_seen` and `last_seen` should span more than a single
   session/event burst where feasible — a pattern seen 3× in one minute is weaker evidence
   than one seen across several sessions. (Soft criterion: `rule-architect` notes it; a
   same-session burst still qualifies if 1–3 hold, but is flagged as "burst evidence" at the
   gate so the human can judge.)
5. **Non-contradiction with existing rules.** The proposed rule must not contradict a rule
   already in `rules.json` unless it is explicitly framed as a *replacement* (specializing a
   preset rule into a project rule — see §4). Silent contradictions are never auto-resolved.

`rule-architect` outputs, per ripe candidate: the exact `rules.json` edit, the
specificity delta (§4), the provenance id, and a one-line rationale citing the evidence.
**It then stops at the gate.** Nothing reaches `rules.json` without explicit human approval.

Candidates that fail any condition stay `candidate` (keep accruing) — they are not rejected.
Only the human (or a clear counter-example) sets `status: rejected`.

---

## 4. Specificity — what the `0..1` number means and how it's computed

`rules.json.specificity` is a single number in `[0, 1]` that answers: **"how much of this
project's rule set is owned by the project itself, versus inherited unchanged from the
generic preset?"** It is the quantitative trace of the generic→specialized journey.

- **specificity = 0** — just deployed. Every rule came verbatim from a
  `references/presets/*.md` seed. omp knows the *kind* of project but nothing project-unique.
- **specificity = 1** — fully specialized. Every active rule was either authored against this
  project (via `omp-init` inductive scan) or promoted from a learned observation. No rule is
  an untouched preset default.
- **in between** — a mix: some preset defaults still stand, some have been specialized or
  added through learning.

### Computation

Each rule entry (a `structure.directories[]` item, a `naming.patterns[]` item, an `ignore[]`
glob) carries an implicit **origin**:

| origin | how it got there | weight toward specificity |
|:---|:---|:---|
| `preset` | copied verbatim from a `presets/*.md` seed at init | 0.0 (generic) |
| `inductive` | authored at init from `project-scanner`'s real-tree scan | 1.0 (project-specific) |
| `learned` | promoted from a `learned.md` observation through the gate | 1.0 (project-specific) |

Then:

```
specificity = (number of rules with origin in {inductive, learned})
              ─────────────────────────────────────────────────────
              (total number of rules)
```

i.e. the **fraction of active rules that are project-owned** rather than untouched preset
defaults. (Implementations may weight rule *types* if a project has many trivial rules of
one kind; the default and the contract is the simple unweighted fraction above. Whatever the
weighting, `specificity` MUST be monotonic: a promotion can only raise or hold it, never
silently lower it.)

### When it moves

- **`omp-init`** sets the initial value. A folder that perfectly matched a preset starts near
  0; a folder whose real structure the scanner had to encode inductively starts higher.
- **Each accepted `omp-learn` promotion** flips one rule's effective origin from `preset` to
  `learned` (or adds a new `learned` rule), then recomputes — so the number rises toward 1.
- **`omp-codify`** recomputes whenever the rule set changes.

This is the "기술적 정의" from Design §4 made operational: *"specificity 0(순수 프리셋)→1(완전
고유). learn 승격마다 프리셋 규칙이 프로젝트 규칙으로 대체·확장."* The number is not cosmetic —
it lets a human (and `omp-audit`) see at a glance whether `.omp/` still mostly speaks
generic-preset or has genuinely learned this project.

---

## 5. The obsidian / second-brain analogy (wiki = backlinked notes recalled by grep)

omp's identity is "a second brain that knows your local directory." The `wiki/` is that
second brain's **note layer**, and it is modeled directly on Obsidian:

- **`wiki/<topic>.md` = a note.** One Markdown file per topic (a dataset, a subsystem, a
  recurring decision). Stages auto-append observations and decisions to the relevant note.
- **`[[backlinks]]` = cross-references.** Notes link to each other and to real paths with
  Obsidian-style `[[wiki-link]]` text. A note about `train.parquet` links `[[data-pipeline]]`;
  the decision note links back. Backlinks are plain text — no database, no index to corrupt.
- **grep = recall.** Next session, omp does not "search its memory" with a model. It runs
  **deterministic grep** over `wiki/` for the terms relevant to the current task, and injects
  the matching notes as context. This is the obsidian "open the backlinked note" gesture,
  done mechanically.

Why this matters: the recall is **reproducible and inspectable**. The same query returns the
same notes every time; a human can run the identical grep and see exactly what omp will
recall. There is no opaque ranking, no embedding drift, no possibility of recalling a note
that does not literally contain the queried terms. The second brain remembers *only what was
actually written*, and recalls it *only by literal match*. That is the entire trust model.

**Wiki notes are append-only.** When a stage revisits an existing `wiki/<topic>.md`, it
*appends* (preferably as a dated `## <ISO date> — <one-line>` section), never rewrites or
truncates the file. Whole-file overwrite is reserved for the paired SSOT docs
(`PROJECT.md` / `STRUCTURE.md` / `NAMING.md` / `DATASETS.md`, regenerated wholesale by
`omp-doc`/`omp-codify`) — *never* for a wiki note. The light channel must accrue, not
replace: a revisited topic deepens (old observation + new section coexist as a ledger the
human reads as an evolution), it does not get clobbered. This mirrors how the heavy channel
already treats `learned.md` (the append-only observation ledger, §2), so both channels share
one append discipline — knowledge accrues without loss. (The `## <date>` heading is a *soft*
convention, not a schema: it is free-form grep-able prose, never a parsed frontmatter field —
§6.A's "no database, no index" trust model is untouched.)

(The light channel is intentionally low-ceremony: a wiki note is never load-bearing for an
enforced rule. If a wiki insight should *become* enforceable, it must be restated as an
observation in `learned.md` and travel the heavy channel through the human gate. The wiki
informs; it does not legislate.)

---

## 6. Anti-patterns (forbidden — these break the trust model)

These are hard prohibitions. omp's value collapses if any is violated, because each one
trades a deterministic, inspectable mechanism for an opaque one that can fabricate.

### A. No embedding / semantic search for recall
Recall over `wiki/` and `learned.md` is **deterministic grep only**. omp MUST NOT use vector
search, embeddings, or any similarity-ranked retrieval to decide what to remember or recall.
Rationale: embedding recall can surface a note that does not literally support the claim, or
silently rank a fabrication above a fact — the same hallucination/citation-unsafe failure
mode that bans parallel generation on citation-bound work elsewhere in this household. omp
recalls *exactly and only* what was written, found by literal match. (This mirrors oms/omd's
"citation 안전" principle, applied to project memory: a recalled note is a citation to
something that exists on disk.)

### B. No auto-promotion without the human gate
A `learned.md` observation MUST NOT become a `rules.json` rule without explicit human
approval — no matter how high its `evidence_count`. There is no `evidence_count` so large
that it bypasses the gate; there is no "high confidence" auto-merge. `rule-architect`
proposes; the human disposes. The gate is not advisory friction — it is the load-bearing
safety boundary, because a promoted rule can drive `omp-organize` to move files.

### C. No silent rule changes
Every change to `rules.json` MUST be (1) traceable to its origin — a promoted observation
records its id in `learned_refs[]`, an init-time inductive rule records `origin: inductive`;
(2) reflected in the paired `.md` (`STRUCTURE.md` / `NAMING.md`) in the **same pass**, so
the human-readable and machine-readable forms never diverge; and (3) accompanied by a
recomputed `specificity`. A rule that appears in `rules.json` with no provenance, or that
contradicts its paired `.md`, is a protocol violation — `omp-audit` should flag it.

### D. (Corollary) No enforcement from the light channel
A `wiki/` note MUST NOT be treated as an enforceable rule. It is context only. Acting on a
wiki note as if it were a rule (e.g. moving files because a note "decided" something) bypasses
both the evidence test (§3) and the human gate (§B). To enforce, escalate to `learned.md`.

### E. (Corollary) No fabricated evidence
An entry in `learned.md` MUST cite real, enumerable paths/events in `evidence[]`. omp does
not invent supporting files to reach the `≥ 3` threshold, and does not "round up" a count.
If the evidence is not on disk, the observation does not exist. (Constraints §3: "추측 금지.")

---

## 7. End-to-end trace (how a real specialization happens)

Putting it together — the canonical lifecycle of one learned rule:

1. **init** — `omp-init` synthesizes (a) `project-scanner`'s inductive scan of the real tree
   + (b) the best-matching `presets/*.md`, drafts `rules.json`, human approves. `specificity`
   starts at, say, 0.3 (mostly preset, a few inductive rules). `.pkl` files have no rule yet.
2. **operation** — across sessions, `omp-audit` / `omp-organize` keep noticing every `.pkl`
   under `data/processed/`. Each sighting appends to `OBS-0007` in `learned.md`:
   `evidence_count` climbs 1 → 2 → 3 → 4, `counter_examples` stays 0, `last_seen` advances.
   In parallel, the *decision* "we keep the scaler.pkl even though it's regenerable" is a
   cheap note → it auto-appends to `wiki/data-pipeline.md` (light channel, no gate).
3. **learn** — `omp-learn` runs. `rule-architect` checks `OBS-0007` against §3: count ≥ 3 ✓,
   counter-examples 0 ✓, not user-overridden ✓, stable across sessions ✓, no contradiction ✓.
   It drafts the `naming.patterns[]` edit + a specificity bump, records provenance, **stops at
   the gate**.
4. **gate** — the human approves. `omp-codify` writes the rule into `rules.json`, sets
   `OBS-0007.status: promoted`, adds `OBS-0007` to `rules.json.learned_refs[]`, regenerates
   `NAMING.md`, and recomputes `specificity` upward (e.g. 0.3 → 0.36). One preset-shaped
   project rule is now genuinely project-owned.
5. **enforce** — from now on `omp-audit` flags any `.pkl` placed outside `data/processed/`,
   and `omp-organize` can propose moving it back (through `safe-fileops.md`, with its own
   move-time human approval). The second brain has specialized — and every step is on disk,
   inspectable, and reversible.

---

## See also

- `references/output-layout.md` — where `.omp/` files live; the .md ↔ .json pairing rule.
- `references/schemas/rules.schema.json` — machine shape of rules (`specificity`,
  `learned_refs`, structure/naming entries).
- `references/schemas/manifest.schema.json` — dataset inventory (separate from learning).
- `references/safe-fileops.md` — the move-time protocol any enforced rule ultimately invokes.
- `references/presets/*.md` — the generic seeds that specialization starts from.
