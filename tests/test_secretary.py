"""Secretary-axis pure functions — contract tests (spec §4.4, references/secretary-protocol.md)."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from omp_secretary import (  # noqa: E402
    find_omp_root, sanitize_session_id, redact_secrets, parse_todo_line,
    append_ledger, derive_status, brief_hash_check, session_stub,
    scan_stale, scan_journal_tags,
)


def _mkroot(tmp_path):
    (tmp_path / ".omp" / "secretary" / "journal").mkdir(parents=True)
    (tmp_path / ".omp" / "secretary" / "decisions").mkdir(parents=True)
    return tmp_path


def test_find_omp_root_ascends(tmp_path):
    root = _mkroot(tmp_path)
    sub = root / "a" / "b"; sub.mkdir(parents=True)
    assert find_omp_root(sub) == root

def test_find_omp_root_none_when_absent(tmp_path):
    assert find_omp_root(tmp_path) is None

def test_sanitize_session_id():
    assert sanitize_session_id("abc-123_X") == "abc-123_X"
    assert sanitize_session_id("../evil") is None
    assert sanitize_session_id("") is None

def test_redact_secrets_masks_known_shapes():
    s = "Bearer abcDEF123456789012345 sk-ant-api03-xxxx ghp_0123456789abcdef0123456789abcdef0123 AKIAIOSFODNN7EXAMPLE xoxb-1234-abcd"
    out = redact_secrets(s)
    for leak in ("sk-ant-api", "ghp_", "AKIA", "xoxb-", "Bearer abc"):
        assert leak not in out
    assert "[REDACTED:" in out

def test_redact_secrets_passthrough_plain():
    assert redact_secrets("일반 한국어 문장 no secrets") == "일반 한국어 문장 no secrets"

def test_parse_todo_line_full():
    t = parse_todo_line("(A) 2026-07-11 fix hook +omp @deep due:2026-07-20 blocked-by:0003")
    assert t["priority"] == "A" and t["created"] == "2026-07-11"
    assert t["projects"] == ["omp"] and t["contexts"] == ["deep"]
    assert t["kv"]["blocked-by"] == "0003" and t["done"] is False

def test_parse_todo_line_done_and_empty():
    d = parse_todo_line("x 2026-07-12 2026-07-11 shipped")
    assert d["done"] is True and d["completed"] == "2026-07-12"
    assert parse_todo_line("   ") is None

def test_append_ledger_appends_jsonl_and_redacts(tmp_path):
    root = _mkroot(tmp_path)
    append_ledger(root, {"event": "task_added", "note": "key sk-ant-api03-secret"})
    append_ledger(root, {"event": "task_done"})
    lines = (root / ".omp/secretary/ledger.jsonl").read_text().splitlines()
    assert len(lines) == 2
    e0 = json.loads(lines[0])
    assert e0["event"] == "task_added" and "ts" in e0
    assert "sk-ant-api" not in lines[0]

def test_derive_status_lights(tmp_path):
    root = _mkroot(tmp_path)
    sec = root / ".omp/secretary"
    (sec / "todo.txt").write_text("(A) 2026-07-11 t1 +p\n", encoding="utf-8")
    (sec / "raid.md").write_text("## Issues\n- [open] I-1 blocked on X\n", encoding="utf-8")
    st = derive_status(root)
    assert st["light"] == "red" and st["open_blockers"] == 1 and st["open_tasks"] == 1

def test_derive_status_green_when_empty(tmp_path):
    root = _mkroot(tmp_path)
    assert derive_status(root)["light"] == "green"

def test_derive_status_tolerates_corrupt_ledger_line(tmp_path, capsys):
    root = _mkroot(tmp_path)
    (root / ".omp/secretary/ledger.jsonl").write_text('{"ts":"t","event":"task_done"}\nNOT-JSON\n')
    st = derive_status(root)  # must not raise
    assert st["light"] in ("green", "yellow", "red")

def test_brief_hash_check_clean_dirty_missing(tmp_path):
    root = _mkroot(tmp_path)
    brief = root / ".omp/secretary/BRIEF.md"
    assert brief_hash_check(brief) == "missing"
    import hashlib
    body = "# BRIEF\nstatus green\n"
    marker = "<!-- omp-managed: sha256:%s -->\n" % hashlib.sha256(body.encode()).hexdigest()
    brief.write_text(marker + body, encoding="utf-8")
    assert brief_hash_check(brief) == "clean"
    brief.write_text(marker + body + "human edit\n", encoding="utf-8")
    assert brief_hash_check(brief) == "dirty"

def test_session_stub_appends_journal_and_ledger(tmp_path):
    root = _mkroot(tmp_path)
    session_stub(root, "sess-1", ["a.md"], last_stage="organize")
    day = datetime.now().strftime("%Y-%m-%d")
    j = (root / ".omp/secretary/journal" / (day + ".md")).read_text()
    assert "sess-1" in j and "organize" in j
    led = (root / ".omp/secretary/ledger.jsonl").read_text()
    assert '"session_end"' in led

def test_session_stub_rejects_bad_id(tmp_path):
    root = _mkroot(tmp_path)
    session_stub(root, "../evil", [])  # must silently no-op, not raise/escape
    assert not (root / ".omp/secretary/ledger.jsonl").exists()

def test_scan_stale_finds_old_task_blocker_conflictcopy(tmp_path):
    root = _mkroot(tmp_path)
    sec = root / ".omp/secretary"
    (sec / "todo.txt").write_text("(B) 2026-01-01 ancient +p\n")
    (sec / "raid.md").write_text("## Issues\n- [open] I-1 (opened:2026-01-02) stuck\n")
    (sec / "ledger 2.jsonl").write_text("{}")
    finds = scan_stale(root, datetime(2026, 7, 11))
    kinds = {f["kind"] for f in finds}
    assert {"stale_task", "stale_blocker", "conflict_copy"} <= kinds

def test_scan_journal_tags(tmp_path):
    root = _mkroot(tmp_path)
    (root / ".omp/secretary/journal/2026-07-11.md").write_text(
        "tried X, failed [BLOCKER:I-1]\nlearned Y [LESSON:xelatex-quirk]\n")
    tags = scan_journal_tags(root)
    assert {t["tag"] for t in tags} == {"BLOCKER", "LESSON"}
    assert {t["ref"] for t in tags} == {"I-1", "xelatex-quirk"}
