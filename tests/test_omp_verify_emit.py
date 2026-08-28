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
from omp_verify_emit import detect, record_emit, should_throttle  # noqa: E402

HOOK = Path(__file__).parent.parent / "hooks" / "omp_verify_emit.py"

_PLACEMENT_RULES = {"structure": {"directories": [
    {"path": "0_Project", "role": "PROJECTS", "enforced": True},
    {"path": "1_Area", "role": "AREAS: 일회성 실행 지시서는 여기가 아니다", "enforced": True},
    {"path": "2_Resource/concepts", "role": "개념 노트", "enforced": False},
]}}


def _placement(tmp_path, rel, tool="Write"):
    return detect(tool, {"file_path": str(tmp_path / rel)}, str(tmp_path), _PLACEMENT_RULES)


def test_placement_fires_on_category_top_level_drop(tmp_path):
    """사건의 형태 — enforced 카테고리 최상단에 일회성 문서가 떨어진다."""
    reason = _placement(tmp_path, "1_Area/2026-08-16-graphify-resume-prompt.md")
    assert "enforced 폴더 최상단" in reason and "1_Area/" in reason
    assert "일회성 실행 지시서는 여기가 아니다" in reason  # role 을 실어 판단 재료를 준다


def test_placement_silent_on_established_and_exempt_paths(tmp_path):
    """오탐 회귀 — 실측(3,292 추적 파일 중 최상단 6건, 그중 4건이 README)이 근거다.

    깊은 경로는 이미 누군가 고른 구조 안이고, 카테고리 README 는 정당한 색인이며,
    enforced:false 폴더는 감사 대상이 아니고, Edit 은 배치가 아니라 내용 변경이다.
    """
    assert not _placement(tmp_path, "1_Area/README.md")
    assert not _placement(tmp_path, "0_Project/in_progress/albc/notes/handoff.md")
    assert not _placement(tmp_path, "2_Resource/concepts/rl/value_iteration.md")
    assert not _placement(tmp_path, "1_Area/2026-08-16-graphify-resume-prompt.md", tool="Edit")


_ROOT_RULES = {"structure": {"directories": [
    {"path": ".", "role": "루트는 진입점 — README·LICENSE 외엔 하위 디렉터리로", "enforced": True},
    {"path": "runtime/skills", "role": "스킬 1개 = 디렉터리 1개", "enforced": True},
]}}


def _root_placement(tmp_path, rel, rules=None, tool="Write"):
    return detect(tool, {"file_path": str(tmp_path / rel)}, str(tmp_path), rules or _ROOT_RULES)


def test_root_entry_fires_on_a_new_top_level_file(tmp_path):
    """`.` 은 프로젝트 루트를 뜻한다. 이 검사가 없어서 `path: "."` 항목이 조용히
    아무것도 안 잡았다 — 접두 검사가 `"./"` 로 시작하는 경로를 찾는데
    `relative_to()` 는 그런 걸 만들지 않는다. enforced 로 읽히면서 무효였다."""
    reason = _root_placement(tmp_path, "ruff.toml")
    assert "ruff.toml" in reason and "루트는 진입점" in reason


def test_root_entry_ignores_anything_deeper(tmp_path):
    """루트 항목이 트리 전체를 삼키면 안 된다 — 최상단만 본다."""
    assert not _root_placement(tmp_path, "docs/note.md")
    assert not _root_placement(tmp_path, "runtime/hooks/x.py")


def test_root_entry_keeps_the_readme_exemption_and_write_only_rule(tmp_path):
    assert not _root_placement(tmp_path, "README.md")
    assert not _root_placement(tmp_path, "ruff.toml", tool="Edit")


def test_empty_path_is_treated_as_root_not_as_a_wildcard(tmp_path):
    """`strip("/")` 이 빈 문자열을 낼 수 있다. 루트로 읽되 깊은 경로는 여전히 제외."""
    rules = {"structure": {"directories": [{"path": "", "role": "루트", "enforced": True}]}}
    assert _root_placement(tmp_path, "stray.md", rules)
    assert not _root_placement(tmp_path, "docs/stray.md", rules)


def test_named_category_still_matches_only_its_own_top_level(tmp_path):
    """루트 분기를 넣으면서 기존 경로 분기가 상하지 않았는지."""
    assert _root_placement(tmp_path, "runtime/skills/loose.md")
    assert not _root_placement(tmp_path, "runtime/skills/my-skill/SKILL.md")
    assert not _root_placement(tmp_path, "runtime/agents/x.md")


def test_placement_silent_without_root_or_rules_and_outside_project(tmp_path):
    """advisory 축이라 근거가 없으면 추측하지 않고 침묵한다 (2인자 호출 하위호환 포함)."""
    fp = str(tmp_path / "1_Area" / "x.md")
    assert not detect("Write", {"file_path": fp})                       # 기존 2인자 호출
    assert not detect("Write", {"file_path": fp}, None, _PLACEMENT_RULES)
    assert not detect("Write", {"file_path": fp}, str(tmp_path), None)
    assert not detect("Write", {"file_path": "/tmp/elsewhere/1_Area/x.md"},
                      str(tmp_path), _PLACEMENT_RULES)


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
    assert "SSOT 파일이 수정됨" in out          # 편집 감지 사유 고정
    assert "audit" in out                       # 후속 audit 안내


def test_reminds_on_hq_file_edit_without_claiming_omp():
    """①b stage 2: `.hq/` 파일 수정도 같은 리마인더를 내되, 실제로는 `.hq/`가
    수정됐는데 ".omp/ SSOT 파일이 수정됨"이라고 고정 문구를 반환하던 결함의
    회귀 방지 — is_inside_store()는 두 루트를 다 감지하므로 reason 문구도
    루트를 특정하지 않아야 한다."""
    out = context_of(run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": "/proj/.hq/config/project/rules.json"},
    }))
    assert "[omp integrity reminder]" in out
    assert "SSOT 파일이 수정됨" in out
    assert ".omp/ SSOT 파일이 수정됨" not in out  # .hq/ 편집을 .omp/ 라 오표기 금지


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


def test_reminds_on_move_after_newline():
    """⑲ 개행으로 이어진 두 번째 줄이 실제 mv라면 탐지(멀티라인 명령 회귀 방지)."""
    out = context_of(run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls\nmv a.txt b.txt"},
    }))
    assert "[omp integrity reminder]" in out


def test_reminds_on_move_inside_command_substitution():
    """⑳ $(...) 서브셸 안의 mv도 탐지(subshell로 경계검사 우회 방지)."""
    out = context_of(run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": 'echo "$(mv a.txt b.txt)"'},
    }))
    assert "[omp integrity reminder]" in out


def test_reminds_on_move_inside_backtick_substitution():
    """㉑ 백틱 서브셸 안의 mv도 탐지."""
    out = context_of(run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": 'echo "`mv a.txt b.txt`"'},
    }))
    assert "[omp integrity reminder]" in out


def test_silent_on_grep_inside_command_substitution():
    """㉒ 서브셸 안에서도 grep이 risky verb를 인용문으로만 언급하면 침묵(false positive 회피 유지)."""
    out = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": 'x=$(grep -c "mv the file" notes.md)'},
    })
    assert out.strip() == ""


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
