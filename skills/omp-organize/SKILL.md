---
name: omp-organize
description: |
  Rule-violation detection → safe relocation — the auditor detects violations against .omp/rules.json,
  and the organizer moves files via the mv→verify→delete safety protocol. Human approval + dry-run enforced before any move.
  Detection (auditor read-only) ≠ execution (organizer write) separation. The only stage that moves files.
  Triggers: 정리해줘, 규칙대로 정리, 재배치, 파일 옮겨, 위반 정리, 폴더 정리,
  organize, reorganize, move files, 제자리에 놓아줘, 어긋난 파일, tidy up
---

# omp-organize — Rule-violation detection → safe relocation

<Purpose>
Find files that break the structure/naming rules codified in `.omp/rules.json`, and safely move them to the place the rules require. This splits into two lanes: **the auditor (read-only) detects violations**, and **the organizer (write) executes the moves**. Because this is the only stage in all of omp that actually moves files, it never bypasses the mv→verify→delete protocol, trash routing, rename avoidance, human approval, and dry-run defined in `references/safe-fileops.md`. If "organizing" loses a file, the entire value of omp collapses — every safeguard in this stage exists to prevent that one thing.
</Purpose>

<Use_When>
- After updating rules with codify, when you want to relocate existing files to match those rules
- When audit produced a violation list, and now you want to actually fix those violations
- "Organize this folder according to the rules" — putting scattered files back in place per the STRUCTURE/NAMING rules
- When you want to move artifacts/data/documents that are in the wrong directory, but move them safely
</Use_When>

<Do_Not_Use_When>
- If you only need a **verdict** on rule compliance (PASS/FAIL with no moving) → `omp-audit`
- If you're going to change the rules themselves or create new ones → `omp-codify` (fix the rules first, then organize)
- If it's dataset metadata registration/tracking → `omp-dataset` (the organizer doesn't move data; the dataset-curator handles metadata only)
- If `.omp/` doesn't exist yet → `omp-init` first (with no rules, you can't define a violation)
- If you're promoting observations into rules → `omp-learn`
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Detection ≠ execution separation (invariant)**: the auditor **only detects** violations and never moves files (disallowedTools=[Write,Edit,NotebookEdit]). Only the organizer moves. Self-approval, where the same context detects and then executes on its own judgment, is forbidden — inherited from oms's "inspector (critique) ≠ drafter (generation)" separation.
- ⚠️ **safe-fileops.md enforced**: every move/delete by the organizer follows `references/safe-fileops.md` as an absolute protocol.
  - **Move = copy-verify-delete**: `mv`/copy → verify the destination with `find`/`ls` (count + SHA-256 comparison for important files) → delete the source **only after verification passes**. Never `rm` the source in the same breath (iCloud/Drive sync lag, exFAT AppleDouble remnants cause file loss).
  - **Delete = via trash**: OS branch — macOS `trash` (else `~/.Trash`) / Linux `gio trash`·`trash-cli` / Windows PowerShell recycle bin. Environments with no trash (Docker/CI) → **STOP** → confirm a copy exists elsewhere + only after the user's explicit "permanent delete" approval may you `rm`. In a git repo, `git rm`+commit is also a recoverable path.
  - **Avoid rename**: in a sync folder, renaming a folder risks the sync engine restoring the old name, leaving a half-copy and the original coexisting. Before deleting the old path after a rename, confirm with `diff -rq old new` that the new path is a **superset** of the old.
- ⚠️ **dry-run first**: every batch move/delete first outputs the full plan (from → to, with the violated rule cited) and the verification commands *that will run*, with **0 mutation**, via dry-run. Actual execution is entered only after showing the dry-run output to a human and getting approval.
- ⚠️ **Human approval gate (before moving)**: the organizer never auto-moves. It presents the move plan, and a human must approve before it touches the filesystem at all.
- All paths are `pathlib`-based, OS-neutral. No hardcoded absolute paths or `~` (`Path.home()`/`Path.cwd()`).
- Lightweight patterns discovered along the way (e.g. "this extension always gathers into this folder") are auto-appended to `.omp/wiki/` per the light channel of `references/learning-protocol.md` (no approval needed). Heavy observations worth hardening into rules are written only as candidates to `.omp/learned.md` → handed to the `omp-learn` gate (rules.json is not edited directly here).
</Execution_Policy>

<Steps>
1. **Confirm target and scope**: confirm the project root to organize and the existence of `.omp/rules.json`·`.omp/STRUCTURE.md`·`.omp/NAMING.md`. Decide the scope (whole tree / a specific subfolder) and the severity filter (error only / error+warn). If `.omp/` is missing, stop immediately and point to `omp-init`.
2. **Delegate the detection lane (auditor, read-only)**: delegate violation detection via `Task(subagent_type="oh-my-project:auditor", ...)`.
   - Inputs: project root, `.omp/rules.json` (the machine-rule SSOT), `references/schemas/rules.schema.json` (schema), scope, severity filter.
   - Instructions: inspect the actual tree according to rules.json's `structure.directories[].enforced`·`naming.patterns[].regex` (Python re)·`ignore` globs. For each violation, output {violating file path, the rule it breaks (structure/naming + rule id), severity (error/warn/info), proposed destination (which rule requires it to go where)}. **Does not move files — detection only**.
3. **Receive the violation list + draft the move plan**: take the auditor output, aggregate by severity, and organize each violation into a `from → to` move plan (with the violated rule cited). Ambiguous destinations (where no single place is pinned down by a rule) are split out as **human-question items**, not move candidates.
4. **Present the dry-run (0 mutation)**: ask the organizer for a dry-run that outputs the full move plan + the verification commands *that will run* (`find`/`ls`/SHA-256 comparison) and delete paths (trash branch). This step does not touch the user's filesystem. The dry-run plan (from→to + violated rule cited + verification commands) is recorded to `.omp/work/plans/organize-{YYYY-MM-DD-HHMM}.md` as undo provenance (`references/output-layout.md` work layer — this record is a write to omp's own workspace, not a user file). After recording, prune `.omp/work/plans/` per retention: keep only the latest N=10 and trash-route older plans (no permanent `rm`), reporting one line "pruned X old plans" — the skill that records trims its own subfolder.

#### wikilink inbound 카운트 (para preset 한정 — Release 2)

`rules.json` 이 para preset(`structure.convention == "para"` 또는
`project.preset_origin == "para"`)이면, 이동 후보에 오른 **각 `.md` 노트**에 대해
inbound 위키링크 수를 dry-run 계획서에 병기한다 — 파일시스템 rename 은 Obsidian 이
모르는 채 일어나 `[[link]]` 가 조용히 깨지기 때문이다.

- 카운트 방법(grep 수준, 임베딩·인덱스 금지 — D11): 노트 basename(확장자 제외)을
  `노트명`이라 할 때, 프로젝트 루트에서 `[[노트명]]`·`[[노트명|` ·`[[노트명#` 패턴을
  `*.md` 전체에 grep 해 합산한다.
- 계획서 표기: 각 이동 행에 `inbound [[links]]: N` 열 병기. **N > 0 인 이동은 링크
  깨짐 경고를 명시**하고, 승인 요청 시 그 경고를 함께 보여준다(이동 자체를 막지는
  않는다 — 판단은 사람 몫).
- Obsidian 이 링크를 자동 갱신해 주는 앱-내 이동과 달리 omp 의 이동은 파일시스템
  레벨임을 계획서 머리에 1줄 고지한다.

5. ━━━ **GATE: move approval (human)** — show the dry-run plan to a human and take a decision: proceed (all) / select some / revise (fix destinations) / abort. **Without approval, not a single item is executed.**
6. **Delegate the execution lane (organizer, write)**: only for the approved plan, delegate the actual moves via `Task(subagent_type="oh-my-project:organizer", ...)`.
   - Inputs: the approved move plan (from→to + rule citation), `references/safe-fileops.md` (absolute protocol), target OS info.
   - Instructions: execute each move in **copy-verify-delete** order — mv/copy → verify the destination with `find`/`ls`+SHA-256 → delete the source via trash only after passing. Avoid rename; for sync folders, confirm superset. If even one item fails verification, **STOP that item in a rollback-able state** and report (whether to proceed with the rest goes to the human).
7. **Post-verification + recording**: after moving, confirm with `omp-audit` (or auditor re-detection) that the violations were actually resolved (target: 0 residual violations). Lightweight patterns surfaced during organizing are appended to `.omp/wiki/`; heavy observations worth turning into rules are written as candidates to `.omp/learned.md` and handed to `omp-learn`.
8. **Index synchronization (mandatory if you changed structure)**: if a move/rename **changed the name, hierarchy, or existence of a folder that appears by name in rules.json `structure.directories[].path` or the STRUCTURE.md tree**, that change makes the index *inconsistent* — `.omp/STRUCTURE.md`·`rules.json` (+ `DATASETS.md` if the path is written there) end up pointing at the old path (drift). This synchronization is **part of organize's definition of done**: finish it inside organize without a separate user request (it's a failure if you make the user say "fix the index too" again). Decision — *is the folder you just moved/renamed written by name in rules.json·STRUCTURE.md?* **No** (you merely moved files into place per the rules, structure definition unchanged) → no-op, the index is already correct. **Yes** → if it's a simple path-string substitution, sync directly with Edit; if the rule *meaning* changed (e.g. new `enforced`·`role`·section) hand it to the `omp-codify` gate (rule-architect proposal → human approval). State the synced files and old→new paths in the Output.

> **Order is invariant**: auditor (detect) → move plan → dry-run → **human approval** → organizer (execute) → post-audit → **index sync**. Under no circumstances does the detection context execute directly, or skip approval/dry-run. **A move that changed structure is one task that runs through index sync** — don't move on to the next task with the old path still in the index.
</Steps>

<Output>
- Violation list (violating file · rule broken (structure/naming + id) · severity · proposed destination) + per-severity counts
- Move plan (from → to, violated rule cited) — presented first as dry-run output (0 mutation)
- Human approval decision history (proceed/some/revise/abort)
- Execution results: copy-verify-delete verification evidence for each move (count·SHA-256 match), trash-routed delete paths, failed/rolled-back items (if any)
- Post-audit result (residual violation count) + human-question items split out for ambiguous destinations
- **Index sync result**: the `.omp/` files updated if structure changed (STRUCTURE.md·rules.json·DATASETS.md) with old→new paths / if structure unchanged, state "index sync not needed (no-op)"
- `.omp/wiki/` auto-append entries / `.omp/learned.md` promotion candidates (→ point to omp-learn)
- ⚠️ State that no move was executed without approval / no safe-fileops.md bypass
</Output>
