# oh-my-project (omp)

> Multi-agent orchestration harness for **project-folder management & evolution** — a second brain that knows your local directory. Ships **generic**, specializes to **your** project the more you use it.

Lineage: [`oh-my-claudecode`](https://github.com/Yeachan-Heo/oh-my-claudecode) (omc) → `oh-my-docs` (omd) → `oh-my-scholar` (oms) → **`oh-my-project` (omp)**

## Philosophy — a folder ≈ living knowledge

If oms/omd are generation pipelines that **produce a fresh artifact every time**, omp is a management loop that **continuously updates a single living `.omp/`**. Where `claude /init` spits out a one-shot snapshot, omp is an assistant that grows more specialized to that folder the more you use it.

| Generic init | omp |
|:---|:---|
| One-time scan → static document | One-time scan → living `.omp/` → evolves the more you use it |
| Identical across every project | Generic on delivery, specialized in use |
| Structure only | Structure + naming rules + dataset tracking |

## Core asymmetry — deliverable + specialized at the same time

```
Harness logic (skills·agents)    = generic·immutable (identical for all users)
Generic presets (references/presets) = generic seed     (provided by harness)
Specialized SSOT (<project>/.omp/)   = per-project divergence (specializes the more you use it)
```

The logic stays fixed and generic; only the artifact (`.omp/`) diverges per project. This asymmetry satisfies "deliverable + specialized" simultaneously.

## Install

Requires the [Claude Code](https://claude.com/claude-code) CLI. Two paths:

- **Via [`oh-my-heroacademia`](https://github.com/luckkim123/oh-my-heroacademia)** (omp is registered there as a sibling of oms/omd):
  ```
  /plugin marketplace add luckkim123/oh-my-heroacademia
  /plugin install oh-my-project@heroacademia
  ```
- **Standalone** (no other harness required — this repo is itself a Claude Code plugin via `.claude-plugin/plugin.json`):
  ```
  git clone https://github.com/luckkim123/oh-my-project.git
  claude --plugin-dir ./oh-my-project
  ```

## Two axes — space (structure) + time (secretary)

omp governs two axes of the same living `.omp/`: the original **space** axis (folder structure/naming/dataset/env rules) and the 0.4.0 **secretary** axis (session journal, todo/RAID, decisions, pull-style briefing). Both share one SSOT, one hook layer, one specialization loop — the secretary is not a separate tool bolted on, it is `omp-audit`/`omp-init`/`omp-pilot` extended to also track *when* and *what happened*, not just *where things live*.

### Space — stage skeleton (management loop)

```
  omp-init      One-time bootstrap — folder scan (inductive) + preset-matched synthesis → creates .omp/
       ━━━ GATE: approve draft rules.json ━━━
  omp-codify    Codify structure·naming rules (rules.json + STRUCTURE/NAMING.md)
  omp-organize  Detect rule violations → safe relocation (mv→verify→delete, via trash)
  omp-dataset   Register datasets·SHA256·split·lineage (manifest.json) — metadata-only
  omp-env       Environment assets (Dockerfile/compose) canonical into .omp/env/; generation gate, in-place preserved
  omp-doc       Generate·update human-facing docs (PROJECT.md etc.)
  omp-learn     Observation → rule promotion (human approval gate) ← the core of evolution
  omp-audit     Rule-compliance verification (read-only PASS/FAIL, space + secretary hygiene axes)
  omp-doctor    Installation/prerequisite self-diagnosis (hooks registered, python3 present, reference cards intact — PASS/WARN/FAIL, read-only, no auto-fix)
  omp-pilot     Full orchestration (absorbs init when no .omp exists)
```

### Time — secretary skeleton (session loop)

```
  omp-log       Universal capture router — journal/todo/raid/decisions/rule-observation, one entry, five destinations
  omp-brief     Pull-style briefing — regenerates .omp/secretary/BRIEF.md from ledger/todo/raid/journal (derive_status-only numbers)
  omp-review    Weekly (or on-demand) re-evaluation — BuJo-style todo migration, scan_stale sweep, raid.md re-triage
  omp-handoff   Delegation-briefing assembler — before handing work to a sibling harness (oms/omd/omx/…), packs a 4-element knowledge packet (Objective/Output format/Tool guidance/Boundaries) from existing omp state
```

Mechanical appends (`ledger.jsonl`, journal session-stubs) are hook-owned (`hooks/omp_secretary.py`); narrative (journal body, `decisions/`, `todo.txt`, `raid.md`, `BRIEF.md`) is written by the single scoped agent `chronicler` — the same "one writer per domain" invariant `organizer`/`dataset-curator` already establish for the space axis. No task/blocker is ever auto-closed and no progress percentage is ever LLM-written — both stay human-gated / code-derived (`derive_status`).

0.5.0 anchors the secretary further: `secretary.sources[]` lets `rules.json` register existing state surfaces (a Kanban board, a daily-notes dir, a status table) as counted read-map sources instead of duplicating them under `.omp/secretary/`, registered only through the `omp-codify` human gate; `omp-handoff` assembles a delegation-briefing packet immediately before handing work to a sibling harness, so the sibling doesn't have to rediscover this project from scratch; and `omp-organize`'s `para` preset dry-run plans now surface wikilink inbound counts alongside each proposed move.

## "Generic→specialized" evolution — 2 channels

Just as Obsidian is a second brain, omp recovers accumulated context via grep.

- **Heavy channel (rules)**: `learned.md` observations accumulate → `omp-learn` promotion decision → **human approval** → `rules.json` evolves (`specificity` rises 0→1)
- **Light channel (patterns/decisions)**: `.omp/wiki/*.md` accumulates automatically → recovered via grep in the next session (no approval needed)

Heavy goes through a gate, light is automatic — inheriting the wiki(automatic) vs gate(approval) split of oms/omd.

## `.omp/` SSOT (dual: human-readable .md + machine-readable .json)

```
<project>/.omp/
├── PROJECT.md     STRUCTURE.md   NAMING.md   DATASETS.md   ← read by humans
├── rules.json     manifest.json                            ← read by the audit hook
├── learned.md                                              ← observations awaiting promotion
└── wiki/                                                   ← auto-accumulated (recovered via grep)
```

## Agents (6)

| agent | model | permissions | role |
|:---|:---|:---|:---|
| project-scanner | sonnet | read-only | Folder inventory, inductive structure |
| rule-architect | opus | read-only | Rule design, preset synthesis, promotion decisions |
| organizer | sonnet | write | **The only file-moving agent** (enforces safety protocol) |
| dataset-curator | sonnet | write(manifest) | Checksums, splits, lineage (does not move data) |
| auditor | opus | read-only | Rule-compliance verification (detection only, no moving; space + secretary axes) |
| chronicler | sonnet | write(`.omp/secretary/**`) | **The only secretary-content writer** (journal narrative, decisions, todo.txt, raid.md, BRIEF.md — never ledger.jsonl, never closes a task/blocker, never writes a progress %) |

**Invariant contract**: only organizer moves files (writes are single-focused). Detection (auditor) ≠ execution (organizer) are kept separate. dataset is metadata-only (delegates when DVC/git-lfs is detected).

## Routing

omp is a **domain handler** (the project-management domain). Working-mode lane (SP/OMC) judgment is handled by [`oh-my-heroacademia`](https://github.com/luckkim123/oh-my-heroacademia) (omha) — omp does not decide the lane. After omha sets the lane, omp's UserPromptSubmit hook (`omp_route_emit.py`) declares which **STAGE** (init/codify/organize/…/log/brief/review) within the project domain on each turn with a single `STAGE(project) → …` line. The PostToolUse hook (`omp_verify_emit.py`) injects an integrity reminder after `.omp/` edits or file moves (it does not auto-fix or freeze). Two new session-scoped hooks round out the secretary axis: `omp_session_brief.py` (SessionStart) advisory-injects `.omp/secretary/BRIEF.md` when present (never auto-resumes), and `omp_session_capture.py` (SessionEnd) appends a machine-only journal stub once per session. All four hooks respect `OMP_SKIP_HOOKS` and fail open.

## Cross-platform

Mac / Linux / Windows. Every hook is **python3 stdlib only + fail-open** (errors never block the session), every path uses `pathlib` (OS-neutral), and deletions go through the per-OS trash.

## Status

v0.6.1 — 14 skills + 6 agents + 8 presets + 6 reference cards + hooks (`omp_route_emit`/`omp_verify_emit` runtime hooks + `omp_session_brief`/`omp_session_capture` session hooks + `omp_atomic` SSOT writes + `omp_content_audit` audit helper + `omp_docker_audit` docker axis + `omp_secretary` secretary pure-function core + `__init__`) + schema implementation. 0.6.1 fixes `ready_to_promote` to honor learning-protocol §3's hard blockers (`counter_examples`/`user_overridden`), so a rejected or contradicted candidate no longer surfaces as ripe for promotion in `omp-brief`/`omp-handoff`. 0.6.0 adds actionable-knowledge carry-forward: `lint_wiki()` gains a `ready_to_promote` finding for `learned.md` candidates past the evidence threshold, and `omp-brief`/`omp-handoff` reconcile their output against open wiki findings instead of silently dropping them. 0.5.0 anchors the secretary axis to existing state surfaces: `secretary.sources[]` (rules.json read-map — registers a Kanban board/daily-notes dir/status table as a counted source, `omp-codify` human gate only, counts always `derive_status`-derived) and adds delegation briefing (`omp-handoff`: a 4-element knowledge packet assembled before handing work to a sibling harness such as oms/omd/omx, STAGE catalog 13 → 14), plus wikilink inbound counts in the `para` preset's organize dry-run plans. 0.4.0 adds the **secretary axis (time)** alongside the existing governance axis (space): 3 new stages (`omp-log` capture router, `omp-brief` pull-style briefing, `omp-review` weekly BuJo-style re-evaluation), 1 new agent (`chronicler`, the sole `.omp/secretary/**` writer), 2 new session hooks (SessionStart advisory brief injection, SessionEnd machine-only journal stub), an append-only `ledger.jsonl` + journal/todo.txt/raid.md/decisions/BRIEF.md layout, and a secretary hygiene audit axis (warn-default) plus a governance-side wiki/learned.md 6-check lint and structure-drift scan. 0.3.0 added **docker environment governance**: the `omp-env` stage canonicalizes Dockerfile/compose assets into `.omp/env/` (generation gate, in-place preserved); a docker audit axis (`omp_docker_audit`, warn-default, rule-id-as-data: DL3007/secret-in-env/compose-version); provenance tracking (`origin:standard` + `standards_registry`, OCI/CIS/SemVer); docker preset + `docker-mechanisms.md` reference card. 0.2.1 fixed a false positive in `find_dead_links` for Obsidian table-escape pipes `[[Note\|alias]]`. Verified with pytest (134 passed). **Runtime end-to-end empirically validated** (confirmed the route/verify hooks, the init→codify→organize→audit flow, and live work/ separation in a plugin-reload session). See the [CHANGELOG](CHANGELOG.md) for full details.
