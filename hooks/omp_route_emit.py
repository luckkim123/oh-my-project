"""omp UserPromptSubmit hook: inject a project-stage routing checkpoint.

Stdlib only (a test enforces this). Mirrors OMS/OMD route_emit.py: the hook does
NOT decide anything itself — it injects a one-line checkpoint that reminds the
session LLM, when a project-management request is detected, to declare which omp
STAGE it is in before acting. The actual stage logic lives in
skills/omp-*/SKILL.md (single source of truth); this hook never embeds that
knowledge inline, so there is no drift.

Layering: omha (the meta-harness) picks the LANE (superpowers / oh-my-claudecode
/ handle-directly). omp is a DOMAIN handler (project-folder management), so this
hook never picks a lane — it only picks the STAGE within the project domain, and
emits it on the line right after omha's ROUTE line. The two do not conflict.

Discoverability: if the current working directory has no `.omp/`, the checkpoint
appends a one-line "no .omp/ yet — run omp-init first" hint, so a user who does not
yet know that init must run first is told (a hint, never a block — the session
proceeds either way). If `.omp/` exists, no hint is added (no false nag). The
`.omp/` probe is best-effort and fail-open: any error falls back to the bare
checkpoint. cwd-relative only (a sub-dir false-negative is harmless — it is a hint).

Fail-open: any error returns 0 so the session is never blocked. Cross-platform:
pure stdlib, pathlib only.
"""
import json
import os
import sys
from pathlib import Path

# 부재 전용 마커 — CHECKPOINT 의 일반 stage 열거("init")와 구별되는 고유 문구
# (테스트가 같은 문구를 본다: tests/test_omp_route_emit.py NO_OMP_MARKER).
NO_OMP_HINT = (
    "\n\n⚠️ 이 폴더엔 아직 .omp/가 없다 — 먼저 `omp-init`으로 부트스트랩해야 "
    "관리·검증·정리가 가능하다(스캔→프리셋 합성→사람 승인 게이트). "
    "통째로 맡기려면 omp-pilot 이 init 을 먼저 흡수한다."
)


def _omp_missing() -> bool:
    """cwd 에 .omp/ 가 없으면 True. best-effort — 판단 불가 시 False(힌트 억제)."""
    try:
        return not (Path.cwd() / ".omp").is_dir()
    except Exception:
        return False  # 확인 실패 시 힌트 안 붙임 (fail-open, false nag 방지)


CHECKPOINT = (
    "<omp-routing>\n"
    "프로젝트 폴더 관리 요청(구조 파악·정리, 명명 규칙, 파일 재배치, dataset 추적, "
    "초기화, .omp 관리)이면, 행동 전에 한 줄로 판정하라:\n"
    "- 단계: init(1회 부트스트랩·.omp 생성) / codify(구조·명명 규칙 성문화) / "
    "organize(규칙 위반 탐지→안전 재배치) / dataset(등록·체크섬·split·lineage) / "
    "env(환경 자산 Dockerfile/compose 정본을 .omp/env/에 생성·관리) / "
    "doc(사람용 문서 생성·갱신) / learn(관찰→규칙 승격, 승인 게이트) / "
    "audit(규칙 준수 검증, read-only PASS/FAIL) / "
    "log(비서 캡처 — 사건·할일·막힘·결정 기록) / brief(현황 브리핑 — 어디까지 왔고 "
    "다음 뭐 할지) / review(주간 재평가 — migration·stale 정리) / "
    "handoff(위임 브리핑 — 형제 하네스(oms·omd·omx 등)에 맡기기 직전, 이 프로젝트 지식을 "
    "4요소 패킷으로 전수), 또는 omp-pilot(통째) / omp-doctor(설치·전제 자가진단).\n"
    "단일 단계면 그 스킬 직접, 폴더 통째 정리·진화면 omp-pilot, "
    "설치/작동 문제 진단이면 omp-doctor.\n"
    "⚠️ 안전: 파일 이동은 mv→검증→삭제·trash 경유, 실제 dataset은 안 옮김(메타만).\n"
    "⚠️ 인덱스 정합: 구조에 영향 주는 이동·리네임(폴더 이름·계층·존재 변경)은 organize 단계로 "
    "다루고, 맨손 mv 였더라도 .omp/(STRUCTURE.md·rules.json·DATASETS.md) 갱신을 같은 작업 안에서 "
    "끝낸다 — 옛 경로가 인덱스에 남는 drift 금지(사용자가 다시 지시하게 만들지 말 것).\n\n"
    "프로젝트 관리 작업이면, 판정을 응답 맨 앞 omha ROUTE 줄 바로 다음에 이 한 줄로 "
    "출력하라(누락 금지):\n"
    "STAGE(project) → <init|codify|organize|dataset|env|doc|learn|audit|log|brief|review|handoff|omp-pilot|omp-doctor> · <한 줄 근거>\n"
    "프로젝트 관리 작업이 아니면 이 블록 전체 무시(STAGE 줄도 출력하지 말 것).\n"
    "</omp-routing>"
)


def _skipped(token):
    return token in {t.strip() for t in os.environ.get("OMP_SKIP_HOOKS", "").split(",") if t.strip()}


def main() -> int:
    try:
        if _skipped("route"):
            return 0
        context = CHECKPOINT + (NO_OMP_HINT if _omp_missing() else "")
        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }
        print(json.dumps(out))
    except Exception as e:  # noqa: BLE001 — fail-open is intentional
        # 에러 맥락을 stderr 로 1줄(디버그용). stdout 계약·exit code 불변 → fail-open. T23.
        sys.stderr.write("[omp_route_emit] swallowed: %r\n" % (e,))
        return 0  # fail-open — never block the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
