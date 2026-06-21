---
name: omp-audit
description: |
  A summative gate that mechanically checks a project folder against .omp/rules.json and manifest.json —
  it judges structure violations, naming violations, dataset checksum drift, split leakage, and lineage/orphan integrity as read-only PASS/FAIL.
  The "CI" of code. Evidence-based only (fresh hashes, grep, tree walk); no critique, no advice, no self-correction.
  It does not fix violations directly — it only hands them off as lists to the organizer (moves) and dataset-curator (re-registration).
  Triggers: 감사해줘, 규칙 준수 확인, audit, 위반 검사, PASS 판정, 체크섬 확인, drift 검사,
  split 누수, 구조 위반 찾아, omp audit, 규칙 어긴 거 찾아, 게이트 확인
---

# omp-audit — rule-compliance summative gate (read-only PASS/FAIL)

<Purpose>
Mechanically checks whether a project folder actually honors, on disk, the rules declared in `.omp/rules.json` and `.omp/manifest.json`. Delegates as a single handoff to `oh-my-project:auditor` (opus, read-only) to judge structure violations, naming violations, dataset checksum drift, split leakage, and lineage/orphan integrity as per-item PASS/FAIL plus evidence. This is the "CI" of code — it judges purely on objective evidence (file:line, expected vs. actual hash, grep results) and offers no critique, advice, or improvement suggestions.

⚠️ **No self-correction.** Even when it detects a violation, it does not move or fix a single byte. Across all of omp, file moves are done only by `organizer`, and manifest re-registration only by `dataset-curator`. The auditor produces only the handoff lists those agents will consume.
⚠️ **If critique/advice is the goal, it is not an audit.** "This structure would be better changed like this" belongs to `omp-codify` (rule-architect). All that comes out here is per-item PASS/FAIL and evidence.
</Purpose>

<Use_When>
- *Right after* moving files with `omp-organize`, when objective re-verification that the disk conforms to the rules is needed (an independent reviewer pass over the organize result)
- After rules.json changes via `omp-codify`/`omp-learn`, to confirm the actual folder honors the new rules
- When mechanically checking whether a dataset has changed since registration (checksum drift), and whether there is no leakage between train/val/test
- When finding orphan entries registered in the manifest but absent on disk, and broken lineage
- Inside the `omp-pilot` loop, to pass/reject the organize/dataset stage results as a gate
</Use_When>

<Do_Not_Use_When>
- If you want to *design or update* rules → `omp-codify` (rule-architect). audit only judges violations against the current rules.json.
- If you want to *fix or move* violations → `omp-organize` (auditor detects → organizer moves). audit only detects.
- If you want to reflect checksum drift into the manifest (re-register) → `omp-dataset` (dataset-curator). audit does not modify the manifest.
- If there is no `.omp/` yet (not init'd) → run `omp-init` first. Without rules.json there is no basis for inspection.
- If the goal is "qualitative improvement points like logic/prose," it is not an audit — audit emits only mechanical PASS/FAIL.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Fresh evidence only** — "should/probably/seems/아마도/잘 정리된 듯" forbidden. Dataset checksums do not trust the value recorded in `manifest.json.datasets[].sha256`; they are judged only from the **recomputed** `hashlib` SHA-256 result. An item whose check could not be run is not marked PASS but rather "check not run — manual verification needed."
- ⚠️ **Automatic fix / automatic move absolutely forbidden** — even when it detects a structure violation it does not `mv`, even when it detects checksum drift it does not overwrite the manifest sha256 with the new value, and even when it detects a naming violation it does not rename. Detected items are passed only as lists for **organizer to handle** (moves) or **dataset-curator to re-register** (metadata).
- ⚠️ **Triple ban on self-approval** — (a) the auditor frontmatter's `disallowedTools: Write, Edit, NotebookEdit` blocks file modification, (b) audit is a **separated reviewer pass**, not the *same active context* that codified the rules or organized the files, (c) the auditor's NOT-responsible section explicitly names "relocation (organizer), rule design (rule-architect), manifest authoring (dataset-curator)" — combining those roles destroys the gate's independence. The context invoking this skill must not imitate the audit itself, but delegate to a fresh `oh-my-project:auditor` subagent.
- **Respect DVC/git-lfs** — if `manifest.json.managed_by_external.tool` is `dvc`/`git-lfs`, or if traces of `.dvc/` / lfs `.gitattributes` appear, then data-content drift is the external tool's domain, so it is demoted from a critical FAIL to a warning of "externally managed — manifest mirrors metadata only" (the dataset analog of citation-safe).
- **Bind the verdict to a snapshot identifier** — every PASS/FAIL is bound to the snapshot identifier of what was actually verified that round (content hash of `.omp/rules.json` / `.omp/manifest.json` + SHA-256/mtime of the inspected dataset files + the set of violation IDs handled). Because the identifier changes when `omp-organize` moves files or `omp-codify` changes rules, a stale PASS is not reused across an audit→organize→re-audit multi-round.
- An overall PASS is only when every error-severity item is PASS. warn/info violations in `naming.patterns[].severity` do not cause an overall FAIL but are tallied in the report.
- All paths are relative to the project root (`pathlib`) — no absolute path or `~` hardcoding. The `rules.json.ignore[]` globs (`.git/**`, `node_modules/**`, `.omp/**`, etc.) are excluded from inspection.
</Execution_Policy>

<Steps>
1. **Confirm target and SSOT**: confirm the project root and the existence of `.omp/rules.json` and `.omp/manifest.json`.
   - If `.omp/` is absent, audit is impossible → report "`omp-init` needed" to the caller and stop (no inspection basis).
   - If the rules.json/manifest.json JSON is broken, mark an overall FAIL and report "SSOT recovery needed via `omp-codify`/`omp-dataset`".
2. **Fix the inspection axes**: state which axes this round covers — structure violations (`rules.json.structure.directories[].enforced`), naming violations (`naming.patterns[]` Python regex + severity), content-convention violations (`content_conventions[]` applies_to × check.pattern/expect/scope, enforced — error→FAIL), wikilink integrity (vault `[[link]]` resolution, info — dead link = health hint, not a FAIL), dataset checksum drift (`manifest.datasets[].sha256` SHA-256 recompute), split leakage (same hash/path within a `split.group`), lineage/orphan integrity, specificity consistency (info), and **Docker anti-pattern** (`.omp/env/` + root `Dockerfile`/compose files, via `hooks/omp_docker_audit.check_dockerfile`/`check_compose`; rule-ids carried as data: `DL3007`/`secret-in-env`/`compose-version`; **warn-default — GUI/sim containers legitimately break these rules, so docker findings do NOT block an overall PASS**; a project may opt out a rule-id via `rules.json` severity-override). **`docker_images[]` are NOT checksum-drift-checked** — an image has no in-tree path and a remote digest cannot be re-hashed with `hashlib` (see auditor.md). Even if the calling context requests only one axis, the dataset axis and the structure/naming axes run independently of each other — a FAIL on one axis does not cause another axis's check to be skipped.
3. **Load reference cards (delegation input)**: gather the SSOT and card paths to hand to the auditor —
   - `.omp/rules.json` + `references/schemas/rules.schema.json` (rule schema SSOT: required fields `omp_version/project/specificity/structure/naming`)
   - `.omp/manifest.json` + `references/schemas/manifest.schema.json` (inventory schema SSOT: required `omp_version/generated/datasets`, sha256 `^[a-f0-9]{64}$|^UNHASHED$`)
   - `.omp/STRUCTURE.md` / `.omp/NAMING.md` / `.omp/DATASETS.md` (human-facing .md — paired with the machine .json, for reference)
   - `references/output-layout.md` (`.omp/` path conventions and "Two learning channels" SSOT)
   - `references/safe-fileops.md` (the mv→verify→delete, trash, dry-run, approval protocol to cite during the organizer handoff — the auditor does not imitate it, only cites it in the handoff list)
   - `references/learning-protocol.md` (heavy/light 2-channel and specificity promotion-gate SSOT — the basis for checking `rules.json.specificity` / `learned_refs[]` consistency)
   - `references/presets/*.md` (the seed that `project.preset_origin` points to — for specificity consistency reference)
4. **Receive inspection results**: collect the auditor's per-item PASS/FAIL + evidence (file path, line, violated rule ID/regex, expected hash vs. recomputed hash, duplicate path). A PASS with no evidence and a "check not run" are not counted as PASS.
5. **Classify handoffs**: split the FAIL violations by the responsible party — **organizer to handle** (structure/naming-violating files: violating path + violated rules.json rule + suggested destination candidates) / **dataset-curator to re-register** (checksum drift, orphan, unregistered: do not touch the data content, only the metadata). audit itself does not dispatch these directly — it produces only the handoff lists, and the actual invocation is done by `omp-organize`/`omp-dataset`/`omp-pilot` through a human-approval gate.
6. **Attach snapshot identifier + record the report**: bind the verdict to the verified-target snapshot identifier to block stale-PASS reuse after organize/codify. Then record the per-item PASS/FAIL + evidence + snapshot identifier to `.omp/work/audits/audit-{YYYY-MM-DD-HHMM}.json` to leave a drift history (time-series comparison). ⚠️ **This record is written by this skill (the controller), not by the read-only auditor** — the auditor only produces output (text), and the work/audits record is the calling skill's job (preserving the auditor's read-only invariant and the detection≠execution separation). After recording, retention-prune `.omp/work/audits/`: keep only the latest N=10 and prune older reports via trash (no permanent `rm`), with a one-line "pruned X old audits" report — this skill that wrote the record trims its own subfolder. `references/output-layout.md` work layer.
7. **Task delegation (single, read-only)**: bundle the above input and delegate to the auditor as a single handoff. Because it is a read-only gate, use a **single dispatch** for the independence of the automated check (do not split the inspection items across multiple agents — one auditor views all axes deterministically):
   ```
   Task(
     subagent_type="oh-my-project:auditor",
     description="omp rule-compliance audit (read-only PASS/FAIL)",
     prompt="""
     Project root: <project root absolute path>
     SSOT: .omp/rules.json, .omp/manifest.json
     Schema cards: references/schemas/rules.schema.json, references/schemas/manifest.schema.json
     Path conventions and 2 channels: references/output-layout.md
     Cite during organizer handoff: references/safe-fileops.md (auditor must not imitate it)
     Learning 2-channel and specificity gate: references/learning-protocol.md
     Preset seed (for specificity consistency reference): references/presets/<preset_origin>.md

     Instruction: output PASS/FAIL + evidence for each axis below, each with fresh evidence. No advice, critique, or auto-fix.
     For dataset checksums, do not trust the manifest-recorded value; judge only by hashlib SHA-256 recompute.
       - Schema validity (rules.json / manifest.json required fields)
       - Structure violations (enforced:true role violations among structure.directories[])
       - Naming violations (naming.patterns[] applies_to glob × regex, tallied per severity)
       - Content-convention violations (content_conventions[] applies_to glob × check.pattern/expect/scope, hooks/omp_content_audit.check_content_rule, tallied per severity, error→FAIL)
       - Wikilink integrity (vault [[link]] resolution, hooks/omp_content_audit.find_dead_links, dead link = info hint, not a FAIL)
       - Dataset checksum drift (manifest.datasets[].sha256 vs. hashlib recompute; UNHASHED falls back to size+mtime)
       - Split leakage (same SHA-256 or duplicate path across train↔val↔test within the same split.group)
       - Lineage/orphan (derived_from/by existence; manifest path existence on disk; warn on unregistered files)
       - Specificity consistency (rules.json.specificity ↔ learned_refs[] consistency, warning only)
       - Docker anti-pattern (run hooks/omp_docker_audit.check_dockerfile / check_compose over .omp/env/ and root Dockerfile/compose; rule-ids DL3007/secret-in-env/compose-version; warn-default — findings do NOT block overall PASS; project may override severity per rule-id via rules.json; docker_images[] are NOT drift-checked — no in-tree path, remote digest un-rehashable)
     On detecting DVC/git-lfs (managed_by_external, .dvc/, lfs .gitattributes), demote data drift to a warning.
     The rules.json.ignore[] globs are excluded from inspection. Paths are relative to the project root (pathlib).
     Violations go only into organizer/dataset-curator handoff lists — direct mv/rm/manifest modification absolutely forbidden.
     Bind the verdict to a snapshot identifier (rules/manifest content hash + dataset SHA-256/mtime + violation IDs).
     Output: per-item PASS/FAIL table + FAIL evidence blocks + organizer/dataset-curator handoff lists + executed commands + snapshot identifier.
     """
   )
   ```
</Steps>

<Output>
- **Per-item result table**: schema validity / structure violations / naming violations (error, warn, info) / content conventions (error, warn, info) / wikilink integrity (dead link info) / dataset checksum drift / split leakage / lineage integrity / manifest path existence (orphan, unregistered) / specificity consistency — each PASS / FAIL / WARN + remarks.
- **FAIL item evidence**: violating file path, line, violated rules.json rule ID/regex, expected hash vs. `hashlib` recomputed hash, duplicate path — in reproducible form.
- **organizer to-handle list** (no automatic move): violating path + violated rule + suggested destination candidates. Handled by `omp-organize` via the `references/safe-fileops.md` protocol (mv→find zero-residue verify→delete, via trash, dry-run, human approval) — audit only cites it and does not move anything directly.
- **dataset-curator to-re-register list** (no automatic update): drift, orphan, unregistered — `omp-dataset` re-registers metadata only, without touching the data content.
- **External-management note**: state that on DVC/git-lfs detection, data drift is demoted to a warning.
- **Executed commands** (a reproducible list of read-only commands) + **snapshot identifier** (rules/manifest content hash + dataset SHA-256/mtime + violation IDs).
- **Final verdict**: **PASS** (all error-severity items pass) or **FAIL** (N items failed). On FAIL, the next step — move needed → `omp-organize`, re-registration needed → `omp-dataset`, rule itself needs touching → `omp-codify`. All go through a human-approval gate, and after handling, close with a **re-audit** (fresh snapshot). State that it does not self-approve.
</Output>
