---
name: omp-doctor
description: |
  omp 설치·전제 자가진단 — hooks 등록·python3 가용성·reference 카드 존재를 점검해
  "omp 가 이 환경에서 작동할 준비가 됐나"를 PASS/WARN/FAIL 로 보고한다. omp-audit 이
  *.omp 가 이미 있다고 가정하고* 규칙 준수를 보는 것과 달리, doctor 는 그 이전의 설치
  층을 본다(audit 과 중복되는 rules.json 스키마 검증은 하지 않는다). read-only, 자동 수정 없음.
  Triggers: omp 진단, doctor, 설치 점검, omp 작동 확인, 왜 안 되지, hooks 확인,
  omp-doctor, 설정 점검, 환경 점검, omp 안 돼
---

# omp-doctor — 설치·전제 자가진단 (read-only)

<Purpose>
omp 가 *작동할 준비가 됐는지*를 본다. `omp-audit` 은 `.omp/` 가 이미 있다고 전제하고
프로젝트 폴더가 규칙을 지키는지(구조/명명/dataset)를 판정하지만, doctor 는 그 **이전 층** —
hook 이 설치됐나, python3 이 있나, omp 자신의 reference 카드가 온전한가 — 를 점검한다.
"omp 를 깔았는데 STAGE 줄이 안 뜬다 / 스킬이 카드를 못 찾는다" 같은 *설치* 문제를 잡는 게 목적이다.
</Purpose>

<When_To_Use>
- omp 를 막 설치했고 제대로 붙었는지 확인하고 싶을 때
- omp 스킬·hook 이 기대대로 동작하지 않아 원인이 *설치/환경* 인지 *규칙* 인지 가르고 싶을 때
- 다른 머신(특히 Windows/Linux)에서 omp 가 처음 작동하는지 크로스플랫폼 점검할 때
</When_To_Use>

<When_Not_To_Use>
- 프로젝트 폴더가 `.omp/rules.json` 규칙을 지키는지 보고 싶으면 → `omp-audit` (그건 규칙 준수 게이트).
  doctor 는 rules.json **스키마 검증을 하지 않는다** — audit 과 중복이라 의도적으로 제외(audit 소관).
- `.omp/` 를 처음 만들고 싶으면 → `omp-init`. doctor 는 진단만 하지 `.omp/` 를 만들지 않는다.
- 규칙을 바꾸고 싶으면 → `omp-codify`.
</When_Not_To_Use>

<Execution_Policy>
- **read-only**: doctor 는 어떤 파일도 쓰거나 고치지 않는다. 진단 결과(PASS/WARN/FAIL + 증거 +
  고치는 법 1줄)만 보고한다. 자동 수정 없음(설치 수정은 사용자가 의식적으로).
- **stdlib·크로스플랫폼**: 점검은 python3 stdlib + 표준 CLI 만으로 한다(`python3 --version`,
  `pathlib` 존재 확인). OS 분기는 `platform`/`os.name`. 절대경로·`~` 하드코딩 금지.
- **fail-soft**: 한 항목 점검이 실패해도 다른 항목은 계속 본다(한 FAIL 이 전체 진단을 멈추지 않음).
- **audit 중복 제외**: rules.json/manifest.json *스키마 유효성·specificity 정합* 은 doctor 가 보지
  않는다(omp-audit Step 1·2 소관). doctor 의 .omp 관련 점검은 "파일이 존재하는가" 수준까지만.
</Execution_Policy>

<Steps>
1. **hooks 설치 점검**:
   - `hooks/omp_route_emit.py`·`hooks/omp_verify_emit.py` 파일이 존재하는가.
   - `.claude-plugin/plugin.json`(또는 설치 환경의 hooks 등록)에 두 hook 이 UserPromptSubmit /
     PostToolUse 로 등록돼 있는가. (등록 안 됐으면 STAGE 줄·integrity 리마인더가 안 뜬다 → WARN.)
   - 실제 동작 확인(선택): `echo '{"prompt":"x"}' | python3 hooks/omp_route_emit.py` 가 exit 0 +
     `STAGE(project)` 를 담은 JSON 을 내는가.
2. **python3 가용성 점검**:
   - `python3 --version` 이 성공하는가(hook·헬퍼의 런타임 전제). 3.x 인가.
   - `hooks/omp_atomic.py` 의 atomic write 가 동작하는지(SSOT 쓰기 안전 전제, T20) — import 가능 여부.
3. **reference 카드 온전성 점검**:
   - `references/` 의 4 카드(`safe-fileops.md`·`output-layout.md`·`omc-backport-analysis.md`·
     `learning-protocol.md`) 가 모두 존재하는가.
   - `references/presets/` 에 6 프리셋, `references/schemas/` 에 2 스키마(`rules.schema.json`·
     `manifest.schema.json`) 가 존재하는가. (스키마 *내용 검증* 은 안 함 — 존재 여부만, audit 중복 제외.)
4. **종합 판정 보고**: 각 항목을 PASS / WARN / FAIL + 증거(무엇이 없거나 실패했나) + 고치는 법
   1줄로 보고한다. 전체 한 줄 요약("omp 설치 OK" / "hook 미등록 — 재설치 필요" 등)으로 끝낸다.
   ⚠️ 어떤 항목도 자동으로 고치지 않는다 — 사용자가 고칠 수 있게 *알려주는* 것이 doctor 의 역할.
</Steps>

<Output>
- 3개 축(hooks / python3 / reference 카드) 각각 PASS|WARN|FAIL + 증거 + 1줄 fix.
- 전체 한 줄 요약(작동 준비 됐나 / 무엇을 고쳐야 하나).
- ⚠️ rules.json 규칙 준수는 이 보고에 없음 — 그건 `omp-audit` 로 (역할 분리 명시).
</Output>
