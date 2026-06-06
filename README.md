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

## Stage skeleton (management loop)

```
  omp-init      One-time bootstrap — folder scan (inductive) + preset-matched synthesis → creates .omp/
       ━━━ GATE: approve draft rules.json ━━━
  omp-codify    Codify structure·naming rules (rules.json + STRUCTURE/NAMING.md)
  omp-organize  Detect rule violations → safe relocation (mv→verify→delete, via trash)
  omp-dataset   Register datasets·SHA256·split·lineage (manifest.json) — metadata-only
  omp-doc       Generate·update human-facing docs (PROJECT.md etc.)
  omp-learn     Observation → rule promotion (human approval gate) ← the core of evolution
  omp-audit     Rule-compliance verification (read-only PASS/FAIL)
  omp-pilot     Full orchestration (absorbs init when no .omp exists)
```

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

## Agents (5)

| agent | model | permissions | role |
|:---|:---|:---|:---|
| project-scanner | sonnet | read-only | Folder inventory, inductive structure |
| rule-architect | opus | read-only | Rule design, preset synthesis, promotion decisions |
| organizer | sonnet | write | **The only file-moving agent** (enforces safety protocol) |
| dataset-curator | sonnet | write(manifest) | Checksums, splits, lineage (does not move data) |
| auditor | opus | read-only | Rule-compliance verification (detection only, no moving) |

**Invariant contract**: only organizer moves files (writes are single-focused). Detection (auditor) ≠ execution (organizer) are kept separate. dataset is metadata-only (delegates when DVC/git-lfs is detected).

## Routing

omp is a **domain handler** (the project-management domain). Working-mode lane (SP/OMC) judgment is handled by [`oh-my-heroacademia`](https://github.com/luckkim123/oh-my-heroacademia) (omha) — omp does not decide the lane. After omha sets the lane, omp's UserPromptSubmit hook (`omp_route_emit.py`) declares which **STAGE** (init/codify/organize…) within the project domain on each turn with a single `STAGE(project) → …` line. The PostToolUse hook (`omp_verify_emit.py`) injects an integrity reminder after `.omp/` edits or file moves (it does not auto-fix or freeze).

## Cross-platform

Mac / Linux / Windows. Every hook is **python3 stdlib only + fail-open** (errors never block the session), every path uses `pathlib` (OS-neutral), and deletions go through the per-OS trash.

## Status

v0.2.1 — 9 skills + 5 agents + 6 presets + 4 reference cards + hooks (`omp_route_emit`/`omp_verify_emit` runtime hooks + `omp_atomic` SSOT writes + `omp_content_audit` audit helper + `__init__`) + schema implementation. 0.2.0 added the `content_conventions[]` rule type (note-body conventions: present/absent × body/frontmatter) plus content/wikilink audit axes. 0.2.1 fixed a false positive in `find_dead_links` for Obsidian table-escape pipes `[[Note\|alias]]`. Hooks, schema, and the content/link pure functions are verified with pytest (49 passed). **Runtime end-to-end empirically validated** (confirmed the route/verify hooks, the init→codify→organize→audit flow, and live work/ separation in a plugin-reload session). See the [CHANGELOG](CHANGELOG.md) for full details.
