# Output Layout — the .hq/ SSOT (path contract)

## Core principle

omp manages **the user's existing project folder in place**. It never relocates the
user's files into `.hq/`. The `.hq/` folder holds only omp's own knowledge about the
project: rules, inventory, human docs, learning state, and accumulated patterns.

The actual project files stay exactly where they are. omp's job is to *understand and
codify* them, not to absorb them.

## Fixed structure (invariant — created by omp-init)

```
<project root>/                          # the user's project — managed in place
├── ... (the user's real files, never moved into .hq/)
└── .hq/                                 # omp's knowledge of this project (the SSOT)
    ├── config/project/                  # ── config layer: what code parses (tracked) ──
    │   ├── rules.json                   # machine: enforceable rules (audit reads this)
    │   ├── manifest.json                # machine: file + dataset inventory (checksum/split/lineage)
    │   ├── STRUCTURE.md                 # human: folder layout + role of each directory
    │   ├── DATASETS.md                  # human: dataset catalog (mirror of manifest)
    │   ├── learned.md                   # observations awaiting promotion (learn gate)
    │   ├── env/                         # environment assets SSOT (omp-env): Dockerfile/compose/config
    │   │   └── *.Dockerfile, *.yml      #   root holds only a build-tool view (symlink or sync copy)
    │   └── secretary/                   # 비서축 SSOT(계약은 references/secretary-protocol.md). BRIEF.md 만 '재생성되는 파생 뷰' 특수 지위(omp-managed 마커).
    │       └── ...                      #   layout detail: references/secretary-protocol.md
    ├── community/                       # ── community layer: human records (tracked) ──
    │   ├── PROJECT.md                   # human: what this project is, one screen
    │   ├── NAMING.md                    # human: naming conventions, with examples
    │   ├── CONVENTIONS.md               # human: file-content conventions — note bodies or code idioms (paired with rules.json.content_conventions[]; only when present)
    │   └── posts/                       # auto-accumulated patterns/decisions (`hq query --ascend` recalled)
    │       └── <kind>/*.md              #   nested one level under a post-directory (finding/, decision/, …)
    └── work/project/                    # ── work layer: regenerable, NOT the SSOT (ignored) ──
        ├── scans/                       # project-scanner raw inventories (input to synthesis)
        │   └── scan-{YYYY-MM-DD-HHMM}.json
        ├── versions/                    # rules.json snapshots before a change (codify/learn rollback)
        │   └── rules-v{NN}-{YYYY-MM-DD}.json
        ├── plans/                       # organize move-plans + dry-run logs (undo provenance)
        │   └── organize-{YYYY-MM-DD-HHMM}.md
        ├── audits/                      # audit PASS/FAIL reports over time (drift history)
        │   └── audit-{YYYY-MM-DD-HHMM}.json
        ├── handoffs/                    # omp-handoff briefing packets — delegation provenance (YYYY-MM-DD-<target>.md)
        └── tmp/                         # transient scratch (safe to delete anytime)
```

### config/community layer vs work layer (the boundary, which oms and omd carry too, under their own `.hq/` anchors)

- **config/community layer** (`.hq/config/project/`, `.hq/community/`) = the durable second-brain.
  Hand-curated or gated. Losing it loses the project's learned knowledge. Tracked in git
  (see `.gitignore` guidance below).
- **work layer** (`.hq/work/project/`) = intermediate artifacts a stage produced on the way to an SSOT
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
- `work/handoffs/` ← **`omp-handoff`** writes the briefing packet copy.
- `work/tmp/` is transient scratch any stage may use and is always safe to wipe.

Retention: keep the latest N (default 10) per subfolder; older ones are pruned into trash (never
permanent `rm`), surfacing a one-line "pruned X old …" note. The pruning runs at the end of
each writing skill's pass (so a skill that writes a snapshot also trims its own subfolder). This is
wired into each writing skill, not just declared here: `omp-init` trims `scans/`, `omp-codify` and
`omp-learn` trim `versions/`, `omp-organize` trims `plans/`, `omp-audit` trims `audits/`, and
`omp-handoff` trims `handoffs/` — each in the same pass that writes the file. `tmp/` is exempt
(always safe to wipe wholesale).

## Human .md  ↔  Machine .json pairing

| Human (.md) | Machine (.json) | Relationship |
|:---|:---|:---|
| STRUCTURE.md, NAMING.md | rules.json | The .md is the readable narrative; rules.json is the enforceable form. codify writes both; they must agree. |
| CONVENTIONS.md | rules.json (content_conventions[]) | The readable narrative of file-content conventions — note bodies or code idioms; the axis is glob-scoped and `check_content_rule` has no extension restriction. rules.json.content_conventions[] is the enforceable form, and idioms not expressible as a regex live here as prose only. Paired only when content_conventions exist; codify writes both together (omp-style proposes the code ones, codify writes them). |
| DATASETS.md | manifest.json (datasets[]) | DATASETS.md is a generated human view of the manifest. |
| DATASETS.md (docker section) or DOCKER.md | manifest.json (docker_images[]) | Human view of the docker image inventory; machine truth is docker_images[]. |

Rule: when codify or dataset changes a .json, it regenerates the paired .md in the same
pass so they never drift. audit reads the .json (machine truth); humans read the .md.

## Two learning channels (where evolution is written)

- **Heavy (rules)**: `learned.md` accumulates observations → `omp-learn` promotes them
  into `rules.json` **only after a human approval gate**. Promotion raises
  `rules.json.specificity` toward 1.
- **Light (patterns/decisions)**: each observation is its own post — `hq post --topic
  <convention|pattern|decision|reference|technique>` — during any omp stage, no gate,
  recalled next session by `hq query --keyword <term> --ascend --topic <category>`
  (deterministic keyword match, never embeddings — the obsidian-backlink feel, minus
  the backlinks). `--ascend` also merges in every ancestor anchor's posts, nearest first.

### Open commitments in a post: write them as `- [ ]`

A post routinely records something the session *promised to do later* — "미결",
"별도 세션 대상", "pending". Write those as **unchecked markdown checkboxes**, one per
line, and close them by changing `[ ]` to `[x]`:

```markdown
- [ ] move the paper artifacts to workspace (out of init's scope)
- [x] decouple the Kanban sources from rules.json
```

`scan_open_items` reports the unchecked ones as `open_item`, and `omp-brief` enumerates
them into the next-session goal. **Prose is not scanned and never will be** — on one
vault a prose-marker scan produced 3 false positives out of 7 hits, because a heading
that *declares an item resolved* contains the same words as the item, and a filename can
too. A checkbox carries its own open/closed state; a sentence does not.

**There is no age gate.** File mtime answers "was this page edited", not "how long has
this item sat": the case that motivated the channel was a three-month-old commitment in
a file whose mtime was same-day, because another session had appended a section that
morning. An unchecked box is actionable on sight, and the human decides — omp never
closes one.

## .gitignore guidance (structural, not a per-project choice)

Tracked-vs-ignored is fixed by layer, not asked: `.hq/config/project/` and `.hq/community/`
(`rules.json`/`*.md`, `learned.md`, `posts/`) are always tracked, sharing conventions with the
team; `.hq/work/project/` and `.hq/runtime/project/` are always gitignored via the two
`**/.hq/work/` / `**/.hq/runtime/` lines (store-spec §5). There is no whole-store commit choice
to make or record.

## What omp never does

- Never moves user files into `.hq/`.
- Never deletes user files without the safe-fileops.md protocol + human approval.
- Never copies/moves dataset *contents* (manifest is metadata-only; see manifest.schema.json).
- Never writes a canonical environment asset (Dockerfile/compose/.env) outside `.hq/config/project/env/` — the root holds only a build-tool view (symlink or sync copy). The "no canonical file outside `.hq/`" invariant is preserved.
