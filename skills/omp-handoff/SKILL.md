---
name: omp-handoff
description: |
  위임 직전 1회 실행하는 브리핑 조립기 — 형제 하네스(oms·omd·omx·omc·superpowers 등)에 작업을
  맡기기 전, 이 프로젝트에 대한 지식을 Anthropic multi-agent 4요소 패킷(Objective / Output format
  / Tool·source guidance / Boundaries)으로 조립해 전수한다. 세션 내 브리핑 블록 + 감사용
  `.omp/work/handoffs/YYYY-MM-DD-<target>.md` 사본 + ledger `handoff_prepared` 이벤트,
  세 산출물을 한 pass 에서 만든다. 참조만 담고 원문 전체를 복붙하지 않는다.
  Triggers: 위임 브리핑, 인수인계, 맡기기 전 브리핑, 형제 하네스에 넘겨, handoff,
  delegation briefing, brief the sibling, hand off to, prepare a briefing
---

# omp-handoff — delegation-briefing assembler (§11.2)

<Purpose>
위임 직전 1회 실행하는 브리핑 조립기. 인자는 대상 레인(oms·omd·omx·omc·superpowers 등) +
임무 한 줄. omha 가 어떤 LANE 으로 위임할지 고르는 계층은 이 스킬로 바뀌지 않는다(§11.3 불변) —
`omp-handoff` 는 위임 **결정 후**, 형제 스킬이 발동하기 **직전**에 끼는 선택적 준비 단계다.
목적은 형제 하네스가 매번 이 프로젝트를 처음부터 다시 파악하지 않도록, omp 가 이미 아는 것을
압축해 건네는 것.
</Purpose>

<Use_When>
- "omx 에 넘기기 전에 브리핑 준비해줘" — 실험 분석을 omx 에 맡기기 전
- "oms 한테 이 섹션 초안 맡길 건데 인수인계 자료 만들어줘"
- 형제 하네스(oms·omd·omx·omc·superpowers)를 호출하기 직전, 이 프로젝트 지식을 넘겨야 할 때
</Use_When>

<Do_Not_Use_When>
- 위임할 대상 레인이 아직 정해지지 않음 → 그건 omha 의 LANE 판단 몫, `omp-handoff` 는 관여하지 않음.
- 단순 현황 보고 → `omp-brief` (BRIEF.md 재생성, 위임 목적 아님).
- 위임 결과를 다시 흡수하는 것 → `omp-log` (반환은 이 스킬이 아니라 omp-log 목적지로 흡수, 강제 아님).
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **패킷 4요소** (Anthropic multi-agent 실증 골격) — 각 요소와 omp 원천은 다음 표대로 채운다:

| 요소 | 원천 |
|:--|:--|
| Objective (임무 + 완료 기준 1줄) | 사용자 인자 + `todo.txt`/`raid.md` 관련 항목 |
| Output format · 산출물 위치 계약 | `output-layout.md` + NAMING/STRUCTURE 의 경계 결정 |
| Tool·source guidance (어디를 읽어라) | PROJECT.md 1줄 + wiki grep-by-topic + `derive_status(root)["sources"]` read-map |
| Boundaries (하지 말 것) | rules.json 관련 규칙 + raid.md open blocker 발췌 |

- ⚠️ **참조만, 복붙 금지**: 브리핑은 경로와 발췌 요지만 담고, 원문 전체(PROJECT.md·rules.json·
  wiki 문서 전체 등)를 인라인하지 않는다. 위임받는 스킬이 필요하면 그 경로를 직접 연다.
- ⚠️ **wiki 는 scope/audience 필드를 만들지 않는다** — grep-by-topic 으로 관련 wiki 문서를 찾는
  것이 먼저이고, 이 스킬이 wiki 스키마를 확장하지 않는다.
- ⚠️ **세 산출물, 한 pass**:
  1. 세션 내 브리핑 블록 — 위임받는 스킬이 같은 컨텍스트에서 바로 소비(D12: IPC 아님, 파일 왕복 없음).
  2. `.omp/work/handoffs/YYYY-MM-DD-<target>.md` — 감사용 사본. retention 10, 쓰는 이 pass 에서
     자기 폴더를 trim한다(output-layout.md 의 work-layer retention 관례를 그대로 따름).
  3. ledger `handoff_prepared {"target": <lane>, "topic": <slug>}` — `hooks/omp_secretary.py` 의
     `append_ledger(root, event)` 를 `python3 -c` 로 호출(기계 append, 이 스킬이 JSON 을 직접
     손으로 조립하지 않는다).
- ⚠️ **반환 대칭**: 위임 결과는 압축 요지(1–2천 토큰)로 받아 `omp-log` 목적지에 흡수한다(강제
  아님 — R5). `omp-handoff` 자신은 반환을 처리하지 않는다.
</Execution_Policy>

<Steps>
1. **인자 확인**: 대상 레인(예: `oms`, `omd`, `omx`, `omc`, `superpowers`)과 임무 한 줄을 받는다.
   레인이 불명확하면 한 줄로 확인 질문.
2. **패킷 4요소 조립**: 위 표의 원천에서 각 요소를 채운다.
   - `derive_status(root)["sources"]` 로 read-map(`{path, kind, open}`) 을 얻어 Tool·source
     guidance 에 `읽을 곳: <path> (<kind>, open N)` 형태로 넣는다.
   - `raid.md` 의 open 항목을 발췌해 Boundaries 에 붙인다(전체 파일 인라인 금지 — 관련 줄만).
3. **세션 내 브리핑 블록 출력**: 4요소 표 형태로 응답에 직접 작성 — 위임받는 스킬이 이 턴에서
   바로 읽는다.
4. **감사 사본 기록**: `.omp/work/handoffs/YYYY-MM-DD-<target>.md` 에 같은 내용을 쓴다. 기존
   파일이 10개를 넘으면 가장 오래된 것부터 trash 로 정리(같은 pass).
5. **ledger 기록**:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, 'hooks')
   from omp_secretary import append_ledger
   append_ledger('<project_root>', {'event': 'handoff_prepared', 'target': '<lane>', 'topic': '<slug>'})
   "
   ```
6. **보고** — see Output.
</Steps>

<Output>
- 대상 레인 + 임무 한 줄
- 조립된 4요소 브리핑 블록 (세션 내 소비용, 이 응답에 그대로 포함)
- 기록된 파일 경로: `.omp/work/handoffs/YYYY-MM-DD-<target>.md`
- retention trim 여부 (10개 초과 시 trash 로 넘긴 파일 수)
- ledger `handoff_prepared` 이벤트 기록 확인 (target/topic 값 인용)
</Output>

<Examples>
- **예시 1** — "omx 에 실험 분석 맡기기 전 이 프로젝트 지식 패킷 준비해줘": target=`omx`,
  topic=`exp-analyze-2026-07`. Objective="런 A/B 비교 리포트", Tool guidance 에
  `derive_status(root)["sources"]` read-map 과 관련 wiki grep 결과, Boundaries 에 raid.md 의
  open blocker(예: "GPU 메모리 제약") 발췌.
- **예시 2** — "oms 에 논문 섹션 초안 맡기기 전 브리핑": target=`oms`, topic=`section3-draft`.
  Objective="§3 실험 섹션 초안", Output format 에 `sections/*.tex` 경로 계약, Tool guidance 에
  PROJECT.md 한 줄 + 관련 wiki 문서 경로.
</Examples>
