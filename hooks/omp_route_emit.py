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

Relevance gate (wave-17, ported from oms's is_paper_related): decides WHETHER
to inject. The predicate is deliberately keyword-OR-marker, never marker-only:
a fresh .omp-less folder must still surface the NO_OMP_HINT discoverability nag
on a keyword-matching prompt (marker-only gating would kill that). Rollout is a
3-state OMP_ROUTE_GATE env flag (off/observe/on), default "off": the gate code
is fully bypassed and the unconditional inject is unchanged. claudebase ships
"on" in config/settings.json, so on a claudebase machine the gate IS live —
read the env, not this default, before concluding anything about behaviour.

Verbosity axis (2026-08-23): a SECOND, orthogonal question — HOW MUCH to inject
once the gate says yes. _keyword_hit (prompt tokens only, marker ignored) picks
CHECKPOINT vs BRIEF. Rationale: the marker says "this folder is an omp
project", which is true of every turn inside it, so marker-only turns were
paying 1,593 chars each for a stage list they never used. BRIEF keeps the STAGE
output format and all three lane-independent safety rules and drops only the
per-stage descriptions, which skills/omp-*/SKILL.md already owns. Coverage is
unchanged — a suppressed turn under the gate is still suppressed, an injected
turn is still injected, just shorter when the prompt gave no reason for detail.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omp_paths import HQ_ROOT, LEGACY_ROOT  # noqa: E402
from omp_paths import has_store  # noqa: E402

# 부재 전용 마커 — CHECKPOINT 의 일반 stage 열거("init")와 구별되는 고유 문구
# (테스트가 같은 문구를 본다: tests/test_omp_route_emit.py NO_OMP_MARKER).
NO_OMP_HINT = (
    "\n\n⚠️ 이 폴더엔 아직 .hq/가 없다 — 먼저 `omp-init`으로 부트스트랩해야 "
    "관리·검증·정리가 가능하다(스캔→프리셋 합성→사람 승인 게이트). "
    "통째로 맡기려면 omp-pilot 이 init 을 먼저 흡수한다."
)


def _omp_missing() -> bool:
    """cwd 에 .omp/ 가 없으면 True. best-effort — 판단 불가 시 False(힌트 억제)."""
    try:
        return not has_store(Path.cwd())
    except Exception:
        return False  # 확인 실패 시 힌트 안 붙임 (fail-open, false nag 방지)


CHECKPOINT = (
    "<omp-routing>\n"
    "프로젝트 폴더 관리 요청(구조 파악·정리, 명명 규칙, 파일 재배치, dataset 추적, "
    "초기화, .hq 관리)이면, 행동 전에 한 줄로 판정하라:\n"
    "- 단계: init(1회 부트스트랩·.hq 생성) / codify(구조·명명 규칙 성문화) / "
    "style(기존 코드에서 관용구 귀납→content_conventions 제안, 쓰기는 codify) / "
    "organize(규칙 위반 탐지→안전 재배치) / dataset(등록·체크섬·split·lineage) / "
    "env(환경 자산 Dockerfile/compose 정본을 .hq/config/project/env/에 생성·관리) / "
    "doc(사람용 문서 생성·갱신) / learn(관찰→규칙 승격, 승인 게이트) / "
    "audit(규칙 준수 검증, read-only PASS/FAIL) / "
    "log(비서 캡처 — 사건·할일·막힘·결정 기록) / brief(현황 브리핑 — 어디까지 왔고 "
    "다음 뭐 할지) / review(주간 재평가 — migration·stale 정리) / "
    "handoff(위임 브리핑 — 형제 하네스(oms·omd·omx 등)에 맡기기 직전, 이 프로젝트 지식을 "
    "4요소 패킷으로 전수) / garden(문서 정원 — 문서가 가리키는 경로가 실재하나, 보고만), 또는 omp-pilot(통째) / omp-doctor(설치·전제 자가진단).\n"
    "단일 단계면 그 스킬 직접, 폴더 통째 정리·진화면 omp-pilot, "
    "설치/작동 문제 진단이면 omp-doctor.\n"
    "⚠️ 안전: 파일 이동은 mv→검증→삭제·trash 경유, 실제 dataset은 안 옮김(메타만).\n"
    "⚠️ 인덱스 정합: 구조에 영향 주는 이동·리네임(폴더 이름·계층·존재 변경)을 **어느 레인에서 "
    "했든**, .hq/config/project/(STRUCTURE.md·rules.json·DATASETS.md) *와* 그 경로를 적어둔 문서(README·인계문·"
    "형제 하네스 posts/)의 갱신을 같은 작업 안에서 끝낸다 — 옛 경로가 남는 drift 금지(사용자가 "
    "다시 지시하게 만들지 말 것). 규칙 위반 재배치가 목적이면 organize 단계로.\n"
    "⚠️ 지식 SSOT 우선(구조·명명·컨벤션 판단 전 필독): '이 프로젝트는 어떻게 조직되나'를 "
    "판단해야 하면, 일반 관행·내 기억보다 먼저 .hq/config/project/(rules.json·STRUCTURE.md)와 "
    ".hq/community/(NAMING.md·CONVENTIONS.md), 그리고 `hq query --ascend`로 읽는 .hq/community/posts/·"
    ".hq/config/project/learned.md를 SSOT로 읽어라. .hq에 규칙이 있는데 "
    "즉흥적으로 구조를 정하는 것은 결함이다.\n\n"
    "프로젝트 관리 작업이면, 판정을 응답 맨 앞 omha ROUTE 줄 바로 다음에 이 한 줄로 "
    "출력하라(누락 금지):\n"
    "STAGE(project) → <init|codify|style|organize|dataset|env|doc|learn|audit|log|brief|review|handoff|garden|omp-pilot|omp-doctor> · <한 줄 근거>\n"
    "프로젝트 관리 작업이 아니면 위 단계 판정·STAGE 줄을 생략한다. 단 ⚠️ 3개는 각자의 전제"
    "(파일 이동 / 구조 리네임 / 구조·명명 판단)가 성립할 때 발동하는 것이라 레인과 무관하게 "
    "유효하다 — '내 레인이 아니다'로 넘기지 말 것.\n"
    "</omp-routing>"
)


# Marker-only turns get this instead of CHECKPOINT. Measured 2026-08-23 on one
# vault: CHECKPOINT injects 1,593 chars on EVERY turn inside an .omp/ folder,
# while the prompt is about project management on a small minority of them —
# the marker says "this folder is an omp project", not "this request is".
#
# What is dropped: the per-stage parenthetical descriptions. Those duplicate
# skills/omp-*/SKILL.md, which the module docstring already names as the single
# source of truth — so CHECKPOINT was violating its own no-drift principle by
# carrying them inline. The stage NAMES are the skill names, so the session can
# still route, and reads the skill when the choice is not obvious.
#
# What is KEPT verbatim in substance: all three ⚠️ rules. They declare
# themselves lane-independent ("어느 레인에서 했든", "레인과 무관하게 유효"), which
# is exactly the claim that makes them wrong to drop on a non-project turn —
# a file move or a structure rename can happen in any lane.
BRIEF = (
    "<omp-routing>\n"
    "프로젝트 폴더 관리 요청(구조·명명·재배치·dataset·환경자산·.hq 관리)이면 응답 맨 앞 "
    "omha ROUTE 줄 바로 다음에 이 한 줄을 출력하라:\n"
    "STAGE(project) → <init|codify|style|organize|dataset|env|doc|learn|audit|log|brief|"
    "review|handoff|garden|omp-pilot|omp-doctor> · <한 줄 근거>\n"
    "각 단계의 정의는 같은 이름의 `omp-*` 스킬 본문이 SSOT다 — 어느 단계인지 갈리면 "
    "추측하지 말고 그 스킬을 읽어라. 프로젝트 관리 작업이 아니면 이 줄을 생략한다.\n"
    "⚠️ 아래 3개는 레인과 무관하게 상시 유효하다 — '내 레인이 아니다'로 넘기지 말 것: "
    "(1) 파일 이동은 mv→검증→삭제·trash 경유, 실제 dataset은 안 옮김(메타만). "
    "(2) 구조에 영향 주는 이동·리네임은 .hq/config/project/(STRUCTURE.md·rules.json·DATASETS.md)와 "
    "그 경로를 적어둔 문서(README·인계문·형제 하네스 posts/)까지 같은 작업 안에서 갱신 — "
    "옛 경로가 남는 drift 금지. (3) 구조·명명·컨벤션을 판단하기 전에 일반 관행·내 기억보다 "
    "먼저 .hq/config/project/(rules.json·STRUCTURE.md)와 .hq/community/(NAMING.md·CONVENTIONS.md), "
    "`hq query --ascend`로 읽는 .hq/community/posts/·.hq/config/project/learned.md를 SSOT로 읽어라.\n"
    "</omp-routing>"
)


def _skipped(token):
    return token in {t.strip() for t in os.environ.get("OMP_SKIP_HOOKS", "").split(",") if t.strip()}


# --- relevance gate (wave-17) -------------------------------------------------
# High-specificity project-management tokens only. Deliberately excludes bare
# 정리/구조/clean (다의성 심각 — "이 함수 정리해줘" is code cleanup, not omp) — a
# genuine organize request is still caught by the phrase tokens below or by
# organize/codify/dataset, and .omp/ present covers every in-project turn.
_CJK_TOKENS = (
    "폴더 구조", "명명 규칙", "재배치", "데이터셋", "초기화", "구조 파악", "정리 규칙", "브리핑",
    # style stage: phrase tokens only. Bare 스타일/컨벤션 are as ambiguous as 정리 —
    # "이 UI 스타일 바꿔" is not omp — so both require the code/관용구 qualifier.
    "코드 스타일", "코드 컨벤션", "관용구", "스타일 드리프트",
    # garden stage: phrase token only. Bare 문서 belongs to the omd lane
    # (a .pptx/.docx deliverable), so the qualifier is what makes it omp.
    "문서 정원", "문서 드리프트",
)
_DOT_TOKENS = (LEGACY_ROOT, HQ_ROOT)
_ASCII_TOKENS = (
    "omp", "omp-init", "omp-pilot", "omp-doctor", "codify", "organize",
    "dataset", "audit", "handoff", "lineage", "checksum",
)
_ASCII_RE = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in _ASCII_TOKENS) + r")\b")


def _keyword_hit(prompt) -> bool:
    """True when the PROMPT ITSELF carries a project-domain token — the marker
    is deliberately NOT consulted. This is the verbosity axis (see
    _emit_checkpoint): a keyword says the user is asking for project work *now*,
    so the full stage list earns its tokens; the marker only says the folder is
    an omp project, which is true of every turn inside it. Fails toward True."""
    try:
        if not isinstance(prompt, str):
            return True
        lowered = prompt.lower()
        if any(tok in lowered for tok in _CJK_TOKENS):
            return True
        if any(tok in lowered for tok in _DOT_TOKENS):
            return True
        return bool(_ASCII_RE.search(lowered))
    except Exception:
        return True


def is_omp_related(prompt) -> bool:
    """True when .omp/ is present (marker OR keyword — NEVER marker-only, so
    NO_OMP_HINT discoverability still surfaces on a keyword match in a fresh
    .omp-less folder), prompt is missing/not-a-string (fail-toward-inject), or
    any project-domain token matches. Never raises -- an internal error
    (including _omp_missing's own probe) also fails toward injection.

    WHETHER to inject, only. HOW MUCH is _keyword_hit's call — the two are
    separate axes, and a marker-only turn injects BRIEF, never nothing."""
    try:
        if not _omp_missing():  # .omp/ present -> marker positive
            return True
        return _keyword_hit(prompt)
    except Exception:
        return True  # gate exception -> inject


def _gate_mode() -> str:
    try:
        v = os.environ.get("OMP_ROUTE_GATE", "off").strip().lower()
    except Exception:
        return "off"
    return v if v in ("off", "observe", "on") else "off"


def _log_would_suppress(prompt) -> None:
    """observe-mode audit trail (rollout §6): one stderr line per turn the gate
    would have suppressed. Best-effort — never raises, never touches stdout."""
    try:
        import hashlib
        digest = (hashlib.sha256(prompt.encode("utf-8", "replace")).hexdigest()[:16]
                  if isinstance(prompt, str) else "none")
        sys.stderr.write(json.dumps({"decision": "would-suppress", "prompt_hash": digest}) + "\n")
    except Exception:
        pass


def _emit_checkpoint(brief: bool = False) -> None:
    # brief only ever fires with .omp/ present, so NO_OMP_HINT resolves to ""
    # there; the expression is left uniform rather than special-cased.
    context = (BRIEF if brief else CHECKPOINT) + (NO_OMP_HINT if _omp_missing() else "")
    out = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(out))


def main() -> int:
    try:
        if _skipped("route"):
            return 0
        mode = _gate_mode()
        if mode == "off":
            _emit_checkpoint()  # today's unconditional inject, unchanged
            return 0
        try:
            payload = json.load(sys.stdin)
        except Exception:
            payload = None
        prompt = payload.get("prompt") if isinstance(payload, dict) else None
        relevant = is_omp_related(prompt)
        if mode == "observe":
            if not relevant:
                _log_would_suppress(prompt)
            _emit_checkpoint()  # observe never suppresses — logging only
            return 0
        if not relevant:
            return 0  # mode == "on": enforce
        # Two axes: `relevant` decided WHETHER (above), _keyword_hit decides
        # HOW MUCH. A marker-only turn (inside an .omp/ folder, prompt says
        # nothing about project work) gets BRIEF; an explicit ask gets the full
        # stage list. Same coverage as before, ~70% fewer chars on the common turn.
        _emit_checkpoint(brief=not _keyword_hit(prompt))
    except Exception as e:  # noqa: BLE001 — fail-open is intentional
        # 에러 맥락을 stderr 로 1줄(디버그용). stdout 계약·exit code 불변 → fail-open. T23.
        sys.stderr.write("[omp_route_emit] swallowed: %r\n" % (e,))
        return 0  # fail-open — never block the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
