# Design — omp `content_conventions` rule type + link-integrity audit axis

**Date**: 2026-05-31
**Target version**: omp 0.2.0 (MINOR, backward-compatible)
**Status**: design approved (brainstorming, 6/6 sections)

---

## 1. Problem & Goal

omp's `rules.json` schema (`structure` / `naming` / `ignore`, `additionalProperties:false`)
expresses only *filesystem placement* rules — "which directory / what basename / where a
file type lives". It cannot express **note-body authoring conventions**: "review notes must
contain a `## Main Ideas` section", "concept notes must not use numbered lists", "tags must
be CamelCase". These live, today, in a downstream Obsidian vault (`~/ksm_Obsidian`) as
`.claude/skills/rules-*` skills that auto-invoke at *authoring* time.

Evidence the gap is structural, not incidental:
- `rules.schema.json:7-8` — `required` + `additionalProperties:false` lock the top-level
  rule containers to `structure`/`naming`/`ignore` (plus `learned_refs` provenance).
- `naming.patterns[].regex` matches **basename only** (`rules.schema.json:87-89`);
  `path_constraint` matches **location only** (`:91-98`). Neither sees file *contents*.
- `auditor.md:14-21,56-67` — every audit axis is tree-walk / glob / hash. No axis opens a
  file to inspect its internal structure.
- `learning-protocol.md:137` — even the learning channel limits `candidate_rule.target` to
  `structure.directories | naming.patterns | ignore`. Content rules cannot be promoted.
- `omp-learn/SKILL.md:58-61` — the design *already* acknowledges schema-unrepresentable
  rules ("schema is law; express the rest as a schema-change request, don't bend JSON").

**Goal**: extend the omp harness with a *content* dimension so these rules become
plugin-owned, then migrate the vault skills into `.omp/` data and delete them.

### Two-layer separation (load-bearing principle)

- **Layer 1 — mechanism** (`~/oh-my-project`, ships to everyone): a new
  `content_conventions[]` rule type + a link-integrity audit axis + validator
  generalization. **No vault-specific value enters the plugin** — only the empty capability.
- **Layer 2 — data** (`~/ksm_Obsidian/.omp/`, this vault only): fill that capability with
  this vault's values (CamelCase tags, ad-block forms, Main Ideas headers) and clean up the
  13 `.claude/` items.

This mirrors `learning-protocol.md`'s identity statement: "specialization is **data, not
code**." A vault quirk ("tags are CamelCase") placed in the plugin body would pollute every
other project that uses omp.

### Success criteria

1. omp 0.2.0 handles `content_conventions` + link axis consistently across
   schema / audit / codify / learn / tests (existing + new tests pass).
2. `grep -ri "ksm_Obsidian\|CamelCase\|Main Ideas" ` over the omp plugin body returns **0**
   (no vault value leaked into the distributed harness).
3. This vault's `.omp/` absorbs the items and `omp-audit` flags real violations using them.
4. Only absorbed skills/agents are deleted; omp-unrelated items (robot 3, calendar-style)
   remain.

### Non-goals (YAGNI)

oms changes; markdown full-parse; semantic ordering checks; auto-fix of content violations
(audit detects only).

---

## 2. Schema — `content_conventions[]`

Register a new **optional** top-level key in `rules.schema.json.properties` (optional like
`ignore`/`learned_refs` → not added to `required` → **every existing rules.json stays valid =
backward-compatible**).

```jsonc
"content_conventions": {
  "type": "array",
  "description": "File-content rules: what must (or must not) appear INSIDE matching files. Checked by omp-audit via deterministic grep/regex over file contents. Distinct from naming (basename/location) — this inspects the body.",
  "items": {
    "type": "object",
    "required": ["applies_to", "check", "description"],
    "additionalProperties": false,
    "properties": {
      "applies_to": { "type": "string", "description": "Glob of files this rule inspects, e.g. '2_Resource/papers/**/Main Ideas.md'." },
      "check": {
        "type": "object",
        "required": ["pattern", "expect"],
        "additionalProperties": false,
        "properties": {
          "pattern": { "type": "string", "description": "Python regex tested against file content (re.MULTILINE)." },
          "expect": { "type": "string", "enum": ["present", "absent"], "description": "'present' = pattern MUST match (section required); 'absent' = pattern must NOT match (forbidden form)." },
          "scope": { "type": "string", "enum": ["body", "frontmatter"], "default": "body", "description": "Where to test: full body, or only YAML frontmatter (between leading '---' fences). 'frontmatter' lets tag-rules match the 'tags:' value." }
        }
      },
      "description": { "type": "string" },
      "origin": { "type": "string", "enum": ["preset", "inductive", "learned"], "default": "preset" },
      "severity": { "type": "string", "enum": ["error", "warn", "info"], "default": "warn" }
    }
  }
}
```

**Rationale**:
- `check.pattern` + `expect: present|absent` expresses all three vault rule classes:
  section-required (present), form-forbidden (absent), tag-shape (frontmatter scope + present).
- `scope: frontmatter` gives what `naming` never could: matching frontmatter values.
- `origin` / `severity` mirror `naming.patterns[]` → fold into specificity + severity
  aggregation unchanged.

Example (a *vault value* — Layer-2 data, never in the schema/plugin):
```jsonc
{ "applies_to": "2_Resource/papers/**/*.md",
  "check": { "pattern": "^## Main Ideas$", "expect": "present" },
  "description": "review notes must have a ## Main Ideas section", "origin": "inductive", "severity": "warn" }
```

---

## 3. Audit axes — content + link integrity

Add **two** new axes to `omp-audit` and the `auditor` agent. Both open file contents (unlike
existing axes) but stay **deterministic stdlib** (Python `re` + file read) — omp's
determinism principle holds.

**Axis A — content_conventions check**
```
For each content_conventions[] rule:
  1. collect target files via applies_to glob (same as naming)
  2. extract scope: body (whole) or frontmatter (between leading --- fences)
  3. re.search(pattern, text, re.MULTILINE)
  4. expect=present & no match → violation;  expect=absent & match → violation
  5. aggregate by severity (one error = axis FAIL)
```

**Axis B — wikilink integrity (absorbs `link-checker`)**
```
1. extract [[target]] / [[target|alias]] / [[target#heading]] / ![[embed]] from all .md
2. resolve each target to an existing .md (or attachment) per Obsidian rules
   (path-suffix / filename match, extension optional)
3. unresolved = dead link → report (severity: info — health hint)
```

**Anti-pattern guards**:
- `learning-protocol.md §6.A` "recall is grep-only" binds **recall**, not audit *checking*.
  `naming` already compiles Python `re`; content checking reuses that, so it is consistent
  (confirmed in recon `ompExt`).
- audit **detects only** — no auto-fix (existing omp principle).
- link axis is **not** an enforced rule — `info` health hint, matching `para.md:216` which
  already designates "wikilink integrity = health hint, light channel". `omp-organize`
  never moves files over a dead link.

**Files**: `agents/auditor.md` (two axes in Investigation_Protocol),
`skills/omp-audit/SKILL.md` (dispatch prompt + two result-table rows: `Content`, `Links`).

---

## 4. codify / learn / specificity integration

The new type must fold into omp's evolution machinery or it becomes a half-rule.

**specificity** (`learning-protocol.md §4`): formula
`specificity = |rules with origin∈{inductive,learned}| / |all rules|`. Add
`content_conventions[]` items to numerator+denominator (each carries `origin`). Update the
§4 rule-entry enumeration to list `content_conventions`. Monotonic invariant preserved.

**heavy channel** (`§1-3`): content_conventions are **enforced** (audit flags) → mandatory
heavy path: `learned.md` observation → `omp-learn` → `rule-architect` → **human gate** →
`rules.json`. Light wiki channel forbidden (anti-pattern D). Add `content_conventions[]` to
the `learned.md` `candidate_rule.target` enum (3 → 4 targets). Promotion criteria §3 apply
verbatim; "evidence" becomes *note instances* satisfying/violating the pattern.

**codify** (`omp-codify`): `rule-architect` may propose content_conventions, must satisfy the
schema. **.md ↔ .json pairing** (anti-pattern C): a new human doc **`CONVENTIONS.md`** is
generated/regenerated in the same pass (STRUCTURE.md=structure, NAMING.md=naming,
**CONVENTIONS.md=content**).

**output-layout** (`output-layout.md`): register `.omp/CONVENTIONS.md` as an SSOT doc; state
the `content_conventions[]` ↔ `CONVENTIONS.md` pairing.

**Files**: `references/learning-protocol.md`, `skills/omp-codify/SKILL.md`,
`skills/omp-learn/SKILL.md`, `references/output-layout.md`, `agents/rule-architect.md`.

---

## 5. Vault migration map (Layer 2)

After T1 completes, process the vault's 13 `.claude/` items in four lanes.

**Lane 1 — migrate to content_conventions, then delete** (3 authoring rules)

| skill | value → `.omp/` | delete |
|:---|:---|:---|
| `rules-note-style` | concept ad-block / math / forbidden-tokens → content_conventions[] + CONVENTIONS.md | ✅ |
| `rules-paper-format` | review-note headers (Main Ideas etc.) → content_conventions[] | ✅ |
| `rules-tag-system` | tag CamelCase / forbidden patterns → content_conventions[] (scope:frontmatter) | ✅ |

**Lane 2 — absorb into audit axis, then delete** (3 validator agents)

| agent | absorbed by | delete |
|:---|:---|:---|
| `link-checker` | audit link-integrity axis (§3-B) | ✅ |
| `paper-checker` | rules-paper-format → content_conventions ⇒ audit verifies automatically | ✅ |
| `kanban-validator` | Kanban content rules (past-date / priority tag) → content_conventions ⇒ audit verifies | ✅ |

**Lane 3 — omp-unrelated, remain** (not deleted)

- `robot-jetson-build`, `robot-pkrc-deploy`, `rules-robot-code` (SSH robot ops)
- `rules-calendar` — structure already absorbed; "authoring style" (past-date ban, dup
  check) left by omp as a *complement*. With kanban rules going to content_conventions,
  trim only the overlap; do not fully delete (separate judgment).

**Lane 4 — delete now**

- `content-restructuring` (empty folder, 0 files)
- `rules-portable-config` (user decision B): SSOT is the **claudebase** README; its trigger
  ("new machine restore") fires *before* the vault is even cloned; currently stale. Not an
  omp-content rule — pure cleanup. Delete.

**Adjacent finding folded in (user decision B)**: 5 vault files still reference the old repo
name `claude-settings` (renamed to **claudebase**): `rules-portable-config/SKILL.md` (7×,
incl. clone URL), `.claude/README.md`, `rules-robot-code/SKILL.md`, `rules-archive/`
×2. During T2, on the *surviving* files, replace `claude-settings` → `claudebase` and update
the repo URL. (rules-portable-config itself is deleted, so its copies vanish with it.)

**Deletion safety** (user-scope rule + omp safe-fileops):
1. Delete **only after** T1 ships and each skill's value is verifiably written into `.omp/`.
2. Delete = `trash` (recycle bin), never permanent erase. In a git repo the commit is itself
   a recovery path.
3. The two agents' **stale reference paths** (`kanban-validator`→`vault-calendar`,
   `paper-checker`→`vault-paper-rules`) resolve by deletion.
4. Run `omp-audit` once before deleting → confirm absorbed rules actually flag violations
   (guard against deleting into an empty shell).

---

## 6. Release / test / execution order

**Version**: omp `0.1.0` → **`0.2.0`** (MINOR). `content_conventions` is an optional key →
existing rules.json all valid = backward-compatible. Bump `omp_version` to 0.2.0.

**T1 files** (`~/oh-my-project`):

| file | change |
|:---|:---|
| `references/schemas/rules.schema.json` | register `content_conventions[]` (§2) |
| `agents/auditor.md` | content + link Investigation_Protocol axes (§3) |
| `agents/rule-architect.md` | may propose content_conventions |
| `skills/omp-audit/SKILL.md` | dispatch + 2 result-table rows |
| `skills/omp-codify/SKILL.md` | content codify + CONVENTIONS.md pairing |
| `skills/omp-learn/SKILL.md` | candidate_rule.target enum += content_conventions |
| `references/learning-protocol.md` | §4 specificity formula, §1-3 target enum |
| `references/output-layout.md` | register `.omp/CONVENTIONS.md` SSOT |
| `tests/test_schemas.py` | content_conventions schema + content/link audit logic |
| `CHANGELOG.md` | 0.2.0 (Added/Changed/Verification) |

**TDD**: content-check logic (present/absent × body/frontmatter) and link-resolution are
pure functions → tests first; fixtures that satisfy/violate each vault rule class.

**Execution order (dependency)**:
```
T1 (omp 0.2.0)  —  superpowers:writing-plans → subagent-driven-development
  schema → tests → audit/codify/learn → docs → CHANGELOG → release
       ↓ (only after T1 ships & tests pass)
T2 (vault .omp migration)
  ├ codify: 3 content rules + kanban rules → content_conventions[], generate CONVENTIONS.md
  ├ audit once: confirm absorbed rules flag real violations (anti empty-shell)
  ├ trash: note-style·paper-format·tag-system·portable-config·content-restructuring + 3 agents
  ├ claude-settings→claudebase on surviving files (robot-code, README, rules-archive) + URL
  └ vault git commit·push ([프로젝트] prefix)
```

**Design doc location**: this file lives in the **omp repo** (the change owner), not the
vault.

**Verification gate**: ① all omp tests pass ② `grep -ri "ksm_Obsidian|vault value"` over omp
body = 0 ③ vault audit flags violations via absorbed rules ④ deleted skills are in trash
(recoverable).
