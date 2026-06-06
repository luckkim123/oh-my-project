# OMC Backport Analysis — oh-my-project (omp)

omp's init scoping gate, consensus layer, organize loop, and self-learning accumulation (wiki/notepad/
verifier tokens) are a port of the proven patterns from **oh-my-claudecode (OMC)** into the project-folder
management/evolution domain. When OMC updates, we need a persistent baseline to judge *what changed and
whether omp needs to be refreshed*. OMC has no CHANGELOG (only GitHub commits/releases) and no per-file
versioning, so this document keeps its own "diff baseline."

> **This document lives in the distributed plugin's references/, so it is independent of any personal environment.** OMC paths
> are written only as the *public plugin's internal structure* (relative expression). No specific machine's absolute paths, work notes, or
> the user's organizational system are embedded here.

> **Beware the domain asymmetry**: oms/omd are "generation pipelines that produce a fresh artifact every time," whereas omp is
> "a management loop that keeps updating one living `.omp/`." When porting OMC patterns, reinterpret *stage = management-loop phase*,
> not *stage = generation step*. This difference governs the rationale for the adopt/exclude decisions below.

---

## §1. OMC 4.14.4 structural snapshot — backport source components

The OMC plugin has a **dual structure**: `skill-bodies/<name>/SKILL.md` holds the full logic, and
`skills/<name>/SKILL.md` is a *compact reference shim* that keeps startup context lightweight
(it loads the body from `skill-bodies/`). The backport source is always the `skill-bodies/` side.

| Source (OMC 4.14.4 internal path) | What was brought over |
|:---|:---|
| `skill-bodies/deep-interview/SKILL.md` | Round 0 topology · per-dimension ambiguity judgment · challenge agents (contrarian/simplifier/ontologist) · soft limits · 3-point injection → the scoping-gate skeleton of **omp-init** (resolving ambiguity in folder identity, structural intent, naming convention, and dataset boundaries) |
| `skill-bodies/plan/SKILL.md`, `skill-bodies/ralplan/SKILL.md` | RALPLAN-DR consensus (Principles/Drivers/Options≥2/steelman/tradeoff/ADR) · sequential-enforcement (parallel-prohibited) prompt discipline → the rule-change consensus of **rule-architect** (when large rules.json changes or learn promotion would trigger file moves) |
| `skill-bodies/autopilot/SKILL.md` | brief→completion stage orchestration + gate skeleton → **omp-pilot** (if `.omp` is absent, absorb init → codify→organize→dataset→doc) |
| `skill-bodies/ralph/SKILL.md` | defect=PRD · fix/verify loop until the passes:true gate · no scope reduction → the loop in **omp-organize** that runs until omp-audit PASS (violation detection→relocation→re-audit) |
| `agents/analyst.md` | upfront-diagnosis / requirements-analysis ethos → folder-identity judgment in init scoping |
| `agents/architect.md` | steelman/antithesis/tradeoff → **absorbed into rule-architect** (no separate consensus agent is created) |
| `agents/planner.md` | structure design · role decomposition → rule-architect's STRUCTURE/NAMING design |
| `agents/critic.md` | pre-commitment · assumption (VERIFIED/REASONABLE/FRAGILE) · pre-mortem · self-audit → **auditor's violation-judgment techniques** |
| OMC MCP tool servers (`wiki_*`/`notepad_*`/`shared_memory_*`/`state_*`) | the *ethos* of accumulation, surviving-compaction, and handoff. ⚠️ omp defaults to **.md degrade** and MCP is an optional accelerant — no new Node MCP is added |

---

## §2. Analysis baseline version + diff baseline

- **Analysis-baseline snapshot = OMC 4.14.4.** This is the OMC version this document saw when reading the backport sources
  (at the time, the plugin's `package.json`, `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`
  all read `"version": "4.14.4"`). **This is a *snapshot at analysis time*, not a runtime pin** —
  the omc marketplace declaration in `~/.claude/settings.json` (`repo: Yeachan-Heo/oh-my-claudecode`) has
  no version or commit-SHA, so **OMC always auto-tracks the marketplace latest**. Nowhere in oms/omd/omp is there
  a pin tying OMC to a specific version. Therefore an OMC upgrade requires no separate work, and
  the diff baseline below exists only to re-examine *whether the backport adopt/exclude decisions are still valid*.
- **diff baseline**: OMC has no CHANGELOG (only GitHub commits/releases). On the next OMC update,
  directly inspect the diff of the §1 source files above (`skill-bodies/{deep-interview,plan,ralplan,autopilot,ralph}/SKILL.md`,
  `agents/{analyst,architect,planner,critic}.md`) and judge whether omp needs updating.
- Judgment rule: if an OMC update changes an ***adopted* area in §3** → review the corresponding backport update.
  If it newly touches an ***excluded* area in §3** → re-examine whether the exclude decision is still valid.

---

## §3. Adopt/exclude mapping (internal backport work ID = Tn)

> Tn is this repo's internal backport work identifier (a mnemonic). Each row is self-describing in terms of *what changed*,
> so it reads without an external plan document. It is isomorphic to oms (papers) and omd (documents), differing only in domain.

### Adopt

| Tn | OMC pattern | omp application (actual change) |
|:---|:---|:---|
| T1 | the stage boundaries of deep-interview/ralplan | init↔codify↔organize boundary convention. **No separate scoping/consensus agent is created** (absorbed into the init skill and rule-architect). Reinterpreted as stage=management-loop phase (not a generation step) |
| T2 | critic's 4 techniques | `agents/auditor.md` adopts the *spirit* of critic (the names and technique labels are not embedded — reimplemented in omp's vocabulary). pre-mortem ("which relocation would break the data") becomes the drift-reasoning narrative in `<Why_This_Matters>`; self-audit (LOW confidence→ask the human) becomes the `<Constraints>` rule "no should/probably/seems + flag checks not run"; assumption verification is absorbed as a **loud-fail evaluation contract** (parse failure / missing required field = immediate full FAIL, distinguishing broken≠empty) — more precise than critic's 4 techniques, though the `pre-commitment`/`VERIFIED-REASONABLE-FRAGILE` labels themselves are not inserted |
| T4 | ralplan RALPLAN-DR + architect steelman | `agents/rule-architect.md` adopts RALPLAN-DR's *consensus discipline* (the `<Consensus_RALPLAN_DR_Protocol>` XML block and steelman/ADR labels are not embedded — reimplemented in omp's vocabulary). The spirit that "large rules.json changes or learn promotion trigger file moves, so conservative consensus is needed" is implemented as **evidence-trace enforcement** (every rule traces to a scan/learned/preset source, no speculative rules) + **one-way ratchet conservative promotion** (held as candidate only if the evidence bar of repetition / zero-counterexamples is unmet) + **human approval gate** (proposal-only, triple prohibition on self-adoption). RALPLAN-DR's distinction of Options≥2/steelman/Deliberate-Short modes is not split into a separate protocol but simplified into the single conservative discipline "fewer, evidenced rules" |
| T5 | ralplan sequential consensus | `skills/omp-codify/SKILL.md` enforces sequencing on rule changes (parallel-prohibited) — because rules trigger file moves, concurrent changes are forbidden. The consensus output = a separate file inside `.omp/` (T7 below) |
| T7 | shared_memory handoff | inter-stage transfer = `.omp/` files by **default** (learned.md · wiki/ · consensus notes), MCP an optional mirror (degrades to .md when absent) |
| T8 | deep-interview gate | the scoping gate in `skills/omp-init/SKILL.md` — Round 0 topology + 4-dimension **qualitative** judgment (folder identity / structural intent / naming convention / dataset boundary, zero quantification) + 3 challenge types + soft limits + human approval (draft rules.json gate). data-fragile flag (marks move-risk folders) |
| T8b | autopilot wiring | in `skills/omp-pilot/SKILL.md` `<Steps>`, inserts an "absorb init when `.omp` is absent" branch + a "codify --consensus on large rule changes" branch — the engine actually fires on the pilot path (preventing dead code) |
| T10 | wiki accumulation (the light channel) | `<project>/.omp/wiki/*.md` + deterministic grep by **default**, with `wiki_query(category)` an abstract function (a future MCP swap point). Patterns/decisions auto-appended (no approval needed) — the light channel of "general→specialized" evolution |
| T11 | notepad surviving-compaction | on entering omp-pilot, records the 3 safe-fileops principles (mv→verify→delete, route via trash, avoid rename) + gate records in `.omp/notepad.md` (or learned.md `## Priority Context`) (.md by default) |
| T12 | verifier request-id | a snapshot-correlation token in `agents/auditor.md` (rules.json mtime/hash + manifest SHA256 + violation ID) — blocks stale-PASS reuse across the multi-round organize loop. The checksum correlation engages directly with the manifest SHA256 |
| T13 | ralph regression ethos | in `skills/omp-organize/SKILL.md`, a full re-audit after relocation for **structural regression** (zero rules.json violations + manifest path consistency + dataset SHA256 unchanged) — machine-verifying that files were not broken |
| T14 | (omp's own routing) | the STAGE catalog in `hooks/omp_route_emit.py` = enumerates 8 stages (init/codify/organize/dataset/doc/learn/audit/omp-pilot) |
| T15 | state path | SSOT = fixed at `<project>/.omp/` (no unverified segments like `.omp/specs` or `sessions/{sid}`). The 30s state-MCP trap is *a future-proofing note only* |
| T16 | (contract history) | a new `CHANGELOG.md` — keeps commit-SHA versioning but explicitly records hook/rules.schema contract changes (tone unified with oms/omd) |
| T17 | (omp-specific) separation of the wiki light channel ↔ the learn heavy channel | concretizes OMC's wiki(auto)/gate(approval) separation as **2-channel evolution**: wiki/ auto-accumulation (grep) vs learned.md→omp-learn→rule-architect promotion→human approval→rules.json. Tracks specificity 0→1 |
| T18 | OMC `REFERENCE.md` artifact-first handoff + descriptor (kind/path/contentHash/producer) | `.omp/work/{scans,versions,plans,audits,tmp}` is this spirit — large intermediates (scan inventories, move plans, audit reports) are left as files and referenced by path rather than pasted into the control plane. Separates the SSOT (top of .omp) from the work layer (output-layout.md) |
| T19 | OMC Platform Support (Windows=no native support, tmux dependency → WSL2 recommended) | omp has **no tmux/Node dependency** — hook=python3 stdlib + paths=pathlib + deletion=per-OS trash branching. Therefore **omp is more Windows-friendly than OMC** (no WSL needed). Cross-platform is omp's intentional strength, not OMC mimicry |

#### Adopt — OMC 4.14.4 deep re-analysis (2026-05-30, 60 candidates→45 refuted/7 survived)

> Beyond the 6 patterns in §5 of the authority document, OMC's source (19 agents + 40 skills + dist/{lib·hooks·features} + docs24) was read
> in 5 areas in parallel → per-candidate adversarial refutation (author≠review) → opus synthesis (workflow wf_11040f52, 58 agents, 2.7M tokens). All 7 survivors
> are "runtime-agnostic + python stdlib under 10 lines" (adopting the *spirit only*, not a port). The 45 refutations are in the exclude table below.

| Tn | OMC pattern (source) | omp application (actual change) |
|:---|:---|:---|
| T20 | `dist/lib/atomic-write.js` (tempfile→fsync→rename) | `hooks/omp_atomic.py` (`atomic_write_json`, stdlib `tempfile`+`os.fsync`+`os.replace`). All 4 skills that write the `.omp/` JSON SSOT are forced through this helper — omp-codify·omp-learn (rules.json + versions/ snapshots), omp-init (rules.json + manifest.json seed), omp-dataset (manifest.json). Prevents SSOT corruption from partial writes. (omp-doc·omp-organize do not write the JSON SSOT, so they are out of scope.) (must: resolves the asymmetry where omp enforced safe-fileops on *moving user files* but had no protection when writing *its own state files*) |
| T21 | `skill-bodies/omc-doctor/` install self-diagnosis | `skills/omp-doctor/SKILL.md` — diagnoses hook installation, python3 availability, and reference-card existence (the install gap *before the .omp existence* that omp-audit assumes). ⚠️ rules.json schema validation belongs to omp-audit, so it is excluded from doctor (avoiding duplication) |
| T22 | `dist/lib/worktree-cleanup-safety.js` `validateWorktreeRemovalTarget` | boundary validation in `references/safe-fileops.md`+`agents/organizer.md` — checks that the move target's realpath (symlink-resolved) is inside the project root, refusing if outside. An iCloud symlink-escape guard. 5 lines of stdlib (not a port) |
| T23 | `dist/lib/swallowed-error.js` `logSwallowedError` | a 1-line stderr (error context) on the bare `except` in both hooks — keeps fail-open while remaining debuggable. 1 line per except (not a module port) |
| T25 | OMC hook non-blocking re-injection philosophy (inject every turn but never block) | the **init discoverability** of `hooks/omp_route_emit.py` — when `.omp/` is absent in cwd, after the STAGE line emit a hint "no .omp/ yet — run omp-init first" (an absence-only marker, suppressed when present = no false nag). best-effort+fail-open, cwd-relative (a sub-dir false-negative is harmless). Resolves the discoverability gap where the user *doesn't know* init is needed; it is not auto-execution. User runtime suggestion (2026-05-30) |

> **T24 = intentional no-add**: the 3 — directory-readme-injector / pre-compact / posttool-capture — each have value
> but all grow the hook count 2→3, diluting the lightweight identity (T19) → **not added** as a single bundle. If an empirical need
> appears, revisit as a single consolidated hook.

### Exclude (with rationale)

| OMC pattern | Exclusion rationale |
|:---|:---|
| **creating** scoping-agent / consensus-agent types | redundant with the init skill and rule-architect → absorbed as an extension |
| **embedding search / semantic search** | file/rule matching is **deterministic grep only**. Embeddings risk "looks similar" false positives that move files into the wrong folder — organize corrupting the data. Permanently forbidden, now and in the future |
| **actual state MCP calls** | overkill for the management-loop philosophy. `.omp/` (.md) does surviving-compaction and inter-session handoff better. The 30s trap is documentation-only |
| **ambiguity quantification** (weighted sum / threshold / stability_ratio) | the qualitative gate is adopted — the magic-number basis is weak. "What is this folder" is honestly a qualitative judgment |
| persistent-mode **Stop-hook enforcement** | freeze risk + because file moves require human approval, an auto-loop is risky. organize's audit-PASS loop is sufficient. Deferred |
| **multi-perspective / realist / adversarial escalation** | redundant with pre-mortem/self-audit, and conflicts with the auditor's "detect only and halt" (detect≠execute separation) |
| 15+ code-only runtimes (comment-checker · code-simplifier · ast/lsp · python_repl · ultragoal · loop_authority etc.) | domain-irrelevant. Only lsp/ast are noted with *room for re-examination* as an aid to a future omp-doc code inventory |
| **dataset real-data movement / remote-push automation** | dataset-curator is metadata-only (SHA256 · split · lineage). Delegates when DVC/git-lfs is detected. Real-data movement carries iCloud/exFAT traps + leakage risk — permanently forbidden |

#### Exclude — OMC 4.14.4 deep re-analysis, 45 refutations (2026-05-30)

> Common principle: **what OMC solves with throughput / a parallel Node runtime, omp *designed away* at a higher level (single writer + human
> gate + deterministic grep).** So the race conditions and runtime assumptions one would import do not exist in omp.
> This table is the defense for "OMC has X, so why doesn't omp" (an intended absence, not an omission).

| Exclusion category | Representative OMC pattern (refuted candidate) | Refutation rationale |
|:---|:---|:---|
| concurrency/locking infrastructure | file-lock, session-isolation, project-memory-merge, mode-state-io `_meta` | omp is single-writer (organizer) + human gate (learn/codify), so concurrent-write contention is structurally absent → there is no problem for locking/merge to solve |
| Node-runtime-assuming hooks | context-injector, keyword-detector, codebase-map(+SKIP_DIRS), rules-injector | either cannot run in a stateless python subprocess or require ~150–300 lines of new infrastructure → would destroy the stdlib 2-hook lightweight strength. (codebase-map is covered by project-scanner, rules-injector by the verify hook + audit) |
| path/payload infrastructure | worktree-paths (785 lines), payload-limits, truncate-prompt | the genuinely needed portion is a 10-line stdlib util, not a module port. The payload guard is already handled by the dataset-curator architecture constraint. truncate has no premise since omp does not re-inject the prompt |
| execution-pipeline vocabulary | task-decomposer, model-routing, deepinit (whole) | generation/execution-domain-specific — orthogonal to the management loop (folders · naming · dataset) |
| already present in omp | learner (↔omp-learn), learner skill injector (↔wiki+route_emit), project-memory learner | observation→rule promotion is already covered by omp-learn + learned.md + wiki as 2 channels. The narrow sliver of automatic passive collection can be absorbed by a few regex lines in route_emit (no new hook needed) |
| session/compaction state | pre-compact checkpoint, session-end cleanup, project-memory pre-compact | omp hooks are stateless (there is no session state to clean up). Surviving compaction is already handled by T11 (notepad Priority Context). A new PreCompact/SessionEnd hook would dilute the lightweight identity |

---

## §5. 0.2.0 additions → propagation review to siblings (oms/omd/omx) (2026-05-31, 0 propagated)

We weighed whether to *propagate* to the siblings the 5 additions omp 0.2.0 made (`content_conventions[]` rule type,
the content audit axis `check_content_rule`, dead-link `find_dead_links`, `.omp/CONVENTIONS.md`, the specificity content item)
via adversarial verification (propose↔refute→synthesize, 2026-05-31) — result: **all 5 candidates × 3 siblings = 15 pairs
REJECT, 0 propagated**. The rationale converges to a single point: all 5 are rooted in omp's identity (**a management loop that
repeatedly re-checks one living `.omp/` with rules.json regular expressions**), whereas the siblings oms/omd/omx are *generation
pipelines that produce a fresh artifact every run*, so that premise (rules.json registry + audit PASS/FAIL gate +
specificity counter) is structurally absent (an intended design, not a defect — they verify via rubric qualitative evaluation). The parts the siblings
had worth porting are already held in domain-appropriate forms (the loud gates of scholar/docs-verify, the PPTEval/inspect
rubric, docs-standardize style spec, venues.md, wiki append-only). Per-sibling verdicts are recorded isomorphically in each sibling's
`references/omc-backport-analysis.md` §4. **This section is the persistent record of the honest conclusion "there is nothing to propagate" —
so the next session does not repeat the same review.** (omx has no backport-analysis document and is self-contained
by design, so it is recorded only in the sibling notes.)

---

**Analysis snapshot**: OMC 4.14.4 (not a runtime pin — auto-tracks marketplace latest, §2) · **isomorphic sibling**: oh-my-scholar `references/omc-backport-analysis.md` (paper domain) · oh-my-docs `references/omc-backport-analysis.md` (document domain) · **0.2.0 sibling propagation review**: 0 propagated (§5)
