# Changelog — oh-my-project (omp)

All notable changes to this harness. Hook contract changes are recorded explicitly
(siblings oms/omd treat the route/verify hook text as a versioned contract).

## [Unreleased]

## [0.3.0] - 2026-06-21

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
