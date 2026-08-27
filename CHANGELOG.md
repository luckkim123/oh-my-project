# Changelog — oh-my-project (omp)

All notable changes to this harness. Hook contract changes are recorded explicitly
(siblings oms/omd treat the route/verify hook text as a versioned contract).

## [Unreleased]

## [0.13.0] — 2026-08-28 — one place that knows where `.omp/` is

Phase 2 of the `.hq/` store unification. Behavior is unchanged: every helper
returns exactly the path its call site computed inline before, and the root
literal is still `.omp` — the switch to `.hq` and the read fallback are the
next phase.

### Added
- `hooks/omp_paths.py` — the single declaration site for `.omp` in this
  repo's code. `LEGACY_ROOT` plus a named helper per derived path
  (`rules_json`, `secretary_dir`, `state_dir`, `wiki_dir`, `learned_md`,
  `structure_md`, `datasets_md`, `garden_state_json`, `brief_md`,
  `verify_throttle_json`), the sweep glob tuple, and the `is_inside_store`
  predicate.
- `tests/test_omp_paths_lint.py` — the re-entry lint. An AST walk flags any
  `str` constant that contains the root literal and holds no whitespace;
  paths have no spaces, prose always does, so a prompt string mentioning
  `.omp/` is not a violation and `".omp/garden-state.json"` is. Docstrings
  are excluded explicitly, f-string pieces are included.

### Changed
- 18 call sites across `omp_content_audit`, `omp_doc_garden`,
  `omp_route_emit`, `omp_secretary`, `omp_session_brief`, and
  `omp_verify_emit` now call the helpers instead of building paths inline.

### Verification
- 246 passed, 5 skipped; exit code read without a pipe.
- The lint was checked for discrimination, not just for passing: a violation
  was planted, exit 1 reproduced, the file removed, exit 0 reproduced.
- `ruff check .` clean.

### Notes
- `tests/` and `references/` are outside the lint's scope, with the reason
  and the measured residual count recorded in the test's own docstring —
  fixtures need the literal, and `references/` python is copied into user
  projects where it cannot import a hook module.


## [0.12.2] — 2026-08-25 — a rule that reads as enforced and matches nothing

`rules.json` 의 `structure.directories[]` 항목은 `path: "."` 로 프로젝트 루트를
가리킬 수 있다. 배치 훅은 그걸 못 받았다 — 판정이 `rel.startswith(path + "/")`
하나였고 `path` 가 `.` 이면 `"./"` 로 시작하는 경로를 찾는데, `relative_to()` 는
그런 문자열을 절대 만들지 않는다. 그래서 루트 항목은 `enforced: true` 를 달고도
**단 한 번도 발화하지 않았다.**

이게 나쁜 종류의 실패인 이유는 조용해서다. 스키마 검증도 통과하고, 훅도 에러 없이
돌고, `rules.json` 을 읽는 사람은 루트가 감시되고 있다고 믿는다. 발견 경위도 그 점을
보여준다 — claudebase 에 `.omp/` 를 얹으며 초안의 `enforced` 근거를 코드로 대조하다
나왔고, 대조하지 않았으면 무효인 규칙이 배포될 뻔했다.

### Fixed

- **`path: "."`(및 빈 문자열)을 프로젝트 루트로 해석한다** (`hooks/omp_verify_emit.py`
  `_category_drop`). 루트 항목은 최상단 파일에만 발화하고 깊은 경로는 그대로 제외한다 —
  루트가 트리 전체를 삼키면 카테고리 개념이 무너진다. `README.md` 면제와 `Write` 전용
  규칙은 변동 없다.

### Added

- `tests/test_omp_verify_emit.py` 에 배치 테스트 5건: 루트 항목 발화 · 깊은 경로 무시 ·
  README 면제와 Edit 무시 유지 · 빈 경로도 루트(와일드카드 아님) · 이름 있는 카테고리
  분기 무회귀. 변별 확인 — 수정을 되돌리면 2건이 빨간불로 바뀐다.

## [0.12.1] — 2026-08-23 — a marker says where you are, not what you asked

훅이 답하던 질문은 하나였다: 주입할까. `.omp/` 가 있으면 예스였고, 프로젝트 폴더
안에서는 *모든* 턴이 그렇다. 그래서 "이어서 진행해줘" 같은 평범한 턴이 한 번도
쓰지 않을 단계 목록에 1,593자를 냈다. 마커는 이 폴더가 omp 프로젝트라는 뜻이지
이 요청이 프로젝트 작업이라는 뜻이 아니다.

### Changed

- **Route injection now has a verbosity axis: marker-only turns get `BRIEF`**
  (`hooks/omp_route_emit.py`). The relevance gate answered one question —
  WHETHER to inject — and `.omp/` being present answered it `yes` for *every*
  turn inside a project folder, so an ordinary "이어서 진행해줘" paid the full
  1,593-char checkpoint for a stage list it never used. A second, orthogonal
  predicate `_keyword_hit` (prompt tokens only, marker deliberately ignored)
  now answers HOW MUCH: an explicit project ask still gets `CHECKPOINT`
  verbatim, everything else gets `BRIEF`. Measured on one vault: **1,593 → 725
  chars** on a non-project turn, 1,593 unchanged on `"폴더 구조 정리해줘"`.

  Coverage is identical — a turn the gate suppressed is still suppressed, a
  turn it injected is still injected. What `BRIEF` drops is only the per-stage
  parenthetical prose, which `skills/omp-*/SKILL.md` already owns; the module
  docstring had claimed "this hook never embeds that knowledge inline, so there
  is no drift" while `CHECKPOINT` did exactly that. What `BRIEF` keeps in full
  is the `STAGE(project) →` output contract, every stage name (they are the
  skill names — routing would break without them), and all three ⚠️ rules,
  which declare themselves lane-independent and so must survive a non-project
  turn. Four tests lock each of those down.

  Also corrected in the docstring: `OMP_ROUTE_GATE`'s code default is `"off"`,
  but claudebase ships `"on"` in `config/settings.json` — read the env, not the
  default, before concluding anything about live behaviour.

## [0.12.0] — 2026-08-16 — the document that still names a folder nobody kept

### Added

- **`omp-garden` — a periodic doc-drift sweep, stage 16** (`skills/omp-garden/`,
  `hooks/omp_doc_garden.py`). Resolves every backtick-quoted path in the project's prose
  against the actual tree and reports the ones that do not exist, with the line and the
  sentence around them. Report-only: it never edits a document, never repoints a path, and
  never deletes anything.

  **Why it is not part of `omp-audit`.** `scan_structure_drift` already covers *declared*
  paths — `rules.json structure.directories[]` plus `.omp/STRUCTURE.md` and
  `.omp/DATASETS.md`. Every path this project actually lost track of was somewhere else: a
  README, a handoff note, a sibling harness's page. Those are the sweep's target, and the two
  `.omp/` documents the audit stage owns are excluded so one drift is never reported under two
  stages. It reuses `_BACKTICK_PATH`/`_PLACEHOLDER_PATH` from that module, so 0.11.1's
  placeholder fix applies here without being restated.

  **It carries state, and that is the other half.** A stateless sweep prints the same finding
  forever, so the third report reads exactly like the first — nothing separates new rot from
  "we looked and did not act". `.omp/garden-state.json` counts the sweeps each finding
  survived, marks it `ESCALATE` at 3, and reports what got resolved since the last run.
  Fingerprints key on file + cited path, deliberately **not** the line number: a line-keyed
  fingerprint resets to 1 on any edit above the citation, so the escalation would never fire
  while the state file still looked healthy.

  **Three verdicts, never one.** Repoint (it moved, the claim holds), rewrite (the claim went
  stale with the path), suppress (`GARDEN_OK: <reason>`, for a historical mention that is
  correct as written). A sweep that only repoints turns a post-mortem's record of where a bug
  used to live into a false statement — and without the escape hatch its reader learns to
  ignore it, which is the failure the vault's `citation-check.py` was rebuilt to avoid.

  **omp ships no scheduler.** Claude Code already provides `/loop` and `/schedule`; what was
  missing was the definition of what to look at periodically, not the timer. Arming it stays
  the human's call.

  **The discriminators were tuned against real corpora, not fixtures.** The first working
  version passed every unit test and produced **755 findings on claudebase** — unusable, and
  the exact failure the stage exists to prevent. Three filters, each measured:

  | Filter | What it removes | claudebase |
  |:---|:---|---:|
  | (none — backtick with a slash) | — | 755 |
  | parent directory must exist | `origin/main`, `remotion-dev/claude-code-plugin`, `a/b`, `claude/settings.json` — strings that were never paths in this tree | 110 |
  | dotted tail >5 chars or with `_` is a symbol | `hooks/omp_content_audit.check_content_rule` | — |
  | default `docs/*.md`, not `docs/**` | `docs/reference/omc-deep-analysis-v4.15.2/**`, a vendored analysis of a *different* repo whose every cited path is correctly absent here — **99 of the 110** | 10 |

  The parent-exists rule trades recall for readability on purpose: a drift that also deleted
  the parent directory is missed. The alternative is a report nobody reads. Widen with
  `--doc-glob` when a subtree really is this project's own documentation.

  First run found real drift on the first try: `CLAUDE.md` cites `./install.sh`, which lives
  at `installer/install.sh`.

  Registered across the 3-way sync invariant (`plugin.json` skills[], the `omp_route_emit`
  stage catalog, `tests/test_plugin_integrity.py`), plus two phrase-only gate tokens
  (`문서 정원`, `문서 드리프트` — bare `문서` belongs to the omd lane). 18 new tests.

## [0.11.1] — 2026-08-14 — a findings list that is mostly wrong stops being read

### Fixed

- **`scan_structure_drift` no longer reports template shapes as missing paths**
  (`hooks/omp_content_audit.py`). `_BACKTICK_PATH` treats any backticked `a/b` string in
  `STRUCTURE.md`/`DATASETS.md` as a path, so documentation that names a *format* rather than
  a file — `journal/YYYY-MM-DD.md`, `decisions/NNNN-slug.md`, `3_Archive/etc/...zip` — was
  reported as drift on every run. Those can never exist on disk; the finding was unfalsifiable.

  Measured on one vault before and after: **13 findings → 9**, removing exactly the 4
  placeholder shapes and leaving all 4 genuine ones (directories moved out by other work,
  plus a wiki note cited but absent). Only shapes actually observed are matched; bare
  `MM`/`DD` are deliberately excluded as too plausible in a real name, and the `YYYY` in a
  date template already carries the match.

  **This is a detection fix, not just tidiness.** The axis is warn-default and advisory, which
  means its only enforcement is a human reading the list. At 4-of-13 noise the list still gets
  read; the reason to cut it is that noise hides its neighbours — the same argument 0.11.0
  used to justify measuring a new guard's firing rate before shipping it, applied backwards to
  an axis that was never measured.

### Notes

- Four false positives remain and are **left alone deliberately**: three are relative
  fragments (`sim_validation/docs` is real at `0_Project/in_progress/albc/…`, quoted without
  its prefix), one is a frontmatter field list (`title/allDay/date/…`), one names a file in
  another repository. Each needs a rule this codebase does not have evidence for yet — whether
  a relative quote is a scanner limitation or a documentation defect is a judgment call, and a
  rule invented from a single sample is how a guard starts lying.
- `python3 -m pytest -q` — **214 passed, 1 skipped** (one new test asserts both directions:
  placeholders skipped, a genuinely missing real path still reported).

## [0.11.0] — 2026-08-14 — the drawer that offered no resistance

### Added

- **A placement signal in the PostToolUse hook** (`hooks/omp_verify_emit.py`). The hook
  already listed `Write` in its matcher, but its logic only looked at `.omp/` edits and
  Bash `mv`/`rm` — a `Write` that landed a whole new file somewhere questionable produced
  nothing. `detect()` gains an optional `(root, rules)` pair (two-arg callers keep working)
  and reports **a file created directly at the top level of an `enforced: true` category
  directory**, quoting that directory's own `role` so the session has the criterion in hand
  rather than a bare complaint. `README.md` is exempt — a category index belongs there.

  The motivating incident: a one-off session prompt, expiring on a fixed date, was written
  into a vault's `1_Area/` (PARA's *"ongoing responsibility with no end date"*). No layer
  objected; a human found it three days later, by which time another session had grown the
  file and a scheduled script had hardcoded its path.

  **Deliberately narrow, and the narrowness is measured.** Deeper paths are excluded because
  `…/albc/notes/x.md` sits inside a structure somebody already chose; only a category's own
  top level is the drawer that offers no resistance. On the vault above — 3,292 tracked
  files — exactly **6** sit at an enforced directory's top level, **4** of them the category
  README. So the rule fires on the 2 known-bad files and nothing else. That rate is the
  gate, not a nice-to-have: a guard that calls current practice a violation gets switched
  off in its first week.

  Advisory, like every other axis here: it reminds, never blocks, never moves a file, and
  stays silent when `root` or `rules.json` is unavailable rather than guessing.

### Notes on what this deliberately is NOT

- **No `placement[]` schema field, and therefore no rule about *which kind* of document
  belongs where.** That was the obvious design (name the document type by filename regex or
  frontmatter, name its destination) and it costs the 4-place coherence this repo charges
  for a new field — schema + codify + learn + audit — the same bill that killed
  `code_conventions[]` in 0.9.0. There is a fresher proof: one vault had hand-added
  `secretary.external_sources[]` to its `rules.json`, and because nothing consumed it the
  field was **read by zero code paths while silently making the whole file fail schema
  validation for four days**. A registration axis with no consumer is not a feature. The
  existing `role` prose plus this signal covers the measured case; a schema field can be
  argued for when a case appears that they do not.
- **No `PreToolUse` block.** omp has no PreToolUse hook at all, and the first one should not
  be a placement guess: a false positive there halts the work instead of annotating it.

## [0.10.0] — 2026-08-14 — the note remembered; nobody asked it again

### Added

- **`open_item` — the eighth `lint_wiki` kind, and the resurfacing channel omp did not
  have.** A wiki note routinely records something a session promised to do later. Nothing
  ever read it again: `lint_wiki`'s seven kinds covered the *page* (orphan / stale /
  oversized) and `learned.md` *rule candidates* (stuck / ready / contradiction), and
  `omp-brief` enumerated only the three `learned.md` kinds. A commitment written in a wiki
  note was, structurally, write-only. Measured on one vault: a "미결 (omp-organize 별도 세션
  대상)" recorded 2026-05-31 was still unread on 2026-08-14 — **three months**, ended by a
  human noticing, not by the harness.

  The unit is an **unchecked markdown checkbox**, `- [ ]`, closed by writing `[x]`
  (`references/output-layout.md` documents the convention; `omp-brief` now enumerates the
  kind alongside `ready_to_promote`/`stuck_candidate`/`contradiction`). Findings are
  per-file with a 3-item preview so one note cannot flood a brief. **omp never closes an
  item** — same detection ≠ execution invariant as every other axis, warn-default, never
  blocks a PASS.

### Notes on what this deliberately is NOT

Two mechanisms were designed, measured against the motivating case, and **rejected** —
recorded because both look obviously right on paper
(`docs/design/2026-08-14-resurfacing-detector-measurement.md` carries the full data):

- **No prose scan.** Matching 미결/TODO/pending in running text produced **3 false
  positives in 7 hits** on the vault above. A heading that *declares the item resolved*
  ("1차 미결 전부 해소") contains the same words as the item, and a filename can too
  (`RL-ALBC - TODO.md`). Open and closed states coexisted in one file with no
  machine-readable link between them. Restricting matches to headings and list items did
  not help — all three survived. A rule that calls current practice a violation gets
  switched off in its first week, so the convention carries the state instead: a checkbox
  is unambiguous and costs one character to close.
- **No age gate.** The obvious "flag it after 30 days" cannot use file mtime, because mtime
  answers *"was this page edited"*, not *"how long has this item sat"*. The motivating
  file's mtime on the day of the incident was **0.0d** — a different session had appended a
  section that morning while the three-month-old commitment sat untouched inside it. An
  unchecked box is actionable on sight; the human decides.

### Fixed

- **The suite now isolates the ambient kill switches** (`tests/conftest.py`, new). `run_hook`
  spawns the hook with `env=None` or `dict(os.environ, …)`, so a developer shell exporting
  `OMP_ROUTE_GATE` or `OMP_SKIP_HOOKS` fed those values straight into the subprocess. On a
  machine where claudebase's `config/settings.json` sets `OMP_ROUTE_GATE=on`, `python3 -m
  pytest -q` failed **8 tests** that have nothing to do with the gate: they took the
  suppression path, stdout came back empty, and the assertion read `"STAGE(project) → 가
  없다"` — a symptom that looks nothing like its cause. The conftest pops both variables once
  at collection; tests that exercise the gate are unaffected because they set the value
  explicitly via `_env(OMP_ROUTE_GATE=…)`.

  `test_ambient_kill_switches_are_scrubbed` asserts the cause directly rather than the
  symptom. Control measured both ways on the same commit: with the conftest,
  `OMP_ROUTE_GATE=on OMP_SKIP_HOOKS=route python3 -m pytest -q` → **207 passed, 1 skipped**;
  with it removed, the same command → **9 failed**.

  Test-only — no runtime behavior changes, so no version bump is required for this to take
  effect.

## [0.9.1] — 2026-08-14 — the index-coherence rule was scoped to the lane that never moves files

### Fixed

- **`⚠️ 인덱스 정합` now binds regardless of lane** (`hooks/omp_route_emit.py`, hook contract).
  The rule told a session to finish the `.omp/` update in the same task as a rename. It sat
  inside a block whose closing line read *"프로젝트 관리 작업이 아니면 이 블록 전체 무시"* —
  so the one turn that most needs it, an experiment or code session that renames a folder in
  passing, was explicitly told to discard it. **Moving files is not a lane.**

  The hook was never the gate, which is why this is a text fix and not a wiring one:
  `is_omp_related()` returns True on the mere presence of `.omp/` — its first branch,
  `if not _omp_missing(): return True` (cite the function, not a line: `CHECKPOINT` grows
  above it and shifts every number below) —
  so in any initialized project the block is injected on **every** prompt at every
  `OMP_ROUTE_GATE` setting. The suppression was happening one layer up — the model reading
  the closing line and honoring it. Measured on one vault mid-incident: a
  `sim_validation/docs/` rename landed in an experiment session and four sibling-harness wiki
  pages citing those paths went stale within the hour, with the coherence rule injected and
  discarded on every one of those turns.

  Two changes, both in `CHECKPOINT`:
  - The closing line now exempts the three `⚠️` items by name — each is self-scoped by its own
    precondition (file move / structural rename / structure-naming judgment), so only the
    stage judgment and the `STAGE(project) →` line stay lane-gated.
  - The coherence rule says **어느 레인에서 했든** out loud, and widens its target from
    `.omp/` alone to *any document that wrote the path down* — README, handoff, sibling-harness
    wiki. `.omp/` being current is not coherence if the handoff still points at the old path.

  +143 characters (1,402 → 1,545). The injection ceiling is counted in characters, so this is
  budgeted, not incidental.

### Notes

- `python3 -m pytest -q` — **206 passed, 1 skipped**. Run it with `OMP_ROUTE_GATE` unset or
  `off`: the suite does not isolate that variable, so a shell exporting `OMP_ROUTE_GATE=on`
  (claudebase sets it in `config/settings.json`) leaks into the subprocess hook calls and
  fails 8 tests spuriously — on this commit **and on its parent**. Pre-existing, not
  introduced here, and deliberately not fixed here; the suite's own env isolation is a
  separate change.

## [0.9.0] — 2026-08-10 — the house style was never written down

### Added

- **`omp-style` — the stage that induces CODE idioms from existing source.** `omp-codify`
  settled *where* a file goes (structure) and *what it is called* (naming). Nothing settled
  *how its contents are written* — the conventions a human author held in their head. An
  agent dropped onto a hand-written tree therefore imposes its pretrained mainstream idiom,
  and the only detector was a reviewer repeating the same correction. The stage scans four
  dimensions (file anatomy, state/control-flow naming, infrastructure placement, error and
  logging shape), induces the idioms actually in force, and proposes them as rules.

  Adapted from ECC's `inherit-legacy-style` (MIT, github.com/affaan-m/ECC, `origin:
  community`), which produced a standalone `.ai-style-rules.md`. Retargeting it at
  `rules.json` is the whole point: a file outside the `.omp/` SSOT is a fourth index that
  audit cannot read.

- **`omp-style` contract test** (`tests/test_plugin_integrity.py::test_omp_style_skill_contracts`)
  — asserts the stage reuses `content_conventions[]`, names `check_content_rule`, hands the
  write to codify behind a human GATE, keeps the 3-witness induction floor, and that
  `rules.json` has **no** `code_conventions` property.

### Changed

- **`content_conventions[]` is documented as what it always was: file-content, not
  note-content.** The schema description was already general ("what must (or must not)
  appear INSIDE matching files") and `hooks/omp_content_audit.check_content_rule` reads any
  file by path and applies a `re.MULTILINE` regex with **no extension restriction** —
  verified against `.py` and `.cpp` fixtures, each caught 1/2 files. But `omp-codify` step 2
  called it a "note-body convention" and `references/output-layout.md` said the same in two
  places, so the axis read as notes-only and a code-idiom axis looked absent. All three
  now say note bodies *or* code.

  This is why **no new schema field was added.** A `code_conventions[]` axis would have cost
  the 4-place coherence this repo charges for a new field (schema + codify + learn + audit)
  and would have handed `omp-audit`, `omp-learn`, and the schema three places to disagree
  about one rule. The gap was never storage or verification — both existed — it was that
  nothing *induced* the rules from source. That is exactly and only what `omp-style` adds.

- **Routing card carries the new stage** (`hooks/omp_route_emit.py`): `style(...)` in the
  stage list, `|style|` in the `STAGE(project)` enum, +65 characters (1,337 → 1,402 — the
  injection ceiling is counted in characters, so this is budgeted, not incidental). Four
  phrase tokens added to the relevance gate — `코드 스타일`, `코드 컨벤션`, `관용구`,
  `스타일 드리프트`. Phrases only: bare `스타일` is as ambiguous as bare `정리`, and
  "이 UI 스타일 바꿔" is not an omp turn. Verified 8/8 on a case set including that
  false-positive pair.

## [0.8.0] — 2026-08-10 — a graph is not coverage

### Added

- **`code_graphs.indexes[]` — the registry axis.** A project's local code indexes
  (code-review-graph, graphify, tokensave) become registered READ targets in
  `rules.json`, each carrying `tool` / `path` / `covers` / `excludes` / `refresh` /
  `convention`. The same contract `secretary.sources[]` established: registered through
  the `omp-codify` human gate, never auto-registered, and **registered without being
  owned** — the artifact stays where its tool put it and is never copied into `.omp/`
  (a graph is a build artifact; `.omp/` is a commit candidate).

  The gap this closes: a graph tool answers "is there a graph?" but never "does it cover
  what you are about to ask it". Measured on one Obsidian vault, `code-review-graph
  status` reported 21,865 nodes over 101 files with languages `bash, python, javascript,
  cpp, objc` — while the repo tracked 2,277 files of which **828 were notes**. The index
  was entirely vendored `.obsidian` plugin JS, the notes were absent, the build was 12
  days behind HEAD, and nothing reported any of it. A user-scope search-guard hook was
  meanwhile instructing every session to consult that graph before grepping.

- **`hooks/omp_graph_audit.py` + the audit graph axis (warn-default).**
  `scan_graphs(root, rules)` returns `graph_missing` (registered but absent on disk),
  `graph_stale` (CRG's `Built at commit` ≠ HEAD, or a graphify `needs_update` marker) and
  `graph_coverage_mismatch` (a language in `covers` the index does not hold). Same idiom
  as the Docker / secretary / governance axes: findings never block an overall PASS, and
  the auditor reports rather than fixes — each finding quotes the entry's own `refresh`
  command for a human to run.

- **`omp-organize`: `inbound imports: N` for code-index projects.** The code-side twin of
  the para preset's `inbound [[links]]: N` — the same "moving it breaks a reference
  silently" problem, sourced from `code-review-graph query importers_of <path>`. N > 0
  warns without blocking; judgement stays human. graphify is explicitly *not* the source:
  it has no incremental update, so its "0 importers" at move time is a false green.

- **`omp-handoff`: coverage travels with the delegation packet.** The Tool·source
  guidance element now carries the registered index's `tool` / `covers` / `convention`,
  plus any open `graph_stale` / `graph_coverage_mismatch`. Passing existence alone is what
  makes a sibling lane read an empty result from an index that never looked as "not here".

- **`omp-init`: propose, never build.** The confirmation report names any code-index
  artifact the scan found and proposes registration through `omp-codify`; for a code-heavy
  project with no index it proposes the build command for the user to run.

### Notes

- **omp does not build or refresh an index**, in any stage — the `omp-env`
  not-a-build-runner boundary, extended. Depending on an external binary would also break
  the stdlib-only / fail-open / cross-platform invariant every omp hook holds.
- **`tokensave` is never executed by omp, in any stage.** Its CLI re-installs agent
  integration as a side effect of commands that look read-only: a measured `tokensave
  status` printed `Wrote ~/.claude/settings.json` and re-injected its own
  UserPromptSubmit and Stop hooks, which then ran twice per prompt alongside the wrapper
  already wired there. A tokensave entry is therefore registration-only and its coverage
  is reported as undeclarable rather than verified — registration still earns its keep,
  because it is what tells a sibling lane "prose lives here, not in the code graph".
  `code-review-graph status` and graphify's read commands were checked against the same
  measurement and have no such side effect.
- Design record: `docs/design/2026-08-10-code-graph-registry-plan.md`.
- Verified with pytest (205 passed, 1 skipped), including 16 new graph-axis tests whose
  status fixture is the real vault measurement above.

## [0.7.0] — 2026-08-10 — absence is not health

### Added

- **`axis_dormant` — the fifth `scan_stale` finding kind, and the first that fires on an
  ABSENT record rather than an aging one.** `stale_task`, `stale_blocker`, `brief_drift`
  and `conflict_copy` each need a record to exist before they can see anything, so a
  chronicler surface nobody has ever written to is the one state the review agenda is
  structurally blind to. `axis_dormant` reports any of `raid.md` / `todo.txt` /
  `decisions/` still holding zero entries after more than `STALE_DORMANT_DAYS` (14) of
  recorded session history. A project with an empty ledger is NEW, not neglected, and is
  never flagged.
- **`raid_dormant` in `derive_status`, and the caveat it puts on the reason line.** RED is
  reachable only through the blocker count, so a `raid.md` nobody has filed against makes
  RED unreachable *and* makes the green/yellow reason assert "no blockers" about a surface
  holding no evidence either way. The count itself is unchanged — the reason now appends
  `raid.md never filed in Nd — 0 blockers is absence, not evidence`. A raid that was filed
  and cleared reports a real zero and is not annotated.

  Measured on a live vault 2026-08-10: `raid.md` still the bootstrap template, `todo.txt`
  and `done.txt` at 0 bytes, `decisions/` empty — all untouched for 30 days — while
  `journal/` grew to 15 files and `ledger.jsonl` to 15 KB. The journal held nothing but
  hook-written session stubs, so chronicler had never run at all, and every BRIEF that
  month reported a healthy `0 open blockers`. This is the omp face of the same defect omx
  v0.11.1 fixed: a mechanism whose input nobody writes reports its emptiness as health.
- **`rules.json` `secretary.surfaces[]` — the opt-out for the two checks above.** A dormancy
  finding nobody intends to clear is noise, not information, and the read-map half of the axis
  (`sources[]`) is independently useful without any chronicler surface at all. Absent means all
  three (never declared is not opted out, so existing projects keep the full check); an explicit
  `[]` declares the chronicler axis unused and silences both; a subset checks only what it names.
  A corrupt or missing `rules.json` fails open to all three.

- **`omp_route_emit` relevance gate (default-off).** An early-return guard decides WHETHER
  to inject the omp-routing checkpoint, never WHAT — the true-positive path emits the same
  context byte-for-byte. Keyword-OR-marker, never marker-only, so an `.omp`-less folder still
  gets the discoverability hint on a matching prompt.
- **Structural skill lint** over `skills/*/SKILL.md`, and a conservative `ruff` config wired
  into CI with existing violations fixed.

### Fixed

- **`ready_to_promote`'s `counter_examples` parse failure now blocks promotion instead of
  permitting it.** A malformed/non-numeric `counter_examples` value fell back to `0` —
  "no counter-examples" — which is exactly the state the §3.2 hard blocker is supposed to
  rule out, so garbage data could silently satisfy the promote gate. The `ValueError`
  fallback now leaves the candidate unable to match the `== 0` check (fail conservative,
  not permissive); 1 new blocking test.

## [0.6.2] — 2026-07-19

### Changed

- **Vendored `hooks/omp_atomic.py` from the new shared `om-core` repo** — byte-identical
  behavior; temp-file prefix changed from `.omp-tmp-` to `.om-tmp-` (no functional change).
  A local-only `tests/test_atomic_vendored_sync.py` byte-compares the vendored copy against
  `~/om-core/atomic_fn.py` and skips gracefully when that sibling repo is absent (clean CI).

## [0.6.1] — 2026-07-16

### Fixed

- **`ready_to_promote` now implements learning-protocol §3's hard blockers, not just the
  evidence threshold.** A candidate with `counter_examples > 0` (kills promotion outright,
  §3.2) or `user_overridden: true` (the user's "no" is durable, §3.3) no longer surfaces as
  ripe — previously both were ignored, so omp-brief/omp-handoff could present a
  user-rejected or violated pattern as "run omp-learn or defer" (2026-07-16 wiki-week
  review, HIGH). §3's non-contradiction criterion deliberately stays at the human gate —
  the independent `contradiction` finding surfaces it. Docstring + omp-audit/omp-brief/
  omp-handoff wording updated to match; 2 new blocking tests.

## [0.6.0] — 2026-07-14

### Added

- **Actionable-knowledge carry-forward (family wiki-status convention)** (`hooks/omp_content_audit.py`,
  `skills/omp-brief/SKILL.md`, `skills/omp-handoff/SKILL.md`, `tests/test_omp_content_audit.py`) — omp's
  adaptation of the om*-family fix for the failure class where an actionable item is recorded in the
  knowledge store yet silently dropped from the next summary. omp keeps its schema unchanged (wiki
  notes are deliberately schema-less; `learned.md` OBS blocks already carry `status`/`evidence_count`),
  so this is a derived-enumeration + prompt-reconcile change, not a new status field.
  - `lint_wiki()` gains a `ready_to_promote` finding: a `learned.md` candidate that reached
    `evidence_count >= 3` is ripe for `omp-learn` promotion. Previously such a candidate produced NO
    finding at all (`stuck_candidate` fires only below threshold), so it was invisible to
    enumeration — exactly the gap this closes. Derived from existing fields; the omp-learn human gate
    still decides.
  - `omp-brief` (step 2) and `omp-handoff` (step 2) now reconcile the next-session goal / delegation
    packet against the open actionable findings from `lint_wiki()` (`ready_to_promote`,
    `stuck_candidate`, `contradiction`): each open one is reflected or consciously deferred, never
    silently omitted. Enumeration-only, WARN-level — omp never hard-gates on the wiki.

### Changed

- `.claude-plugin/plugin.json`: `version` 0.5.0 → 0.6.0.

## [0.5.0] — 2026-07-11

### Added

- **`secretary.sources[]` read-map** (`references/schemas/rules.schema.json`, `references/secretary-protocol.md`) — registers existing project state surfaces (Kanban board, daily-notes dir, status table) as counted sources rather than duplicating them under `.omp/secretary/`. Kinds: `todo`/`schedule` are count-parsed (todo.txt lines / markdown checkboxes; `path` may be a file or a directory — directory sums non-recursive `*.md` open-counts), `journal`/`status` are read-map only (no count). `derive_status(root)` return gains a `"sources"` key. Registration only through the `omp-codify` human gate (D14) — never auto-discovered or auto-registered.
- **`omp-organize` para preset — §7 source proposal table** (`references/presets/para.md`) — when running the `para` preset, dry-run move plans now propose known state surfaces as `secretary.sources[]` codify candidates (a table the human reviews at the codify gate, not an auto-write).
- **`omp-organize` wikilink inbound counts** — para dry-run move plans now show each note's wikilink inbound count alongside the move, surfacing orphan/hub notes before relocation.
- **`omp-handoff` skill** (`skills/omp-handoff/SKILL.md`) — a delegation-briefing assembler run once immediately before handing work to a sibling harness (oms/omd/omx/omc/superpowers). Assembles an Anthropic multi-agent 4-element knowledge packet (Objective / Output format / Tool·source guidance / Boundaries) from existing omp state (`todo.txt`/`raid.md`, `output-layout.md`, PROJECT.md + wiki grep-by-topic + `derive_status(root)["sources"]`, rules.json + open raid blockers) — references only, never inlines full source documents. Produces three artifacts in one pass: a session-consumed briefing block, an audit copy under `.omp/work/handoffs/YYYY-MM-DD-<target>.md` (retention 10, self-trimmed), and a ledger `handoff_prepared {target, topic}` event. `omp_route_emit.py` STAGE catalog gains `handoff` (13 → 14 stages); does not decide the delegation lane (omha's role, unchanged, §11.3).
- **`omp-log` handoff-return absorption** — a sibling harness's compressed return digest (1–2k tokens) is absorbed into `omp-log`'s existing five destinations rather than a new sixth one; not enforced (R5).

### Changed

- `.claude-plugin/plugin.json`: `version` 0.4.0 → 0.5.0; `skills[]` gains `omp-handoff` (13 → 14); description gains the two 0.5.0 capabilities.
- `hooks/omp_route_emit.py` **CHECKPOINT text changed** (hook contract — siblings oms/omd treat this as versioned): STAGE catalog line now enumerates `...|log|brief|review|handoff|omp-pilot|omp-doctor` (13-way → 14-way).
- README.md: skill table 13 → 14 rows (adds `omp-handoff` under the secretary skeleton), "13 skills" status line → "14 skills", secretary axis section gains a sources read-map / delegation-handoff / wikilink-inbound-counts summary.

### Notes

- D8 (derived-only status, no LLM estimate) extends to `secretary.sources[]`: counts come from `count_source_open`, never an LLM guess.
- D12 (handoff is same-context consumption, not IPC) — the session-in briefing block is the primary artifact; the `work/handoffs/` copy is audit-only.
- D14 (registration is human-gated) — `secretary.sources[]` entries are proposed by presets/organize but only written through `omp-codify`'s approval gate, same as structure/naming rules.
- §11.3 (omp does not pick the delegation lane) is unchanged by `omp-handoff` — it assembles the packet strictly after omha has already decided the target lane.
- R6 (registering the vault's own `secretary.sources[]` against this feature) is a human-gated operational act performed in the vault's own `.omp/`, not part of this repo's release.
- `omha` `cards/omp.json` route-catalog sync (the `handoff` STAGE) is a separate commit in the `oh-my-heroacademia` repo (R7), out of scope for this release.

### Verification

- `python3 -m pytest -q` — 122 passed (15 new tests over 0.4.0's 107: secretary sources schema + `derive_status` aggregation + directory-source support, para preset/organize content, omp-handoff integrity/contract sync).

## [0.4.0] — 2026-07-11

### Added

- **Secretary axis (time)** — a second axis alongside the existing governance axis (space), sharing the same `.omp/` SSOT, hook layer, and generic→specialized loop. Adds session journal, todo/RAID, decisions, and pull-style briefing under `.omp/secretary/`.
- **3 new stage skills** (`skills/omp-log`, `skills/omp-brief`, `skills/omp-review`):
  - `omp-log` — universal capture router, one entry point / five destinations (journal, todo.txt, raid.md, decisions/ ADR, rule observation).
  - `omp-brief` — pull-style briefing; regenerates `.omp/secretary/BRIEF.md` from ledger/todo/raid/journal state (traffic light, state-of-play, top-5 tasks, open blockers, next-session goal, decision paths) — every number is `derive_status(root)` output quoted verbatim, never an LLM estimate (D8).
  - `omp-review` — weekly (or on-demand) re-evaluation: BuJo-style migration for every open `todo.txt` task (migrate/strike/done, human-judged per item, never auto-carried-over), a `scan_stale` sweep, `raid.md` re-triage.
- **1 new agent** (`agents/chronicler.md`, sonnet) — the sole LLM writer of `.omp/secretary/**` (journal narrative, `decisions/`, `todo.txt`, `raid.md`, `BRIEF.md`). Never writes `ledger.jsonl` or the hook's session-stub lines (D7, disjoint at the line level); never closes a task/blocker (D9); never writes a progress percentage (D8).
- **`hooks/omp_secretary.py`** — pure-function core (stdlib only) for the secretary axis: ledger append/parse, `derive_status(root, sources=None)`, `scan_stale`, `redact_secrets`, journal tag extraction, session-stub construction. `sources=None` keeps Part I behavior unchanged and opens the signature for a future `secretary.sources[]` extension (design v3 footnote) without rework.
- **2 new session hooks**: `omp_session_brief.py` (SessionStart) — advisory-only injection of `.omp/secretary/BRIEF.md` (≤30 lines) when present, silent otherwise, never auto-resumes work; `omp_session_capture.py` (SessionEnd) — appends a machine-only journal session-stub once per session, no LLM involved, ascends to find `.omp/` root, redacts before write.
- **`.omp/secretary/` layout** (`references/secretary-protocol.md`, new; `references/output-layout.md` §addition) — `ledger.jsonl` (append-only event log: `task_added|task_done|blocker_opened|blocker_closed|decision_recorded|gate_passed|session_start|session_end`), `journal/YYYY-MM-DD.md`, `todo.txt`, `raid.md`, `decisions/`, `BRIEF.md`.
- **Secretary hygiene audit axis** (warn-default, in `omp_content_audit.py`/`auditor`) — reuses `scan_stale`/`brief_hash_check` to flag stale tasks/blockers, BRIEF drift, and sync-conflict copies (e.g. `ledger 2.jsonl`) under `.omp/secretary/**`.
- **Governance-side wiki/learned.md lint** (warn-default) — 6 mechanical checks (orphan, stale, broken-ref, oversized, stuck-candidate, structural-contradiction) plus a `scan_structure_drift` sweep, both reusing secretary pure functions; no auto-promotion or auto-deletion.
- **Route/hook wiring** — `omp_route_emit.py` STAGE catalog gains `log|brief|review` (13 stages total); `OMP_SKIP_HOOKS` kill-switch unified across all four hooks; `omp_verify_emit.py` gains a content-hash advisory throttle (`.omp/state/verify-throttle.json`) so repeated organizer batch-moves don't re-fire the same reminder.
- **Existing-stage integration** — `omp-init` creates the `.omp/secretary/` skeleton by default (GATE 1 note), `omp-pilot` runs `omp-brief` once at the end, `omp-doc`/`omp-codify` cross-reference secretary sources, `omp-doctor` checks the two new hooks are registered.

### Changed

- `.claude-plugin/plugin.json`: `version` 0.3.0 → 0.4.0; `skills[]` gains `omp-log`/`omp-brief`/`omp-review` (10 → 13); `hooks` gains `SessionStart` (`omp_session_brief.py`) and `SessionEnd` (`omp_session_capture.py`) entries alongside the existing `UserPromptSubmit`/`PostToolUse`; description now names the secretary axis.
- README.md: skill table 10 → 13 rows, agent table 5 → 6 rows (adds `chronicler`), roster summary line, new "Time — secretary skeleton" section alongside the existing "Space — stage skeleton" section.

### Notes

- Secretary content is strictly human/hook-authored, never LLM-estimated: `chronicler` writes narrative and judgment only; every status figure traces to `derive_status`; no task/blocker auto-closes (D9); journal/ledger are append-only, never truncated (D6).
- Sibling propagation reviewed and rejected — oms/omd are output-per-artifact generation pipelines with no daybook/session-journal concept; the secretary axis is unique to omp's "living folder, revisited over many sessions" identity (recorded in `references/omc-backport-analysis.md` §6 and `learning-protocol.md`'s "Secretary-axis boundary" section).
- `omha` `cards/omp.json` route-catalog sync (log/brief/review verbs) is a separate commit in the `oh-my-heroacademia` repo, out of scope for this release.

### Verification

- `python3 -m pytest -q` — 107 passed (40 new tests over 0.3.0's 67: secretary pure-function core, ledger schema round-trip, `derive_status`/`scan_stale`, redaction, chronicler write-scope contract, session hook fail-open/once-per-session/advisory-only, route STAGE 12-way enumeration, plugin skill/hook registration round-trip, governance lint axis).

## [0.3.0] — 2026-06-21

### Added

- **omp-env stage** — environment assets (Dockerfile/compose) canonical into `.omp/env/`; generation gate (dry-run → approval → verification), personal-value resolver, in-place invariant preserved.
- **docker environment governance** — `rules.json` `docker_naming` (optional), `manifest.json` `docker_images[]` (optional, external ref), `omp-audit` docker axis (`hooks/omp_docker_audit.py`, warn-default, rule-id-as-data: DL3007/secret-in-env/compose-version).
- **provenance tracking** — rule `origin:standard` + `provenance` object (OCI/CIS/SemVer and other external standards; MUST→error / SHOULD→warn) + `standards_registry`. New data file: `references/standards-registry.seed.json`.
- **docker preset** (`references/presets/docker.md`) + **`docker-mechanisms` reference card** (`references/docker-mechanisms.md`) — scaffold/inventory methodology, multi-user server patterns, pitfalls, remote-training knowledge (absorbed from claudebase docker-env skill, personal values removed).

### Changed

- omp identity: "folder governance" → "project environment + structure governance" (output-layout.md constitution fence: `.omp/env/` SSOT, root holds build-tool view only).
- `omp-codify` (docker_naming + provenance), `omp-dataset` (docker_images[]), `omp-audit` / `auditor` (docker axis, image-drift exception handling).

### Notes

- claudebase `docker-env` skill is absorbed into omp and scheduled for removal (single ownership).
- All new schema sections (`docker_naming`, `docker_images[]`, `provenance`, `standards_registry`) are optional — existing `.omp/*.json` files remain fully backward-compatible.

### Verification

- `python3 -m pytest -q` — 67 passed (18 new tests covering docker audit axis, docker_images schema, provenance schema, standards_registry, omp-env generation gate).

---

### Changed (Unreleased pre-0.3.0 carry-in)

- **Clarified the dataset definition to be format-agnostic (role-based) — blocks the "dataset = ML input file" misreading (code/schema unchanged, prompts only).**
  In real use, when trying to register a ROS bag or experiment data, *every example* across the skills/agents was filled
  with a single structured ML pipeline like `train.parquet`/`rows`/`.csv`, leaving a gap where "dataset = tabular ML input"
  got narrowly induced; this fills that gap. The schema (`manifest.schema.json`) already makes `rows`/`split`/`lineage`
  all optional, so it can already accommodate unstructured data — the problem was not the *rules* but the *biased example
  distribution*, so the schema/code logic stays unchanged and only the definition/example wording was strengthened:
  - `skills/omp-dataset/SKILL.md`: in `<Use_When>` and `<Steps>`, demoted the extension enumeration to *examples* and
    added unstructured ones (`.bag`/`.db3`/`.png`/`.mp4`/`.pcd`) alongside. Added a one-liner: "dataset discrimination
    criterion = role, not format (is it a fixed, tracking-worthy input/collected data?)" — `.npy` produced every run = run
    artifact (out of scope), `.bag` one-time collection = dataset (in scope).
  - `agents/dataset-curator.md`: added a new paragraph at the Role source point — "What counts as a dataset is defined by
    ROLE, not format" (explicitly naming robotics/sensor/media). Changed the extensions in the Investigation_Protocol from
    a whitelist to a hint, reinforced the `rows` tabular-only wording with "omission is normal for unstructured data," and
    added a ROS bag registration pair to the Good/Bad examples (skipping `.bag` for format reasons = Bad). 47 tests pass
    (documentation change, 0 regressions).
- **Prevent index drift after organize — codified that "a move that changes structure is one task that includes syncing the `.omp/` index" (hook contract change).**
  In real use, after a folder rename/flattening (`12_Theses_Defense` → `12_Masters_Thesis` + abolishing the intermediate
  layer), `.omp/STRUCTURE.md`/`rules.json`/`DATASETS.md` were left pointing at the old paths, forcing the user to explicitly
  instruct "update the index too"; this fills that gap. Strengthened three places at the guidance/wording level only (code
  logic unchanged):
  - `skills/omp-organize/SKILL.md`: added Step 8 (index sync) — if a moved folder is written by name in rules.json/STRUCTURE.md,
    syncing is part of the definition of organize completion (simple path substitution = direct Edit, changing rule meaning =
    codify gate). No-op if structure is unchanged. Reflected in "order unchanged" and Output as well.
  - `hooks/omp_route_emit.py`: added a one-liner to CHECKPOINT — "⚠️ index consistency" — finish the `.omp/` update within
    the same task after a structure-affecting move or a bare-hand mv (no drift). Existing STAGE/NO_OMP markers unchanged.
  - `hooks/omp_verify_emit.py`: added a one-liner to the PostToolUse reminder — "if it's a move that changed structure, the
    index update is part of this task." Avoids freeze-inducing wording ("fix before continuing") (suggestion → completion-condition
    tone only). 49 tests pass.
- **Added `references/omc-backport-analysis.md` §5 — sibling propagation review of 0.2.0 additions (propagation 0).**
  Adversarially verified (15 pairs) whether the 5 items 0.2.0 added (content_conventions, content audit, dead-link,
  CONVENTIONS.md, the specificity content term) should propagate to oms/omd/omx → all REJECT. All 5 depend on omp's
  "living `.omp/` management loop" identity and have no place in the generation-pipeline siblings (intended absence).
  Permanently recorded the "nothing to propagate" conclusion to prevent repeated re-review. The per-sibling isomorphism
  verdict is recorded in oms/omd `omc-backport-analysis.md` §4 (omx is self-contained/has no docs, so only in the sibling
  record). 0 code changes — docs only.

## [0.2.1] — 2026-05-31

### Fixed

- **`find_dead_links`: Obsidian table-escaped pipe `[[Note\|alias]]` no longer
  false-flagged as dead** (was capturing the trailing backslash into the target,
  e.g. `Perceptron\`, which never matched the stem set). Table cells escape the
  alias separator as `\|`; the target is now normalized by stripping a trailing
  backslash before resolution. Found via real-vault audit (67 false positives → 0).

## [0.2.0] — 2026-05-31

### Added

- **`content_conventions[]` rule type** (`references/schemas/rules.schema.json`) — note-body
  authoring rules the structure/naming axes could not express: `check.pattern` (Python `re`)
  × `expect` (present/absent) × `scope` (body/frontmatter), with `applies_to` glob, `origin`,
  `severity`. Optional top-level key → every existing rules.json stays valid (backward-compatible MINOR).
- **content + wikilink audit axes** — `hooks/omp_content_audit.py` (`check_content_rule`,
  `find_dead_links`, `split_frontmatter`), pure stdlib, the canonical algorithm the `auditor`
  agent now invokes. Content axis is enforced (error/warn/info → error fails the gate); wikilink
  integrity is a health hint (info, never fails the gate). Absorbs the downstream `link-checker`
  validator (preserves its case-insensitive resolution and non-md embed handling).
- **`.omp/CONVENTIONS.md`** — human-readable narrative paired with
  `rules.json.content_conventions[]`, alongside STRUCTURE.md/NAMING.md. Created by codify/learn
  only when content_conventions exist (not an init invariant).

### Changed

- `specificity` now counts `content_conventions[]` entries (learning-protocol §4) — content
  rules with origin inductive/learned raise specificity like structure/naming rules. Formula
  and monotonic property unchanged.
- `learned.md` `candidate_rule.target` enum gains `content_conventions[]` — content observations
  travel the heavy channel through the human gate, never the light wiki channel.
- `omp-codify` / `omp-learn` / `rule-architect` handle the new type; `auditor` / `omp-audit`
  gained the content + wikilink axes.
- **`learning-protocol.md` §5 — wiki append-only discipline made explicit.** The light
  channel (`.omp/wiki/`) always *intended* accumulation ("more specialized the more you write", "accrue freely"),
  but never wrote the binding rule that a revisited `wiki/<topic>.md` is *appended* (not
  rewritten/truncated) and that whole-file overwrite is reserved for the paired SSOT docs
  (PROJECT/STRUCTURE/NAMING/DATASETS), never for a wiki note. Adjacent in `omp-doc`, the
  same controller is told to whole-overwrite the human .md docs — this clause forecloses
  that habit bleeding into the light channel. The `## <date>` section heading is a *soft*
  free-form convention, **not** a frontmatter schema (§6.A's "no database, no index" trust
  model is untouched). Echoed in `skills/omp-doc/SKILL.md` where both instructions sit
  together. Sourced from a cross-harness analysis against **omx** (oh-my-experiments) wiki,
  whose INV-2 append-merge invariant (e2e-verified) proved the discipline; omp adopts the
  written rule only — none of omx's engine (file-locks, frontmatter schema, scoring/lint)
  transfers (single-writer, free-form-grep domain — correctly rejected).

### Verification

- `python3 -m pytest -q` — 48 passed (schema content_conventions validation + content/link
  pure-function tests: present/absent × body/frontmatter, dead-link detection, case-insensitive
  resolution, non-md embed skip, CRLF frontmatter).
- Backward-compat: existing rules.json validate unchanged (content_conventions optional).

## [0.1.0] — 2026-05-30

Initial implementation. Project-folder management & evolution harness — sibling of
oh-my-scholar (oms) and oh-my-docs (omd), modeled on their verified stage-driven golden.

### Added

- **9 stage skills** (`skills/omp-*/SKILL.md`): init, codify, organize, dataset, doc,
  learn, audit, pilot, doctor — a management loop, not a generation pipeline.
- **5 agents** (`agents/*.md`, 11-section `<Agent_Prompt>` XML):
  - `project-scanner` (sonnet, read-only) — inventory + inductive structure/naming scan
  - `rule-architect` (opus, read-only) — preset×scan synthesis, promotion judgment
  - `organizer` (sonnet, write) — the ONLY file-moving agent; obeys safe-fileops.md
  - `dataset-curator` (sonnet, write manifest) — checksum/split/lineage, metadata-only
  - `auditor` (opus, read-only) — rule-compliance PASS/FAIL, detection-only
- **7 preset cards** (`references/presets/`): python-ml, web-app, research-lab,
  monorepo, johnny-decimal, para, generic — generic seeds for the "ships generic" half.
- **4 reference cards** (`references/`): safe-fileops.md (organizer's hard protocol),
  output-layout.md (.omp/ path SSOT), omc-backport-analysis.md (OMC adopt/exclude),
  learning-protocol.md (the generic→specialized self-evolution SSOT).
- **2 machine schemas** (`references/schemas/`): rules.schema.json (with `specificity`
  0..1 tracking generic→specialized), manifest.schema.json (metadata-only datasets).
- **4 hook-layer files** (`hooks/`, stdlib-only, fail-open, cross-platform) — 2 passive
  hooks + 1 write helper + package init (the lean identity stays "2 passive hooks"):
  - `omp_route_emit.py` (UserPromptSubmit) — injects `STAGE(project) → …` checkpoint; also
    appends a one-line "no `.omp/` yet — run omp-init first" hint when cwd lacks `.omp/` (T25).
  - `omp_verify_emit.py` (PostToolUse) — integrity reminder after `.omp/` edits or
    move/delete commands. Deliberately avoids the freeze-inducing "fix before
    continuing" phrasing (OMC freeze pattern); reminder tone only, never auto-fixes.
  - `omp_atomic.py` — `atomic_write_json` helper (tempfile→fsync→os.replace) for `.omp/`
    SSOT writes; not a hook, a library the writing skills route through (T20).
  - `__init__.py` — package marker so the helper/tests import cleanly.

### Hook contract

- `omp_route_emit.py` STAGE catalog = `init|codify|organize|dataset|doc|learn|audit|omp-pilot|omp-doctor` (9 stages).
- `omp_verify_emit.py` fires on `Edit|Write|MultiEdit|Bash`; reminds only on `.omp/`
  paths (incl. Windows `\` separators) or move/delete commands; silent otherwise.

### Verification

- `tests/` — 34 passed, 1 skipped (jsonschema optional). Covers: route 9-stage
  enumeration, fail-open, sibling-label distinctness (STAGE(project) ≠ paper/docs/ROUTE),
  no-emoji, stdlib-only; verify .omp/ detection, move detection, silence on unrelated
  work, **no-freeze-phrase**, Windows path, no-auto-fix; schema validity, specificity
  bounds, metadata-only manifest, SHA-256 determinism + pattern match.

### Deployment

- **omha routing: no card** — omp is a 2nd-tier domain handler, exactly like siblings oms/omd
  (omha `cards/` holds only the tier-1 *how-you-work* lanes: omc, superpowers). omp is routed via its
  own `hooks/omp_route_emit.py` (`STAGE(project) → …`) plus its `plugin.json` description landing on
  omha's 2nd-tier domain-skill path. omha core / omc / superpowers cards stay untouched. (Card-tier
  rationale: design §6 re-review correction. The earlier `cards/oh-my-project.json` was removed via trash.)
- **Marketplace registration + git push: done.** The harness is pushed to the GitHub source
  (`luckkim123/oh-my-project`, public) and registered in heroacademia's
  `.claude-plugin/marketplace.json` alongside siblings oms/omd, with `oh-my-project@heroacademia`
  enabled in claudebase `config/settings.json` — installable like the other siblings.

### Notes

- **runtime end-to-end not yet measured** — Claude Code does not reload plugins mid-session;
  a fresh session is required to load the skills/hooks and exercise the full loop.
- Identity axis unique to omp (absent in oms/omd): the **generic→specialized** evolution
  — logic stays generic, the per-project `.omp/` diverges (see learning-protocol.md).
