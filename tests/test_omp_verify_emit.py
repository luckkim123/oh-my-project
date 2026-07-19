"""Tests for the PostToolUse integrity-reminder hook.

핵심 계약: .omp/ 파일 수정 또는 move/delete 명령 후에만 리마인더를 낸다.
무관한 작업엔 침묵. 자동수정·freeze 안 함('fix before continuing' 금지).
stdlib only, fail-open."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from omp_verify_emit import should_throttle, record_emit  # noqa: E402

HOOK = Path(__file__).parent.parent / "hooks" / "omp_verify_emit.py"


def run_hook(payload: dict, cwd=None, env=None) -> str:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True, cwd=cwd, env=env,
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


def test_silent_on_grep_mentioning_risky_verb():
    """⑯ grep이 인용문 안에서 risky verb를 언급해도 침묵 (false positive 회피)."""
    out = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": 'grep -c "mv the file then verify" notes.md'},
    })
    assert out.strip() == ""


def test_silent_on_echo_mentioning_risky_verb():
    """⑰ echo가 risky verb를 인용문 안에서 언급해도 침묵."""
    out = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": 'echo "do not rm anything"'},
    })
    assert out.strip() == ""


def test_reminds_on_move_after_boundary_operator():
    """⑱ && 뒤 두 번째 명령이 실제 mv라면 여전히 탐지(경계 검사가 과교정 아님)."""
    out = context_of(run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls && mv a.txt b.txt"},
    }))
    assert "[omp integrity reminder]" in out


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


def test_verify_emit_skip_gate():
    """⑩ OMP_SKIP_HOOKS=verify 로 실행 시 stdout 빈 문자열 + exit 0(4훅 공통 게이트)."""
    env = dict(os.environ, OMP_SKIP_HOOKS="verify")
    out = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "rm old.txt"},
    }, env=env)
    assert out.strip() == ""


def test_verify_emit_skip_gate_other_token_does_not_skip():
    """⑪ 다른 토큰만 있으면 verify 는 스킵되지 않는다(토큰별 개별 게이트)."""
    env = dict(os.environ, OMP_SKIP_HOOKS="route,session_capture")
    out = context_of(run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "rm old.txt"},
    }, env=env))
    assert "[omp integrity reminder]" in out


def test_throttle_suppresses_within_cooldown(tmp_path):
    """⑫ content-hash throttle: 동일 reason 을 300초 내 재출력하면 침묵."""
    (tmp_path / ".omp").mkdir()
    reason = "파일 이동/삭제 명령이 실행됨."
    record_emit(tmp_path, reason, now=1000.0)
    assert should_throttle(tmp_path, reason, now=1100.0) is True  # 100s < 300s


def test_throttle_allows_after_cooldown(tmp_path):
    """⑬ 쿨다운(300s) 경과 후엔 다시 출력."""
    (tmp_path / ".omp").mkdir()
    reason = "파일 이동/삭제 명령이 실행됨."
    record_emit(tmp_path, reason, now=1000.0)
    assert should_throttle(tmp_path, reason, now=1301.0) is False  # 301s >= 300s


def test_throttle_end_to_end_second_call_silent(tmp_path):
    """⑭ 훅을 같은 root 에서 두 번 연달아 호출하면 두 번째는 침묵(실제 stdin/stdout 왕복)."""
    (tmp_path / ".omp").mkdir()
    payload = {"tool_name": "Bash", "tool_input": {"command": "mv a.txt b.txt"}, "cwd": str(tmp_path)}
    first = run_hook(payload)
    assert "[omp integrity reminder]" in first
    second = run_hook(payload)
    assert second.strip() == ""


def test_throttle_state_io_failure_is_fail_open(monkeypatch, tmp_path):
    """⑮ 상태 파일 IO 실패는 재출력(fail-open이 안전 신호를 침묵시키지 않음)."""
    (tmp_path / ".omp").mkdir()
    state_dir = tmp_path / ".omp" / "state"
    state_dir.mkdir()
    bad_state = state_dir / "verify-throttle.json"
    bad_state.write_text("not valid json{{{", encoding="utf-8")
    from hooks import omp_verify_emit
    assert omp_verify_emit.should_throttle(tmp_path, "reason") is False
