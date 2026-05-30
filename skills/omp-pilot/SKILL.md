---
name: omp-pilot
description: |
  프로젝트 폴더 한 줄 지정 → `.omp/` SSOT 전체 오케스트레이션. `.omp/`가 없으면 init을 흡수
  (스캔→귀납+프리셋 합성→초안 rules.json→사람 게이트)해 부트스트랩한 뒤 codify→organize→
  dataset→doc 관리 루프를 게이트마다 사용자 확인하며 엮는다. OMC autopilot의 프로젝트 관리판 —
  생성 파이프라인이 아니라 살아있는 `.omp/`를 갱신하는 루프. `--from <stage>` 재진입 지원.
  Triggers: 이 프로젝트 정리해줘, 폴더 통째로 관리, 프로젝트 셋업, .omp 만들어줘, omp 부트스트랩,
  project pilot, manage this project, end to end 프로젝트, 알아서 정리해줘, omp pilot
---

# omp-pilot — `.omp/` 전체 오케스트레이션 (autopilot 프로젝트 관리판)

<Purpose>
프로젝트 폴더 하나를 받아 `.omp/` SSOT를 부트스트랩·갱신하는 전 단계(부트스트랩 → 규칙 성문화 → 재배치 → dataset 등록 → 문서)를 자동 조율한다. 사용자는 *어느 폴더를 비서에게 맡길지*만 말하고, *어떤 프리셋과 합성할지·어떤 규칙으로 검증할지·무엇을 옮길지*는 하네스가 정한다. omc autopilot의 프로젝트 관리판이되, omp의 본질이 **생성 파이프라인이 아니라 관리 루프**임을 지킨다 — 매번 새 산출물이 아니라 하나의 살아있는 `.omp/`를 계속 갱신한다. 위험(규칙 변경이 파일 이동을 유발)이 크므로 단계마다 게이트 — 완전 자율 아님.
</Purpose>

<Use_When>
- "이 프로젝트 폴더 통째로 관리해줘" 류 end-to-end 요청 — `.omp/`가 아직 없는 새 폴더부터
- 이미 `.omp/`가 있는 프로젝트의 전체 관리 루프를 한 번에 돌리고 싶을 때 (codify→organize→dataset→doc 갱신)
- 상위 메타-하네스(omha)가 프로젝트 관리 작업을 omp에 위임할 때 (자족 진입점)
- 어느 단계부터 시작할지 명확하면 그 단계부터 (`--from`)
</Use_When>

<Do_Not_Use_When>
- 한 단계만 필요하면 → 해당 omp-* skill 직접 (`omp-audit`만, `omp-organize`만 등)
- 규칙 후보 승격만 검토할 때 → `omp-learn` 직접 (pilot 루프에 끼우지 않음 — 승격은 무거운 게이트라 별도 의식)
- 단순 규칙 준수 PASS/FAIL 판정만 → `omp-audit` 직접
- dataset 실제 데이터를 옮기거나 remote push를 기대할 때 → omp는 메타데이터-only. 실제 데이터 이동은 omp의 일이 아님 (DVC/git-lfs 감지 시 위임)
</Do_Not_Use_When>

<Execution_Policy>
- 각 단계는 fresh subagent로 dispatch — 컨트롤러 컨텍스트 보호. 각 단계는 전용 omp-* skill에 위임 (재구현 금지).
- 게이트는 사용자 결정점 — 자동 통과 금지. 위험 = 사용자 파일이 옮겨지는 것이므로 확인 생략 안 함.
- **쓰기 단일 집중 강제**: 파일을 옮기는 agent는 `organizer` 단 하나. 나머지(project-scanner / rule-architect / auditor)는 read-only(`disallowedTools: [Write, Edit, NotebookEdit]`). dataset-curator는 manifest만 쓰고 데이터는 안 옮긴다. 어떤 단계도 self-approve 안 한다(탐지 ≠ 실행 분리: auditor 탐지 → organizer 이동).
- ⚠️ **omp-organize는 절대 auto-move 금지**: `references/safe-fileops.md`를 organizer가 강제 — (1) **dry-run** 먼저(전체 이동 계획 + 실행될 verify 명령을 mutation 0으로 출력), (2) **사람 승인** 후에만 실행, (3) move = `mv`→`find`/`ls`로 목적지 잔류 검증(중요 파일은 SHA-256 비교)→**그 다음에야** 원본 삭제(같은 호흡에 `rm` 금지 — iCloud/Drive 동기화 지연·exFAT AppleDouble 잔재), (4) 삭제는 **trash 경유**(OS 분기: macOS `trash`/`~/.Trash`, Linux `gio trash`/`trash-cli`, Windows recycle bin; trash 없으면 사람 재확인 후에만), (5) sync 폴더에선 **rename 지양**(`diff -rq old new` 부분집합 검증 통과 시에만 구경로 삭제).
- ⚠️ **omp는 사용자 파일을 `.omp/`로 절대 흡수하지 않는다** (`references/output-layout.md` core principle). `.omp/`는 omp가 이 프로젝트에 *대해* 아는 지식(rules/inventory/docs/learning)만 담고, 실제 프로젝트 파일은 제자리에서 in-place 관리된다.
- **범용→특화 합성 + 사람 게이트 명시 (omp 고유)**: init 흡수 단계는 (a) project-scanner의 실제 폴더 귀납 + (b) rule-architect의 최적 프리셋 매칭을 **합성**해 초안 `rules.json`을 만든다 — 절대 자동 확정하지 않고 **사람 승인 게이트**를 거쳐야 `.omp/rules.json`이 된다. 이후 운영 중 특화는 2채널(`references/output-layout.md` §"Two learning channels"): 무거운 채널(`learned.md`→`omp-learn`→rule-architect 승격 판단→**사람 승인 게이트**→`rules.json.specificity` 0→1 상승)과 가벼운 채널(`wiki/*.md` 자동 append, 승인 불필요, 다음 세션 grep 회수). 학습 승격 프로토콜은 `references/learning-protocol.md`가 SSOT(부재 시 `output-layout.md` §learning channels로 fallback) — pilot은 무거운 채널을 자동으로 끼우지 않고 별도 `omp-learn`에 맡긴다.
- **진입 시 priority 컨텍스트 기록 (압축 생존)**: 파이프라인 시작 시 `<project>/.omp/notepad.md`의 `## Priority Context` 섹션에 치명 제약을 적는다 — "사용자 파일을 `.omp/`로 옮기지 않음 / organizer만 이동·safe-fileops 강제·이동 전 dry-run+사람 승인 / dataset은 메타만·데이터 안 건드림 / 규칙 변경=무거운 게이트 + 현재 게이트 위치 + 프로젝트 root 경로". 긴 루프에서 컨텍스트가 압축돼도 안전 프로토콜과 게이트 위치가 항상 복원되도록.
  - **.md가 기본**: 직접 `<project>/.omp/notepad.md`에 write/append. notepad MCP 가용 시 `notepad_write_priority(...)`로 미러 가능(같은 .md 대상, 선택 가속) — 부재해도 .md write로 동일 동작, 에러 아님.
- 단계 산출·진행 상태는 **`<project>/.omp/`** 고정 (검증된 실재 경로 — `PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md` + `rules.json`/`manifest.json` + `learned.md` + `wiki/`; `.omp/state`·`sessions/{sid}` 같은 미검증 하위 세그먼트는 박지 않는다). codify/dataset이 .json을 바꾸면 페어 .md를 같은 pass에 재생성해 drift 0 유지.
  - ⚠️ **30s 트랩 (향후 state MCP 도입 시에만 — 지금은 미적용)**: state MCP를 쓰게 되면 단계 핸드오프 *직전*에 `state_clear`를 호출하지 말 것(30s간 stop-hook 비활성화로 루프가 조용히 끊긴다). 비종료 핸드오프는 `state_write(active=false)`로, `state_clear`는 *terminal에서만*. **현재는 state MCP를 실호출하지 않으므로(.md/`.omp/` 파일이 기본) 순수 미래 대비 메모.**
</Execution_Policy>

<Steps>
0. **`.omp/` 존재 확인 → 분기** (pilot 첫 동작):
   - `<project>/.omp/rules.json`이 **없으면** → **init 흡수 분기**: omp-init을 이 pilot 안에서 1회 부트스트랩으로 실행한다 (omd docs-pilot이 intake를 흡수하듯).
     - (a) project-scanner가 실제 폴더 트리·확장자 분포·명명 패턴을 **귀납** (read-only, 추측 0)
     - (b) rule-architect(opus)가 `references/presets/*.md`(python-ml/web-app/research-lab/monorepo/johnny-decimal/para/generic) 중 최적 프리셋을 매칭
     - (c) (a)+(b) **합성** → 초안 `rules.json`(`references/schemas/rules.schema.json` 준수) + `manifest.json`(`references/schemas/manifest.schema.json`) + 사람용 `PROJECT.md`/`STRUCTURE.md`/`NAMING.md` 초안
     ━━━ **GATE 0: 초안 rules.json 승인 (human)** — proceed/revise/abort. `.omp/` 커밋 여부(`.gitignore` 힌트)도 여기서 한 번 묻고 기록 ━━━
   - `<project>/.omp/rules.json`이 **이미 있으면** → init은 "재초기화?" 경고만 하고 **skip**, 기존 `.omp/`를 입력으로 1번 단계(codify)부터 관리 루프 시작.
1. **codify**: omp-codify → 구조·명명 규칙 성문화·갱신 (`rules.json` + `STRUCTURE.md`/`NAMING.md`, 페어 동기화). dispatch: rule-architect.
   - *규칙이 GATE 0 직후 그대로이고 갱신할 변경이 없으면* skip.
   ━━━ **GATE 1: 규칙 변경 승인 (human)** — 변경 diff 제시, proceed/revise/abort ━━━
2. **organize**: omp-organize → 규칙 위반 탐지(auditor) → 재배치 제안·실행(organizer). dispatch: auditor(탐지) → organizer(이동).
   - ⚠️ `references/safe-fileops.md` 강제 + **dry-run 먼저** + **이동 전 사람 승인**. 위반 없으면 "정리 불필요" 보고 후 skip.
   ━━━ **GATE 2: 이동 계획 승인 (human)** — dry-run 출력(from→to + 위반 규칙 인용) 확인, approve/revise/abort. 승인 전 어떤 파일도 mutation 0 ━━━
3. **dataset**: omp-dataset → dataset 등록·SHA256·split·lineage 추적 (`manifest.json` + `DATASETS.md`). dispatch: dataset-curator.
   - ⚠️ **메타데이터-only**: 실제 데이터 복사·이동·remote push 안 함. `.dvc/`·git-lfs 감지 시 "DVC 관리 중 — manifest는 메타만 미러" 위임. dataset이 없으면 skip.
   ━━━ **GATE 3: dataset 등록 확인 (human)** — manifest 엔트리 확인, confirm/revise ━━━
4. **doc**: omp-doc → `.omp/` 사람용 문서 생성·갱신 (`PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md`). dispatch: project-scanner(인벤토리 공급). (omp-doc은 `.omp/` 문서 중심 — 루트 README 생성기가 아니다.)
   - 문서가 최신이면 skip. (게이트 없음 — 사람용 문서는 가벼운 산출)
5. **terminal**: 관리 루프 1회전 완료 보고. `.omp/`의 갱신된 SSOT 경로 일람 + 각 게이트 결정 이력 + 다음 권장 행동(`omp-audit`로 준수 재확인 / 관찰 누적 시 `omp-learn`으로 승격 검토).
   - ⚠️ omp는 **사용자 파일을 정리·삭제하지 않는다** — pilot의 terminal은 `.omp/` 지식 갱신 보고일 뿐, 사용자 자산 cleanup은 명시적 `omp-organize`(safe-fileops 강제) 경로로만.

> **`--from <stage>` 진입점**: 중간 단계부터 시작 가능 — `init|codify|organize|dataset|doc`. `.omp/`가 이미 있으면 0번 분기는 자동으로 codify부터(init skip). 예: `--from organize`면 기존 `rules.json`을 입력으로 위반 탐지(organize)부터, `--from dataset`이면 dataset 등록부터. 모든 진입은 해당 단계의 게이트를 그대로 거친다(게이트 우회 없음).

6. **Task 위임 (각 단계의 최종 동작)**: 위 단계들은 fresh subagent로 dispatch된다. omp-init 흡수 분기의 귀납 채널(0-(a)) 및 omp-doc 인벤토리(4번)는 read-only project-scanner에 위임한다:

```
Task(
  subagent_type="oh-my-project:project-scanner",
  description="<project> 폴더 read-only 인벤토리 + de-facto 구조·명명 패턴 귀납",
  prompt="""
프로젝트 root: <project absolute path>
임무 (read-only — 절대 쓰거나 옮기지 마라):
1. 디렉토리 트리 인벤토리: 깊이, 디렉토리별 파일 수, 확장자 분포, 대략 크기.
   비-소스/무시 영역(.git/ node_modules/ .venv/ __pycache__/ .omp/)을 rules.json.ignore 후보로 분리.
2. de-facto 구조 귀납: 각 디렉토리가 *사실상* 하는 역할 + 관찰 증거(예: 'data/raw/ 12개 전부 .csv → 원본 데이터 전용').
3. 명명 패턴 귀납: basename 반복 규칙 → 후보 Python re 정규식(rules.schema.json의 naming.patterns[].regex 형식)
   + 만족 예시 + 위반 예시 + 신뢰도(N/M 일치, 강/약).
4. 외부 관리 신호 보고: .dvc/ git-lfs(.gitattributes lfs 항목) — dataset-curator의 '메타만 미러' 판단 입력.
제약: 추측·상상 0건, 실제 트리/grep 결과에만 묶을 것. 규칙 *설계*나 프리셋 합성은 하지 마라(그건 rule-architect).
PASS/FAIL 판정 금지(그건 auditor). .omp/ 어떤 파일도 쓰지 마라 — 출력은 보고서(텍스트)뿐.
출력: 인벤토리 + 귀납 구조 패턴(증거 첨부) + 귀납 명명 패턴(정규식+예시+신뢰도) + ignore 후보 + 외부 관리 신호.
"""
)
```

dispatch 후: project-scanner의 귀납 보고를 rule-architect(opus)에게 넘겨 프리셋과 합성 → 초안 rules.json → GATE 0. 이후 단계(codify/organize/dataset)는 각 omp-* skill이 rule-architect / auditor→organizer / dataset-curator를 dispatch한다 (pilot은 게이트와 핸드오프만 조율, agent 재구현 금지).
</Steps>

<Output>
관리 루프 1회전의 산출 = **갱신된 `<project>/.omp/` SSOT** (생성 파이프라인의 "새 산출물"이 아니라 살아있는 지식의 갱신):
- 사람용: `PROJECT.md` / `STRUCTURE.md` / `NAMING.md` / `DATASETS.md`
- 기계용: `rules.json`(specificity 추적) / `manifest.json`(SHA256·split·lineage)
- 학습: `learned.md`(승격 대기) / `wiki/`(자동 누적)

경로 규약은 `references/output-layout.md`가 SSOT. + GATE 0~3 결정 이력 + organize의 이동 로그(실제 이동된 from→to, dry-run 거쳐 승인된 것만) + dataset 외부 관리 위임 여부(.dvc/git-lfs) + 사람 확인 필요 잔여(rule-architect가 보류한 약한 패턴·승격 후보) + 다음 권장 단계(`omp-audit` 재확인 / `omp-learn` 승격 검토). 사용자 파일은 그대로 제자리(`.omp/`로 흡수 안 됨), self-approve 안 함 명시.
</Output>

<Self_Sufficiency>
이 스킬은 자족적 진입점이다. 상위 메타-하네스(omha)가 프로젝트 관리 작업을 "omp omp-pilot에 위임" 한 줄로 부를 수 있도록, 외부 컨텍스트 없이 프로젝트 root 경로만으로 `.omp/` 부트스트랩(init 흡수)부터 관리 루프 전 단계를 게이트와 함께 완주한다.
</Self_Sufficiency>
