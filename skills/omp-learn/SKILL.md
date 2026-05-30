---
name: omp-learn
description: |
  관찰 → 규칙 승격 (omp의 핵심 진화 게이트) — 운영 중 `.omp/learned.md`에 쌓인 관찰과
  `.omp/wiki/`의 자동 누적 패턴을 rule-architect가 검토해 어느 것이 `rules.json` 규칙으로
  승격될 자격이 있는지 판단한다. 무거운 채널(규칙)은 반드시 사람 승인 게이트를 거치고,
  승격될 때마다 rules.json의 specificity가 올라가 "범용 → 그 프로젝트 특화"가 한 칸 진행된다.
  자동 승격 없음 — 사람이 게이트를 끊는다.
  Triggers: 학습 반영, 규칙 승격, 관찰 정리, learned 검토, 패턴 굳혀, 이거 규칙으로,
  omp learn, promote observation, learn rules, specificity 올려, 진화 게이트
---

# omp-learn — 관찰 → 규칙 승격 (핵심 진화 게이트)

<Purpose>
omp의 비대칭 — "배포 시 범용, 쓸수록 특화" — 이 *기록되는* 단계. 운영 중 `.omp/learned.md`에
쌓인 관찰(예: "이 폴더에서 .pkl은 항상 data/processed/로 들어간다 — 3회 반복")을 rule-architect가
읽고, 어느 관찰이 `rules.json`의 강제 규칙으로 **승격(promote)** 될 자격이 있는지 판단한다.
승격은 실제 파일에 영향을 주는 **한 방향 래칫**(잘못 승격된 규칙은 omp-audit 거짓 위반 폭주 +
organizer의 실제 오이동을 유발)이라 항상 사람 승인 게이트를 거친다. 승격마다 rules.json의
`specificity`가 0(순수 프리셋)→1(완전 특화) 쪽으로 올라간다. rule-architect는 **제안만** 한다 —
규칙을 직접 쓰거나 강제하지 않으며, 사람이 게이트를 끊은 뒤에야 이 스킬이 디스크에 반영한다.
</Purpose>

<Use_When>
- 운영 중 `.omp/learned.md`에 관찰이 충분히 쌓여 "이제 규칙으로 굳힐까?"를 판단할 때
- 같은 패턴(폴더 배치·명명)이 반복 관측돼 강제 규칙으로 올리고 싶을 때
- specificity를 올려 omp가 이 프로젝트에 더 특화되길 원할 때
- omp-pilot이 운영 루프 중 learn 단계를 호출할 때
</Use_When>

<Do_Not_Use_When>
- 아직 `.omp/`가 없으면 → 먼저 `omp-init` (부트스트랩 + 초안 rules.json 승인). learned.md는
  init 이후 운영 중에만 쌓인다.
- 규칙을 *처음 설계*하거나 구조/명명 규칙을 직접 손보는 거라면 → `omp-codify`
  (learn은 *관찰 → 기존 규칙 진화*, codify는 *규칙 성문화·갱신*).
- 가벼운 패턴·결정 메모일 뿐 강제 규칙까지는 아니면 → 승격하지 말고 `.omp/wiki/`에 자동 누적되게
  둔다 (게이트 불필요, 다음 세션 grep 회수). 모든 관찰이 규칙이 되는 건 아니다.
- 규칙 *준수 검증*(PASS/FAIL)이라면 → `omp-audit` (auditor). learn은 규칙을 *만들고*, audit는
  규칙을 *판정*한다 — 서로 다른 lane.
- 파일을 옮기는 거라면 → `omp-organize` (organizer). learn은 규칙 제안까지, 이동은 별도 게이트.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **사람 승인 게이트 절대 강제 (핵심)** — rule-architect는 승격 *제안*만 낸다. 어떤 관찰도
  사람 승인 없이 `rules.json`에 자동 반영되지 않는다. 자동 통과 없음. 승격은 실제 파일에 영향을
  주는 한 방향 래칫이라, 무인 자동은 금지된 행위다.
- ⚠️ **보수적 승격 (한 방향 래칫)** — 증거 기준(반복 관측 ≥ N회 + 반례 없음)을 넘은 관찰만
  승격 후보로 제안. 애매하면 `learned.md`에 남겨 "candidate — 추가 관측/사람 판단 필요"로
  surfacing. 잘못 승격된 규칙 1개의 비용(거짓 위반 + organizer 오이동) > 놓친 규칙 1개의 비용
  (다음 learn에서 다시 올리면 됨).
- ⚠️ **2채널 분리 존중** — *무거운 채널*(규칙: learned.md → 승격 → rules.json)만 이 스킬의
  대상이고 게이트를 거친다. *가벼운 채널*(패턴/결정: `.omp/wiki/*.md` 자동 append)은 게이트
  불필요 — 손대지 않고 둔다. 규칙으로 굳힐 가치가 없는 관찰을 억지로 승격하지 말 것.
- ⚠️ **provenance(출처) 강제** — 승격되는 각 규칙은 그 근거가 된 learned.md 관찰 id를
  `rules.json.learned_refs[]`에 기록한다 (스키마의 추적 필드). 출처 없는 규칙 = 추측 = 두 단계
  뒤 silent 파일 손실.
- ⚠️ **schema is law** — 승격 결과 draft는 `references/schemas/rules.schema.json`에 정확히
  부합해야 한다 (`additionalProperties:false`, `specificity` ∈ [0,1], naming `severity` ∈
  error/warn/info, regex는 Python `re` 문법). 스키마가 담을 수 없는 걸 표현하려면 JSON을 휘지
  말고 schema-change 요청으로 prose에 남긴다.
- ⚠️ **specificity는 정직하게** — 승격된 규칙(scan/learn 유래) 대 프리셋 기본값의 비율에서
  honest하게 계산. 더 특화돼 보이려 부풀리지 않는다.
- **설계 ≠ 강제·검증 분리 (self-approval 3중 금지)** — rule-architect는 read-only
  (`disallowedTools: [Write, Edit, NotebookEdit]`)로 규칙을 *설계*만 하고, 같은 컨텍스트에서
  자기 규칙의 준수를 판정하지 않는다. 준수 판정은 다른 agent(auditor, 별도 컨텍스트, omp-audit)
  몫. 이동은 organizer. learn은 제안·게이트 단계에서 끝난다.
- **diff로 제시** — 기존 `rules.json`이 있으므로 rule-architect는 전체 파일이 아니라 *delta*
  (Added / Changed / Removed 규칙)로 제안해 사람이 변경분만 검토하게 한다.
- 학습 채널·승격 기준의 정본 절차는 `references/learning-protocol.md`(2채널 정의·증거 바),
  `.omp/` 경로 규약은 `references/output-layout.md`가 SSOT.
</Execution_Policy>

<Steps>
1. **SSOT·전제 확인**: 프로젝트 루트와 `<project>/.omp/`가 존재하는지 확인. 없으면 중단하고
   `omp-init`을 먼저 권한다 (learned.md는 init 이후 운영 중에만 쌓이므로). 다음 파일을 읽는다:
   - `<project>/.omp/learned.md` — 승격 대기 중인 관찰 (이 스킬의 입력)
   - `<project>/.omp/rules.json` — 진화시킬 기존 규칙 (blind 교체가 아니라 *evolve*)
   - `<project>/.omp/wiki/*.md` — 가벼운 채널. 규칙으로 굳을 신호가 여기 누적됐는지 grep 회수
     (단 wiki는 게이트 없이 자동 누적되는 영역이라 *읽기*만, 손대지 않는다)
2. **관찰 분류 (2채널 판별)**: learned.md의 각 관찰을 (a) 규칙으로 승격될 후보(무거운 채널 —
   게이트 대상) vs (b) 패턴/결정 메모(가벼운 채널 — wiki로 두고 게이트 불필요)로 가른다. 모든
   관찰이 규칙이 되는 게 아니다 — `references/learning-protocol.md`의 채널 기준 적용.
3. **승격 후보 1차 선별 (증거 바)**: 무거운 채널 후보 각각에 대해 반복 횟수·반례 유무를 본다.
   증거 바(반복 ≥ N회 + 반례 없음)를 넘으면 "승격 제안", 애매하면 "held candidate"로 분류.
   이 1차 판단의 *근거 수집*까지가 컨트롤러 몫이고, *최종 설계·검증*은 다음 단계 agent에 위임.
4. **agent 위임 (승격 판단 + draft 설계)** — rule-architect에 단일 위임. fresh subagent로
   컨트롤러 컨텍스트 오염 방지. 하나의 신중한 합성이므로 **병렬 architect 금지**:

   ```
   Task(
     subagent_type="oh-my-project:rule-architect",
     description="omp-learn: judge learned.md observations for promotion into rules.json",
     prompt="""
     역할: omp-learn 승격 판단. 아래 .omp/ SSOT를 읽고, learned.md 관찰 중 어느 것이
     rules.json 강제 규칙으로 승격될 자격이 있는지 판단해 **제안(diff)** 을 내라. 너는
     read-only다 — rules.json을 직접 쓰지 말고, 파일을 옮기지 말고, 준수를 판정하지 마라.
     사람 승인 게이트가 네 제안과 디스크 사이에 있다.

     입력 (읽을 것):
     - <project>/.omp/learned.md      # 승격 대기 관찰 (occurrence·반례 포함)
     - <project>/.omp/rules.json      # 진화시킬 기존 규칙 (evolve, not replace)
     - <project>/.omp/wiki/*.md       # 가벼운 채널 신호 (읽기만)
     - references/schemas/rules.schema.json   # draft는 여기에 정확히 부합 (additionalProperties:false)
     - references/learning-protocol.md        # 2채널 정의 + 증거 바 (승격 기준의 정본)

     지시:
     - 보수적 승격 (한 방향 래칫): 반복 ≥ N회 + 반례 없음을 넘은 관찰만 승격 제안.
       애매하면 held candidate로 사람에게 surfacing — 자동 승격 금지.
     - 승격되는 각 규칙은 근거 learned.md 관찰 id를 learned_refs[]에 기록 (provenance).
     - specificity를 정직하게 재계산 (scan/learn 유래 대 프리셋 비율) — 부풀리지 말 것.
     - 전체 파일이 아니라 기존 rules.json 대비 **diff** (Added/Changed/Removed)로 제시.
     - schema is law: 담을 수 없는 건 JSON 휘지 말고 schema-change 요청으로 prose에.
     - 출력: 승격/held 결정 + provenance 표 + specificity 근거 + 사람 결정 목록.
       rules.json을 쓰지 말고 제안만. 너는 self-approve 금지 (설계 ≠ 강제·검증 분리).
     """
   )
   ```

   ━━━ **GATE (핵심 승격 게이트 — human)**: rule-architect의 diff·provenance·specificity 근거를
   사람에게 제시하고 결정을 받는다 — promote(승인) / hold(이번엔 보류) / edit(일부만 승격) /
   abort. **자동 통과 절대 없음.** held candidate 중 사람이 "이번에 올려"라고 하면 그것도 여기서
   결정. ━━━
5. **승인분 반영 (게이트 통과 후에만)**: 사람이 승인한 규칙만 이 스킬이 디스크에 쓴다.
   - **먼저** 기존 `.omp/rules.json`을 `.omp/work/versions/rules-v{NN}-{YYYY-MM-DD}.json`으로 스냅샷한다
     (승격은 한 방향 래칫 — 잘못 승격 시 롤백 지점. `references/output-layout.md` work layer).
   - `<project>/.omp/rules.json` — 승인된 규칙 추가/변경, `learned_refs[]`에 출처 관찰 id 기록,
     `specificity` 갱신, `project.last_codified` 갱신. (스키마 부합 재확인. rules.json·스냅샷 쓰기는
     부분쓰기 손상을 막기 위해 `hooks/omp_atomic.py` atomic write 경유 — T20.)
   - 페어 .md 동기 재생성 (output-layout.md의 .md↔.json 페어 규칙): rules.json 구조/명명 규칙이
     바뀌면 `STRUCTURE.md`·`NAMING.md`를 같은 패스에서 갱신해 drift 방지.
   - `<project>/.omp/learned.md` — 승격된 관찰은 "promoted → rules.json (date)"로 마킹, held는
     candidate 상태 유지 (다음 learn에서 재평가).
6. **후속 안내**: 규칙이 바뀌었으므로 `omp-audit`로 새 규칙 준수를 확인하고, 위반이 나오면
   `omp-organize`(safe-fileops.md + dry-run + 이동 전 승인)로 재배치하라고 안내한다. learn 자체는
   파일을 옮기지 않는다.
</Steps>

<Output>
- rule-architect의 **승격 제안 diff** (Added/Changed/Removed 규칙) + provenance 표(각 규칙 →
  learned.md 관찰 id) + specificity 변화 근거 + 사람 결정 목록.
- GATE 결정 이력 (promote/hold/edit/abort).
- 게이트 통과 시: 갱신된 `<project>/.omp/rules.json` (learned_refs[]·specificity·last_codified)
  + 동기 재생성된 `STRUCTURE.md`/`NAMING.md` + 마킹된 `learned.md` 경로.
- held candidate 목록 (다음 learn에서 재평가할 관찰) + "omp-audit로 새 규칙 준수 확인 권장"
  안내. rule-architect는 self-approve 안 함을 명시 — 승격은 사람 게이트가 끊었고, 준수 판정은
  별도 컨텍스트(auditor)의 몫.
</Output>
