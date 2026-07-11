---
name: omp-init
description: |
  One-time bootstrap — inductively scans a project folder, matches the best-fitting preset, and **synthesizes**
  the entire `.omp/` SSOT (PROJECT/STRUCTURE/NAMING/DATASETS.md + rules.json/manifest.json + learned.md + wiki/).
  The draft rules.json is finalized only after a human approval gate — starts generic and immediately becomes a starting point specialized to this project.
  If `.omp/` already exists, it warns "re-initialize?" and stops.
  Triggers: omp 초기화, 프로젝트 초기화, .omp 만들어, init, 부트스트랩, 폴더 스캔해줘,
  이 프로젝트 파악해, 프로젝트 세팅, omp init, project init, initialize project, scan this folder
---

# omp-init — one-time bootstrap (folder scan + preset synthesis → create .omp/)

<Purpose>
The bootstrap you run exactly once when first encountering a project folder. It **inductively** scans the actual folder tree (project-scanner) and **matches and synthesizes** the best-fitting generic preset (rule-architect) to produce the entire `.omp/` SSOT. Synthesis is the key — copy-pasting the preset alone stays generic, and induction alone has no seed. Combining the two produces a draft rules.json that is *generic at distribution, specialized to this folder the moment it lands*, then passes it through a human approval gate. This is the starting point of omp's "generic→specialized" asymmetry.
</Purpose>

<Use_When>
- A project folder does not yet have `.omp/`, and you are starting to manage it with omp
- A first entry like "understand this project / scan the folder / omp initialize"
- When `omp-pilot` detects the absence of `.omp` and absorbs init as a call (in that case the caller enters via this skill)
</Use_When>

<Do_Not_Use_When>
- `.omp/` already exists → re-initializing wipes existing learning (learned.md, wiki, specificity). To change only the rules → `omp-codify`; to promote observations into rules → `omp-learn`. (Still, if the user deliberately wants to re-initialize, use the re-initialization branch in Steps below.)
- You want to keep the rules as-is and only catch violations → `omp-audit` (detect) / `omp-organize` (relocate)
- You only want to register datasets → `omp-dataset`
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Synthesis is the essence, no copy-paste**: the draft rules.json must be a **synthesis of both** (a) project-scanner's induction of the actual tree, extensions, and naming patterns + (b) rule-architect's preset match. Copying a preset verbatim leaves `specificity` stuck at 0. Synthesize so the actually-observed structure from induction overwrites the preset seed. (Evolution mechanism SSOT: `references/learning-protocol.md`; channel definitions: `references/output-layout.md` §"Two learning channels".)
- ⚠️ **The human approval gate must not auto-pass**: the draft rules.json is a *proposal*. Do not commit `.omp/rules.json` as final until the human decides proceed/revise/abort. Because the rules are a heavy decision that triggers file moves (organize), the gate is mandatory.
- **Stop if `.omp` exists**: in the first step, check `<project>/.omp/`. If present, stop immediately and warn "already initialized — re-initializing causes learning loss (learned.md/wiki/specificity)" + require explicit user re-confirmation before proceeding.
- **Read first, write only after the gate**: both project-scanner and rule-architect are **read-only** (disallowedTools=[Write,Edit,NotebookEdit]) — at the init stage they never write a file. The actual writing of `.omp/` is done by the calling context after the gate passes (or delegated to codify). No self-approval: the rule-architect that designed the rules cannot approve and enforce those same rules in the same pass.
- **Record `specificity` honestly**: right after synthesis, the draft's specificity is usually 0.1–0.4 (preset skeleton + inductive correction). Do not inflate it to 1 — true specialization rises during operation via `omp-learn` promotion.
- **Metadata-only**: the scanner only *identifies* dataset candidates (large files, extensions). Actual recording of SHA256/split/lineage is the job of `omp-dataset` (dataset-curator). init only seeds an empty/shallow inventory in manifest.json.
- **Cross-platform**: all paths are relative or based on `Path.cwd()`. No hardcoded absolute paths or `~`. When scanning the tree, put `.git/**`, `node_modules/**`, `.omp/**` into the ignore seed.
- **Ask about .gitignore once**: per `references/output-layout.md` §".gitignore guidance", init asks once whether to commit `.omp/` (sharing `rules.json`/`*.md` recommended, `wiki/` is personal) and records the choice.
</Execution_Policy>

<Steps>
1. **Check `.omp` existence (gate 0)**: if `<project>/.omp/` exists, stop and warn — "already initialized. Re-initializing loses learned.md, wiki/, specificity. Really re-initialize?" Continue only after explicit user consent (recommend backing up existing learning: via trash or preserving to `.omp.bak/`). If absent, move on.
2. **Confirm scan scope**: briefly confirm the project root path, the rough nature (if the user knows it), and any huge directories to ignore (build artifacts, etc.). If unknown, proceed with defaults (full scan, standard ignore).
3. **Inductive scan (dispatch ①)**: delegate the folder inventory, structure induction, and file classification to project-scanner — produce the actual tree, extension distribution, naming patterns, and large-file/data candidates *as observed facts only* (no guessing). read-only. Since the scanner output (inventory report) is the synthesis input, record it to `.omp/work/scans/scan-{YYYY-MM-DD-HHMM}.json` — ⚠️ because the scanner is read-only (it cannot write its own output to disk), **this recording is done by the calling skill (init)** (preserving the scanner read-only invariant). After recording, run retention cleanup on `.omp/work/scans/`: keep only the latest N=10 and prune older scans via trash (no permanent `rm`), with a one-line "pruned X old scans" report — the skill that recorded trims its own subfolder. `references/output-layout.md` work layer.
4. **Preset match + synthesis (dispatch ②)**: delegate to rule-architect with the scanner output as input — pick the best-fitting seed among `references/presets/*.md` (python-ml/web-app/research-lab/monorepo/johnny-decimal/para/generic), correct it with the inductive results, and synthesize the **draft rules.json**. The schema must conform to `references/schemas/rules.schema.json` (`omp_version`/`project`/`specificity`/`structure`/`naming` required; specify the chosen preset in `preset_origin`). Seed manifest.json shallowly per `references/schemas/manifest.schema.json` (file inventory; dataset entries are candidate-identification only). read-only — does not write to disk, returns the draft as text.
   ━━━ **GATE 1 (core): approve the draft rules.json (human)** — proceed / revise / abort. Present the matched preset, the synthesized structure/naming rules, and the estimated specificity to the human and get a decision. Also note that approval creates a `secretary/` skeleton (empty todo/raid/journal/decisions) alongside the SSOT. No auto-pass. On revise, go back to step 4 and re-synthesize. ━━━
5. **Write `.omp/` (only after the gate passes)**: generate the SSOT with the approved draft per the fixed structure in `references/output-layout.md` —
   - `.omp/rules.json` (approved), `.omp/manifest.json` (seed inventory) — both .json writes go through the atomic write in `hooks/omp_atomic.py` to prevent partial-write corruption (T20).
   - `.omp/STRUCTURE.md`, `.omp/NAMING.md` (the human-facing narrative of rules.json — .md↔.json pairs, kept consistent with each other)
   - `.omp/PROJECT.md` (what this project is, one screen), `.omp/DATASETS.md` (the manifest dataset view; at init time a candidate list or an empty catalog)
   - `.omp/learned.md` (empty observation log, the promotion-pending channel), `.omp/wiki/` (empty directory, the auto-accumulating channel)
   - `.omp/secretary/` skeleton (created by default — the secretary/time axis, `references/secretary-protocol.md` SSOT): empty `todo.txt`, a `raid.md` with the 4 empty section headers (`## Risks` / `## Assumptions` / `## Issues` / `## Dependencies`), and empty `journal/` and `decisions/` directories. `BRIEF.md` and `ledger.jsonl` are **not** created here — the first `omp-brief`/ledger-writing event creates them, so an empty BRIEF is never mistaken for a stale one.
   - record the .gitignore choice (§Execution_Policy).
6. **Confirmation report**: report to the user the list of generated `.omp/` paths (including the `secretary/` skeleton) + the selected `preset_origin` + the draft `specificity` + "next-step candidates (refine rules with codify / register datasets / check compliance with audit)". Since init is a one-time bootstrap, it ends here (no loop entry).

> **dispatch reality**: the two delegations through step 4 are read-only diagnostics — zero disk changes. The actual `.omp/` writing happens only in step 5 after GATE 1 passes.
>
> ```
> # Step 3 — inductive scan
> Task(
>   subagent_type="oh-my-project:project-scanner",
>   description="Inductive scan of the project folder",
>   prompt="Scan the <project root> folder read-only. Produce the actual tree, extension distribution, naming patterns, "
>          "and large-file/data candidates as observed facts only (no guessing). ignore: .git/** node_modules/** .omp/**. "
>          "The output is the inventory that rule-architect will use for preset synthesis."
> )
> # Step 4 — preset match + synthesis (with scanner output as input)
> Task(
>   subagent_type="oh-my-project:rule-architect",
>   description="Match preset and synthesize draft rules.json",
>   prompt="With the project-scanner inventory as input, pick the best match among references/presets/*.md and "
>          "correct it with the inductive results to synthesize the draft rules.json. Conform to references/schemas/rules.schema.json, "
>          "record preset_origin and specificity honestly. read-only — do not write to disk, return only the draft text. "
>          "No self-approval (GATE 1 is the human)."
> )
> ```
</Steps>

<Output>
The full list of generated `.omp/` SSOT paths (`PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md` + `rules.json`/`manifest.json` + `learned.md` + `wiki/` + the `secretary/` skeleton — `todo.txt`/`raid.md`/`journal/`/`decisions/`) — `CONVENTIONS.md` is not always created by init; codify/learn generate it when `content_conventions[]` exists + the matched `preset_origin` + the draft `specificity` (an honest starting value close to 0) + the GATE 1 decision history (proceed/revise/abort) + the recorded .gitignore choice + next-step candidates (codify/dataset/audit). If `.omp` already exists: state the warning message + that re-initialization was not performed (or proceeds only with explicit user consent). Report that nothing was committed to disk as final before the gate passed (only read-only diagnostics were performed).
</Output>
