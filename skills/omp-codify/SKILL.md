---
name: omp-codify
description: |
  The management stage that codifies and updates structure/naming rules — writes rules.json (machine) +
  STRUCTURE.md/NAMING.md (human) together in one pass to prevent drift. Takes the existing .omp/rules.json
  as input, has rule-architect propose changes, and any rule change (a heavy decision that triggers file moves)
  must pass a human approval gate. Not a generation pipeline but a loop that updates a living .omp/ — rules are
  only proposed; the human gates enforcement.
  Triggers: 규칙 성문화, 규칙 갱신, codify, 구조 규칙 정리, 명명 규칙 정리, rules 갱신,
  STRUCTURE 갱신, NAMING 갱신, 규칙 바꿔, 폴더 규칙 명문화, codify rules, update rules,
  organize structure rules, organize naming rules, change rules, formalize folder rules
---

# omp-codify — Codify/Update Structure & Naming Rules (Management Loop, Stage 1)

<Purpose>
Codifies and updates a project's structure rules (which folder holds what) and naming rules (filename patterns). Updates `.omp/rules.json` (the machine truth the audit hook reads) and `.omp/STRUCTURE.md`/`.omp/NAMING.md` (the human-readable narrative) **together in one pass** so the two never drift apart. Delegates to rule-architect to receive the proposed change, and rule changes pass through a human approval gate. This is the code equivalent of "defining lint rules" — the stage that first nails down what counts as a violation.
</Purpose>

<Use_When>
- `.omp/` already exists (= omp-init done) and you want to add/modify/remove structure or naming rules.
- You want to codify rules like "this folder holds only X" or "filenames of this kind follow this pattern".
- The project has evolved and the existing rules.json no longer matches the real structure (re-codification).
- Right after omp-learn promotes an observation into a rule, to formally reflect rule-architect's proposed rule into rules.json.
</Use_When>

<Do_Not_Use_When>
- `.omp/` does not exist yet → **omp-init first** (bootstrap + preset synthesis). codify is the stage that *updates* the rules.json that init created.
- You want to leave rules as-is and only find violating *files* → omp-audit (read-only verdict).
- You want to actually *relocate* rule-violating files → omp-organize (moves happen only there, safe-fileops enforced).
- You are dealing with dataset metadata (SHA256/split/lineage) → omp-dataset (manifest.json dedicated).
- You need the judgment of raising an observation to a rule *candidate* → omp-learn (promotion gate). codify confirms and reflects the promoted result.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **No drift — .json and .md are written together in one pass.** Partial updates that fix only rules.json without STRUCTURE.md/NAMING.md (or vice versa) are forbidden. When the machine truth (rules.json) and the human narrative (.md) diverge, audit and the human end up looking at different rules. Always change them as a pair. (Path convention: `references/output-layout.md` §"Human .md ↔ Machine .json pairing".)
- ⚠️ **Rule change = human approval gate.** Changing a rule is a heavy decision that triggers file moves in the next omp-organize. rule-architect **only proposes**, and no rule enters rules.json without human approval (design §3 "rules are only proposed; the human enforces").
- ⚠️ **Schema compliance.** rules.json must satisfy `references/schemas/rules.schema.json` (required: omp_version/project/specificity/structure/naming, additionalProperties:false). regex uses Python `re` syntax, severity ∈ {error,warn,info}. Not "done" until it passes schema validation after the change.
- ⚠️ **codify does not move files.** It writes only rule text (.json/.md). Relocating user files is done only by omp-organize's organizer, which enforces `references/safe-fileops.md`. Even if a move is proposed within codify, execution is handed off to organize.
- **specificity tracking.** When a learn promotion replaces/extends a preset rule with a project-specific rule, raise the `specificity` in rules.json (0 = pure preset → 1 = fully custom) accordingly. Record the promotion source in `learned_refs[]` (provenance). The evolution mechanism is in design §4.
- rule-architect is read-only (disallowedTools=[Write,Edit,NotebookEdit]) — it *designs* and returns the proposed rule, and the actual `.omp/` write is performed by this skill (the controller) after human approval. It does not self-approve its own design.
- Light decisions/patterns (e.g., "why this rule was added this time") may be auto-appended to `.omp/wiki/` (no approval needed, recoverable via grep next session). Only heavy rule changes go through the gate (design §4, 2 channels).
</Execution_Policy>

<Steps>
1. **Load current rules.** Read `.omp/rules.json` (schema: `references/schemas/rules.schema.json`), and read the paired `.omp/STRUCTURE.md`/`.omp/NAMING.md` to grasp the current state and specificity/preset_origin/learned_refs. If `.omp/` is absent, stop immediately and direct to "omp-init first" (codify is the update stage).
2. **Confirm the change intent.** What is being added/modified/removed — a new directory role, naming pattern (regex), severity adjustment, note-body convention (content_conventions[]), docker_naming rule (image_ref_template/container_name_template/service_name_template/version_scheme), provenance entry (origin:standard, standards-registry id), convention change, etc. If it came from an omp-learn promotion, include that observation ID and its rationale in the input.
3. **Delegate the proposed change to rule-architect** (Task dispatch below). Input: current rules.json/STRUCTURE.md/NAMING.md, the change intent, the relevant preset (`references/presets/<preset_origin>.md`), and (if a promotion) the learned.md observation. Output: ① the updated rules.json **draft** (schema-compliant), ② the STRUCTURE.md/NAMING.md body that corresponds exactly to it (plus the CONVENTIONS.md body if content_conventions exist), ③ a diff summary (which rules were added/changed/deleted, how specificity changes, and a rough outline of affected files).
4. ━━━ **GATE — Rule change approval (human).** Present rule-architect's diff summary to the human: proceed / revise / abort. No auto-pass. No file is written before approval. ━━━
5. **Write together (drift prevention).** ⚠️ **Managed-hash check first (§2.6 governance improvement).** Before touching disk, compare the current on-disk `rules.json`/`STRUCTURE.md`/`NAMING.md` content hash against the latest snapshot in `.omp/work/versions/` (the same `brief_hash_check`-style sha256 comparison the secretary axis uses for `BRIEF.md`). A mismatch means a human hand-edited the SSOT since the last codify pass — **STOP** and surface a one-line gate: "human-edited since last regeneration — overwrite / merge / skip?" before proceeding. Only a hash match (or no prior snapshot) continues. Once cleared, **first** snapshot the existing `.omp/rules.json` to `.omp/work/versions/rules-v{NN}-{YYYY-MM-DD}.json` (a pre-edit rollback point — `references/output-layout.md` work layer). Then write the three together in the same pass: `.omp/rules.json` (+ update `project.last_codified`, and update `specificity`/`learned_refs` if needed) **and** `.omp/STRUCTURE.md`/`.omp/NAMING.md` (also include `.omp/CONVENTIONS.md` in the same pass if you touched content_conventions — only when content_conventions exist; not every project has them). If any one of the set is missing, it is incomplete. (Snapshot and rules.json writes go through the atomic write of `hooks/omp_atomic.py` to prevent partial-write corruption — T20.) **After writing the snapshot,** apply retention cleanup to `.omp/work/versions/` (`output-layout.md`): keep only the latest N=10 and prune older snapshots via trash (no permanent `rm`), reporting one line "pruned X old snapshots". This trim is performed by this skill — the one that wrote the snapshot — on its own subfolder in the same pass.
6. **Validate.** Schema-validate rules.json against `references/schemas/rules.schema.json` (Python stdlib). Verify regex compiles. Round-trip-check that the .md matches the .json (rule count/role/pattern reflected on both sides; if content_conventions exist, include the content_conventions↔CONVENTIONS.md pair too). Append the light decision memo to `.omp/wiki/`.
7. **Follow-up guidance.** If rules changed, explain the continuation: "whether existing files now break the new rules" goes to omp-audit (verdict) → relocating violations goes to omp-organize (safe-fileops enforced). codify only nails down rules and stops.

**Final step — Task dispatch (rule-architect):**
```
Task(
  subagent_type="oh-my-project:rule-architect",
  description="Codify structure/naming rules",
  prompt="""
  Design the proposed change by updating the current rules. You are read-only — do not write
  rules.json/.md directly; return only the finished draft body + diff summary (after human approval
  the controller writes them to disk).

  Input:
  - Current .omp/rules.json (schema: references/schemas/rules.schema.json)
  - Current .omp/STRUCTURE.md, .omp/NAMING.md (pair)
  - Change intent: <structure/naming rule to add/modify/remove>
  - Applied preset: references/presets/<preset_origin>.md
  - (If an omp-learn promotion) the corresponding observation + ID in .omp/learned.md

  Requirements:
  1) Updated rules.json draft — satisfies rules.schema.json (required fields, additionalProperties:false,
     regex is Python re, severity∈{error,warn,info}). The proposable rule kinds also include content_conventions[]
     (note-body conventions: applies_to glob × check.pattern/expect/scope, optional type — only when observed)
     and docker_naming (image_ref_template / container_name_template / service_name_template / version_scheme)
     with provenance (origin:standard, referencing a `references/standards-registry.seed.json` id). Severity
     for docker rules follows the normative word in the seed: MUST→error, SHOULD→warn, MAY→info. Docker rule
     seeds come from `references/presets/docker.md`. **Do NOT generate Dockerfiles or compose files** — file
     generation is omp-env's job; codify writes only rule text in rules.json/.md.
     Record the change source in learned_refs[].
  2) STRUCTURE.md/NAMING.md body that *exactly matches* that rules.json (drift 0; if content_conventions
     exist, the CONVENTIONS.md body too — only when content_conventions exist).
  3) diff summary: rules added/changed/deleted, specificity change (0→1 direction), rough outline of affected files.
  Rules are only proposed — the human gates enforcement. Move proposals are handed off to organize.
  """
)
```
</Steps>

<Output>
`.omp/rules.json` with the approved change reflected + the paired `.omp/STRUCTURE.md`/`.omp/NAMING.md` (all three updated together, drift 0) + rule-architect's diff summary (rules added/changed/deleted, specificity change, affected files) + evidence of schema validation passing + the GATE decision history (proceed/revise/abort). The impact of the rule change on existing files is closed out with the follow-up guidance "check violations with omp-audit → relocate with omp-organize (safe-fileops enforced)" (codify itself does not move files). The light decision memo is auto-accumulated in `.omp/wiki/`.
</Output>
