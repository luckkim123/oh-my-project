# Preset Card — `python-ml`

> **What this is**: This is a data file, not a skill. The `omp-init` and `rule-architect` agents read
> this card, then **synthesize** a draft `rules.json` by combining it with `project-scanner`'s
> **inductive scan** (the actual folder tree, extensions, and naming patterns). This card is a
> **generic seed** — it is distributed identically to every user.
> Do not bake a specific project's unique rules in here. Those are promoted by `omp-learn` into
> `<project>/.omp/rules.json`.
>
> **Synthesis principle**: This card is only a **prior** stating "a project of this type usually looks
> like this." When the actual scanned folders disagree with the card, **the actual folders win**
> (induction first, the preset just fills in the blanks). Directories that the card lists but the folder
> lacks are not force-created — only proposed, leaving the decision to the human gate.

## 0. What it matches

Python ML / research projects, centered on model training, experiments, and data pipelines. If **two or
more** of the following signals are present, this preset is matched as a strong candidate (`rule-architect`
scores it):

| signal | rationale |
|:---|:---|
| `requirements.txt` / `pyproject.toml` / `environment.yml` / `setup.py` present | Python project |
| `torch` / `tensorflow` / `jax` / `sklearn` / `lightning` / `transformers` dependency | ML stack |
| many `.ipynb` notebooks | exploratory research workflow |
| `data/` directory + many `.csv`/`.parquet`/`.npy`/`.pkl`/`.h5` files | dataset-heavy |
| `models/` / `checkpoints/` / `*.pt`·`*.ckpt`·`*.onnx` | model artifacts |
| `configs/` + `.yaml`/`.json` hyperparameters | experiment config management |

> **Boundaries**: if web framework (`fastapi`/`django`/`flask`) signals are stronger, use the `web-app`
> preset; if multiple packages are split across `packages/`·`apps/`, use the `monorepo` preset. When ML
> + serving are mixed, use `python-ml` as the base but let `rule-architect` add the serving directories
> as supplementary rules.
>
> **`python-ml` vs `research-lab` tiebreaker** (their signals overlap — pick one with an explicit rule):
> if `experiments/` is present (one directory per experiment as a reproduction unit) or `paper/`·`.tex`·`.bib`
> are visible → prefer **research-lab**.
> If it uses `src/<pkg>` packaging (an installable library, `[project]`/`packages` in `pyproject.toml`) and
> there is no `experiments/` → prefer **python-ml**. If both are strong (installable package + experiments
> coexisting), `rule-architect` presents both candidates to the human but pins one recommendation based on
> the signal priority above.

## 1. Canonical directory layout

Two real-world conventions coexist. `project-scanner` looks at the import root to determine which one applies.

- **src-layout** — the importable package is isolated under `src/<pkg>/` (tests import the installed build;
  the recommended packaging convention).
- **flat-layout** — the package sits directly under the repo root as `<pkg>/`, or modules are scattered
  (common in research code).

Record `"src-layout"` or `"flat"` in `structure.convention` of `rules.json`.

```
<project>/
├── src/<pkg>/ or <pkg>/     # importable library code (reusable logic)
├── data/
│   ├── raw/                 # immutable originals — never modify/overwrite directly (treat as read-only)
│   ├── processed/           # cleaned/feature-engineered results (regenerable by script)
│   └── external/            # third-party datasets received externally (track provenance)
├── notebooks/               # exploratory/analysis .ipynb (graduate reproducible code into src/)
├── models/                  # training artifacts: weights·checkpoints (large, usually .gitignore)
├── configs/                 # hyperparameter/experiment config .yaml/.json
├── scripts/                 # execution entry points (train.py, evaluate.py, preprocess.py)
├── reports/figures/         # (optional) generated figures·plots
├── tests/                   # (optional) pytest tests
├── requirements.txt /       # dependency declarations
│   pyproject.toml
└── README.md
```

### Directory role table (→ maps 1:1 to `structure.directories[]` in `rules.json`)

| path | role (one sentence, into the `role` field) | enforced | notes |
|:---|:---|:---:|:---|
| `data/raw` | Immutable original data. Never modify in place — new outputs go to `processed/`. | true | first line of defense against data leakage |
| `data/processed` | Cleaned/feature data, regenerable by script. | true | trace back to source via `lineage` |
| `data/external` | Datasets from external sources (downloaded·third-party). | true | record `source` in manifest |
| `notebooks` | Exploratory/analysis `.ipynb`. Graduate reusable logic into `src/`. | true | core logic left in a notebook = audit warn |
| `models` | Trained weights·checkpoint artifacts. | false | large — `ignore` candidate |
| `configs` | Hyperparameter/experiment config files. | true | — |
| `scripts` | CLI entry points (train/eval/preprocess). | true | move import logic into `src/` |
| `src/<pkg>` or `<pkg>` | Importable library code. | true | path decided by `convention` |

> **Meaning of `enforced`**: if true, `omp-audit` flags "files in this directory that don't fit its role"
> as violations. `models/` is an artifact dump, so it is usually `enforced:false` + registered in `ignore`.
> Directories that the scan does not actually find are not added to `directories[]` (don't enforce a rule
> for something that doesn't exist).

## 2. Naming conventions

Python ecosystem conventions. Each item maps to a `naming.patterns[]` entry in `rules.json` (`applies_to`
glob + `regex` + `description` + `severity`). Regexes use **Python `re` syntax, matched against the basename**.

| applies_to (glob) | rule | regex (seed) | severity | example |
|:---|:---|:---|:---:|:---|
| `**/*.py` (source modules) | snake_case module name | `^[a-z_][a-z0-9_]*\.py$` | warn | `data_loader.py` ✓ / `DataLoader.py` ✗ |
| `notebooks/*.ipynb` | number prefix + snake_case (makes execution order visible) | `^(\d{2}[-_])?[a-z0-9_]+\.ipynb$` | info | `01_eda.ipynb`, `02_baseline.ipynb` |
| `configs/*.yaml` | snake_case config name | `^[a-z0-9_]+\.(yaml\|yml\|json)$` | warn | `train_resnet.yaml` ✓ |
| `data/**/*` (data files) | version/date tag recommended (track immutable data) | `.*(_v\d+\|_\d{4}-\d{2}-\d{2})\.[^.]+$` | info | `train_v2.parquet`, `dump_2026-05-30.csv` |
| `models/*` (checkpoints) | model name + version/epoch | `.*(_v\d+\|_ep\d+\|_\d{4}-\d{2}-\d{2})\.[^.]+$` | info | `resnet_v3.pt`, `unet_ep050.ckpt` |
| `scripts/*.py` | verb-initial entry point | `^(train\|eval\|evaluate\|predict\|preprocess\|run_\|make_).*\.py$` | info | `train.py`, `run_sweep.py` |

> **Default severity**: code consistency (module names) is `warn`; data/model version tagging is `info`
> (recommended, not enforced). If the user wants enforcement at the human gate, `omp-codify` promotes
> `warn`→`error`. Notebook number prefixes are common but not universal, so they start at `info`; `omp-learn`
> promotes them when it actually observes the practice repeated.

## 3. Dataset conventions (dataset-heavy — paired with `omp-dataset`)

For this type, **datasets are first-class citizens**. When `omp-init` detects `data/`·`models/`, it proposes
`omp-dataset` as a follow-up, and `dataset-curator` fills in `manifest.json`. It is **metadata-only** —
`dataset-curator` does not move or copy the actual data (it only records checksums·splits·lineage).

Standard data flow (lineage skeleton):

```
data/raw/<source>.csv  ──[scripts/preprocess.py]──▶  data/processed/<name>_v<N>.parquet
                                                              │
                                                    split: train / val / test (group tag)
```

`manifest.json` seed conventions (fields `omp-dataset` will fill):

- **`split.group`** — train/val/test must share the same `group`. If groups differ, `omp-audit` warns of
  **suspected data leakage** (checking whether the same source crosses split boundaries).
- **`lineage.derived_from` + `lineage.by`** — a `processed/` file tracks which raw it came from and via which
  script. The core of reproducibility.
- **`sha256` + `size_bytes` + `rows`** — detects "did the data change?". If content changes under the same
  filename, it warns.
- **`source`** — `data/external/` is `"external"`, `data/raw/` is usually `"internal"`.

> **Respect DVC / git-lfs**: if `.dvc/` exists or `.gitattributes` has an lfs filter, the data is already
> managed by an external tool. `dataset-curator` then **mirrors only the metadata** and does not hijack the
> tracking (on scan it reports this signal to `rule-architect` → marks `manifest.json`'s
> `managed_by_external.tool = "dvc"`, conforming to the object-with-tool-enum shape in `manifest.schema.json`).

## 4. How `omp-init` maps scan results into this preset (synthesis)

`omp-init` = inductive scan (`project-scanner`) × preset matching (`rule-architect`) → draft `rules.json` →
human gate. When this preset matches, the synthesis procedure is:

1. **Determine layout** — if `src/<pkg>/__init__.py` exists, `convention:"src-layout"`; if a root package,
   `"flat"`. Add only actually-discovered directories to `directories[]`. If it's in the card but not in the
   folder, **do not add it**.
2. **Attribute roles** — match each discovered directory against the §1 role table. For directories not in
   the table (e.g. `serving/`, `airflow/`), induce the `role` from scan evidence (dominant extensions·filenames)
   and start conservatively with `enforced:false`.
3. **Validate naming patterns** — run the §2 regexes against a sample of actual filenames to measure the
   **fit rate**. If the fit rate is low (e.g. the project uses CamelCase modules), **drop that pattern or
   re-induce the regex to match the actual practice**. Don't force preset rules onto the user's code.
4. **Seed ignores** — propose `models/`, `data/raw/` (large), `.ipynb_checkpoints/`, `__pycache__/`,
   `*.egg-info/`, `.venv/`, `wandb/`, `mlruns/`, `.dvc/cache/` into `ignore` (block audit noise).
5. **Compute specificity** — don't hardcode a number; *compute* it with the formula in `learning-protocol.md`
   §4: the ratio of each rule's `origin` weight (`preset`=0, `inductive`/`learned`=1). `directories[]`
   discovered inductively and re-induced naming get `origin: inductive`; the bare preset skeleton gets
   `origin: preset`. Pure preset is 0.0, with anything >0 reflecting how much inductive correction is mixed
   in. It then converges to 1 with each `omp-learn` promotion. (Every preset follows this same rule — no
   hardcoded numbers.)
6. **`project.preset_origin`** = record `"python-ml"` (provenance).

> **Handling empty channels**: if the scan finds no `data/`, **do not create** any dataset-related rules or
> manifest (forcing something that doesn't exist is noise). This preset's dataset section is active only when
> `data/` actually exists.

## 5. What `omp-learn` usually specializes for this type (specialization examples)

Patterns frequently observed in operation → promotion candidates (via the human approval gate, with provenance
recorded in `learned_refs`):

| observation | promotion result (project-owned rule) |
|:---|:---|
| ".pkl always lands in `data/processed/`" 3+ times | add a `data/processed/*.pkl` enforcement rule, any other location = error |
| "checkpoints follow the `models/<exp>/epoch=NN.ckpt` pattern" | pin the Lightning naming regex as a project rule |
| "each experiment has a 1:1 `configs/<exp>.yaml` + `models/<exp>/`" | config↔model pairing validation rule (`omp-audit` detects orphans) |
| "raw is date-foldered as `data/raw/YYYY-MM-DD_<source>/`" | enforce date-directory naming, severity warn→error |
| "notebook number prefixes are actually consistent" | promote §2's `info` notebook rule to `warn` |
| "this repo uses an `experiments/` directory (not in the preset)" | add a new `directories[]` entry, specificity rises |

What accumulates automatically into the light channel (`.omp/wiki/`) without approval: **reference notes** like
"this project uses parquet", "the seed=42 convention", "the train script reads a hydra config". **Context** that
isn't a rule (doesn't trigger file moves) goes to the wiki.

---

**Seed sources**: the intersection of the Cookiecutter Data Science layout + Python `src`-layout packaging
conventions + common ML research repo practices. To avoid coupling to a specific framework
(PyTorch/TF/Lightning/Hydra), it holds **only a generic skeleton** — framework-specific specialization is
induced by `omp-learn` from actual usage.
