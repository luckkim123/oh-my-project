# Changelog — oh-my-project (omp)

All notable changes to this harness. Hook contract changes are recorded explicitly
(siblings oms/omd treat the route/verify hook text as a versioned contract).

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
  channel (`.omp/wiki/`) always *intended* accumulation ("쓸수록 특화", "accrue freely"),
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
