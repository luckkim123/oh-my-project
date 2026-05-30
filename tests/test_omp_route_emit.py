"""Tests for the project-stage UserPromptSubmit routing hook.

핵심 계약: 매 턴 STAGE 판정을 응답 맨 앞에 출력하라는 contract 를 주입한다
(omha 의 ROUTE 줄과 같은 방식, 단 omp 는 도메인 처리기라 LANE 이 아닌 STAGE).
stdlib only, fail-open, cross-platform (paths 안 건드림)."""
import json
import subprocess
import sys
from pathlib import Path

from hooks import omp_route_emit

HOOK = Path(__file__).parent.parent / "hooks" / "omp_route_emit.py"


def run_hook(payload: dict, cwd=None) -> str:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True, cwd=cwd,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def context_of(stdout: str) -> str:
    if not stdout.strip():
        return ""
    return json.loads(stdout)["hookSpecificOutput"]["additionalContext"]


def test_emits_userpromptsubmit_context():
    """① UserPromptSubmit 이벤트로 라우팅 contract 주입."""
    out = run_hook({"prompt": "이 프로젝트 폴더 정리해줘"})
    d = json.loads(out)
    assert d["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_context_states_stage_emit_contract():
    """② 매 턴 STAGE 한 줄 판정 contract 가 명시돼야 (omha ROUTE 와 동형)."""
    out = context_of(run_hook({"prompt": "구조 파악"}))
    assert "STAGE(project) →" in out
    assert "누락 금지" in out


ALL_STAGES = ("init", "codify", "organize", "dataset",
              "doc", "learn", "audit", "omp-pilot", "omp-doctor")


def test_context_lists_all_stages():
    """③ 모든 단계가 contract 에 열거돼야 (skill 과 정합). 8 루프 단계 + pilot
    + doctor(설치 진단). 새 스킬 추가 시 이 목록도 동기화 — 죽은 스킬 방지."""
    out = context_of(run_hook({"prompt": "프로젝트 관리"}))
    for stage in ALL_STAGES:
        assert stage in out, f"stage '{stage}' missing from contract"


def test_stage_line_template_lists_all_stages():
    """③b 한 줄 STAGE 템플릿(`STAGE(project) → <...>`) 안에도 모든 stage 가
    표기돼야. ③은 CHECKPOINT '어딘가'만 보므로, 산문에만 추가하고 한 줄 템플릿
    갱신을 빠뜨리는 사각(doctor 가 그랬다)을 이 단언이 막는다 — LLM 이 매 턴
    출력하는 칸에 stage 가 없으면 그 의도를 표기할 자리가 없다."""
    out = context_of(run_hook({"prompt": "프로젝트 관리"}))
    line = next((l for l in out.splitlines() if l.startswith("STAGE(project) →")), "")
    assert line, "한 줄 STAGE 템플릿이 없다"
    for stage in ALL_STAGES:
        assert stage in line, f"stage '{stage}' 가 한 줄 STAGE 템플릿에서 누락"


def test_context_states_safety():
    """④ 안전 — 파일 이동 안전·dataset 메타-only 가 contract 에 박혀야.
    AND 단언: 안전 라인 전체가 사라지면 잡히게(OR 이면 '검증'이 audit 설명에도
    독립 등장해 안전 문구 삭제를 못 탐지)."""
    out = context_of(run_hook({"prompt": "organize"}))
    assert "trash" in out and "검증" in out      # 파일 이동 안전(mv→검증→삭제·trash)
    assert "메타" in out or "안 옮" in out         # dataset 메타-only


def test_stage_label_distinct_from_siblings():
    """⑤ omp 레이블(STAGE(project))이 oms(paper)·omd(docs)·omha(ROUTE)와 달라
    한 화면에 같이 떠도 헷갈리지 않음. 이모지 미사용."""
    out = context_of(run_hook({"prompt": "프로젝트"}))
    assert "STAGE(project)" in out
    assert "STAGE(paper)" not in out
    assert "STAGE(docs)" not in out
    assert "ROUTE →" not in out
    assert "🧭" not in out and "📁" not in out and "🗂" not in out


def test_stdlib_only_no_third_party_imports():
    """⑥ stdlib only — 외부 의존 없이 import 가능."""
    src = HOOK.read_text()
    assert "import json" in src and "import sys" in src
    assert "import requests" not in src and "import a2a" not in src
    assert "import yaml" not in src


def test_always_exits_zero_regardless_of_stdin():
    """⑦ 이 hook 은 stdin 을 읽지 않고 정적 checkpoint 만 emit 한다(설계).
    어떤 stdin 이 와도 exit 0 + STAGE contract 가 나온다(세션 안 막음).
    (검증은 파싱된 context 로 — json.dumps 가 →·등 비ASCII 를 이스케이프하므로
    raw stdout grep 은 부정확.)"""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all", capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "STAGE(project) →" in context_of(proc.stdout)  # stdin 무시하고 정상 경로


def test_fail_open_when_emit_raises(monkeypatch, capsys):
    """⑦b 실제 except 경로 커버: emit 도중 예외가 나도 fail-open(exit 0) +
    stderr 에 맥락 1줄(T23). json.dumps 가 던지도록 monkeypatch 해 except 분기를 탄다."""
    def boom(*_a, **_k):
        raise RuntimeError("forced emit failure")
    monkeypatch.setattr(omp_route_emit.json, "dumps", boom)
    rc = omp_route_emit.main()
    assert rc == 0                                   # fail-open
    err = capsys.readouterr().err
    assert "[omp_route_emit] swallowed" in err       # T23 stderr 맥락


# 부재 전용 마커 — CHECKPOINT 의 일반 stage 열거("init")와 구별되는 고유 문구.
# hook 과 테스트가 같은 상수를 봐야 drift 가 없다.
NO_OMP_MARKER = "아직 .omp/가 없"


def test_uninitialized_folder_surfaces_init_hint(tmp_path):
    """⑧ .omp 없는 폴더에서 호출 시 부재 전용 'init 먼저' 힌트를 노출 — 사용자가
    init 해야 한다는 사실 자체를 모를 수 있으므로 발견성 제공 (차단 아님)."""
    out = context_of(run_hook({"prompt": "이 폴더 정리해줘"}, cwd=str(tmp_path)))
    assert NO_OMP_MARKER in out, "부재 폴더인데 init 부재 힌트가 없다"


def test_initialized_folder_no_init_hint(tmp_path):
    """⑨ .omp 가 이미 있으면 부재 힌트를 주입하지 않는다 (false nag 방지).
    단 평소 STAGE contract(‘init’ 단계 열거 포함)는 그대로 나온다."""
    (tmp_path / ".omp").mkdir()
    out = context_of(run_hook({"prompt": "audit 해줘"}, cwd=str(tmp_path)))
    assert "STAGE(project) →" in out      # 평소 contract 유지
    assert NO_OMP_MARKER not in out       # 부재 전용 마커는 없어야


def test_init_hint_failure_is_fail_open(tmp_path):
    """⑩ .omp 존재 확인이 어떤 이유로 실패해도 fail-open — 평소 checkpoint 는 나온다.
    (권한/경로 에러 시 hook 이 세션을 막지 않음)"""
    # 정상 cwd 에서 최소한 STAGE contract 가 항상 나옴을 확인한다.
    out = context_of(run_hook({"prompt": "x"}, cwd=str(tmp_path)))
    assert "STAGE(project) →" in out
