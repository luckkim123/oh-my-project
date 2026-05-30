"""Tests for the PostToolUse integrity-reminder hook.

핵심 계약: .omp/ 파일 수정 또는 move/delete 명령 후에만 리마인더를 낸다.
무관한 작업엔 침묵. 자동수정·freeze 안 함('fix before continuing' 금지).
stdlib only, fail-open."""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent / "hooks" / "omp_verify_emit.py"


def run_hook(payload: dict) -> str:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def context_of(stdout: str) -> str:
    if not stdout.strip():
        return ""
    return json.loads(stdout)["hookSpecificOutput"]["additionalContext"]


def test_reminds_on_omp_file_edit():
    """① .omp/ SSOT 파일 수정 시 리마인더. 구체 레이블·문구를 고정해
    본문 재작성 시에도 계약이 유지되게 한다(약한 'omp' in out 대신)."""
    out = context_of(run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": "/proj/.omp/rules.json"},
    }))
    assert "[omp integrity reminder]" in out   # 리마인더 레이블 고정
    assert ".omp/ SSOT 파일이 수정됨" in out    # .omp 편집 감지 사유 고정
    assert "audit" in out                       # 후속 audit 안내


def test_reminds_on_move_command():
    """② mv/rm/trash 명령 시 안전 프로토콜 리마인더."""
    out = context_of(run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "mv data/foo.csv data/raw/foo.csv"},
    }))
    assert "trash" in out or "잔류" in out


def test_silent_on_unrelated_edit():
    """③ 무관한 파일 수정엔 침묵 (.omp 밖, 이동 아님)."""
    out = run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": "/proj/src/main.py"},
    })
    assert out.strip() == ""


def test_silent_on_read_only_bash():
    """④ 읽기 전용 bash(ls 등)엔 침묵."""
    out = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la data/"},
    })
    assert out.strip() == ""


def test_no_freeze_phrase():
    """⑤ freeze 유발 문구 'fix before continuing' 절대 없음 (OMC freeze 패턴 회피)."""
    out = context_of(run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "rm old.txt"},
    }))
    assert "fix before continuing" not in out.lower()


def test_no_auto_fix_directive():
    """⑥ 자동수정 지시 없음 — 리마인더(권장)만, 강제 아님."""
    out = context_of(run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": "/proj/.omp/manifest.json"},
    }))
    assert "확인" in out  # '확인할 것'(권장) 톤


def test_windows_path_separator():
    """⑦ Windows 역슬래시 경로도 .omp/ 매칭 (크로스플랫폼)."""
    out = context_of(run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": "C:\\\\proj\\\\.omp\\\\rules.json"},
    }))
    assert out != ""


def test_stdlib_only():
    """⑧ stdlib only."""
    src = HOOK.read_text()
    assert "import requests" not in src and "import yaml" not in src


def test_fail_open():
    """⑨ fail-open: 잘못된 입력에도 exit 0."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="garbage", capture_output=True, text=True,
    )
    assert proc.returncode == 0
