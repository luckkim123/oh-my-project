# content_conventions + link-integrity audit — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `content_conventions[]` rule type and a wikilink-integrity audit axis to omp, so the harness can express and check note-body authoring rules (release 0.2.0).

**Architecture:** A new optional top-level key in `rules.schema.json` (backward-compatible). Two new pure-Python check functions in `hooks/omp_content_audit.py` (content + link), tested via pytest `tmp_path` fixtures. The `auditor` agent + `omp-audit`/`omp-codify`/`omp-learn` skills + `learning-protocol`/`output-layout` references are updated in parallel patterns. `CONVENTIONS.md` joins STRUCTURE/NAMING as a paired SSOT doc.

**Tech Stack:** Python 3 stdlib (`re`, `json`, `pathlib`), pytest 8.4 (0-config, rootdir-import), optional `jsonschema` (importorskip), Markdown agent/reference cards.

**Design source:** `docs/plans/2026-05-31-content-conventions-design.md`
**Branch:** `feat/content-conventions` (created; design committed). **Final task merges to `main` and deletes the branch — user dislikes lingering branches.**

**Test command (always run from repo root):** `python3 -m pytest -q`
Baseline before starting: **34 passed, 1 skipped**.

---

## Task 1: Schema — register `content_conventions[]`

**Files:**
- Modify: `references/schemas/rules.schema.json` (add key under `properties`, after `naming` block ~line 116, before `ignore` line 117)
- Test: `tests/test_schemas.py`

**Step 1: Write the failing test**

In `tests/test_schemas.py`, after `test_rules_schema_has_specificity` (line 28-33), add:

```python
def test_rules_schema_has_content_conventions():
    """content_conventions[]: note-body authoring rules (present/absent × body/frontmatter)."""
    s = load(RULES_SCHEMA)
    cc = s["properties"]["content_conventions"]
    assert cc["type"] == "array"
    item = cc["items"]
    assert set(item["required"]) == {"applies_to", "check", "description"}
    chk = item["properties"]["check"]
    assert set(chk["required"]) == {"pattern", "expect"}
    assert chk["properties"]["expect"]["enum"] == ["present", "absent"]
    assert chk["properties"]["scope"]["enum"] == ["body", "frontmatter"]
    assert chk["properties"]["scope"]["default"] == "body"
    # origin/severity mirror naming.patterns[]
    assert item["properties"]["origin"]["enum"] == ["preset", "inductive", "learned"]
    assert item["properties"]["severity"]["enum"] == ["error", "warn", "info"]
    # optional: NOT in required top-level (backward-compatible)
    assert "content_conventions" not in s["required"]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_schemas.py::test_rules_schema_has_content_conventions -v`
Expected: FAIL with `KeyError: 'content_conventions'`

**Step 3: Write minimal implementation**

In `references/schemas/rules.schema.json`, insert this key into `properties` after the `naming` object's closing brace (before `"ignore"`). Use the exact JSON from design §2:

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
          "expect": { "type": "string", "enum": ["present", "absent"], "description": "'present' = pattern MUST match; 'absent' = pattern must NOT match." },
          "scope": { "type": "string", "enum": ["body", "frontmatter"], "default": "body", "description": "Where to test: full body, or only YAML frontmatter (between leading '---' fences)." }
        }
      },
      "description": { "type": "string" },
      "origin": { "type": "string", "enum": ["preset", "inductive", "learned"], "default": "preset", "description": "Provenance for specificity (learning-protocol.md §4): 'preset' weight 0, 'inductive'/'learned' weight 1." },
      "severity": { "type": "string", "enum": ["error", "warn", "info"], "default": "warn" }
    }
  }
},
```

(Do NOT add it to `required` — keep it optional so existing rules.json stay valid.)

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_schemas.py -q`
Expected: all pass (now 35 passed, 1 skipped — the +1 is this new test).

**Step 5: Commit**

```bash
git add references/schemas/rules.schema.json tests/test_schemas.py
git commit -m "feat(schema): add content_conventions[] rule type"
```

---

## Task 2: Schema instance validation (jsonschema round-trip)

**Files:**
- Modify: `tests/test_schemas.py` (REPRESENTATIVE_RULES line 46-61; test_representative_instances line 76-80)

**Step 1: Add a representative content_conventions instance**

In `REPRESENTATIVE_RULES` (line 46-61), add before the `"ignore"` key:

```python
    "content_conventions": [
        {
            "applies_to": "papers/**/*.md",
            "check": {"pattern": "^## Main Ideas$", "expect": "present"},
            "description": "review notes need a Main Ideas section",
            "origin": "inductive",
            "severity": "warn",
        },
        {
            "applies_to": "concepts/**/*.md",
            "check": {"pattern": r"^\d+\.", "expect": "absent"},
            "description": "no numbered lists in concept notes",
            "origin": "inductive",
            "severity": "info",
        },
    ],
```

**Step 2: Add a negative test (enum violation rejected)**

After `test_representative_instances_match_schema` (line 76-80), add:

```python
def test_content_conventions_rejects_bad_enum():
    """An invalid expect value must fail jsonschema validation."""
    jsonschema = pytest.importorskip("jsonschema")
    bad = json.loads(json.dumps(REPRESENTATIVE_RULES))
    bad["content_conventions"][0]["check"]["expect"] = "maybe"  # not present/absent
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, load(RULES_SCHEMA))
```

**Step 3: Run**

Run: `python3 -m pytest tests/test_schemas.py -q`
Expected: pass. (If `jsonschema` is not installed, the two importorskip tests skip — that is acceptable, matching the existing 1 skip. To actually exercise: `pip install jsonschema` then re-run; the round-trip + negative must pass.)

**Step 4: Commit**

```bash
git add tests/test_schemas.py
git commit -m "test(schema): content_conventions instance + negative validation"
```

---

## Task 3: Content-check pure function

**Files:**
- Create: `hooks/omp_content_audit.py`
- Test: `tests/test_omp_content_audit.py` (new — clone header style from `tests/test_omp_atomic.py`)

**Why a pure function:** recon found omp has NO importable audit logic today — the `auditor` agent only *describes* checks in prose. To test deterministically (design §6 "pure functions → tests first"), the content/link logic must live as importable functions. `auditor` will reference these as the canonical algorithm.

**Step 1: Write the failing test**

Create `tests/test_omp_content_audit.py`:

```python
"""Tests for omp content_conventions + wikilink audit pure functions."""
from hooks.omp_content_audit import check_content_rule, split_frontmatter


def test_present_rule_passes_when_section_exists(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("# Title\n\n## Main Ideas\n\nstuff\n")
    rule = {"applies_to": "*.md", "check": {"pattern": "^## Main Ideas$", "expect": "present"}, "severity": "warn"}
    violations = check_content_rule(rule, [f])
    assert violations == []


def test_present_rule_flags_when_section_missing(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("# Title\n\nno sections here\n")
    rule = {"applies_to": "*.md", "check": {"pattern": "^## Main Ideas$", "expect": "present"}, "severity": "warn"}
    violations = check_content_rule(rule, [f])
    assert len(violations) == 1
    assert violations[0]["file"].endswith("note.md")
    assert violations[0]["severity"] == "warn"


def test_absent_rule_flags_when_forbidden_pattern_present(tmp_path):
    f = tmp_path / "c.md"
    f.write_text("1. first\n2. second\n")
    rule = {"applies_to": "*.md", "check": {"pattern": r"^\d+\.", "expect": "absent"}, "severity": "info"}
    violations = check_content_rule(rule, [f])
    assert len(violations) == 1


def test_frontmatter_scope_only_checks_yaml(tmp_path):
    f = tmp_path / "t.md"
    f.write_text("---\ntags: [MachineLearning]\n---\n\nbody has lowercase word\n")
    # rule: tags must be CamelCase — checked only in frontmatter; body lowercase must not trip it
    rule = {"applies_to": "*.md",
            "check": {"pattern": r"tags:.*[a-z]", "expect": "absent", "scope": "frontmatter"},
            "severity": "warn"}
    violations = check_content_rule(rule, [f])
    assert violations == []  # 'MachineLearning' has no lowercase-after-colon-space tag-name violation... see note


def test_split_frontmatter_extracts_yaml_block():
    body = "---\ntitle: x\ntags: [A]\n---\n\ncontent\n"
    fm, rest = split_frontmatter(body)
    assert "title: x" in fm
    assert "content" in rest
    assert "title" not in rest
```

> Note for implementer: the frontmatter regex in the 4th test is illustrative — when writing the *real* vault tag rule in T2, refine the pattern. Here we only assert the *scope mechanism* (frontmatter text is isolated from body).

**Step 2: Run to verify it fails**

Run: `python3 -m pytest tests/test_omp_content_audit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'hooks.omp_content_audit'`

**Step 3: Write minimal implementation**

Create `hooks/omp_content_audit.py`:

```python
"""Deterministic content_conventions + wikilink checks for omp-audit.

Pure stdlib (re, pathlib). No file mutation. Returns violation dicts.
The `auditor` agent invokes these as the canonical check algorithm.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable

_FM = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_text, body_text). Empty frontmatter if no leading --- fence."""
    m = _FM.match(text)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def check_content_rule(rule: dict, files: Iterable[Path]) -> list[dict]:
    """Apply one content_conventions rule to files. Returns a list of violation dicts."""
    chk = rule["check"]
    pattern = re.compile(chk["pattern"], re.MULTILINE)
    expect = chk["expect"]                      # 'present' | 'absent'
    scope = chk.get("scope", "body")
    severity = rule.get("severity", "warn")
    violations = []
    for f in files:
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        target = split_frontmatter(text)[0] if scope == "frontmatter" else text
        matched = bool(pattern.search(target))
        bad = (expect == "present" and not matched) or (expect == "absent" and matched)
        if bad:
            violations.append({"file": str(f), "severity": severity,
                               "rule": rule.get("description", ""), "expect": expect})
    return violations
```

**Step 4: Run to verify it passes**

Run: `python3 -m pytest tests/test_omp_content_audit.py -q`
Expected: pass (5 tests). Then full suite `python3 -m pytest -q` still green.

**Step 5: Commit**

```bash
git add hooks/omp_content_audit.py tests/test_omp_content_audit.py
git commit -m "feat(audit): content_conventions check pure function"
```

---

## Task 4: Wikilink-integrity pure function

**Files:**
- Modify: `hooks/omp_content_audit.py` (add `find_dead_links`)
- Modify: `tests/test_omp_content_audit.py`

**Step 1: Write the failing test**

Append to `tests/test_omp_content_audit.py`:

```python
from hooks.omp_content_audit import find_dead_links


def test_dead_link_detected(tmp_path):
    (tmp_path / "a.md").write_text("see [[b]] and [[missing]]\n")
    (tmp_path / "b.md").write_text("target\n")
    dead = find_dead_links(tmp_path)
    targets = {d["target"] for d in dead}
    assert "missing" in targets
    assert "b" not in targets


def test_link_alias_and_heading_resolve(tmp_path):
    (tmp_path / "a.md").write_text("[[b|alias]] and [[b#section]] and ![[b]]\n")
    (tmp_path / "b.md").write_text("x\n")
    dead = find_dead_links(tmp_path)
    assert dead == []
```

**Step 2: Run to verify it fails**

Run: `python3 -m pytest tests/test_omp_content_audit.py::test_dead_link_detected -v`
Expected: FAIL `ImportError: cannot import name 'find_dead_links'`

**Step 3: Implement**

Add to `hooks/omp_content_audit.py`:

```python
_WIKILINK = re.compile(r"!?\[\[([^\]\|#]+)(?:#[^\]\|]+)?(?:\|[^\]]+)?\]\]")


def find_dead_links(root: Path) -> list[dict]:
    """Scan all .md under root for [[target]] links whose target resolves to no file.

    Obsidian resolution: match by basename (extension optional) anywhere in the vault.
    alias (|...) and heading (#...) are stripped before resolving. Returns info-level hints.
    """
    root = Path(root)
    md_files = list(root.rglob("*.md"))
    stems = {f.stem for f in md_files} | {f.name for f in md_files}
    dead = []
    for f in md_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in _WIKILINK.finditer(text):
            target = m.group(1).strip()
            base = target.rsplit("/", 1)[-1]  # path-style link → last segment
            if base not in stems and f"{base}.md" not in stems and base.removesuffix(".md") not in stems:
                dead.append({"file": str(f), "target": target, "severity": "info"})
    return dead
```

**Step 4: Run to verify it passes**

Run: `python3 -m pytest tests/test_omp_content_audit.py -q`
Expected: pass (7 tests). Full suite green.

**Step 5: Commit**

```bash
git add hooks/omp_content_audit.py tests/test_omp_content_audit.py
git commit -m "feat(audit): wikilink-integrity check (absorbs link-checker)"
```

---

## Task 5: auditor agent — content + link axes

**Files:**
- Modify: `agents/auditor.md` (4 parallel spots: Role axis list, Investigation_Protocol, result table, Final_Checklist)
- Modify: `skills/omp-audit/SKILL.md` (dispatch bullet list, Output table line)

**No test** (these are agent-prompt Markdown). Verify by reading.

**Step 1: Role axis list** — `auditor.md` after the 명명 위반 bullet (~L16), before dataset drift (~L17), add two bullets matching the existing `- **축**: ... — ...` format:

```markdown
- **콘텐츠 컨벤션 위반**: `rules.json.content_conventions[]`의 `applies_to` glob에 걸리는 파일을 열어 `check.pattern`(Python re)을 `check.expect`(present/absent)로 대조 — `hooks/omp_content_audit.check_content_rule`가 정본 알고리즘. severity별 집계
- **wikilink 무결성**: vault 전체 `[[target]]`이 실재 .md로 해소되는지 — `hooks/omp_content_audit.find_dead_links`. dead link는 health hint(severity info), 위반 아님
```

**Step 2: Investigation_Protocol** — after step 4 (명명 위반 검사, ~L60), insert two steps; renumber subsequent (dataset→6, ... snapshot/종합 +2):

```markdown
5) **콘텐츠 컨벤션 검사**: 각 `content_conventions[]`에 대해 `applies_to` glob으로 파일을 모으고, `check.scope`(body/frontmatter)에서 `check.pattern`을 `expect`로 대조 (알고리즘: `hooks/omp_content_audit.check_content_rule`). expect=present인데 미매치 / expect=absent인데 매치 = 위반. error 1건 이상이면 콘텐츠 항목 FAIL.
6) **wikilink 무결성 검사**: vault .md의 `[[link]]`를 추출해 실재 파일로 해소 (`hooks/omp_content_audit.find_dead_links`). dead link는 info hint로만 기록 (FAIL 아님).
```

**Step 3: Result table** — `auditor.md` after 명명 위반 row (~L107), before dataset row, add:

```markdown
| 콘텐츠 컨벤션 (content_conventions) | PASS/FAIL | error N / warn N / info N |
| wikilink 무결성 (dead link) | PASS | dead N건 (health hint) |
```

**Step 4: Final_Checklist** — add content/link lines mirroring existing axis checklist entries.

**Step 5: omp-audit/SKILL.md dispatch** (~L79-86) — add two bullets so the controller tells auditor to run these axes:

```markdown
- 콘텐츠 컨벤션 (rules.json.content_conventions[] — applies_to glob × check.pattern/expect/scope, hooks/omp_content_audit)
- wikilink 무결성 (vault [[link]] 해소, dead link = info hint)
```

And the `<Output>` result-table line (~L97): append `· 콘텐츠 · 링크` to the slash-separated axis list.

**Step 6: Verify & commit**

Read both files to confirm the axis appears in all parallel spots and numbering is consistent.

```bash
git add agents/auditor.md skills/omp-audit/SKILL.md
git commit -m "feat(auditor): content_conventions + wikilink audit axes"
```

---

## Task 6: codify / learn / rule-architect — handle the new type

**Files:**
- Modify: `skills/omp-codify/SKILL.md` (rule-type enumeration + CONVENTIONS.md pairing)
- Modify: `skills/omp-learn/SKILL.md` (candidate_rule.target enum)
- Modify: `agents/rule-architect.md` (may propose content_conventions)

**No test** (Markdown). Verify by reading.

**Step 1:** `omp-learn/SKILL.md` — find the `candidate_rule.target` enum (`structure.directories | naming.patterns | ignore`) and add `| content_conventions`.

**Step 2:** `omp-codify/SKILL.md` — wherever it enumerates the rule containers it codifies (structure/naming/ignore), add `content_conventions`. Add CONVENTIONS.md to the paired-.md regeneration step (alongside STRUCTURE.md/NAMING.md), per anti-pattern C (.md↔.json same pass).

**Step 3:** `rule-architect.md` — wherever it lists rule-entry targets it may propose, add `content_conventions[]` with the schema shape (applies_to / check / severity).

**Step 4: Commit**

```bash
git add skills/omp-codify/SKILL.md skills/omp-learn/SKILL.md agents/rule-architect.md
git commit -m "feat(codify,learn): content_conventions in promotion + codify path"
```

---

## Task 7: learning-protocol + output-layout — specificity & SSOT doc

**Files:**
- Modify: `references/learning-protocol.md` (§4 specificity rule-entry enumeration; §1-3 target enum)
- Modify: `references/output-layout.md` (register `.omp/CONVENTIONS.md` + pairing rule)

**Step 1:** `learning-protocol.md §4` — the rule-entry enumeration (`structure.directories[]`, `naming.patterns[]`, `ignore[]` glob) that the specificity formula counts: add `content_conventions[]`. Confirm the formula text still reads "fraction of project-owned rules" (content rules with origin inductive/learned now count).

**Step 2:** `learning-protocol.md §1-3` — the `candidate_rule.target` line: add `content_conventions`.

**Step 3:** `output-layout.md` — in the `.omp/` file list (PROJECT/STRUCTURE/NAMING/DATASETS.md, rules.json, ...), add `CONVENTIONS.md` with role "human-readable content_conventions, paired with rules.json.content_conventions[]". State the .md↔.json pairing.

**Step 4: Commit**

```bash
git add references/learning-protocol.md references/output-layout.md
git commit -m "docs(protocol): content_conventions in specificity + CONVENTIONS.md SSOT"
```

---

## Task 8: CHANGELOG + version bump → release 0.2.0

**Files:**
- Modify: `CHANGELOG.md` (new `## [0.2.0]` section; fold the existing `[Unreleased]` wiki-append entry in or keep it — check current state)

**Step 1:** Move the `[Unreleased]` content into a new `## [0.2.0] — 2026-05-31` section and add:

```markdown
## [0.2.0] — 2026-05-31

### Added
- **`content_conventions[]` rule type** (`rules.schema.json`) — note-body authoring rules:
  `check.pattern` (Python re) × `expect` (present/absent) × `scope` (body/frontmatter).
  Optional top-level key → all existing rules.json stay valid (backward-compatible MINOR).
- **content + wikilink audit axes** — `hooks/omp_content_audit.py` (`check_content_rule`,
  `find_dead_links`, `split_frontmatter`), pure stdlib, the canonical algorithm the
  `auditor` agent now invokes. content axis is enforced (error/warn/info); wikilink
  integrity is a health hint (info). Absorbs the downstream `link-checker` validator.
- **`.omp/CONVENTIONS.md`** — human-readable SSOT paired with `content_conventions[]`,
  alongside STRUCTURE.md/NAMING.md.

### Changed
- `specificity` now counts `content_conventions[]` entries (learning-protocol §4).
- `learned.md` `candidate_rule.target` enum gains `content_conventions` — content rules
  travel the heavy channel through the human gate, never the light wiki channel.
- `omp-codify`/`omp-learn`/`rule-architect` handle the new type.

### Verification
- `python3 -m pytest -q` — N passed (schema + content/link pure-function tests).
- Backward-compat: existing rules.json validate unchanged (content_conventions optional).
```

**Step 2:** Bump version references: any `omp_version` default and the schema `$id`/version note that says 0.1.0 → 0.2.0 (grep `0\.1\.0` across the repo; update the harness-version mentions, NOT historical changelog entries).

**Step 3: Run full suite + commit**

Run: `python3 -m pytest -q` — expected all green.

```bash
git add CHANGELOG.md
git commit -m "release: omp 0.2.0 — content_conventions + wikilink audit"
```

---

## Task 9: Verification gate + merge to main + branch cleanup

**Step 1: Full verification**
- Run: `python3 -m pytest -q` — all pass (no skips beyond the pre-existing jsonschema-optional ones, or install jsonschema to exercise them).
- Run: `grep -rni "ksm_Obsidian\|CamelCase\|Main Ideas" --include=*.json --include=*.py hooks/ references/ skills/ agents/` — **must be empty** (no vault value leaked into the plugin body; the `Main Ideas` strings in *tests* and *design/plan docs* are fixtures/examples and are acceptable — scope the grep to hooks/references/skills/agents).
- Read the design's §1 success criteria 1 — confirm schema/audit/codify/learn/tests all consistently reference content_conventions.

**Step 2: Merge to main and delete the branch** (user requires no lingering branches)

```bash
git checkout main
git merge --squash feat/content-conventions
git commit -m "feat: omp 0.2.0 — content_conventions rule type + wikilink audit axis

content_conventions[] (present/absent × body/frontmatter) + content/link
audit pure functions + CONVENTIONS.md SSOT + specificity/codify/learn
integration. Backward-compatible MINOR. Absorbs downstream link-checker.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git branch -D feat/content-conventions
```

**Step 3:** Confirm `git branch` shows only `main`, and `git log --oneline -3` shows the squashed 0.2.0 commit. (Push only if the user asks.)

---

## After T1: hand off to T2

T1 (this plan) ships omp 0.2.0 mechanism. **T2 (vault `.omp/` migration + skill deletion)** is a separate effort, gated on T1 being merged. Do NOT start T2 until T1's verification gate passes. T2 will: codify the 3 content rules + kanban rules into this vault's `.omp/content_conventions[]`, generate `.omp/CONVENTIONS.md`, run `omp-audit` to confirm the rules flag real violations, then `trash` the absorbed skills/agents + replace `claude-settings`→`claudebase` on surviving files. (See design §5.)
```
