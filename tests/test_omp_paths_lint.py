"""Re-entry lint: fails the build if a new root-literal string constant — for
EITHER store, the legacy one or the unified one — lands anywhere outside
hooks/omp_paths.py (the single declaration point, spec
~/oh-my-orchestrator/skills/harness/references/store-spec.md §9.5).

P3 widened this from one literal to two. Guarding only the legacy root would
have left the new root free to spread through the hooks during the very
refactor that exists to prevent exactly that — the cutover is when a root
string is most likely to be re-typed, not least.

Violation rule (ast-based, not regex-on-text): a `str` ast.Constant — including
one nested inside an f-string's JoinedStr, since ast.walk descends into those
too — counts as a violation iff it CONTAINS the root literal AND contains NO
whitespace character at all. Paths never have spaces; prose always does, so
this is what tells a literal path (`".omp/rules.json"`) apart from a sentence
that merely mentions one (`"확인 안 함. 잘못된 .omp 판단은..."`). A module,
function, async-function, or class docstring (the first statement, when it is
a plain `Expr(Constant(str))`) is explicitly exempt — that is where the prose
describing this whole convention necessarily lives.

Scope: every tracked `.py` file in the repo, minus:
  - `tests/**` (this file's own directory) — fixtures legitimately need the
    literal to build `.omp/...` paths on disk. Measured 2026-08-28, same
    violation rule as above: 70 hits across 8 files (test_secretary.py 23,
    test_omp_content_audit.py 20, test_omp_verify_emit.py 8,
    test_session_hooks.py 7, test_omp_route_emit.py 4, test_schemas.py 3,
    test_omp_doc_garden.py 3, test_plugin_integrity.py 2).
  - `references/**` — copied into user projects, so a reference file can't
    import a hooks module. Measured 2026-08-28: 0 `.py` files exist under
    references/ in this repo, so this exclusion is currently a no-op; it stays
    listed because the store-spec exclusion applies repo-wide, not just to
    today's tree.
  - `hooks/omp_paths.py` — the one file allowed to declare the literal.

omp has no `.phase0-scratch/**` (that exclusion in the spec is omo-only).
"""
import ast
from pathlib import Path

from hooks.omp_paths import HQ_ROOT, LEGACY_ROOT

ROOTS = (LEGACY_ROOT, HQ_ROOT)

REPO_ROOT = Path(__file__).parent.parent
PATHS_MODULE = REPO_ROOT / "hooks" / "omp_paths.py"
EXCLUDED_DIRS = {"tests", "references"}


def _is_violation(value: str) -> bool:
    return any(r in value for r in ROOTS) and not any(ch.isspace() for ch in value)


def _docstring_constant_ids(tree: ast.AST) -> set:
    """id() of every Constant node that is a module/function/class docstring —
    the first statement of the node, when it is a plain `Expr(Constant(str))`."""
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                ids.add(id(body[0].value))
    return ids


def violations_in_source(source: str, filename: str = "<string>") -> list:
    """[(lineno, value), ...] — every non-docstring str Constant (f-string
    pieces included, via ast.walk descending into JoinedStr) that is a
    violation per `_is_violation`."""
    tree = ast.parse(source, filename=filename)
    skip = _docstring_constant_ids(tree)
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in skip and _is_violation(node.value)):
            out.append((node.lineno, node.value))
    return out


def _scanned_files():
    for path in sorted(REPO_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel_parts = path.relative_to(REPO_ROOT).parts
        if rel_parts[0] in EXCLUDED_DIRS:
            continue
        if path == PATHS_MODULE:
            continue
        yield path


def test_scan_targets_exist():
    # a vacuous pass (0 files scanned) must not read as "0 violations, all clear"
    assert list(_scanned_files()), "no .py files found to scan — lint scope is broken"


def test_no_root_literal_reentry():
    offenders = []
    for path in _scanned_files():
        rel = path.relative_to(REPO_ROOT)
        for lineno, value in violations_in_source(path.read_text(encoding="utf-8"), str(rel)):
            offenders.append(f"{rel}:{lineno}: {value!r}")
    assert not offenders, (
        f"new {' or '.join(repr(r) for r in ROOTS)} literal(s) outside "
        "hooks/omp_paths.py — "
        "add a named helper there instead:\n" + "\n".join(offenders)
    )


# --- meta-tests: prove the detector itself actually bites -------------------

def test_meta_bare_literal_bites():
    v = violations_in_source('X = ".omp"\n')
    assert v == [(1, ".omp")]


def test_meta_path_literal_bites():
    v = violations_in_source('X = ".omp/garden-state.json"\n')
    assert len(v) == 1 and v[0][1] == ".omp/garden-state.json"


def test_meta_fstring_piece_bites():
    v = violations_in_source('name = "x"\nX = f".omp/{name}.md"\n')
    assert any(".omp/" in val for _, val in v)


def test_meta_prose_with_whitespace_is_not_a_violation():
    v = violations_in_source('X = ".omp/STRUCTURE.md 갱신은 이 작업의 일부"\n')
    assert v == []


def test_meta_module_docstring_is_exempt():
    v = violations_in_source('""".omp/rules.json is the SSOT."""\nX = 1\n')
    assert v == []


def test_meta_function_docstring_is_exempt():
    v = violations_in_source('def f():\n    """.omp/wiki holds notes."""\n    return 1\n')
    assert v == []


def test_meta_hq_literal_bites():
    v = violations_in_source('X = ".hq/config/project/rules.json"\n')
    assert len(v) == 1 and v[0][1] == ".hq/config/project/rules.json"


def test_meta_hq_prose_with_whitespace_is_not_a_violation():
    v = violations_in_source('X = "이 앵커는 .hq 루트를 가리킨다"\n')
    assert v == []


def test_meta_non_docstring_string_still_bites():
    # a bare string statement that is NOT the first statement must not be
    # mistaken for a docstring
    v = violations_in_source('def f():\n    x = 1\n    ".omp/state"\n    return x\n')
    assert v == [(3, ".omp/state")]
