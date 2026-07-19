"""SessionStart/SessionEnd hooks — once-per-session, fail-open, OMP_SKIP_HOOKS gated."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CAPTURE = ROOT / "hooks" / "omp_session_capture.py"
BRIEF_HOOK = ROOT / "hooks" / "omp_session_brief.py"


def _run(hook, payload, env_extra=None, cwd=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                          capture_output=True, text=True, env=env, cwd=cwd)


def test_capture_writes_stub_in_omp_project(tmp_path):
    (tmp_path / ".omp" / "secretary").mkdir(parents=True)
    sub = tmp_path / "src"
    sub.mkdir()
    r = _run(CAPTURE, {"session_id": "s1", "cwd": str(sub)})
    assert r.returncode == 0
    assert (tmp_path / ".omp/secretary/ledger.jsonl").exists()  # ascend from subdir worked

def test_capture_noop_without_omp(tmp_path):
    r = _run(CAPTURE, {"session_id": "s1", "cwd": str(tmp_path)})
    assert r.returncode == 0 and r.stdout.strip() == ""

def test_capture_skip_gate(tmp_path):
    (tmp_path / ".omp" / "secretary").mkdir(parents=True)
    r = _run(CAPTURE, {"session_id": "s1", "cwd": str(tmp_path)},
             env_extra={"OMP_SKIP_HOOKS": "session_capture"})
    assert r.returncode == 0
    assert not (tmp_path / ".omp/secretary/ledger.jsonl").exists()

def test_capture_fail_open_on_garbage():
    r = subprocess.run([sys.executable, str(CAPTURE)], input="NOT JSON",
                       capture_output=True, text=True)
    assert r.returncode == 0

def test_brief_injects_when_present(tmp_path):
    sec = tmp_path / ".omp" / "secretary"
    sec.mkdir(parents=True)
    (sec / "BRIEF.md").write_text("# BRIEF\ngreen\n", encoding="utf-8")
    r = _run(BRIEF_HOOK, {"session_id": "s1", "cwd": str(tmp_path)})
    out = json.loads(r.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "BRIEF" in ctx and out["hookSpecificOutput"]["hookEventName"] == "SessionStart"

def test_brief_truncates_to_30_lines(tmp_path):
    sec = tmp_path / ".omp" / "secretary"
    sec.mkdir(parents=True)
    (sec / "BRIEF.md").write_text("\n".join("line%d" % i for i in range(100)))
    r = _run(BRIEF_HOOK, {"cwd": str(tmp_path)})
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert len(ctx.splitlines()) <= 32  # 30 content lines + header allowance

def test_brief_silent_when_absent_or_skipped(tmp_path):
    r = _run(BRIEF_HOOK, {"cwd": str(tmp_path)})
    assert r.returncode == 0 and r.stdout.strip() == ""
    sec = tmp_path / ".omp" / "secretary"
    sec.mkdir(parents=True)
    (sec / "BRIEF.md").write_text("x")
    r2 = _run(BRIEF_HOOK, {"cwd": str(tmp_path)}, env_extra={"OMP_SKIP_HOOKS": "session_brief"})
    assert r2.stdout.strip() == ""
