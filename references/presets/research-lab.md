# Preset — `research-lab`

> **omp preset card** — universal seed rules for the `research-lab` project type.
> `omp-init` / `rule-architect` **synthesizes this card with an inductive scan of the actual folder**
> to produce a draft `rules.json`. The card is universal and portable (distributed to all users); the synthesized result diverges per project.

| Field | Value |
|:---|:---|
| `preset_origin` | `research-lab` |
| Suited for | academic / research-lab projects — repeated experiments, datasets, results/figures outputs, accompanied by paper writing |
| Matching signals (candidate when the inductive scan finds 2+ of these) | `experiments/`·`exp*/`·date/number directories, `data/` + `results/` + `figures/` coexisting, `paper/`·`.tex`·`.bib`, `*.ipynb` + `seed`·`config` patterns, `references/`·`.bib` |
| Initial `specificity` | `0` (pure preset — right after init. Rises with each learn promotion) |
| `structure.convention` | `research-lab` |

---

## 1. Canonical directory layout (directory roles)

The standard skeleton of a research-lab project. Each dir's `role` goes directly into `structure.directories[].role` of `rules.json`.
When `enforced: true`, `omp-audit` flags files that violate that dir's role.

```
<project>/
├── experiments/    # experiment unit — one experiment per directory by date or number (reproduction unit)
│   └── exp-2026-05-30_baseline/
│       ├── config.yaml      # this experiment's hyperparameters/seed (reproduction key)
│       ├── run.log
│       └── checkpoints/
├── data/           # input data — NEVER modify in place; keep originals isolated in raw
│   ├── raw/        # immutable originals received from outside (treat as read-only, never process or overwrite)
│   ├── interim/    # intermediate processed artifacts (optional)
│   └── processed/  # cleaned data used directly for training/analysis (must be regenerable by script)
├── results/        # experiment output numbers/metrics/tables (.csv/.json/.parquet) — tracked by experiment ID
├── figures/        # figures for papers/presentations (.pdf/.png/.svg) — derived from results, regenerable
├── paper/          # paper manuscript (oms's .tex/.bib may live here) — omp owns structure only, content is oms's
├── references/     # external literature/citation materials (.bib, received PDFs) — reading material, not an output
├── src/            # (optional) shared library code — imported by experiments
├── scripts/        # (optional) one-off / reproduction scripts (clean.py, make_figures.py, etc. — the `by` of lineage)
├── notebooks/      # (optional) exploratory .ipynb — formal results get promoted to results/
└── README.md
```

**Role boundaries (the key separations audit uses):**
- `data/raw/` is **immutable** — no script writes here. Processed artifacts go to `data/processed/`.
- `results/` (numbers) ≠ `figures/` (visualizations). A figure is derived from a result — it must be regenerable.
- omp **does not touch the content** inside `paper/` — papers are the oms domain. omp only checks that `paper/` is in place and consistent with `references/.bib`.
- `experiments/<id>/` is the **reproduction unit** — config + output logs gather in one directory. Results (`results/`) and figures (`figures/`) must be traceable back by experiment ID.

**Synthesis rule (for omp-init):** Put **only the dirs actually found in the scan** into `rules.json.structure.directories`. Do not create a dir that doesn't exist just because it's in the preset — the card is a *role vocabulary dictionary*, not a mandatory creation list. If a found dir has a different name (e.g. `exp/` vs `experiments/`, `outputs/` vs `results/`), **use the actual name as the path and take only the role from this card**.

---

## 2. Naming conventions (rules + examples)

Candidates that go into `rules.json.naming.patterns[]`. The regex is Python `re` syntax, matched against the basename. Initial `severity` is conservatively `warn` (suppress false positives before specialization).

| `applies_to` (glob) | Rule | Example (good) | Example (bad) | regex seed | severity |
|:---|:---|:---|:---|:---|:---|
| `experiments/*` | experiment directory = date or number + short slug | `exp-2026-05-30_baseline`, `exp-007_ablation` | `final`, `test2`, `김승민_실험` | `^exp[-_](\d{4}-\d{2}-\d{2}|\d{3,})[-_].+$` | `warn` |
| `experiments/*/config.*` | one reproduction config per experiment | `config.yaml` | (experiment dir without a config) | `^config\.(ya?ml|json|toml)$` | `warn` |
| `data/raw/*` | originals identifiable by source/date | `census_2026-01.csv` | `data.csv`, `final_v2.csv` | (per project — seed is non-enforced, learn fills it) | `info` |
| `data/processed/*` | cleaned data identifiable by split/version | `train-v2.parquet`, `val.parquet` | `output.pkl`, `temp.parquet` | `^[a-z0-9-]+(-(v\d+))?\.(parquet|csv|npz|pkl)$` | `warn` |
| `results/*` | results tracked by experiment ID | `exp-007_metrics.json`, `2026-05-30_eval.csv` | `results.csv`, `new.json` | `^(exp[-_][\w-]+|\d{4}-\d{2}-\d{2})[_-].+\.(csv|json|parquet|tsv)$` | `warn` |
| `figures/*` | figures named by paper figure number or descriptively | `fig3_loss_curve.pdf`, `arch_diagram.svg` | `Untitled.png`, `image (1).png` | `^[\w-]+\.(pdf|png|svg|eps)$` | `info` |

**Date/ID conventions:**
- date = `YYYY-MM-DD` (ISO, lexicographic sort = chronological sort). Ambiguous formats like `MM-DD-YY` are forbidden.
- experiment number = zero-padded (`exp-007`, not `exp-7`) — stable sorting and tab-completion.
- The two styles (date vs number) are usually **unified to one within a single project** — if the scan finds both, omp-init adopts the majority and leaves the minority as `omp-organize` violation candidates.

**Synthesis rule:** The regexes above are **seeds**. omp-init looks at the actual basenames and (a) adopts a seed as-is if it matches most files, or (b) narrows the regex to the observed pattern (inductively) if it doesn't. Do not raise any pattern to `error` at the init stage — `error` promotion is the job of the learn gate (human approval).

---

## 3. Dataset conventions (manifest seed — research-lab specifics)

Dataset tracking is a first-class concern in a research-lab project. The expectations this preset gives when `omp-dataset` / `dataset-curator` writes `manifest.json`:

- **Default paths to track**: `data/raw/`, `data/processed/`, `results/*.{parquet,csv,npz}`. (Figures/logs are not manifest targets — they are regenerable outputs.)
- **Split tracking is central**: group the `train`/`val`/`test` files under `data/processed/` by the same `split.group` to enable **leakage detection** (is the same row in both train and test?). Split leakage is the most common accident in a research-lab.
- **Lineage strongly recommended**: fill `lineage.derived_from` (source path / dataset id) + `lineage.by` (`scripts/clean.py`, etc.) for `data/processed/*` and `results/*`. "Which data and which code did this result come from" is the heart of reproducibility.
- **`source` vocabulary**: external datasets use `kaggle:<slug>`, `vendor-X`; internal collection uses `internal`.
- **Respect DVC/git-lfs**: when an lfs filter is detected in `.dvc/` or `.gitattributes`, fill `manifest.managed_by_external.tool` and **mirror metadata only**. omp never copies, moves, or pushes the actual data (metadata-only philosophy).
- **Large files**: for files where hashing is costly, `sha256: "UNHASHED"` is allowed (change detection via size+mtime). Avoids the iCloud/exFAT move pitfall — the data is not moved.

---

## 4. omp-init mapping (scan → synthesizing this preset)

The procedure by which `omp-init` overlays a folder onto this preset. **rule-architect does not force the preset; it yields to the actual observations.**

1. **Type decision**: from project-scanner's inductive results (tree/extensions/naming), finding 2+ of the §0 matching signals → `research-lab` candidate. If the signals are weak or compete with another preset (python-ml, etc.), present 2 candidates to the human.
2. **dir mapping**: actual dirs found by the scan → mapped to this card's role vocabulary. If the name differs, **keep the actual name + adopt only the role** (`outputs/`→role="result numbers", `exp/`→role="experiment unit"). A dir present in the card but absent from the scan is **not** put into `rules.json`.
3. **naming induction**: validate/narrow the §2 seed regexes against the majority of observed basenames. Adopt if they match, re-extract the pattern from observations if they don't. At the init stage severity is `warn`/`info` only.
4. **dataset seed**: when `data/`·`results/` exist, leave a recommendation note in STRUCTURE.md to call `omp-dataset` (no auto-registration — registration is a human-confirm gate). Also record the DVC detection result.
5. **specificity = 0** for the draft + `project.preset_origin = "research-lab"`. After passing the human gate (draft rules.json approval), `.omp/rules.json` is finalized.
6. **STRUCTURE.md / NAMING.md**: transcribe this card's role boundaries (§1) and date conventions (§2) into prose in the human-facing documents — so a human can read them and correct any mismatched rule.

**Synthesis vs enforcement, one line**: this card is a dictionary of *what to expect*, not a command of *what to create*. On conflict, **the observations win** — the preset provides only vocabulary and defaults.

---

## 5. omp-learn specialization paths (typical evolutions in a research-lab)

Typical patterns by which `omp-learn` diverges this preset into project rules during operation (accumulated observations → promotion gate → `rules.json` + a rise in `specificity`):

- **Extension→folder fixed rules**: "in this project `.pkl` always goes in `data/processed/`", "`.pth` checkpoints always go in `experiments/<id>/checkpoints/`" — observed 3 times → learned.md candidate → approval → an enforced rule in `structure.directories`.
- **Experiment ID scheme settled**: whether the project is date-style or number-style firms up during operation → promote one of the two candidates in §2 to `error` severity (the other becomes a violation).
- **results↔experiments link enforcement**: a cross-dir integrity rule like "a `results/` filename must have a corresponding `experiments/<id>/` that exists" may be added via learn.
- **Split group naming standard**: `split.group` naming (e.g. `exp-2026-05`-style) gets standardized during manifest operation → fixed in DATASETS.md.
- **paper directory oms handoff boundary**: an `ignore` entry firms up stating that omp excludes the inside of `paper/` from audit and delegates it to oms (`paper/**` ignore).
- **figure regeneration contract**: the rule "every `figures/*` has lineage to a generation script in `scripts/`" — promoted when reproducibility is reinforced.

Each time learn promotes one item, `specificity` shifts from 0 toward 1, and the source observation ID is recorded in that rule's `learned_refs`.

---

## 6. wiki auto-accumulation examples (lightweight channel, no approval needed)

Lightweight patterns/decisions auto-appended to `.omp/wiki/` during `research-lab` operation (recalled by grep in the next session):
- "Started writing the seed into config.yaml from exp-013 on — earlier experiments have unknown seeds"
- "data/raw/ is a NAS mirror, local keeps only processed — original hash is UNHASHED in the manifest"
- "Figure font fixed at 16pt for presentations (rcParams in make_figures.py)"

These items are *context notes*, not rules, so they accumulate without a gate and have no effect on audit.

---

**Card version**: omp v0.2.1 seed · preset family: one of `python-ml` / `web-app` / `research-lab` / `monorepo` / `johnny-decimal` / `generic`.
**Reference schemas**: `references/schemas/rules.schema.json` (structure/naming) · `references/schemas/manifest.schema.json` (dataset).
