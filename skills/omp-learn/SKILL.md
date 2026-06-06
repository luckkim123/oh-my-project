---
name: omp-learn
description: |
  Observation → rule promotion (omp's core evolution gate) — rule-architect reviews the observations
  accumulated in `.omp/learned.md` during operation plus the auto-accumulated patterns in `.omp/wiki/`,
  and judges which of them qualify to be promoted into `rules.json` rules. The heavy channel (rules)
  must always pass a human approval gate, and each promotion raises rules.json's specificity, advancing
  "generic → specialized to this project" by one notch.
  No auto-promotion — the human breaks the gate.
  Triggers: 학습 반영, 규칙 승격, 관찰 정리, learned 검토, 패턴 굳혀, 이거 규칙으로,
  omp learn, promote observation, learn rules, specificity 올려, 진화 게이트
---

# omp-learn — Observation → rule promotion (core evolution gate)

<Purpose>
This is the step where omp's asymmetry — "generic at deploy, specialized as you use it" — is *recorded*.
rule-architect reads the observations accumulated in `.omp/learned.md` during operation (e.g. "in this
folder .pkl always goes into data/processed/ — repeated 3 times") and judges which observations qualify
to be **promoted** into rules.json's enforced rules. Promotion is a **one-way ratchet** that affects
actual files (a wrongly promoted rule triggers a flood of omp-audit false violations + organizer's actual
misplacements), so it always passes a human approval gate. Each promotion raises rules.json's
`specificity` toward 0 (pure preset) → 1 (fully specialized). rule-architect only **proposes** — it does
not write or enforce rules directly, and only after the human breaks the gate does this skill apply it to
disk.
</Purpose>

<Use_When>
- During operation, enough observations have accumulated in `.omp/learned.md` to judge "shall we solidify these into rules now?"
- The same pattern (folder placement, naming) has been repeatedly observed and you want to elevate it to an enforced rule
- You want to raise specificity so omp becomes more specialized to this project
- omp-pilot calls the learn step during its operating loop
</Use_When>

<Do_Not_Use_When>
- If `.omp/` does not exist yet → run `omp-init` first (bootstrap + draft rules.json approval). learned.md
  accumulates only during operation after init.
- If you are *designing rules for the first time* or directly editing structure/naming rules → `omp-codify`
  (learn is *observation → evolving existing rules*, codify is *codifying/updating rules*).
- If it is just a lightweight pattern/decision memo and not an enforced rule → do not promote; leave it to
  auto-accumulate in `.omp/wiki/` (no gate needed, recalled via grep next session). Not every observation
  becomes a rule.
- If it is rule *compliance verification* (PASS/FAIL) → `omp-audit` (auditor). learn *creates* rules, audit
  *adjudicates* them — different lanes.
- If it is moving files → `omp-organize` (organizer). learn goes only up to rule proposal; moving is a separate gate.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Human approval gate is absolutely enforced (core)** — rule-architect only emits a promotion
  *proposal*. No observation is auto-applied to `rules.json` without human approval. No auto-pass. Because
  promotion is a one-way ratchet that affects actual files, unattended automation is a forbidden act.
- ⚠️ **Conservative promotion (one-way ratchet)** — only observations that clear the evidence bar (repeated
  observations ≥ N times + no counterexamples) are proposed as promotion candidates. If ambiguous, leave it
  in `learned.md` surfaced as "candidate — needs more observations / human judgment". The cost of 1 wrongly
  promoted rule (false violations + organizer misplacement) > the cost of 1 missed rule (just elevate it
  again at the next learn).
- ⚠️ **Respect the 2-channel separation** — only the *heavy channel* (rules: learned.md → promotion →
  rules.json) is this skill's target and passes the gate. The *light channel* (patterns/decisions:
  `.omp/wiki/*.md` auto-append) needs no gate — leave it untouched. Do not force-promote an observation
  that is not worth solidifying into a rule.
- ⚠️ **Provenance enforced** — each promoted rule records the learned.md observation id that was its basis in
  `rules.json.learned_refs[]` (the schema's tracing field). A rule without provenance = a guess = silent file
  loss two steps later.
- ⚠️ **schema is law** — the promotion-result draft must exactly conform to
  `references/schemas/rules.schema.json` (`additionalProperties:false`, `specificity` ∈ [0,1], naming
  `severity` ∈ error/warn/info, regex in Python `re` syntax). To express something the schema cannot hold,
  do not bend the JSON — leave it as a schema-change request in prose.
- ⚠️ **Be honest about specificity** — compute it honestly from the ratio of promoted rules (from scan/learn)
  vs preset defaults. Do not inflate it to look more specialized.
- **Design ≠ enforcement/verification separation (3-way self-approval ban)** — rule-architect is read-only
  (`disallowedTools: [Write, Edit, NotebookEdit]`) and only *designs* rules; it does not adjudicate compliance
  of its own rules in the same context. Compliance adjudication is for a different agent (auditor, separate
  context, omp-audit). Moving is organizer's job. learn ends at the proposal/gate step.
- **Present as a diff** — since `rules.json` already exists, rule-architect proposes as a *delta* (Added /
  Changed / Removed rules) rather than the whole file, so the human reviews only the changes.
- The canonical procedure for the learning channels and promotion criteria is in
  `references/learning-protocol.md` (2-channel definitions, evidence bar); the SSOT for `.omp/` path
  conventions is `references/output-layout.md`.
</Execution_Policy>

<Steps>
1. **Confirm SSOT and preconditions**: verify the project root and `<project>/.omp/` exist. If not, stop and
   recommend running `omp-init` first (learned.md accumulates only during operation after init). Read the
   following files:
   - `<project>/.omp/learned.md` — observations awaiting promotion (this skill's input)
   - `<project>/.omp/rules.json` — existing rules to evolve (not a blind replacement, but *evolve*)
   - `<project>/.omp/wiki/*.md` — light channel. grep to recall whether signals worth solidifying into rules
     have accumulated here (but wiki is an area that auto-accumulates without a gate, so *read* only — leave it untouched)
2. **Classify observations (2-channel discrimination)**: for each observation in learned.md, separate into
   (a) candidate for promotion into a rule (heavy channel — subject to the gate) vs (b) pattern/decision memo
   (light channel — leave in wiki, no gate needed). Not every observation becomes a rule — apply the channel
   criteria in `references/learning-protocol.md`.
3. **First-pass promotion candidate selection (evidence bar)**: for each heavy-channel candidate, look at the
   repetition count and presence of counterexamples. If it clears the evidence bar (repeated ≥ N times + no
   counterexamples), classify as "promotion proposal"; if ambiguous, classify as "held candidate". The
   controller's job is the *evidence gathering* for this first-pass judgment; the *final design/verification*
   is delegated to the agent in the next step.
4. **Agent delegation (promotion judgment + draft design)** — single delegation to rule-architect. Use a fresh
   subagent to prevent controller context pollution. Since this is one careful synthesis, **no parallel
   architects**:

   ```
   Task(
     subagent_type="oh-my-project:rule-architect",
     description="omp-learn: judge learned.md observations for promotion into rules.json",
     prompt="""
     Role: omp-learn promotion judgment. Read the .omp/ SSOT below and judge which of the
     learned.md observations qualify to be promoted into rules.json enforced rules, then emit
     a **proposal (diff)**. You are read-only — do not write rules.json directly, do not move
     files, and do not adjudicate compliance. A human approval gate sits between your proposal
     and the disk.

     Input (to read):
     - <project>/.omp/learned.md      # observations awaiting promotion (incl. occurrence·counterexamples)
     - <project>/.omp/rules.json      # existing rules to evolve (evolve, not replace)
     - <project>/.omp/wiki/*.md       # light-channel signals (read only)
     - references/schemas/rules.schema.json   # draft must conform exactly here (additionalProperties:false)
     - references/learning-protocol.md        # 2-channel definitions + evidence bar (SSOT for promotion criteria)

     Instructions:
     - Rule kinds eligible for promotion: structure.directories[] / naming.patterns[] / **content_conventions[]** (note-body conventions: applies_to glob × check.pattern/expect/scope) / ignore[]. Content observations go through the same evidence bar·gate.
     - Conservative promotion (one-way ratchet): propose for promotion only observations that
       clear repeated ≥ N times + no counterexamples. If ambiguous, surface to the human as a
       held candidate — no auto-promotion.
     - Each promoted rule records its source learned.md observation id in learned_refs[] (provenance).
     - Recompute specificity honestly (ratio of scan/learn-derived vs preset) — do not inflate it.
     - Present as a **diff** against the existing rules.json (Added/Changed/Removed), not the whole file.
     - schema is law: for anything the schema cannot hold, do not bend the JSON — put it in prose as a schema-change request.
     - Output: promote/held decisions + provenance table + specificity rationale + human decision list.
       Do not write rules.json — propose only. You are forbidden to self-approve (design ≠ enforcement·verification separation).
     """
   )
   ```

   ━━━ **GATE (core promotion gate — human)**: present rule-architect's diff, provenance, and specificity
   rationale to the human and get a decision — promote (approve) / hold (defer this time) / edit (promote
   only some) / abort. **Absolutely no auto-pass.** Among held candidates, if the human says "elevate this
   one this time", that is also decided here. ━━━
5. **Apply approved items (only after passing the gate)**: only rules the human approved are written to disk by
   this skill.
   - **First** snapshot the existing `.omp/rules.json` to `.omp/work/versions/rules-v{NN}-{YYYY-MM-DD}.json`
     (promotion is a one-way ratchet — a rollback point if wrongly promoted; `references/output-layout.md` work
     layer). After the snapshot, apply retention to `.omp/work/versions/`: keep only the latest N=10, prune
     older ones via trash (no permanent `rm`), and report one line "pruned X old snapshots" — the same skill
     that wrote the snapshot trims its own subfolder in the same pass (`output-layout.md`).
   - `<project>/.omp/rules.json` — add/change approved rules, record source observation ids in
     `learned_refs[]`, update `specificity`, update `project.last_codified`. (Re-confirm schema conformance.
     rules.json and snapshot writes go through the `hooks/omp_atomic.py` atomic write to prevent partial-write
     corruption — T20.)
   - Synchronously regenerate the paired .md (the .md↔.json pairing rule in output-layout.md): if rules.json
     structure/naming rules change, update `STRUCTURE.md`·`NAMING.md`; if content_conventions change, update
     `CONVENTIONS.md` in the same pass to prevent drift (CONVENTIONS.md only when content_conventions exist).
   - `<project>/.omp/learned.md` — mark promoted observations as "promoted → rules.json (date)"; held ones keep
     candidate status (re-evaluated at the next learn).
6. **Follow-up guidance**: since the rules changed, advise checking the new rule compliance with `omp-audit`, and
   if violations arise, re-placing files with `omp-organize` (safe-fileops.md + dry-run + approval before moving).
   learn itself does not move files.
</Steps>

<Output>
- rule-architect's **promotion proposal diff** (Added/Changed/Removed rules) + provenance table (each rule →
  learned.md observation id) + specificity-change rationale + human decision list.
- GATE decision history (promote/hold/edit/abort).
- On passing the gate: the updated `<project>/.omp/rules.json` (learned_refs[]·specificity·last_codified) +
  the synchronously regenerated `STRUCTURE.md`/`NAMING.md` + the marked `learned.md` path.
- The held candidate list (observations to re-evaluate at the next learn) + guidance "recommend checking new
  rule compliance with omp-audit". Note explicitly that rule-architect does not self-approve — promotion was
  broken by the human gate, and compliance adjudication is the job of a separate context (auditor).
</Output>
