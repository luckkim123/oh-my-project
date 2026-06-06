---
name: omp-doc
description: |
  Human-facing project documentation generation and refresh — writes or updates the human-readable .md files like
  `.omp/PROJECT.md`·`STRUCTURE.md`·`NAMING.md`·`DATASETS.md`, grounded in the project-scanner inventory. It absorbs the
  "read the codebase and produce professional documentation" spirit of readme-project, but omp centers on the `.omp/`
  docs rather than the repo root — the output is knowledge *about* the project, not the project itself. Reflects only the
  actual tree, no guessing. omp stage 4.
  Triggers: 문서 갱신, PROJECT.md 써줘, 프로젝트 문서, 개요 정리, STRUCTURE.md 갱신, 폴더 설명 써줘,
  document the project, update project docs, write PROJECT.md, refresh .omp docs
---

# omp-doc — human-facing project documentation generation and refresh (omp stage 4)

<Purpose>
Create and update **human-facing .md documents** so that someone seeing the project for the first time (or future-you)
can learn, from a single screen, "what this project is, how the folders are laid out, how things are named, and what the
data is."

The targets are the 4 human documents in `.omp/` — `PROJECT.md` / `STRUCTURE.md` / `NAMING.md` / `DATASETS.md`.
All of them must be written grounded in project-scanner's actual folder inventory (no guessing). Just as readme-project
produces a README at the repo root, omp-doc follows the same "read the codebase carefully → professional documentation"
spirit, except the output is not the project itself but the *knowledge about the project* inside `<project>/.omp/`.

⚠️ **Essential distinction — human .md ↔ machine .json are a pair but have different authority.** omp-doc is the skill
that writes the narrative of the *human .md*. The enforced-rule SSOT for `STRUCTURE.md`/`NAMING.md` is `rules.json`, and
that belongs to `omp-codify` (rule-architect); the SSOT for `DATASETS.md` is `manifest.json`, and that belongs to
`omp-dataset` (dataset-curator). omp-doc does the **narrative update that unpacks the already-finalized .json into a
human-readable form**, it does not newly *decide* the rules or inventory themselves. When a decision is needed, hand off
to codify/dataset.
</Purpose>

<Use_When>
- `.omp/` already exists (= init done) and you need to newly write or refresh the human docs
- The folders have drifted significantly and `STRUCTURE.md`/`PROJECT.md` no longer match reality ("update the docs")
- A first-time reader needs a single-screen overview (`PROJECT.md`) of "what this project is"
- Right after codify/dataset changed `rules.json`/`manifest.json`, to sync the paired .md narrative
- A single document is specifically targeted ("rewrite just `NAMING.md`")
</Use_When>

<Do_Not_Use_When>
- When `.omp/` does not exist yet → `omp-init` first (bootstrap already lays down a *draft* of PROJECT/STRUCTURE/NAMING)
- When trying to change the enforced rules themselves → `omp-codify` (rule-architect, `rules.json` SSOT). omp-doc only
  *narrates* the rules, it does not *decide* them.
- When registering datasets, checksumming, splitting, or tracking lineage → `omp-dataset` (dataset-curator, `manifest.json` SSOT).
  omp-doc's `DATASETS.md` is just a human view of the manifest, it does not newly write the manifest.
- When detecting rule violations and relocating → `omp-audit` (detect) → `omp-organize` (move). omp-doc does not move files.
- When the goal is a deployable README at the repo root, unrelated to `.omp/` knowledge → the user-scope `readme-project` skill
  (omp centers on .omp/ docs, it is not a root-README generator. That said, if the request is to draft a README based on
  PROJECT.md, omp-doc can assist with that conversion — but the output's SSOT is .omp/.)
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **No guessing — actual tree only.** Every narrative must be grounded in the folders, files, extensions, and naming
  patterns that project-scanner actually measured. Do not fill the document with generalities like "projects like this
  usually…". Inventing a folder or role not in the inventory makes the document a lie (same as readme-project's "read the
  codebase carefully" principle).
- ⚠️ **Read-only dispatch.** The project-scanner this stage calls is a read-only agent
  (`disallowedTools: [Write, Edit, NotebookEdit]`). It only retrieves the inventory; *writing* the `.omp/*.md` files is
  done by the controller (this skill). The human .md does not move code or data, so an organizer is not needed.
- ⚠️ **Does not touch .json.** omp-doc never modifies `rules.json`/`manifest.json` (read-only). If the .md narrative
  appears to conflict with the .json → the .json is the truth, so update the .md to match the .json, or if the .json side
  is wrong, hand off to codify/dataset (do not fix the .json here). The pair-sync rule is governed by the
  `references/output-layout.md` "Human .md ↔ Machine .json pairing" section as SSOT.
- **In-place update + change summary.** If an existing .md is present, before overwriting it wholesale show the human a
  one-line diff summary of what changes (added/removed folders, new naming patterns, etc.) and then proceed. Human
  documents may have the user's handwriting mixed in — for large structural changes, get confirmation.
- **Auto-accumulate to wiki (light channel).** Non-obvious patterns and decisions discovered while writing the docs
  ("in this repo `tests/` mirrors the `src/` structure", "`legacy/` is frozen") are auto-appended to `.omp/wiki/*.md` —
  no approval gate, for grep retrieval next session. ⚠️ The wiki is **append-only, no wholesale overwrite** — the
  "overwrite wholesale" just above applies only to the *human SSOT .md (PROJECT/STRUCTURE/NAMING/DATASETS)*, and a wiki
  note never erases existing content, it only appends a new section (`references/learning-protocol.md` §5). For an
  observation worth *promoting* to a rule, do not auto-enforce — record it as a candidate in `.omp/learned.md` and pass
  it to the `omp-learn` gate. For the distinction between the two channels, see `references/learning-protocol.md`.
- **Single dispatch.** The inventory can scan multiple folders in one pass, so a single project-scanner dispatch is
  enough. Do not parallel fan-out to scan the 4 documents separately (that just reads the same tree redundantly).
- **No gate (not a verdict stage).** omp-doc is a light stage that writes human documents and has no risky actions like
  moving files or enforcing rules, so it has no approval gate (in contrast to `omp-organize`/`omp-learn`). The
  confirmation above for large structural changes is a courtesy one-line check, not a formal gate.
</Execution_Policy>

<Steps>
1. **Determine target documents.** Figure out which document(s) the user wants — a refresh of all 4
   (`PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md`), or a specific one. First confirm whether `.omp/` actually
   exists (if not, guide to `omp-init` and stop). Path convention is governed by `references/output-layout.md` as SSOT.
2. **Read the existing SSOT.** Read the existing 4 .md files in `.omp/` plus the paired `.omp/rules.json`·`.omp/manifest.json`
   to grasp the current state. The schemas are `references/schemas/rules.schema.json`·
   `references/schemas/manifest.schema.json`. The .md narrative must *agree* with these .json files (the .json is the
   truth). Also grep `.omp/wiki/` to retrieve patterns and decisions left by previous sessions.
3. **Hypothesize what changed.** Point out where the existing documents drifted from reality (e.g., a new folder not in
   the doc, a vanished directory, a new extension cluster). Validate this hypothesis with the next scan — before
   *rewriting* the document, figure out *what* to fix first.
4. **Pre-announce the change summary (when an existing document is present).** Before overwriting wholesale, show the user
   a one-line diff of the folders/roles/naming patterns to be added/removed. For large structural changes, get
   confirmation to proceed (protect human handwriting).
5. **Write/update the documents (controller writes the .md).** Write the .md grounded in the project-scanner inventory:
   - `PROJECT.md` — single-screen overview (what project, core purpose, entry points). Absorb readme-project's
     hero/value-prop spirit into .omp/: scanability > completeness.
   - `STRUCTURE.md` — folder tree + role of each directory. Unpack `rules.json`'s structure rules into a human-readable narrative.
   - `NAMING.md` — naming rules + actual examples. Make it consistent with `rules.json`'s naming rules.
   - `DATASETS.md` — a human catalog view of `manifest.json` datasets[] (checksum·split·lineage summary).
   If it conflicts with the paired .json, match the .json. Record non-obvious patterns separately in `.omp/wiki/` and
   rule-promotion candidates in `.omp/learned.md` (`references/learning-protocol.md`).
6. **Task dispatch (inventory collection — always the core of the final step).** The measured inventory that *grounds*
   the writing/updating above is delegated to the read-only `project-scanner`. This skill is the controller that receives
   the inventory and writes the .md:

   ```
   Task(
     subagent_type="oh-my-project:project-scanner",
     description="Inventory project tree for .omp human docs",
     prompt="""
     Measure the folder tree and file inventory of <project> and return it as the basis for omp-doc's human-facing documentation.
     - Folder tree (directories by depth + the representative file clusters / extension distribution of each folder)
     - Naming-pattern induction (prefix/suffix/case/numbering scheme — only from actual filenames, no generalities)
     - Entry-point candidates (real files of the README/main/entrypoint/manifest kind)
     - Mismatches between the existing .omp/rules.json·manifest.json and reality (folders in the docs but absent, and vice versa)
     - Non-obvious structural observations (mirror structure, frozen folders, data-directory location, etc.)
     ⚠️ No guessing — only what is actually in the tree. Do not invent folders or roles that do not exist.
     ⚠️ read-only — do not create or move files (writing .omp/*.md is done by the omp-doc controller).
     Output: a per-folder role table + a naming-pattern list + entry points + a .json↔reality diff + non-obvious observations.
     """
   )
   ```

   Once the scanner returns the inventory → perform the step 5 writing, complete the pair-.json sync, wiki accumulation,
   and learned-candidate separation, then report the output paths (omp-doc itself does not render a PASS/FAIL verdict —
   that is `omp-audit`).
</Steps>

<Output>
A list of refreshed/created `.omp/` human .md paths (whichever of `PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md`
you worked on) + a change summary versus the previous state (added/removed folders·naming patterns) + the pair-.json sync
result (whether the conflict was matched to the .md side, or a .json mismatch needing handoff to codify/dataset) + the
patterns newly appended to `.omp/wiki/` (if any) + the rule-promotion candidates written to `.omp/learned.md` (if any, →
to the `omp-learn` gate). Path convention is governed by `references/output-layout.md` as SSOT. Next-step guidance: to
enforce rules use `omp-codify`, for compliance verification use `omp-audit`.
</Output>
