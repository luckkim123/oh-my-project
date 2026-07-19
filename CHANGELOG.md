# Changelog — oh-my-project (omp)

All notable changes to this harness. Hook contract changes are recorded explicitly
(siblings oms/omd treat the route/verify hook text as a versioned contract).

## [Unreleased]

### Fixed

- **`ready_to_promote`'s `counter_examples` parse failure now blocks promotion instead of
  permitting it.** A malformed/non-numeric `counter_examples` value fell back to `0` —
  "no counter-examples" — which is exactly the state the §3.2 hard blocker is supposed to
  rule out, so garbage data could silently satisfy the promote gate. The `ValueError`
  fallback now leaves the candidate unable to match the `== 0` check (fail conservative,
  not permissive); 1 new blocking test.

## [0.6.1] — 2026-07-16

### Fixed

- **`ready_to_promote` now implements learning-protocol §3's hard blockers, not just the
  evidence threshold.** A candidate with `counter_examples > 0` (kills promotion outright,
  §3.2) or `user_overridden: true` (the user's "no" is durable, §3.3) no longer surfaces as
  ripe — previously both were ignored, so omp-brief/omp-handoff could present a
  user-rejected or violated pattern as "run omp-learn or defer" (2026-07-16 wiki-week
  review, HIGH). §3's non-contradiction criterion deliberately stays at the human gate —
  the independent `contradiction` finding surfaces it. Docstring + omp-audit/omp-brief/
  omp-handoff wording updated to match; 2 new blocking tests.

## [0.6.0] — 2026-07-14

### Added

- **Actionable-knowledge carry-forward (family wiki-status convention)** (`hooks/omp_content_audit.py`,
  `skills/omp-brief/SKILL.md`, `skills/omp-handoff/SKILL.md`, `tests/test_omp_content_audit.py`) — omp's
  adaptation of the om*-family fix for the failure class where an actionable item is recorded in the
  knowledge store yet silently dropped from the next summary. omp keeps its schema unchanged (wiki
  notes are deliberately schema-less; `learned.md` OBS blocks already carry `status`/`evidence_count`),
  so this is a derived-enumeration + prompt-reconcile change, not a new status field.
  - `lint_wiki()` gains a `ready_to_promote` finding: a `learned.md` candidate that reached
    `evidence_count >= 3` is ripe for `omp-learn` promotion. Previously such a candidate produced NO
    finding at all (`stuck_candidate` fires only below threshold), so it was invisible to
    enumeration — exactly the gap this closes. Derived from existing fields; the omp-learn human gate
    still decides.
  - `omp-brief` (step 2) and `omp-handoff` (step 2) now reconcile the next-session goal / delegation
    packet against the open actionable findings from `lint_wiki()` (`ready_to_promote`,
    `stuck_candidate`, `contradiction`): each open one is reflected or consciously deferred, never
    silently omitted. Enumeration-only, WARN-level — omp never hard-gates on the wiki.

### Changed

- `.claude-plugin/plugin.json`: `version` 0.5.0 → 0.6.0.

## [0.5.0] — 2026-07-11

### Added

- **`secretary.sources[]` read-map** (`references/schemas/rules.schema.json`, `references/secretary-protocol.md`) — registers existing project state surfaces (Kanban board, daily-notes dir, status table) as counted sources rather than duplicating them under `.omp/secretary/`. Kinds: `todo`/`schedule` are count-parsed (todo.txt lines / markdown checkboxes; `path` may be a file or a directory — directory sums non-recursive `*.md` open-counts), `journal`/`status` are read-map only (no count). `derive_status(root)` return gains a `"sources"` key. Registration only through the `omp-codify` human gate (D14) — never auto-discovered or auto-registered.
- **`omp-organize` para preset — §7 source proposal table** (`references/presets/para.md`) — when running the `para` preset, dry-run move plans now propose known state surfaces as `secretary.sources[]` codify candidates (a table the human reviews at the codify gate, not an auto-write).
- **`omp-organize` wikilink inbound counts** — para dry-run move plans now show each note's wikilink inbound count alongside the move, surfacing orphan/hub notes before relocation.
- **`omp-handoff` skill** (`skills/omp-handoff/SKILL.md`) — a delegation-briefing assembler run once immediately before handing work to a sibling harness (oms/omd/omx/omc/superpowers). Assembles an Anthropic multi-agent 4-element knowledge packet (Objective / Output format / Tool·source guidance / Boundaries) from existing omp state (`todo.txt`/`raid.md`, `output-layout.md`, PROJECT.md + wiki grep-by-topic + `derive_status(root)["sources"]`, rules.json + open raid blockers) — references only, never inlines full source documents. Produces three artifacts in one pass: a session-consumed briefing block, an audit copy under `.omp/work/handoffs/YYYY-MM-DD-<target>.md` (retention 10, self-trimmed), and a ledger `handoff_prepared {target, topic}` event. `omp_route_emit.py` STAGE catalog gains `handoff` (13 → 14 stages); does not decide the delegation lane (omha's role, unchanged, §11.3).
- **`omp-log` handoff-return absorption** — a sibling harness's compressed return digest (1–2k tokens) is absorbed into `omp-log`'s existing five destinations rather than a new sixth one; not enforced (R5).

### Changed

- `.claude-plugin/plugin.json`: `version` 0.4.0 → 0.5.0; `skills[]` gains `omp-handoff` (13 → 14); description gains the two 0.5.0 capabilities.
- `hooks/omp_route_emit.py` **CHECKPOINT text changed** (hook contract — siblings oms/omd treat this as versioned): STAGE catalog line now enumerates `...|log|brief|review|handoff|omp-pilot|omp-doctor` (13-way → 14-way).
- README.md: skill table 13 → 14 rows (adds `omp-handoff` under the secretary skeleton), "13 skills" status line → "14 skills", secretary axis section gains a sources read-map / delegation-handoff / wikilink-inbound-counts summary.

### Notes

- D8 (derived-only status, no LLM estimate) extends to `secretary.sources[]`: counts come from `count_source_open`, never an LLM guess.
- D12 (handoff is same-context consumption, not IPC) — the session-in briefing block is the primary artifact; the `work/handoffs/` copy is audit-only.
- D14 (registration is human-gated) — `secretary.sources[]` entries are proposed by presets/organize but only written through `omp-codify`'s approval gate, same as structure/naming rules.
- §11.3 (omp does not pick the delegation lane) is unchanged by `omp-handoff` — it assembles the packet strictly after omha has already decided the target lane.
- R6 (registering the vault's own `secretary.sources[]` against this feature) is a human-gated operational act performed in the vault's own `.omp/`, not part of this repo's release.
- `omha` `cards/omp.json` route-catalog sync (the `handoff` STAGE) is a separate commit in the `oh-my-heroacademia` repo (R7), out of scope for this release.

### Verification

- `python3 -m pytest -q` — 122 passed (15 new tests over 0.4.0's 107: secretary sources schema + `derive_status` aggregation + directory-source support, para preset/organize content, omp-handoff integrity/contract sync).

## [0.4.0] — 2026-07-11

### Added

- **Secretary axis (time)** — a second axis alongside the existing governance axis (space), sharing the same `.omp/` SSOT, hook layer, and generic→specialized loop. Adds session journal, todo/RAID, decisions, and pull-style briefing under `.omp/secretary/`.
- **3 new stage skills** (`skills/omp-log`, `skills/omp-brief`, `skills/omp-review`):
  - `omp-log` — universal capture router, one entry point / five destinations (journal, todo.txt, raid.md, decisions/ ADR, rule observation).
  - `omp-brief` — pull-style briefing; regenerates `.omp/secretary/BRIEF.md` from ledger/todo/raid/journal state (traffic light, state-of-play, top-5 tasks, open blockers, next-session goal, decision paths) — every number is `derive_status(root)` output quoted verbatim, never an LLM estimate (D8).
  - `omp-review` — weekly (or on-demand) re-evaluation: BuJo-style migration for every open `todo.txt` task (migrate/strike/done, human-judged per item, never auto-carried-over), a `scan_stale` sweep, `raid.md` re-triage.
- **1 new agent** (`agents/chronicler.md`, sonnet) — the sole LLM writer of `.omp/secretary/**` (journal narrative, `decisions/`, `todo.txt`, `raid.md`, `BRIEF.md`). Never writes `ledger.jsonl` or the hook's session-stub lines (D7, disjoint at the line level); never closes a task/blocker (D9); never writes a progress percentage (D8).
- **`hooks/omp_secretary.py`** — pure-function core (stdlib only) for the secretary axis: ledger append/parse, `derive_status(root, sources=None)`, `scan_stale`, `redact_secrets`, journal tag extraction, session-stub construction. `sources=None` keeps Part I behavior unchanged and opens the signature for a future `secretary.sources[]` extension (design v3 footnote) without rework.
- **2 new session hooks**: `omp_session_brief.py` (SessionStart) — advisory-only injection of `.omp/secretary/BRIEF.md` (≤30 lines) when present, silent otherwise, never auto-resumes work; `omp_session_capture.py` (SessionEnd) — appends a machine-only journal session-stub once per session, no LLM involved, ascends to find `.omp/` root, redacts before write.
- **`.omp/secretary/` layout** (`references/secretary-protocol.md`, new; `references/output-layout.md` §addition) — `ledger.jsonl` (append-only event log: `task_added|task_done|blocker_opened|blocker_closed|decision_recorded|gate_passed|session_start|session_end`), `journal/YYYY-MM-DD.md`, `todo.txt`, `raid.md`, `decisions/`, `BRIEF.md`.
- **Secretary hygiene audit axis** (warn-default, in `omp_content_audit.py`/`auditor`) — reuses `scan_stale`/`brief_hash_check` to flag stale tasks/blockers, BRIEF drift, and sync-conflict copies (e.g. `ledger 2.jsonl`) under `.omp/secretary/**`.
- **Governance-side wiki/learned.md lint** (warn-default) — 6 mechanical checks (orphan, stale, broken-ref, oversized, stuck-candidate, structural-contradiction) plus a `scan_structure_drift` sweep, both reusing secretary pure functions; no auto-promotion or auto-deletion.
- **Route/hook wiring** — `omp_route_emit.py` STAGE catalog gains `log|brief|review` (13 stages total); `OMP_SKIP_HOOKS` kill-switch unified across all four hooks; `omp_verify_emit.py` gains a content-hash advisory throttle (`.omp/state/verify-throttle.json`) so repeated organizer batch-moves don't re-fire the same reminder.
- **Existing-stage integration** — `omp-init` creates the `.omp/secretary/` skeleton by default (GATE 1 note), `omp-pilot` runs `omp-brief` once at the end, `omp-doc`/`omp-codify` cross-reference secretary sources, `omp-doctor` checks the two new hooks are registered.

### Changed

- `.claude-plugin/plugin.json`: `version` 0.3.0 → 0.4.0; `skills[]` gains `omp-log`/`omp-brief`/`omp-review` (10 → 13); `hooks` gains `SessionStart` (`omp_session_brief.py`) and `SessionEnd` (`omp_session_capture.py`) entries alongside the existing `UserPromptSubmit`/`PostToolUse`; description now names the secretary axis.
- README.md: skill table 10 → 13 rows, agent table 5 → 6 rows (adds `chronicler`), roster summary line, new "Time — secretary skeleton" section alongside the existing "Space — stage skeleton" section.

### Notes

- Secretary content is strictly human/hook-authored, never LLM-estimated: `chronicler` writes narrative and judgment only; every status figure traces to `derive_status`; no task/blocker auto-closes (D9); journal/ledger are append-only, never truncated (D6).
- Sibling propagation reviewed and rejected — oms/omd are output-per-artifact generation pipelines with no daybook/session-journal concept; the secretary axis is unique to omp's "living folder, revisited over many sessions" identity (recorded in `references/omc-backport-analysis.md` §6 and `learning-protocol.md`'s "Secretary-axis boundary" section).
- `omha` `cards/omp.json` route-catalog sync (log/brief/review verbs) is a separate commit in the `oh-my-heroacademia` repo, out of scope for this release.

### Verification

- `python3 -m pytest -q` — 107 passed (40 new tests over 0.3.0's 67: secretary pure-function core, ledger schema round-trip, `derive_status`/`scan_stale`, redaction, chronicler write-scope contract, session hook fail-open/once-per-session/advisory-only, route STAGE 12-way enumeration, plugin skill/hook registration round-trip, governance lint axis).

## [0.3.0] — 2026-06-21

### Added

- **omp-env stage** — environment assets (Dockerfile/compose) canonical into `.omp/env/`; generation gate (dry-run → approval → verification), personal-value resolver, in-place invariant preserved.
- **docker environment governance** — `rules.json` `docker_naming` (optional), `manifest.json` `docker_images[]` (optional, external ref), `omp-audit` docker axis (`hooks/omp_docker_audit.py`, warn-default, rule-id-as-data: DL3007/secret-in-env/compose-version).
- **provenance tracking** — rule `origin:standard` + `provenance` object (OCI/CIS/SemVer and other external standards; MUST→error / SHOULD→warn) + `standards_registry`. New data file: `references/standards-registry.seed.json`.
- **docker preset** (`references/presets/docker.md`) + **`docker-mechanisms` reference card** (`references/docker-mechanisms.md`) — scaffold/inventory methodology, multi-user server patterns, pitfalls, remote-training knowledge (absorbed from claudebase docker-env skill, personal values removed).

### Changed

- omp identity: "folder governance" → "project environment + structure governance" (output-layout.md constitution fence: `.omp/env/` SSOT, root holds build-tool view only).
- `omp-codify` (docker_naming + provenance), `omp-dataset` (docker_images[]), `omp-audit` / `auditor` (docker axis, image-drift exception handling).

### Notes

- claudebase `docker-env` skill is absorbed into omp and scheduled for removal (single ownership).
- All new schema sections (`docker_naming`, `docker_images[]`, `provenance`, `standards_registry`) are optional — existing `.omp/*.json` files remain fully backward-compatible.

### Verification

- `python3 -m pytest -q` — 67 passed (18 new tests covering docker audit axis, docker_images schema, provenance schema, standards_registry, omp-env generation gate).

---

### Changed (Unreleased pre-0.3.0 carry-in)

- **Clarified the dataset definition to be format-agnostic (role-based) — blocks the "dataset = ML input file" misreading (code/schema unchanged, prompts only).**
  In real use, when trying to register a ROS bag or experiment data, *every example* across the skills/agents was filled
  with a single structured ML pipeline like `train.parquet`/`rows`/`.csv`, leaving a gap where "dataset = tabular ML input"
  got narrowly induced; this fills that gap. The schema (`manifest.schema.json`) already makes `rows`/`split`/`lineage`
  all optional, so it can already accommodate unstructured data — the problem was not the *rules* but the *biased example
  distribution*, so the schema/code logic stays unchanged and only the definition/example wording was strengthened:
  - `skills/omp-dataset/SKILL.md`: in `<Use_When>` and `<Steps>`, demoted the extension enumeration to *examples* and
    added unstructured ones (`.bag`/`.db3`/`.png`/`.mp4`/`.pcd`) alongside. Added a one-liner: "dataset discrimination
    criterion = role, not format (is it a fixed, tracking-worthy input/collected data?)" — `.npy` produced every run = run
    artifact (out of scope), `.bag` one-time collection = dataset (in scope).
  - `agents/dataset-curator.md`: added a new paragraph at the Role source point — "What counts as a dataset is defined by
    ROLE, not format" (explicitly naming robotics/sensor/media). Changed the extensions in the Investigation_Protocol from
    a whitelist to a hint, reinforced the `rows` tabular-only wording with "omission is normal for unstructured data," and
    added a ROS bag registration pair to the Good/Bad examples (skipping `.bag` for format reasons = Bad). 47 tests pass
    (documentation change, 0 regressions).
- **Prevent index drift after organize — codified that "a move that changes structure is one task that includes syncing the `.omp/` index" (hook contract change).**
  In real use, after a folder rename/flattening (`12_Theses_Defense` → `12_Masters_Thesis` + abolishing the intermediate
  layer), `.omp/STRUCTURE.md`/`rules.json`/`DATASETS.md` were left pointing at the old paths, forcing the user to explicitly
  instruct "update the index too"; this fills that gap. Strengthened three places at the guidance/wording level only (code
  logic unchanged):
  - `skills/omp-organize/SKILL.md`: added Step 8 (index sync) — if a moved folder is written by name in rules.json/STRUCTURE.md,
    syncing is part of the definition of organize completion (simple path substitution = direct Edit, changing rule meaning =
    codify gate). No-op if structure is unchanged. Reflected in "order unchanged" and Output as well.
  - `hooks/omp_route_emit.py`: added a one-liner to CHECKPOINT — "⚠️ index consistency" — finish the `.omp/` update within
    the same task after a structure-affecting move or a bare-hand mv (no drift). Existing STAGE/NO_OMP markers unchanged.
  - `hooks/omp_verify_emit.py`: added a one-liner to the PostToolUse reminder — "if it's a move that changed structure, the
    index update is part of this task." Avoids freeze-inducing wording ("fix before continuing") (suggestion → completion-condition
    tone only). 49 tests pass.
- **Added `references/omc-backport-analysis.md` §5 — sibling propagation review of 0.2.0 additions (propagation 0).**
  Adversarially verified (15 pairs) whether the 5 items 0.2.0 added (content_conventions, content audit, dead-link,
  CONVENTIONS.md, the specificity content term) should propagate to oms/omd/omx → all REJECT. All 5 depend on omp's
  "living `.omp/` management loop" identity and have no place in the generation-pipeline siblings (intended absence).
  Permanently recorded the "nothing to propagate" conclusion to prevent repeated re-review. The per-sibling isomorphism
  verdict is recorded in oms/omd `omc-backport-analysis.md` §4 (omx is self-contained/has no docs, so only in the sibling
  record). 0 code changes — docs only.

## [0.2.1] — 2026-05-31

### Fixed

- **`find_dead_links`: Obsidian table-escaped pipe `[[Note\|alias]]` no longer
  false-flagged as dead** (was capturing the trailing backslash into the target,
  e.g. `Perceptron\`, which never matched the stem set). Table cells escape the
  alias separator as `\|`; the target is now normalized by stripping a trailing
  backslash before resolution. Found via real-vault audit (67 false positives → 0).

## [0.2.0] — 2026-05-31

### Added

- **`content_conventions[]` rule type** (`references/schemas/rules.schema.json`) — note-body
  authoring rules the structure/naming axes could not express: `check.pattern` (Python `re`)
  × `expect` (present/absent) × `scope` (body/frontmatter), with `applies_to` glob, `origin`,
  `severity`. Optional top-level key → every existing rules.json stays valid (backward-compatible MINOR).
- **content + wikilink audit axes** — `hooks/omp_content_audit.py` (`check_content_rule`,
  `find_dead_links`, `split_frontmatter`), pure stdlib, the canonical algorithm the `auditor`
  agent now invokes. Content axis is enforced (error/warn/info → error fails the gate); wikilink
  integrity is a health hint (info, never fails the gate). Absorbs the downstream `link-checker`
  validator (preserves its case-insensitive resolution and non-md embed handling).
- **`.omp/CONVENTIONS.md`** — human-readable narrative paired with
  `rules.json.content_conventions[]`, alongside STRUCTURE.md/NAMING.md. Created by codify/learn
  only when content_conventions exist (not an init invariant).

### Changed

- `specificity` now counts `content_conventions[]` entries (learning-protocol §4) — content
  rules with origin inductive/learned raise specificity like structure/naming rules. Formula
  and monotonic property unchanged.
- `learned.md` `candidate_rule.target` enum gains `content_conventions[]` — content observations
  travel the heavy channel through the human gate, never the light wiki channel.
- `omp-codify` / `omp-learn` / `rule-architect` handle the new type; `auditor` / `omp-audit`
  gained the content + wikilink axes.
- **`learning-protocol.md` §5 — wiki append-only discipline made explicit.** The light
  channel (`.omp/wiki/`) always *intended* accumulation ("more specialized the more you write", "accrue freely"),
  but never wrote the binding rule that a revisited `wiki/<topic>.md` is *appended* (not
  rewritten/truncated) and that whole-file overwrite is reserved for the paired SSOT docs
  (PROJECT/STRUCTURE/NAMING/DATASETS), never for a wiki note. Adjacent in `omp-doc`, the
  same controller is told to whole-overwrite the human .md docs — this clause forecloses
  that habit bleeding into the light channel. The `## <date>` section heading is a *soft*
  free-form convention, **not** a frontmatter schema (§6.A's "no database, no index" trust
  model is untouched). Echoed in `skills/omp-doc/SKILL.md` where both instructions sit
  together. Sourced from a cross-harness analysis against **omx** (oh-my-experiments) wiki,
  whose INV-2 append-merge invariant (e2e-verified) proved the discipline; omp adopts the
  written rule only — none of omx's engine (file-locks, frontmatter schema, scoring/lint)
  transfers (single-writer, free-form-grep domain — correctly rejected).

### Verification

- `python3 -m pytest -q` — 48 passed (schema content_conventions validation + content/link
  pure-function tests: present/absent × body/frontmatter, dead-link detection, case-insensitive
  resolution, non-md embed skip, CRLF frontmatter).
- Backward-compat: existing rules.json validate unchanged (content_conventions optional).

## [0.1.0] — 2026-05-30

Initial implementation. Project-folder management & evolution harness — sibling of
oh-my-scholar (oms) and oh-my-docs (omd), modeled on their verified stage-driven golden.

### Added

- **9 stage skills** (`skills/omp-*/SKILL.md`): init, codify, organize, dataset, doc,
  learn, audit, pilot, doctor — a management loop, not a generation pipeline.
- **5 agents** (`agents/*.md`, 11-section `<Agent_Prompt>` XML):
  - `project-scanner` (sonnet, read-only) — inventory + inductive structure/naming scan
  - `rule-architect` (opus, read-only) — preset×scan synthesis, promotion judgment
  - `organizer` (sonnet, write) — the ONLY file-moving agent; obeys safe-fileops.md
  - `dataset-curator` (sonnet, write manifest) — checksum/split/lineage, metadata-only
  - `auditor` (opus, read-only) — rule-compliance PASS/FAIL, detection-only
- **7 preset cards** (`references/presets/`): python-ml, web-app, research-lab,
  monorepo, johnny-decimal, para, generic — generic seeds for the "ships generic" half.
- **4 reference cards** (`references/`): safe-fileops.md (organizer's hard protocol),
  output-layout.md (.omp/ path SSOT), omc-backport-analysis.md (OMC adopt/exclude),
  learning-protocol.md (the generic→specialized self-evolution SSOT).
- **2 machine schemas** (`references/schemas/`): rules.schema.json (with `specificity`
  0..1 tracking generic→specialized), manifest.schema.json (metadata-only datasets).
- **4 hook-layer files** (`hooks/`, stdlib-only, fail-open, cross-platform) — 2 passive
  hooks + 1 write helper + package init (the lean identity stays "2 passive hooks"):
  - `omp_route_emit.py` (UserPromptSubmit) — injects `STAGE(project) → …` checkpoint; also
    appends a one-line "no `.omp/` yet — run omp-init first" hint when cwd lacks `.omp/` (T25).
  - `omp_verify_emit.py` (PostToolUse) — integrity reminder after `.omp/` edits or
    move/delete commands. Deliberately avoids the freeze-inducing "fix before
    continuing" phrasing (OMC freeze pattern); reminder tone only, never auto-fixes.
  - `omp_atomic.py` — `atomic_write_json` helper (tempfile→fsync→os.replace) for `.omp/`
    SSOT writes; not a hook, a library the writing skills route through (T20).
  - `__init__.py` — package marker so the helper/tests import cleanly.

### Hook contract

- `omp_route_emit.py` STAGE catalog = `init|codify|organize|dataset|doc|learn|audit|omp-pilot|omp-doctor` (9 stages).
- `omp_verify_emit.py` fires on `Edit|Write|MultiEdit|Bash`; reminds only on `.omp/`
  paths (incl. Windows `\` separators) or move/delete commands; silent otherwise.

### Verification

- `tests/` — 34 passed, 1 skipped (jsonschema optional). Covers: route 9-stage
  enumeration, fail-open, sibling-label distinctness (STAGE(project) ≠ paper/docs/ROUTE),
  no-emoji, stdlib-only; verify .omp/ detection, move detection, silence on unrelated
  work, **no-freeze-phrase**, Windows path, no-auto-fix; schema validity, specificity
  bounds, metadata-only manifest, SHA-256 determinism + pattern match.

### Deployment

- **omha routing: no card** — omp is a 2nd-tier domain handler, exactly like siblings oms/omd
  (omha `cards/` holds only the tier-1 *how-you-work* lanes: omc, superpowers). omp is routed via its
  own `hooks/omp_route_emit.py` (`STAGE(project) → …`) plus its `plugin.json` description landing on
  omha's 2nd-tier domain-skill path. omha core / omc / superpowers cards stay untouched. (Card-tier
  rationale: design §6 re-review correction. The earlier `cards/oh-my-project.json` was removed via trash.)
- **Marketplace registration + git push: done.** The harness is pushed to the GitHub source
  (`luckkim123/oh-my-project`, public) and registered in heroacademia's
  `.claude-plugin/marketplace.json` alongside siblings oms/omd, with `oh-my-project@heroacademia`
  enabled in claudebase `config/settings.json` — installable like the other siblings.

### Notes

- **runtime end-to-end not yet measured** — Claude Code does not reload plugins mid-session;
  a fresh session is required to load the skills/hooks and exercise the full loop.
- Identity axis unique to omp (absent in oms/omd): the **generic→specialized** evolution
  — logic stays generic, the per-project `.omp/` diverges (see learning-protocol.md).
