# Preset Card — generic

> **What this is**: A data file, not a skill. `omp-init`/`rule-architect` read this card and
> **synthesize** it with an inductive scan of the real folder (`project-scanner`) into a draft
> `rules.json`. This is the **fallback seed** — used when no richer preset (python-ml / web-app /
> research-lab / monorepo / johnny-decimal) confidently matches the scanned folder. It carries only
> **minimal sane defaults**; `omp-learn` specializes it over time as the project reveals its real
> shape. Do not duplicate this knowledge into agent files — point at this card. `preset_origin` in
> `rules.json` becomes `"generic"`.

## Identity (when this preset wins)

This preset is the **"safe default for when you're not sure."** rule-architect picks it when the folder does **not** show enough of a specific project type's signature (e.g. `pyproject.toml`+`src/`, `package.json`+`src/`, `data/raw`+`notebooks/`, `XX-YY_` Johnny-Decimal ID, monorepo `packages/`).

The core idea is **under-specification**. It does not invent what it doesn't know. There are almost no enforced rules; most are just soft `info`/`warn`-level recommendations. It starts at `specificity: 0`, and as patterns surface during actual use, `omp-learn` promotes them and gradually hardens them into real rules. In other words, generic is a **starting point, not a destination** — over time almost every generic project diverges into its own rule set.

## (1) Canonical directory layout

generic does not force a specific layout. It seeds only the **minimal skeleton** that nearly every project shares. The actual directories are filled in by the inductive scan (see §4 below).

| path | role | id | enforced | notes |
|:---|:---|:---|:---|:---|
| `.` (root) | Project entry point. README, license, and top-level config only. No stray artifacts. | — | `true` | root cleanliness is generic's only strong rule |
| `docs/` | Human-facing docs/notes (when present) | — | `false` | added if found by scan, not enforced if absent |
| `src/` or code root | Source code (inferred by scan) | — | `false` | name is decided by scan (`src`/`lib`/`app`/project name) |
| `data/` | Data files (when present) | — | `false` | registered if it exists; substructure not enforced |
| `scripts/` or `bin/` | Executable scripts/tools (when present) | — | `false` | |
| `tests/` | Tests (when present) | — | `false` | |

**Core rule — root hygiene**: generic's single strong (enforced) structural rule is "**don't leave stray junk files at the root**." The root permits only the README, the license, top-level config files (`pyproject.toml`/`package.json`/`Makefile`/`.gitignore`, etc.), and first-class subdirectories. If temporary files, artifacts, or one-off scripts pile up at the root, audit flags them. **All other directories are `enforced: false`** — their role is recorded once their existence is confirmed, but what should go inside them is not enforced (since we don't know yet).

> **Synthesis rule**: Of the directories in the table above, **only those whose existence is actually confirmed by the scan** go into `rules.json.structure.directories[]`. Don't pre-create nonexistent directories or hardcode them into rules (generic does not force a blueprint). Keep `structure.convention` as `"flat"` (no named layout). The one entry that is always present is root (`path: "."`, `enforced: true`).

## (2) Naming conventions

generic's naming rule is a single one: **consistency** — rather than forcing a specific case, it recommends "keep using the case this project already uses."

| applies_to | regex (Python `re`) | description | severity |
|:---|:---|:---|:---|
| `*` (all new files/folders) | `^[A-Za-z0-9._-]+$` | Names without spaces or special characters (portability/shell safety) | `warn` |
| `*` | (filled by scan — see below) | Consistent with the project's dominant case (e.g. if everything is `snake_case`, a new `kebab-case` file is warned) | `info` |
| `README*` | `^README(\.[a-z]+)?$` | The root README uses the standard name | `info` |

**Case consistency (decided by scan)**: generic does not force one of `snake_case`/`kebab-case`/`camelCase`/`PascalCase`. Instead, `project-scanner` **inductively determines the dominant case of existing files**, and rule-architect encodes it as an `info` rule. Example: if 80% of existing files are `snake_case`, a rule "new files should prefer `snake_case`" is created. The reason for not hardcoding one case from the start — generic respects the convention the project has already settled on rather than forcing a new one.

**Examples (Good/Bad)**:
- Good: `data_loader.py`, `user-profile.tsx`, `README.md`, `2026-05-30-notes.md`
- Bad: `data loader.py` (space), `final FINAL (2).docx` (space+parentheses), `Untitled.md` (meaningless name)

> **Synthesis rule**: Row 1 above (no spaces/special characters) is always included (cross-OS safe). Row 2 (case consistency) is included as `info` only when the scan found a dominant case with ≥60% confidence — if it can't be found, omit it (don't make it up). All generic naming rules are `warn`/`info`, never `error` — soft recommendations that don't trigger forced moves.

## (3) Dataset conventions

generic assumes the project **may not** be dataset-centric. Therefore dataset rules are **conditional**.

- If the scan **finds** `data/`/`datasets/` or large binaries (`.parquet`/`.csv`/`.npz`/`.h5`/`.pkl`):
  `omp-dataset` registers them as metadata-only in `manifest.json` (SHA256, size, row count). The actual data is
  **never moved** (`dataset-curator` contract — see `references/manifest.schema.json`).
- If it **doesn't find** any: leave dataset rules empty. Don't force-create a `data/`.
- When `.dvc/`/`.git/lfs`/`.gitattributes` (lfs filter) is detected: delegate as "already managed by DVC/git-lfs — manifest only mirrors the metadata." generic respects existing data-management tools.

> generic has no seeded data split/lineage naming convention (since it doesn't know the project type). If data actually shows up and the user wants split tracking, `omp-dataset` will fill it in per the manifest schema at that point.

## (4) How omp-init maps a scanned folder onto this preset

`omp-init`'s synthesis = **(a) inductive scan + (b) generic seed → draft rules.json**. In generic, the induction (scan) **dominates** the seed (preset) — since the seed is nearly empty, the scan fills in the substance.

1. **Root inventory**: `project-scanner` lists the root's files and first-class directories. Checks whether a README exists.
2. **Directory role induction**: For each first-class directory found, infer its role from its contents
   (high code proportion → source root, `.csv`/`.parquet` proportion → data, `.md` proportion → docs, test files → tests).
   Put only what can be inferred into `directories[]`; when uncertain, mark `role` as "scan inferred — needs confirmation."
3. **Case induction**: Tally the dominant case of existing filenames → if ≥60%, create an `info` naming rule.
4. **Data detection**: Apply the §3 conditional rules.
5. **ignore seed**: Always put `.git/**`, `.omp/**`, `node_modules/**`,
   `__pycache__/**`, `.venv/**`, `*.pyc`, `.DS_Store` into `rules.json.ignore[]` (noise common to all types).
6. **specificity = 0**: Make explicit that it's a pure-preset starting point. preset_origin = `"generic"`.
7. **Human gate**: Present the synthesized draft rules.json to the human. Confirm "is this really your project?" before finalizing.

> **Synthesis posture**: In generic, init's mission is not "create lots of rules" but "encode only the minimum we are certain of right now, and defer the rest to learn." When in doubt, **don't add** a rule — just leave the observation in wiki/learned. An incorrect enforced rule (one that moves files to the wrong place) is far more harmful than an empty rule.

## (5) What omp-learn typically specializes here

generic is the preset with the greatest divergence (since it starts nearly empty). What `omp-learn` commonly promotes:

- **Confirming directory roles**: an observation like "`scratch/` always holds only temporary notes" repeated 3 times → promoted to an `enforced: true`
  structural rule. specificity rises.
- **Extension ↔ location rules**: "in this project `.pkl` is always in `outputs/models/`" → a new naming/structural rule.
- **Pinning the case**: the case-consistency rule that was `info` at init is upgraded to `warn` once it's confirmed that violations are nearly nonexistent.
- **Preset reclassification signal**: when signatures of a specific type accumulate during scan/use (e.g. a `pyproject.toml` is added),
  rule-architect proposes to the human "wouldn't it be better to reinitialize with the python-ml preset now?"
  generic can **graduate** to a more specific preset.

> Every promotion goes through `learned.md` → a human approval gate (heavy channel). A promoted rule leaves its source in `rules.json`'s `learned_refs[]`. Light patterns/decisions accumulate automatically in `.omp/wiki/` (no approval needed).

## Draft rules.json skeleton (generic seed)

The skeleton `rule-architect` uses as a starting point during synthesis. **The bracketed parts are filled by the inductive scan** —
if the scan can't fill one, omit that entry (don't make it up). Conforms to `rules.schema.json`.

```json
{
  "omp_version": "0.2.1",
  "project": {
    "name": "[scan: root folder name, or the name in manifest/pyproject]",
    "preset_origin": "generic",
    "initialized": "[ISO date]"
  },
  "specificity": 0,
  "structure": {
    "convention": "flat",
    "directories": [
      { "path": ".", "role": "Project root — README, license, top-level config, first-class directories only. No stray artifacts.", "enforced": true }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "*", "regex": "^[A-Za-z0-9._-]+$", "description": "Portable, safe names without spaces or special characters.", "severity": "warn" }
    ]
  },
  "ignore": [".git/**", ".omp/**", "node_modules/**", "__pycache__/**", ".venv/**", "*.pyc", ".DS_Store"],
  "learned_refs": []
}
```

> First-class directories confirmed by the scan are appended to `directories[]`, and the case-consistency rule (when the scan found it with ≥60% confidence) is appended to `naming.patterns[]`. The skeleton above is a conservative starting point holding **only the always-true minimum** — exactly generic's core philosophy: "only what's certain, the rest to learn."
