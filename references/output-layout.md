# Output Layout — the .omp/ SSOT (path contract)

## Core principle

omp manages **the user's existing project folder in place**. It never relocates the
user's files into `.omp/`. The `.omp/` folder holds only omp's own knowledge about the
project: rules, inventory, human docs, learning state, and accumulated patterns.

The actual project files stay exactly where they are. omp's job is to *understand and
codify* them, not to absorb them.

## Fixed structure (invariant — created by omp-init)

```
<project root>/                  # the user's project — managed in place
├── ... (the user's real files, never moved into .omp/)
└── .omp/                        # omp's knowledge of this project (the SSOT)
    │                            # ── SSOT layer (the durable knowledge — read these) ──
    ├── PROJECT.md               # human: what this project is, one screen
    ├── STRUCTURE.md             # human: folder layout + role of each directory
    ├── NAMING.md                # human: naming conventions, with examples
    ├── DATASETS.md              # human: dataset catalog (mirror of manifest)
    ├── rules.json               # machine: enforceable rules (audit reads this)
    ├── manifest.json            # machine: file + dataset inventory (checksum/split/lineage)
    ├── learned.md               # observations awaiting promotion (learn gate)
    ├── wiki/                    # auto-accumulated patterns/decisions (grep-recalled)
    │   └── *.md
    │
    │                            # ── work layer (intermediate artifacts — you rarely read these) ──
    └── work/                    # everything below is regenerable scratch, NOT the SSOT
        ├── scans/               # project-scanner raw inventories (input to synthesis)
        │   └── scan-{YYYY-MM-DD-HHMM}.json
        ├── versions/            # rules.json snapshots before a change (codify/learn rollback)
        │   └── rules-v{NN}-{YYYY-MM-DD}.json
        ├── plans/               # organize move-plans + dry-run logs (undo provenance)
        │   └── organize-{YYYY-MM-DD-HHMM}.md
        ├── audits/              # audit PASS/FAIL reports over time (drift history)
        │   └── audit-{YYYY-MM-DD-HHMM}.json
        └── tmp/                 # transient scratch (safe to delete anytime)
```

### SSOT layer vs work layer (the boundary, like oms `.oms/` / omd `.omd/`)

- **SSOT layer** (top of `.omp/`) = the durable second-brain. Hand-curated or gated. Losing it
  loses the project's learned knowledge. Committed by choice (see `.gitignore` guidance below).
- **work layer** (`.omp/work/`) = intermediate artifacts a stage produced on the way to an SSOT
  change. **Regenerable, never authoritative.** A user never needs to open these; they exist for
  rollback (versions/), undo provenance (plans/), and drift history (audits/). Each subfolder has
  one fixed name pattern (above) so the work layer is itself as well-organized as the projects omp
  manages — no loose files. `work/tmp/` is always safe to wipe.

**Who writes where** (the *controller skill* writes, never a read-only agent — `project-scanner`
and `auditor` are read-only and cannot write their own output):
- `work/scans/` ← **`omp-init`** records the `project-scanner` inventory (scanner reports; init writes).
- `work/versions/` ← **`omp-codify`** and **`omp-learn`** snapshot the old `rules.json` here *before*
  editing it (the rollback point), via the `hooks/omp_atomic.py` atomic write.
- `work/plans/` ← **`omp-organize`** records its dry-run move-plan here (undo provenance) before any move.
- `work/audits/` ← **`omp-audit`** writes each report here (the skill writes, not the read-only `auditor`).
- `work/tmp/` is transient scratch any stage may use and is always safe to wipe.

Retention: keep the latest N (default 10) per subfolder; older ones are pruned into trash (never
permanent `rm`), surfacing a one-line "pruned X old snapshots" note. The pruning runs at the end of
each writing skill's pass (so a skill that writes a snapshot also trims its own subfolder).

## Human .md  ↔  Machine .json pairing

| Human (.md) | Machine (.json) | Relationship |
|:---|:---|:---|
| STRUCTURE.md, NAMING.md | rules.json | The .md is the readable narrative; rules.json is the enforceable form. codify writes both; they must agree. |
| DATASETS.md | manifest.json (datasets[]) | DATASETS.md is a generated human view of the manifest. |

Rule: when codify or dataset changes a .json, it regenerates the paired .md in the same
pass so they never drift. audit reads the .json (machine truth); humans read the .md.

## Two learning channels (where evolution is written)

- **Heavy (rules)**: `learned.md` accumulates observations → `omp-learn` promotes them
  into `rules.json` **only after a human approval gate**. Promotion raises
  `rules.json.specificity` toward 1.
- **Light (patterns/decisions)**: `wiki/*.md` is auto-appended during any omp stage,
  no gate, recalled next session by deterministic grep (the obsidian-backlink feel).

## .gitignore guidance (omp emits this hint, does not force it)

`.omp/wiki/` and `.omp/learned.md` are project-local working memory. Whether to commit
`.omp/` is the user's call: committing `rules.json`/`*.md` shares conventions with the
team (recommended); `wiki/` may be personal. omp-init asks once and records the choice.

## What omp never does

- Never moves user files into `.omp/`.
- Never deletes user files without the safe-fileops.md protocol + human approval.
- Never copies/moves dataset *contents* (manifest is metadata-only; see manifest.schema.json).
