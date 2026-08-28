"""P3 cutover acceptance — the four-state gate, new-path resolution, and the
legacy-only read fallback.

store-spec.md section 6 requires a fixture for all four gate rows, and it is
worth saying why each of the three "not normal" rows is here rather than folded
into one "not on the new store" case:

  off      the harness must be genuinely inert in a folder that is not an omp
           project at all — the one row where silence is correct
  legacy   the most dangerous state of the whole migration, and the one a
           three-state design would send into `off` where a stopped hook looks
           exactly like a correctly-quiet one
  corrupt  the row that reverses omp's blanket fail-open: a store that will not
           parse is not an absent store

The write-gating tests below are the other half. `_write` has three branches and
the middle one — anchored, but this artifact not copied yet — is invisible to a
test that only checks "anchored writes new, unanchored writes legacy". That
window is exactly where the pilot lives between seeding an anchor and copying
the files, so it gets its own case.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from omp_paths import (  # noqa: E402
    GATE_CORRUPT, GATE_LEGACY, GATE_NORMAL, GATE_OFF, AnchorError,
    brief_md, gate_state, garden_state_json, garden_state_json_write,
    is_inside_store, learned_md, parse_anchor_id, rules_json, secretary_dir,
    secretary_dir_write, structure_md, verify_throttle_json,
    verify_throttle_json_write, wiki_dir,
)

ROOT = Path(__file__).parent.parent
BRIEF_HOOK = ROOT / "hooks" / "omp_session_brief.py"


def _run(hook, payload, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                          capture_output=True, text=True, env=env)


def _seed_anchor(base, text="id: fixture\n"):
    (base / ".hq").mkdir(parents=True, exist_ok=True)
    (base / ".hq" / ".anchor").write_text(text, encoding="utf-8")


def _seed_legacy(base):
    (base / ".omp" / "secretary").mkdir(parents=True, exist_ok=True)
    (base / ".omp" / "rules.json").write_text("{}", encoding="utf-8")


def _seed_migrated(base):
    """A fully cut-over anchor: anchor + every layer populated."""
    _seed_anchor(base)
    cfg = base / ".hq" / "config" / "project"
    (cfg / "secretary").mkdir(parents=True, exist_ok=True)
    (cfg / "rules.json").write_text("{}", encoding="utf-8")
    (cfg / "STRUCTURE.md").write_text("# s\n", encoding="utf-8")
    (cfg / "learned.md").write_text("# l\n", encoding="utf-8")
    (base / ".hq" / "community" / "wiki").mkdir(parents=True, exist_ok=True)
    rt = base / ".hq" / "runtime" / "project"
    rt.mkdir(parents=True, exist_ok=True)
    (rt / "garden-state.json").write_text("{}", encoding="utf-8")
    (rt / "verify-throttle.json").write_text("{}", encoding="utf-8")


# --- the four gate states ---------------------------------------------------

def test_gate_off(tmp_path):
    assert gate_state(tmp_path) == GATE_OFF


def test_gate_legacy(tmp_path):
    _seed_legacy(tmp_path)
    assert gate_state(tmp_path) == GATE_LEGACY


def test_gate_normal(tmp_path):
    _seed_anchor(tmp_path)
    assert gate_state(tmp_path) == GATE_NORMAL


@pytest.mark.parametrize("bad", [
    "id: a\nid: b\n",          # two lines
    "vault\n",                 # missing the id: prefix
    "id:   \n",                # empty value
    "",                        # empty file
])
def test_gate_corrupt(tmp_path, bad):
    _seed_anchor(tmp_path, bad)
    assert gate_state(tmp_path) == GATE_CORRUPT


def test_gate_corrupt_beats_legacy(tmp_path):
    """A broken anchor next to a populated legacy store is corrupt, not legacy —
    the pair is read anchor-first, or a typo would silently look like 'not yet
    migrated' and keep writing to the old store forever."""
    _seed_legacy(tmp_path)
    _seed_anchor(tmp_path, "id: a\nid: b\n")
    assert gate_state(tmp_path) == GATE_CORRUPT


def test_parse_anchor_id_roundtrip(tmp_path):
    _seed_anchor(tmp_path, "id: vault\n")
    assert parse_anchor_id(tmp_path / ".hq" / ".anchor") == "vault"
    with pytest.raises(AnchorError):
        parse_anchor_id(tmp_path / ".hq" / "nope")


# --- the same four rows through the SessionStart hook -----------------------

def test_hook_off_is_silent(tmp_path):
    r = _run(BRIEF_HOOK, {"cwd": str(tmp_path)})
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_hook_legacy_warns_even_without_a_brief(tmp_path):
    _seed_legacy(tmp_path)
    r = _run(BRIEF_HOOK, {"cwd": str(tmp_path)})
    assert r.returncode == 0
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "[omp store]" in ctx and ".hq/.anchor" in ctx


def test_hook_legacy_warn_precedes_the_brief(tmp_path):
    _seed_legacy(tmp_path)
    (tmp_path / ".omp" / "secretary" / "BRIEF.md").write_text("BODY\n",
                                                              encoding="utf-8")
    r = _run(BRIEF_HOOK, {"cwd": str(tmp_path)})
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert ctx.index("[omp store]") < ctx.index("BODY")


def test_hook_normal_has_no_warn(tmp_path):
    _seed_migrated(tmp_path)
    (tmp_path / ".hq" / "config" / "project" / "secretary" / "BRIEF.md").write_text(
        "BODY\n", encoding="utf-8")
    r = _run(BRIEF_HOOK, {"cwd": str(tmp_path)})
    assert r.returncode == 0
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "BODY" in ctx and "[omp store]" not in ctx


def test_hook_corrupt_is_loud_and_nonzero(tmp_path):
    _seed_legacy(tmp_path)
    _seed_anchor(tmp_path, "garbage\n")
    r = _run(BRIEF_HOOK, {"cwd": str(tmp_path)})
    assert r.returncode == 2
    assert "CORRUPT" in r.stderr
    assert r.stdout.strip() == ""


# --- read resolution: new path when migrated, legacy when not ---------------

def test_every_helper_resolves_to_the_new_store_when_migrated(tmp_path):
    _seed_migrated(tmp_path)
    hq = tmp_path / ".hq"
    assert rules_json(tmp_path) == hq / "config/project/rules.json"
    assert structure_md(tmp_path) == hq / "config/project/STRUCTURE.md"
    assert learned_md(tmp_path) == hq / "config/project/learned.md"
    assert secretary_dir(tmp_path) == hq / "config/project/secretary"
    assert brief_md(tmp_path) == hq / "config/project/secretary/BRIEF.md"
    assert wiki_dir(tmp_path) == hq / "community/wiki"
    assert garden_state_json(tmp_path) == hq / "runtime/project/garden-state.json"
    assert verify_throttle_json(tmp_path) == hq / "runtime/project/verify-throttle.json"


def test_every_helper_falls_back_when_only_the_legacy_store_exists(tmp_path):
    _seed_legacy(tmp_path)
    (tmp_path / ".omp" / "wiki").mkdir()
    (tmp_path / ".omp" / "STRUCTURE.md").write_text("# s\n", encoding="utf-8")
    (tmp_path / ".omp" / "learned.md").write_text("# l\n", encoding="utf-8")
    (tmp_path / ".omp" / "garden-state.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".omp" / "state").mkdir()
    (tmp_path / ".omp" / "state" / "verify-throttle.json").write_text("{}",
                                                                      encoding="utf-8")
    legacy = tmp_path / ".omp"
    assert rules_json(tmp_path) == legacy / "rules.json"
    assert structure_md(tmp_path) == legacy / "STRUCTURE.md"
    assert learned_md(tmp_path) == legacy / "learned.md"
    assert secretary_dir(tmp_path) == legacy / "secretary"
    assert brief_md(tmp_path) == legacy / "secretary/BRIEF.md"
    assert wiki_dir(tmp_path) == legacy / "wiki"
    assert garden_state_json(tmp_path) == legacy / "garden-state.json"
    assert verify_throttle_json(tmp_path) == legacy / "state/verify-throttle.json"


def test_fallback_is_per_file_not_per_directory(tmp_path):
    """A machine that pulled the anchor commit has the tracked layers but not
    the ignored ones. rules.json must already be new while the throttle file is
    still read from the legacy store."""
    _seed_anchor(tmp_path)
    (tmp_path / ".hq" / "config" / "project").mkdir(parents=True)
    (tmp_path / ".hq" / "config" / "project" / "rules.json").write_text(
        "{}", encoding="utf-8")
    (tmp_path / ".omp" / "state").mkdir(parents=True)
    (tmp_path / ".omp" / "state" / "verify-throttle.json").write_text(
        "{}", encoding="utf-8")
    assert rules_json(tmp_path) == tmp_path / ".hq/config/project/rules.json"
    assert verify_throttle_json(tmp_path) == tmp_path / ".omp/state/verify-throttle.json"


# --- write gating: the anchor decides, and a half-migrated root stays put ----

def test_write_goes_legacy_without_an_anchor(tmp_path):
    _seed_legacy(tmp_path)
    assert secretary_dir_write(tmp_path) == tmp_path / ".omp/secretary"
    assert garden_state_json_write(tmp_path) == tmp_path / ".omp/garden-state.json"
    assert verify_throttle_json_write(tmp_path) == \
        tmp_path / ".omp/state/verify-throttle.json"


def test_write_goes_new_when_migrated(tmp_path):
    _seed_migrated(tmp_path)
    assert secretary_dir_write(tmp_path) == tmp_path / ".hq/config/project/secretary"
    assert garden_state_json_write(tmp_path) == \
        tmp_path / ".hq/runtime/project/garden-state.json"
    assert verify_throttle_json_write(tmp_path) == \
        tmp_path / ".hq/runtime/project/verify-throttle.json"


def test_write_stays_legacy_while_anchored_but_not_yet_copied(tmp_path):
    """The pilot's own window. Seeding the anchor is step 0 and copying the
    files is step 2; a write landing in the new store in between would be
    invisible to every reader, which still resolves to the populated old one."""
    _seed_legacy(tmp_path)
    (tmp_path / ".omp" / "garden-state.json").write_text("{}", encoding="utf-8")
    _seed_anchor(tmp_path)
    assert secretary_dir_write(tmp_path) == tmp_path / ".omp/secretary"
    assert garden_state_json_write(tmp_path) == tmp_path / ".omp/garden-state.json"


def test_write_goes_new_for_a_project_anchored_from_scratch(tmp_path):
    """Neither path holds the artifact and there is no legacy store to orphan —
    this is the only case where the new path wins by default."""
    _seed_anchor(tmp_path)
    assert secretary_dir_write(tmp_path) == tmp_path / ".hq/config/project/secretary"


# --- is_inside_store now covers both roots ----------------------------------

@pytest.mark.parametrize("p", [
    "/x/.omp/rules.json", "/x/.omp", "/x/.hq/config/project/rules.json", "/x/.hq",
])
def test_is_inside_store_true(p):
    assert is_inside_store(p)


@pytest.mark.parametrize("p", ["/x/omp/rules.json", "/x/hq", "/x/docs/.hqx/a"])
def test_is_inside_store_false(p):
    assert not is_inside_store(p)
