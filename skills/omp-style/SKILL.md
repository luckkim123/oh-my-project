---
name: omp-style
description: |
  The stage that induces a project's implicit CODE idioms from its existing source and turns them into
  machine-checkable rules — in-file declaration order, state/flag naming, where cross-cutting utilities live,
  and error/logging shape. Reads the code that is already there, proposes `content_conventions[]` entries with
  code globs (the same axis omp-audit already verifies deterministically), and hands the write to omp-codify.
  Detection only — it never writes rules.json itself and never edits source. Exists because an agent dropped
  onto a hand-written legacy codebase imposes its pretrained mainstream idiom unless the house style is
  written down first.
  Triggers: 코드 스타일 성문화, 관용구 규칙, 우리 코드 스타일대로, 스타일 드리프트, 레거시 스타일 상속,
  코드 컨벤션 정리, 기존 코드 스타일 파악, omp style, code idiom, code conventions, inherit legacy style,
  style drift, house style, codify code style
---

# omp-style — Induce & Codify Code Idioms (Management Loop, Stage 1b)

<Purpose>
`omp-codify` nails down **where** a file goes (structure) and **what it is called** (naming). This stage nails down **how its contents are written** — the conventions a human author held in their head and never wrote down. It reads the source that already exists, induces the idioms actually in force, and proposes them as `content_conventions[]` rules so `omp-audit` can fail a PASS/FAIL verdict on drift. The write itself is `omp-codify`'s job; this stage proposes.

The mechanism is deliberately **not new**. `rules.json.content_conventions[]` is already "what must (or must not) appear INSIDE matching files", `applies_to` is any glob, and `hooks/omp_content_audit.check_content_rule` reads a file by path and applies a Python regex to its body or frontmatter with no extension restriction — verified against `.py` and `.cpp` fixtures. Adding a parallel `code_conventions[]` axis would be a second architecture for a problem the first one already solves, and would put the same rule in two places for `omp-audit`, `omp-learn`, and the schema to disagree about.
</Purpose>

<Use_When>
- The store exists and an agent is about to write code in a codebase a human hand-wrote — before the first feature, not after the style has already drifted.
- Generated code keeps coming back "not wrong, but not how we write it here", and review comments repeat the same correction.
- Onboarding a subagent fleet onto a legacy tree: they inherit hooks, not your resolve, and not your reading of a prose style guide.
- A convention exists but only in a reviewer's head, so `omp-audit` cannot fail anything when it is broken.
</Use_When>

<Do_Not_Use_When>
- No omp store exists → **omp-init first**. This stage updates rules that init created.
- The convention is about *which folder* or *what filename* → that is `omp-codify` (structure/naming), not contents.
- The convention is about note or document bodies rather than code → also `omp-codify`, same `content_conventions[]` axis; you do not need this stage to reach it.
- You want to find files that already violate an existing rule → `omp-audit` (read-only verdict).
- You want to *rewrite source* to match the induced idiom → out of scope for every omp stage. omp never edits a user's source; it writes rules and moves files (organize only). Reformatting is a human's call with a formatter.
- The language has an authoritative formatter that already settles the question (`gofmt`, `rustfmt`, `black`, `clang-format`) → record the formatter as the rule and stop. Do not re-encode what a formatter enforces; a rule that duplicates a formatter is drift waiting to happen.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Induce, never invent.** Every proposed rule cites the files it was induced from — at least **3 existing files** agreeing, or it is not a convention, it is a preference. A rule with 1 witness is a coincidence; with 2, a habit; the floor is 3. State the witness count per rule and drop anything below it.
- ⚠️ **Machine-checkable or prose, never a fake rule.** A proposed `content_conventions[]` entry must be a regex `check_content_rule` can actually run. If an idiom cannot be expressed that way ("errors are handled at the boundary, not inline"), it goes into `.hq/community/CONVENTIONS.md` as prose and **must not** be smuggled into `rules.json` as an approximate regex — an approximate rule produces false violations, and a rule nobody trusts is worse than a documented habit.
- ⚠️ **Detection ≠ write.** This stage proposes; `omp-codify` writes `rules.json` + `CONVENTIONS.md` together in one pass with its managed-hash check, snapshot, and schema validation. Do not write `.hq/config/project/rules.json` here, and do not write half of the pair.
- ⚠️ **Human approval gate.** A code-idiom rule makes `omp-audit` fail on existing files, which is a heavy consequence. Present the proposal with its per-rule witness count and predicted violation count on the current tree; proceed / revise / abort. No auto-pass.
- ⚠️ **Predict the violations before proposing.** Run the candidate regex over the tree and report how many files it would fail *today*. A rule that fails 200 of 210 files is not the house style — it is the inverse of the house style, or the regex is wrong. This check is what stops a confidently backwards rule from entering the SSOT.
- ⚠️ **Never edit source.** Not to "demonstrate" the convention, not to fix a violation found while scanning. `omp-organize` is the only stage that touches user files at all, and even that only moves them.
- **specificity + provenance.** An induced rule is `origin: "inductive"` (never `preset`). Raise `specificity` and record the source in `learned_refs[]` through codify, exactly as a learn promotion does.
- Light observations ("this tree splits helpers by layer, unusually") become a post (`hq post`) without a gate. Only the rule change is gated.
</Execution_Policy>

<Steps>

1. **Confirm scope and pick the sample.** Read `.hq/config/project/rules.json` (existing `content_conventions[]` — never re-propose one that is already there) and `.hq/config/project/STRUCTURE.md` for the layer map. Then size the code surface per language:

   ```bash
   git ls-files -z | tr '\0' '\n' | sed -n 's/.*\.\([A-Za-z0-9_+]*\)$/\1/p' | sort | uniq -c | sort -rn | head
   ```

   `-z` matters: `git ls-files` renders non-ASCII filenames as octal escapes without it, and a survey that silently skips them is not a survey. Choose the sampling tier by count — ≲50 files: read all; 50–500: read every file in the infrastructure layer plus 3 per business-layer dimension; ≳500: sample 3–5 per dimension per layer and say so in the report. **Vendored trees are excluded** (`node_modules`, `vendor`, third-party checked into the tree): they carry someone else's idiom, and inducing from them proposes rules against your own code. If the repo has a code graph, `code_graphs.indexes[].excludes` already lists them.

2. **Scan the four idiom dimensions.** For each, record the observed pattern, the witness count, and whether it is regex-expressible:

   | # | Dimension | What to look for | Typically regex-able |
   |---|:---|:---|:---|
   | 1 | **File anatomy** | Declaration order inside a file (imports → types → public API → helpers), header/guard conventions, `__future__`/`#pragma once`/license header | yes — anchored `\A` patterns |
   | 2 | **State & control flow** | Naming of async state, flags, error variables; early-return vs nested; loop idiom | partly — naming yes, shape no |
   | 3 | **Infrastructure placement** | Where cross-cutting code lives (formatters, middleware, interceptors, logging) | usually structure, not content — hand to `omp-codify` |
   | 4 | **Error & logging shape** | Exception taxonomy, log call form, what is never swallowed | partly — call form yes, policy no |

   Anything in the "no" column is prose for `CONVENTIONS.md`, by the Execution_Policy rule above.

3. **Draft candidate rules and measure them.** For each regex-able idiom, write the `content_conventions[]` entry and *run it before proposing it*:

   ```bash
   python3 - <<'PY'
   import sys, pathlib; sys.path.insert(0, 'hooks')   # omp repo root, or the installed hooks dir
   from omp_content_audit import check_content_rule
   rule = {"applies_to": "src/**/*.py",
           "check": {"pattern": r"\Afrom __future__ import annotations", "expect": "present"},
           "description": "python module opens with __future__ annotations",
           "severity": "warn", "origin": "inductive"}
   files = list(pathlib.Path('.').glob(rule["applies_to"]))
   v = check_content_rule(rule, files)
   print(f"{len(v)}/{len(files)} files would fail today")
   PY
   ```

   Report `violations/total` per candidate. Near-zero confirms the induction. A majority failing means the rule is backwards or the regex is wrong — fix it or drop it, do not propose it with a caveat.

4. **Delegate the rule design to `rule-architect`.** Same read-only designer `omp-codify` uses, so the proposal arrives in the shape codify expects. Dispatch below.

5. ━━━ **GATE — code-idiom rule approval (human).** Present, per rule: the dimension, the induced pattern, the witness count, `violations/total` today, `severity`, and the prose-only leftovers. Then: proceed / revise / abort. Nothing is written before approval. ━━━

6. **Hand the write to `omp-codify`.** Pass the approved `content_conventions[]` entries plus the `CONVENTIONS.md` prose section. codify performs the managed-hash check, the `.hq/work/project/versions/` snapshot, the paired `rules.json` + `CONVENTIONS.md` write, and schema validation. Do not duplicate any of that here.

7. **Follow-up guidance.** Point at the continuation and stop: `omp-audit` for which files break the new rules; a formatter or a human for actually reshaping code (never an omp stage); `omp-learn` if a reviewer keeps correcting something this scan did not catch, so the next promotion carries evidence.

**Final step — Task dispatch (rule-architect):**
```
Task(
  subagent_type="oh-my-project:rule-architect",
  description="Design induced code-idiom rules",
  prompt="""
  Design content_conventions[] entries for CODE files from an idiom scan. You are read-only —
  propose, never write.

  INPUT
  - current .hq/config/project/rules.json (respect existing content_conventions[]; never duplicate one)
  - the four-dimension scan: per idiom, the observed pattern, the witness files, the witness count
  - per candidate regex, the measured violations/total on the current tree

  RULES
  - origin MUST be "inductive" — this came from the tree, not a preset.
  - Drop any candidate with fewer than 3 witnesses. Say which you dropped and why.
  - A rule must be a Python regex that hooks/omp_content_audit.check_content_rule can run
    (re.MULTILINE, scope body|frontmatter). If an idiom is not expressible that way, put it in the
    CONVENTIONS.md prose body instead — never approximate it as a regex.
  - Do not re-encode what an authoritative formatter (gofmt/rustfmt/black/clang-format) already
    enforces; name the formatter instead.
  - severity: error only for an idiom whose violation is a real defect (missing include guard,
    swallowed exception). Style-only idioms are warn or info.

  OUTPUT
  1. the content_conventions[] entries, schema-compliant per references/schemas/rules.schema.json
  2. the CONVENTIONS.md prose body for the non-regex-able idioms
  3. a diff summary: rules added, resulting specificity change, predicted violations per rule,
     and the candidates you dropped with their witness counts
  """
)
```
</Steps>

<Anti_Patterns>
- **Proposing the agent's own preferred idiom.** The output of this stage is a description of the tree, not an improvement to it. If a proposed rule is not visible in ≥3 existing files, it is the model's pretraining talking — which is the exact drift this stage exists to stop.
- **Adding a `code_conventions[]` field to the schema.** `content_conventions[]` is glob-scoped and format-agnostic, and audit already verifies it. A second axis buys nothing and gives `omp-audit`, `omp-learn`, and the schema three places to disagree.
- **Proposing rules without running them.** An unmeasured regex is a guess with a JSON schema around it. Step 3 exists because a backwards rule looks identical to a correct one until it is executed.
- **Writing `rules.json` here.** codify owns the paired write, the hash check, and the snapshot. Half a write is drift.
</Anti_Patterns>

<Done_When>
- Every approved idiom is either a schema-valid `content_conventions[]` entry with a measured violation count, or prose in `CONVENTIONS.md` — with nothing in between.
- `rules.json` and `CONVENTIONS.md` were written **by omp-codify**, in one pass, and the schema validates.
- Dropped candidates are reported with their witness counts, so the next run does not re-litigate them.
- No source file was modified.
</Done_When>
