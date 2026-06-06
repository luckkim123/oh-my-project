---
name: omp-dataset
description: |
  dataset registration and tracking — records each data file's SHA-256 (hashlib), size, rows, split, and lineage in `.omp/manifest.json`
  and refreshes the human-readable `.omp/DATASETS.md` catalog. Metadata-only: never copies, moves, or pushes the actual data; it only
  tracks "has it changed / where did it come from / is there leakage". On detecting DVC/git-lfs it does not claim ownership but delegates (mirrors metadata only).
  Triggers: dataset 등록, 데이터셋 추적, 체크섬, SHA256, manifest 갱신, split 추적, lineage,
  register dataset, track dataset, data inventory, train val leakage, 데이터 카탈로그
---

# omp-dataset — dataset registration and tracking (metadata-only inventory)

<Purpose>
Registers the project's data files into `.omp/manifest.json` as **pure metadata** — SHA-256 checksum, byte size, row count, train/val/test split membership, lineage (where it came from and what produced it), and source. After registration it regenerates the paired human-readable `.omp/DATASETS.md` catalog in the same pass. It is the "inventory ledger" of the code — it moves not a single byte of the actual data, only *describes* it, so it can answer "has this file changed?", "is there train/val leakage?", "where did this come from?". It delegates singly to the dataset-curator agent.
</Purpose>

<Use_When>
- When first registering a data file into `.omp/manifest.json` — **format is irrelevant**. Not only structured ML inputs (`.parquet`/`.csv`/`.npy`/`.pkl`/`.h5`/`.tfrecord`) but also robotics, sensor, and media data are all datasets: ROS bags (`.bag`/`.db3` + `metadata.yaml`), images and video (`.png`/`.jpg`/`.mp4`), point clouds (`.pcd`/`.las`), audio, checkpoints, embeddings, etc. — any data that "must stay fixed once produced and is worth tracking".
- When you want to track and refresh whether the data has changed (SHA-256 drift)
- When you want to group train/val/test splits to build a basis for leakage checks
- When you want to record lineage (source → generation script → output) to leave provenance behind
- When you want to keep the `.omp/DATASETS.md` human-readable data catalog in sync with the manifest

> **The criterion for what counts as a dataset = *role*, not format.** The test is "is this an input/collected data that must stay fixed and whose byte-level changes you want to track?". Even a `.npy` that is overwritten fresh every run is an *output*, not a dataset (→ run artifact); even a `.bag` is a dataset if it is an immutable *input* once collected. Do not let the extension whitelist narrow the definition — fields like `rows` that are specific to structured data can simply be omitted, so unstructured data registers fine as-is.
</Use_When>

<Do_Not_Use_When>
- If you need to **move** actual data files → this is not the dataset lane at all. File relocation is `omp-organize` (organizer + `references/safe-fileops.md`)
- If you are **inducing/classifying** folder structure or extension patterns → `omp-init`/project-scanner (the manifest handles datasets only)
- If you are creating or changing structure/naming **rules** → `omp-codify`/rule-architect (`rules.json`)
- If you need a PASS/FAIL **verdict** on rule compliance → `omp-audit`/auditor (dataset-curator does not self-audit)
- When the data is already **managed by DVC/git-lfs** and you feel omp should take it over → do not take it over. On detection, the policy is to delegate (mirror metadata only)
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Metadata-only, absolute rule**: the dataset-curator **never** does `mv`/`cp`/`rm`/symlink/`dvc push`/`git lfs push`/upload on data files. *Reading* bytes to hash them is the only contact with a data file. Moving data is outside the dataset lane (it belongs to `omp-organize`'s organizer). "Moving while registering" is the #1 failure mode of this domain — the dataset equivalent of citation fabrication.
- ⚠️ **SHA-256 is deterministic via the stdlib `hashlib`**: stream the raw file bytes in chunks (e.g. 1 MiB) to a lowercase 64-hex digest. Do not use per-OS CLIs (`shasum`/`sha256sum`/`certutil`) as the source of truth (hashlib is identical on macOS/Linux/Windows). If the hash is nondeterministic, the "has it changed?" signal itself becomes meaningless. For files too large, honestly substitute `"sha256": "UNHASHED"` (the schema allows it) + size/mtime — **never fabricate a fake hash**.
- ⚠️ **Do not invent metadata**: no uncounted `rows`, no plausible-looking `lineage`, no made-up `source`. If you don't know, **omit** the optional field. A wrong-but-plausible lineage is worse than none. If ambiguous (split assignment / lineage / whether this is even a dataset), don't guess — surface it to the human.
- ⚠️ **DVC/git-lfs is delegation, not competition**: on detecting `.dvc/`, `*.dvc`, or `filter=lfs` in `.gitattributes`, set `manifest.json.managed_by_external` (`tool: "dvc"` or `"git-lfs"`) + mirror metadata only + note "managed externally" in `DATASETS.md`. Do not re-hash to "verify" or push.
- **Paired regeneration is mandatory and in the same pass**: when `manifest.json.datasets[]` changes, regenerate `DATASETS.md` in the same run (`references/output-layout.md`: the human .md and machine .json must never drift).
- **Deterministic output**: sort `datasets[]` by a stable key (`id`) + a stable JSON format (sorted keys, fixed indentation) → an unchanged folder yields a byte-identical manifest. Paths use `pathlib.Path`, and a dataset `path` is **a project-root-relative path** (machine/OS portability).
- **No self-approval**: the dataset-curator only registers. Declaring dataset state "audited/compliant" is the separate `omp-audit` (auditor) lane. The handoff is "registered — ready for audit", never "registered and verified-clean".
- Generation is single and careful (the dataset equivalent of the citation-safe philosophy) — do not spin up multiple dataset-curators in parallel.
</Execution_Policy>

<Steps>
1. **Confirm `.omp/` exists**: if `<project>/.omp/` is absent, dataset registration is impossible — announce that `omp-init` must be run first to bootstrap, and stop. If it exists, load the existing `manifest.json` (the update target, do not clobber) and the contract (`references/schemas/manifest.schema.json`).
2. **Confirm registration scope**: the user-specified paths or data locations (`data/`/`datasets/`/`raw/`/`processed/` + structured `.parquet`/`.csv`/`.npy`/`.pkl`/`.h5`/`.tfrecord` *or* unstructured `.bag`/`.db3`/`.png`/`.mp4`/`.pcd` etc. — extensions are only examples; the determination follows the "role" criterion above). Take split membership/lineage/source from the user if they know them, but leave unknowns empty and let the dataset-curator fill them only on the basis of evidence.
3. **Detect external versioning first** (before hashing): `.dvc/`, `*.dvc`, `filter=lfs` in `.gitattributes`. If found, the delegation policy — set `managed_by_external` + mirror metadata only, confirm as the working policy that takeover/push is forbidden.
4. **Delegate singly to the dataset-curator** — `Task(subagent_type="oh-my-project:dataset-curator", ...)`:
   - **Inputs**: (a) the in-scope data file paths (if any), (b) known split/lineage/source hints (if any — otherwise omit), (c) the project root, (d) the contract card `references/schemas/manifest.schema.json`, (e) the output-path convention `references/output-layout.md`, (f) the data-movement boundary reference `references/safe-fileops.md` (stating that movement is the organizer's responsibility), (g) the self-learning channel `references/learning-protocol.md` (recurring observations go to `.omp/learned.md`/`.omp/wiki/` — rule promotion is `omp-learn`).
   - **Instructions**: write **only the two files** `.omp/manifest.json` and `.omp/DATASETS.md`. SHA-256 via stdlib `hashlib` streaming raw bytes (deterministic, lowercase 64-hex); if too large, an honest `UNHASHED`. `rows` only when actually counted, `lineage` only when there is evidence of a real script/source, group sibling splits via `split.group`. **Never** `mv`/`cp`/`rm`/push a data file. On detecting DVC/git-lfs, `managed_by_external` + mirror metadata only. Write after schema validation — writing `manifest.json` goes through the atomic write in `hooks/omp_atomic.py` so a partial write cannot corrupt the existing inventory (T20). Sort `datasets[]` by `id`, surface rather than invent when ambiguous, no self-approval ("registered — ready for audit" handoff).
5. Take the dataset-curator's output and consolidate: the list of registered datasets (id, path, sha256, size, rows, split, source) + external-versioning detection/action + the 2 files written + evidence-based lineage/split notes + ambiguous items requiring a human decision (not invented) + the "metadata-only confirmation (0 data files moved) + ready for omp-audit" handoff.
6. If there are items requiring a human decision (ambiguous split/lineage, `UNHASHED` handling), ask the user to confirm, then re-delegate to the dataset-curator to update the manifest. Recurring patterns worth solidifying into a rule (e.g. "the .pkl in this folder is always the processed split") are promoted via `omp-learn` (human gate) — the dataset-curator does not turn them into rules directly.
</Steps>

<Output>
The list of registered datasets (id → relative path · sha256 (64hex or UNHASHED) · size_bytes · rows · split role/ratio/group · source) + external-versioning detection result and action (DVC/git-lfs → `managed_by_external` mirror / none) + the 2 files written (`<project>/.omp/manifest.json`·`<project>/.omp/DATASETS.md`, regenerated in the same pass for 0 drift) + evidence-based lineage/split notes + remaining items needing human confirmation (ambiguous split/lineage/`UNHASHED` — not invented) + "metadata-only: 0 data files moved/copied/pushed, deterministic re-run = byte-identical manifest, no self-approval → ready for omp-audit (a separate pass)". The path/pairing convention is the SSOT in `references/output-layout.md`, the schema in `references/schemas/manifest.schema.json`.
</Output>
