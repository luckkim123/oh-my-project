---
name: omp-pilot
description: |
  Point at one project folder → full `.omp/` SSOT orchestration. If `.omp/` is missing, absorb init
  (scan → inductive + preset synthesis → draft rules.json → human gate) to bootstrap, then weave the
  codify → organize → dataset → doc management loop with a user confirmation at every gate. The
  project-management counterpart of OMC autopilot — not a generation pipeline but a loop that updates
  a living `.omp/`. Supports `--from <stage>` re-entry.
  Triggers: 이 프로젝트 정리해줘, 폴더 통째로 관리, 프로젝트 셋업, .omp 만들어줘, omp 부트스트랩,
  project pilot, manage this project, end to end 프로젝트, 알아서 정리해줘, omp pilot
next-skill: omp-brief
---

# omp-pilot — full `.omp/` orchestration (the project-management counterpart of autopilot)

<Purpose>
Takes a single project folder and auto-coordinates every stage that bootstraps and updates the `.omp/` SSOT (bootstrap → rule codification → relocation → dataset registration → docs). The user only says *which folder to hand off to the assistant*; the harness decides *which preset to synthesize with, which rules to verify against, and what to move*. It is the project-management counterpart of omc autopilot, but it preserves the essence of omp: **a management loop, not a generation pipeline** — it keeps updating one living `.omp/` rather than producing a fresh artifact each time. Because the risk is high (a rule change can trigger file moves), there is a gate at every stage — it is not fully autonomous.
</Purpose>

<Use_When>
- End-to-end requests like "manage this whole project folder for me" — starting from a new folder that has no `.omp/` yet
- When you want to run the full management loop of a project that already has `.omp/` in one shot (codify → organize → dataset → doc update)
- When a higher meta-harness (omha) delegates project-management work to omp (a self-sufficient entry point)
- When it's clear which stage to start from, start there (`--from`)
</Use_When>

<Do_Not_Use_When>
- If only one stage is needed → use the corresponding omp-* skill directly (`omp-audit` only, `omp-organize` only, etc.)
- When you only want to review rule-candidate promotions → use `omp-learn` directly (not wired into the pilot loop — promotion is a heavy gate, so it's a separate ritual)
- When you only want a plain rule-compliance PASS/FAIL verdict → use `omp-audit` directly
- When you expect actual dataset data to be moved or a remote push → omp is metadata-only. Moving actual data is not omp's job (delegate when DVC/git-lfs is detected)
</Do_Not_Use_When>

<Execution_Policy>
- Each stage is dispatched as a fresh subagent — protecting controller context. Each stage delegates to a dedicated omp-* skill (no re-implementation).
- Gates are user decision points — no automatic pass-through. Risk = the user's files being moved, so confirmation is never skipped.
- **Single-focus write enforcement**: the only agent that moves files is `organizer`. The rest (project-scanner / rule-architect / auditor) are read-only (`disallowedTools: [Write, Edit, NotebookEdit]`). dataset-curator writes only the manifest and does not move data. No stage self-approves (detection ≠ execution separation: auditor detects → organizer moves).
- ⚠️ **omp-organize must never auto-move**: `references/safe-fileops.md` is enforced by organizer — (1) **dry-run** first (output the full move plan + the verify commands that will run, with 0 mutations), (2) execute only after **human approval**, (3) move = `mv` → verify the destination retains the files via `find`/`ls` (compare SHA-256 for critical files) → **only then** delete the source (no `rm` in the same breath — iCloud/Drive sync lag, exFAT AppleDouble residue), (4) deletion goes **through trash** (OS branch: macOS `trash`/`~/.Trash`, Linux `gio trash`/`trash-cli`, Windows recycle bin; if no trash, only after human re-confirmation), (5) in sync folders **avoid rename** (delete the old path only when the `diff -rq old new` subset check passes).
- ⚠️ **omp never absorbs the user's files into `.omp/`** (`references/output-layout.md` core principle). `.omp/` holds only the knowledge omp has *about* this project (rules/inventory/docs/learning); the actual project files are managed in-place where they are.
- **Generic→specialized synthesis + explicit human gate (omp-specific)**: the init-absorption stage **synthesizes** (a) project-scanner's actual folder induction + (b) rule-architect's best-preset match into a draft `rules.json` — it is never auto-finalized; it must pass a **human approval gate** to become `.omp/rules.json`. Specialization during later operation runs on 2 channels (`references/output-layout.md` §"Two learning channels"): the heavy channel (`learned.md` → `omp-learn` → rule-architect promotion judgment → **human approval gate** → `rules.json.specificity` rising 0→1) and the light channel (`wiki/*.md` auto-append, no approval needed, recovered via grep next session). The learning-promotion protocol is owned by `references/learning-protocol.md` as SSOT (fall back to `output-layout.md` §learning channels if absent) — pilot does not wire in the heavy channel automatically; it leaves that to a separate `omp-learn`.
- **Record priority context on entry (compaction survival)**: at pipeline start, write the critical constraints into the `## Priority Context` section of `<project>/.omp/notepad.md` — "do not move user files into `.omp/` / only organizer moves, safe-fileops enforced, dry-run + human approval before any move / dataset is metadata-only, never touches data / a rule change = heavy gate + current gate position + project root path". So that even if context is compacted in a long loop, the safety protocol and gate position are always restorable.
  - **.md is the default**: write/append directly to `<project>/.omp/notepad.md`. When the notepad MCP is available, it can be mirrored via `notepad_write_priority(...)` (same .md target, optional accelerator) — equivalent behavior via .md write even when absent; not an error.
- **Every gate passage is logged to the ledger (secretary axis §4.1).** Immediately after each GATE decision (0/1/2/3) is made, call `hooks/omp_secretary.py`'s `append_ledger(root, {"event": "gate_passed", "stage": <init|codify|organize|dataset>, "decision": <proceed|revise|abort>})`. This is the only place pilot writes to the secretary axis directly (hook-owned mechanical append, D7) — it is what lets `omp-brief`'s `derive_status` later say "last session ended at organize GATE 2" instead of that history living only in the turn's own output (design §2.1). A `revise` loop re-logs the event each time the same gate is re-decided; only the human's decision text goes in `decision`, never a derived judgment.
- Stage outputs and progress state are fixed at **`<project>/.omp/`** (a verified real path — `PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md` + `rules.json`/`manifest.json` + `learned.md` + `wiki/`; unverified sub-segments like `.omp/state`·`sessions/{sid}` are not hard-coded). When codify/dataset changes a .json, regenerate the paired .md in the same pass to keep drift at 0.
  - ⚠️ **The 30s trap (only when state MCP is adopted in the future — not in effect now)**: if you start using the state MCP, do not call `state_clear` *right before* a stage handoff (it disables the stop-hook for 30s, silently breaking the loop). Use `state_write(active=false)` for non-terminal handoffs; reserve `state_clear` for *terminal only*. **Right now the state MCP is not actually invoked (the .md/`.omp/` files are the default), so this is a pure future-proofing note.**
</Execution_Policy>

<Steps>
0. **Check whether `.omp/` exists → branch** (pilot's first action):
   - If `<project>/.omp/rules.json` is **missing** → **init-absorption branch**: run omp-init as a one-shot bootstrap inside this pilot (the way omd docs-pilot absorbs intake).
     - (a) project-scanner **induces** the actual folder tree, extension distribution, and naming patterns (read-only, 0 guessing)
     - (b) rule-architect(opus) matches the best preset among `references/presets/*.md` (python-ml/web-app/research-lab/monorepo/johnny-decimal/para/generic)
     - (c) **synthesize** (a)+(b) → draft `rules.json` (conforming to `references/schemas/rules.schema.json`) + `manifest.json` (`references/schemas/manifest.schema.json`) + human-facing draft `PROJECT.md`/`STRUCTURE.md`/`NAMING.md`
     ━━━ **GATE 0: draft rules.json approval (human)** — proceed/revise/abort. Whether to commit `.omp/` (`.gitignore` hint) is also asked once and recorded here. Log `append_ledger(root, {"event":"gate_passed","stage":"init","decision":<proceed|revise|abort>})`. ━━━
   - If `<project>/.omp/rules.json` **already exists** → init only warns "re-initialize?" and **skips**, starting the management loop from step 1 (codify) with the existing `.omp/` as input.
1. **codify**: omp-codify → codify and update structure/naming rules (`rules.json` + `STRUCTURE.md`/`NAMING.md`, paired sync). dispatch: rule-architect.
   - *If the rules are unchanged right after GATE 0 and there is nothing to update*, skip.
   ━━━ **GATE 1: rule change approval (human)** — present the change diff, proceed/revise/abort. Log `append_ledger(root, {"event":"gate_passed","stage":"codify","decision":<proceed|revise|abort>})`. ━━━
2. **organize**: omp-organize → detect rule violations (auditor) → propose and execute relocation (organizer). dispatch: auditor (detect) → organizer (move).
   - ⚠️ `references/safe-fileops.md` enforced + **dry-run first** + **human approval before any move**. If there are no violations, report "no cleanup needed" and skip.
   ━━━ **GATE 2: move-plan approval (human)** — review the dry-run output (from→to + cited violated rule), approve/revise/abort. 0 mutations on any file before approval. Log `append_ledger(root, {"event":"gate_passed","stage":"organize","decision":<proceed|revise|abort>})`. ━━━
3. **dataset**: omp-dataset → register datasets, track SHA256, split, lineage (`manifest.json` + `DATASETS.md`). dispatch: dataset-curator.
   - ⚠️ **metadata-only**: does not copy/move actual data or remote-push. When `.dvc/`·git-lfs is detected, delegate with "under DVC management — manifest mirrors metadata only". If there are no datasets, skip.
   ━━━ **GATE 3: dataset registration confirmation (human)** — review the manifest entries, confirm/revise. Log `append_ledger(root, {"event":"gate_passed","stage":"dataset","decision":<proceed|revise|abort>})`. ━━━
4. **doc**: omp-doc → generate and update the human-facing `.omp/` docs (`PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md`). dispatch: project-scanner (supplies inventory). (omp-doc is `.omp/`-doc-centric — not a root README generator.)
   - If the docs are up to date, skip. (No gate — human-facing docs are a light artifact)
5. **terminal**: report completion of one turn of the management loop. A listing of the updated SSOT paths in `.omp/` + the decision history of each gate + the next recommended action (re-confirm compliance with `omp-audit` / review promotion with `omp-learn` once observations have accumulated).
   - ⚠️ omp does **not** clean up or delete the user's files — pilot's terminal is merely a report of the `.omp/` knowledge update; cleanup of user assets only goes through the explicit `omp-organize` path (safe-fileops enforced).
   - **Terminal handoff to `omp-brief` (once, always last)**: after the completion report above, invoke `omp-brief` exactly once to regenerate `.omp/secretary/BRIEF.md` from the ledger this run just wrote (frontmatter `next-skill: omp-brief`). This is a pull-style refresh, not a second gate — it runs whether the loop ended in full completion, an early skip, or an `abort`, so the next session's SessionStart briefing always reflects where this run actually stopped.

> **`--from <stage>` entry point**: you can start from a middle stage — `init|codify|organize|dataset|doc`. If `.omp/` already exists, step 0's branch automatically starts from codify (init skipped). E.g. `--from organize` starts from violation detection (organize) using the existing `rules.json` as input; `--from dataset` starts from dataset registration. Every entry goes through that stage's gate as-is (no gate bypass).

6. **Task delegation (the final action of each stage)**: the stages above are dispatched as fresh subagents. The induction channel of the omp-init absorption branch (0-(a)) and the omp-doc inventory (step 4) are delegated to the read-only project-scanner:

```
Task(
  subagent_type="oh-my-project:project-scanner",
  description="<project> folder read-only inventory + induction of de-facto structure/naming patterns",
  prompt="""
Project root: <project absolute path>
Mission (read-only — never write or move):
1. Directory tree inventory: depth, file count per directory, extension distribution, approximate size.
   Separate non-source/ignore areas (.git/ node_modules/ .venv/ __pycache__/ .omp/) as rules.json.ignore candidates.
2. Induce de-facto structure: what each directory *actually* does + observed evidence (e.g. 'data/raw/ all 12 are .csv → dedicated to raw data').
3. Induce naming patterns: recurring basename rules → candidate Python re regex (the naming.patterns[].regex format of rules.schema.json)
   + matching examples + violation examples + confidence (N/M match, strong/weak).
4. Report external-management signals: .dvc/ git-lfs (.gitattributes lfs entries) — input for dataset-curator's 'mirror metadata only' judgment.
Constraints: 0 guessing/imagination, bind only to actual tree/grep results. Do not *design* rules or synthesize presets (that's rule-architect).
No PASS/FAIL verdict (that's auditor). Do not write any file under .omp/ — the output is the report (text) only.
Output: inventory + induced structure patterns (with evidence) + induced naming patterns (regex+examples+confidence) + ignore candidates + external-management signals.
"""
)
```

After dispatch: hand project-scanner's induction report to rule-architect(opus) to synthesize with the preset → draft rules.json → GATE 0. The later stages (codify/organize/dataset) each have their own omp-* skill dispatch rule-architect / auditor→organizer / dataset-curator (pilot only coordinates the gates and handoffs, no agent re-implementation).
</Steps>

<Output>
The output of one turn of the management loop = the **updated `<project>/.omp/` SSOT** (an update of living knowledge, not a "new artifact" of a generation pipeline):
- Human-facing: `PROJECT.md` / `STRUCTURE.md` / `NAMING.md` / `DATASETS.md`
- Machine-facing: `rules.json` (specificity tracking) / `manifest.json` (SHA256·split·lineage)
- Learning: `learned.md` (awaiting promotion) / `wiki/` (auto-accumulated)

Path conventions are owned by `references/output-layout.md` as SSOT. + GATE 0~3 decision history + organize's move log (the actual from→to moves, only those approved after dry-run) + whether dataset was delegated to external management (.dvc/git-lfs) + remaining items needing human confirmation (weak patterns / promotion candidates held back by rule-architect) + the next recommended stage (`omp-audit` re-check / `omp-learn` promotion review). User files stay in place (not absorbed into `.omp/`); states explicitly that it does not self-approve.
</Output>

<Self_Sufficiency>
This skill is a self-sufficient entry point. So that a higher meta-harness (omha) can call it with a single line — "delegate to omp omp-pilot" — for project-management work, it runs the full management loop, gates and all, from `.omp/` bootstrap (init absorption) onward with nothing but the project root path and no external context.
</Self_Sufficiency>
