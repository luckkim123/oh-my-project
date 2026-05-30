---
name: omp-codify
description: |
  구조·명명 규칙을 성문화·갱신하는 관리 단계 — rules.json(기계) + STRUCTURE.md·NAMING.md(사람)를
  한 번에 함께 써서 드리프트를 막는다. 기존 .omp/rules.json을 입력으로 받아 rule-architect가 변경안을
  제안하고, 규칙이 바뀌면(파일 이동을 유발하는 무거운 결정) 반드시 사람 승인 게이트를 통과한다.
  생성 파이프라인이 아니라 살아있는 .omp/를 갱신하는 루프 — 규칙은 제안만, 강제는 사람이 끊는다.
  Triggers: 규칙 성문화, 규칙 갱신, codify, 구조 규칙 정리, 명명 규칙 정리, rules 갱신,
  STRUCTURE 갱신, NAMING 갱신, 규칙 바꿔, 폴더 규칙 명문화
---

# omp-codify — 구조·명명 규칙 성문화·갱신 (관리 루프 1단계)

<Purpose>
프로젝트의 구조 규칙(어떤 폴더가 무엇을 담는가)과 명명 규칙(파일명 패턴)을 명문화하고 갱신한다. `.omp/rules.json`(audit hook이 읽는 기계 진실)과 `.omp/STRUCTURE.md`·`.omp/NAMING.md`(사람이 읽는 서술)를 **한 번의 패스에서 함께** 갱신해 둘이 절대 드리프트하지 않게 한다. rule-architect에게 위임해 변경안을 받고, 규칙 변경은 사람 승인 게이트를 거친다. 코드의 "lint 규칙 정의" — 무엇을 위반으로 볼지를 먼저 굳히는 단계.
</Purpose>

<Use_When>
- 이미 `.omp/`가 있고(=omp-init 완료) 구조·명명 규칙을 새로 추가/수정/제거할 때
- "이 폴더에는 X만 둔다", "이런 파일명은 이 패턴을 따른다" 같은 규칙을 명문화하고 싶을 때
- 프로젝트가 진화해 기존 rules.json이 실제 구조와 어긋났을 때(재성문화)
- omp-learn이 관찰을 규칙으로 승격한 직후, rule-architect가 만든 규칙안을 정식으로 rules.json에 반영할 때
</Use_When>

<Do_Not_Use_When>
- `.omp/`가 아직 없을 때 → **omp-init 먼저**(부트스트랩 + 프리셋 합성). codify는 init이 만든 rules.json을 *갱신*하는 단계다.
- 규칙은 그대로 두고 위반 *파일*만 찾고 싶을 때 → omp-audit(read-only 판정)
- 규칙 위반 파일을 실제로 *재배치*하고 싶을 때 → omp-organize(이동은 거기서만, safe-fileops 강제)
- 데이터셋 메타데이터(SHA256·split·lineage)를 다룰 때 → omp-dataset(manifest.json 전담)
- 관찰을 규칙 *후보*로 올리는 판단이 필요할 때 → omp-learn(승격 게이트). codify는 승격된 결과를 확정 반영한다.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **드리프트 금지 — .json과 .md는 한 패스에서 함께 쓴다.** rules.json만 고치고 STRUCTURE.md/NAMING.md를 안 고치는(혹은 그 반대) 부분 갱신은 금지. 기계 진실(rules.json)과 사람 서술(.md)이 어긋나면 audit과 사람이 다른 규칙을 보게 된다. 변경은 항상 페어로. (경로 규약: `references/output-layout.md` §"Human .md ↔ Machine .json pairing".)
- ⚠️ **규칙 변경 = 사람 승인 게이트.** 규칙을 바꾸면 다음 omp-organize에서 파일 이동을 유발하는 무거운 결정이다. rule-architect는 **제안만** 하고, 어떤 규칙도 사람 승인 없이 rules.json에 들어가지 않는다(설계 §3 "규칙은 제안만, 강제는 사람").
- ⚠️ **스키마 준수.** rules.json은 `references/schemas/rules.schema.json`을 만족해야 한다(required: omp_version·project·specificity·structure·naming, additionalProperties:false). regex는 Python `re` 문법, severity ∈ {error,warn,info}. 변경 후 스키마 검증을 거치기 전엔 "완료" 아님.
- ⚠️ **codify는 파일을 옮기지 않는다.** 규칙 텍스트(.json/.md)만 쓴다. 사용자 파일 재배치는 omp-organize의 organizer만 하고 `references/safe-fileops.md`를 강제한다. codify에서 이동을 제안받아도 실행은 organize로 넘긴다.
- **specificity 추적.** learn 승격으로 프리셋 규칙이 프로젝트 고유 규칙으로 대체/확장되면 rules.json의 `specificity`(0=순수 프리셋 → 1=완전 고유)를 그에 맞게 올린다. 승격 출처는 `learned_refs[]`에 기록(provenance). 진화 메커니즘은 설계 §4.
- rule-architect는 read-only(disallowedTools=[Write,Edit,NotebookEdit]) — 규칙안을 *설계*해 돌려주고, 실제 `.omp/` 쓰기는 사람 승인 후 이 스킬(컨트롤러)이 수행한다. 자기 설계를 자기 승인하지 않는다.
- 가벼운 결정·패턴(예: "이번에 왜 이 규칙을 추가했나")은 `.omp/wiki/`에 자동 append 가능(승인 불필요, 다음 세션 grep 회수). 무거운 규칙 변경만 게이트(설계 §4 2채널).
</Execution_Policy>

<Steps>
1. **현재 규칙 적재.** `.omp/rules.json`을 읽고(스키마: `references/schemas/rules.schema.json`), 페어인 `.omp/STRUCTURE.md`·`.omp/NAMING.md`를 읽어 현 상태와 specificity·preset_origin·learned_refs를 파악한다. `.omp/`가 없으면 즉시 중단하고 "omp-init 먼저"를 안내(codify는 갱신 단계).
2. **변경 의도 확정.** 무엇을 추가/수정/제거하는가 — 새 디렉토리 역할, 명명 패턴(regex), severity 조정, convention 변경 등. omp-learn에서 넘어온 승격건이면 그 관찰 ID와 근거를 입력에 포함.
3. **rule-architect에게 변경안 위임**(아래 Task 디스패치). 입력: 현 rules.json/STRUCTURE.md/NAMING.md, 변경 의도, 관련 프리셋(`references/presets/<preset_origin>.md`), 승격건이면 learned.md 관찰. 산출: ① 갱신된 rules.json **초안**(스키마 준수), ② 그에 정확히 대응하는 STRUCTURE.md·NAMING.md 본문, ③ diff 요약(어떤 규칙이 추가/변경/삭제되었고 specificity가 어떻게 바뀌는지, 영향받는 파일 개략).
4. ━━━ **GATE — 규칙 변경 승인 (human).** rule-architect의 diff 요약을 사람에게 제시: proceed / revise / abort. 자동 통과 없음. 승인 전엔 어떤 파일도 쓰지 않는다. ━━━
5. **함께 쓰기(드리프트 방지).** 승인되면, **먼저** 기존 `.omp/rules.json`을 `.omp/work/versions/rules-v{NN}-{YYYY-MM-DD}.json`으로 스냅샷한다(편집 전 롤백 지점 — `references/output-layout.md` work layer). 그런 다음 같은 패스에서 셋을 함께 쓴다: `.omp/rules.json`(+ `project.last_codified` 갱신, 필요 시 `specificity`·`learned_refs` 갱신) **그리고** `.omp/STRUCTURE.md`·`.omp/NAMING.md`. 셋 중 하나라도 빠지면 미완. (스냅샷·rules.json 쓰기는 부분쓰기 손상을 막기 위해 `hooks/omp_atomic.py`의 atomic write를 경유한다 — T20.)
6. **검증.** rules.json을 `references/schemas/rules.schema.json`으로 스키마 검증(파이썬 stdlib). regex 컴파일 가능 여부 확인. .md가 .json과 일치하는지 round-trip 확인(규칙 개수·역할·패턴이 양쪽에 모두 반영). 가벼운 결정 메모는 `.omp/wiki/`에 append.
7. **후속 안내.** 규칙이 바뀌었으면 "기존 파일이 새 규칙을 어기는지"는 omp-audit(판정) → 위반 재배치는 omp-organize(safe-fileops 강제)로 이어짐을 안내. codify는 규칙만 굳히고 멈춘다.

**최종 단계 — Task 디스패치 (rule-architect):**
```
Task(
  subagent_type="oh-my-project:rule-architect",
  description="Codify structure/naming rules",
  prompt="""
  현 규칙을 갱신해 변경안을 설계하라. 너는 read-only — rules.json/.md를 직접 쓰지 말고
  완성된 초안 본문 + diff 요약만 돌려준다(사람 승인 후 컨트롤러가 디스크에 쓴다).

  입력:
  - 현 .omp/rules.json (스키마: references/schemas/rules.schema.json)
  - 현 .omp/STRUCTURE.md, .omp/NAMING.md (페어)
  - 변경 의도: <추가/수정/제거할 구조·명명 규칙>
  - 적용 프리셋: references/presets/<preset_origin>.md
  - (omp-learn 승격건이면) .omp/learned.md의 해당 관찰 + ID

  요구:
  1) 갱신된 rules.json 초안 — rules.schema.json 만족(required 필드, additionalProperties:false,
     regex는 Python re, severity∈{error,warn,info}). 변경 출처는 learned_refs[]에 기록.
  2) 그 rules.json과 *정확히 일치*하는 STRUCTURE.md·NAMING.md 본문(드리프트 0).
  3) diff 요약: 추가/변경/삭제된 규칙, specificity 변화(0→1 방향), 영향받는 파일 개략.
  규칙은 제안만 — 강제는 사람이 게이트에서 끊는다. 파일 이동 제안은 organize로 핸드오프.
  """
)
```
</Steps>

<Output>
승인된 변경이 반영된 `.omp/rules.json` + 페어인 `.omp/STRUCTURE.md`·`.omp/NAMING.md`(셋이 함께 갱신되어 드리프트 0) + rule-architect의 diff 요약(추가/변경/삭제 규칙·specificity 변화·영향 파일) + 스키마 검증 통과 증거 + GATE 결정 이력(proceed/revise/abort). 규칙 변경이 기존 파일에 미치는 영향은 "omp-audit로 위반 확인 → omp-organize로 재배치(safe-fileops 강제)" 후속 안내로 마무리(codify 자체는 파일을 옮기지 않음). 가벼운 결정 메모는 `.omp/wiki/`에 자동 누적.
</Output>
