"""Tests for the version SSOT sync checker, ported from oh-my-scholar's
tag-drift test (same semantics: latest reachable v-tag may be at most ONE
version behind the declared plugin version — release-in-progress OK; TWO+
behind is drift; no tags at all skips the tag surface, not a failure).
`check()` is pure logic, testable without a repo; `test_live_repo_surfaces_agree`
is the live lock that forces every release commit to bump plugin.json +
CHANGELOG.md together — this only runs meaningfully in CI when tags are
actually fetched (see .github/workflows/tag-guard.yml)."""
import importlib.util
import re
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "sync_version.py"
spec = importlib.util.spec_from_file_location("sync_version", SCRIPT)
sv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sv)

ROOT = Path(__file__).parent.parent


def test_in_sync_passes():
    assert sv.check("0.8.0", "0.8.0", "0.7.0", "v0.7.0", "0.8.0") == []  # pre-tag window
    assert sv.check("0.8.0", "0.8.0", "0.7.0", "v0.8.0", "0.8.0") == []  # post-tag


def test_plugin_changelog_drift_detected():
    drift = sv.check("0.8.0", "0.7.0", "0.6.0", None, None)
    assert drift
    assert any("0.8.0" in d and "0.7.0" in d for d in drift)


def test_tag_two_behind_is_drift():
    drift = sv.check("0.8.0", "0.8.0", "0.7.0", "v0.6.0", None)
    assert drift
    assert any("v0.6.0" in d for d in drift)


def test_tag_ahead_is_drift():
    drift = sv.check("0.8.0", "0.8.0", "0.7.0", "v0.9.0", None)
    assert drift
    assert any("v0.9.0" in d for d in drift)


def test_no_tags_skips_tag_surface():
    assert sv.check("0.8.0", "0.8.0", "0.7.0", None, None) == []


def test_card_absent_skips():
    assert sv.check("0.8.0", "0.8.0", "0.7.0", "v0.8.0", None) == []


def test_card_mismatch_is_drift():
    drift = sv.check("0.8.0", "0.8.0", "0.7.0", "v0.8.0", "0.1.0")
    assert drift
    assert any(d.startswith("card:") and "0.1.0" in d for d in drift)


def test_card_non_object_json_degrades_to_none(tmp_path, monkeypatch):
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    monkeypatch.setenv("OMHA_ROOT", str(tmp_path))
    card_path = cards_dir / "omp.json"
    for payload in ("null", "[]", '"foo"', "42", '{"version": 42}'):
        card_path.write_text(payload, encoding="utf-8")
        surfaces = sv.gather(ROOT)  # must not raise, must degrade to None
        assert surfaces["card"] is None


def test_changelog_parser_skips_unreleased(tmp_path):
    p = tmp_path / "CHANGELOG.md"
    p.write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [0.8.0] — 2026-07-20\n\n"
        "## [0.7.0] — 2026-07-13\n",
        encoding="utf-8",
    )
    versions = sv.parse_changelog(p)
    assert versions[0] == "0.8.0"


def test_tag_parse_is_exact_match():
    tags = ["v0.7.0", "v0.7.0-rc1", "x0.9.9", "v10.0"]
    assert sv.parse_tags(tags) == "v0.7.0"


def test_live_repo_surfaces_agree():
    surfaces = sv.gather(ROOT)
    assert surfaces["plugin"] == surfaces["changelog_top"], (
        f"plugin.json version {surfaces['plugin']!r} != "
        f"CHANGELOG top released {surfaces['changelog_top']!r}"
    )
    if surfaces["latest_tag"] is not None:
        tag_version = surfaces["latest_tag"].lstrip("v")
        assert tag_version in (surfaces["plugin"], surfaces["changelog_prev"]), (
            f"latest tag {surfaces['latest_tag']!r} matches neither plugin "
            f"{surfaces['plugin']!r} nor previous released {surfaces['changelog_prev']!r}"
        )


def test_cli_read_only():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "atomic_write_json" not in src
    assert not re.search(r'open\([^)]*["\']w', src)
    assert "write_text(" not in src
