---
name: omp-doc
description: |
  사람용 프로젝트 문서 생성·갱신 — `.omp/PROJECT.md`·`STRUCTURE.md`·`NAMING.md`·`DATASETS.md` 같은
  사람이 읽는 .md 를 project-scanner 인벤토리를 근거로 새로 쓰거나 최신화한다. readme-project 의
  "코드베이스를 읽고 전문적 문서를 만든다" 정신을 흡수하되, omp 는 repo 루트가 아니라 `.omp/` 문서
  중심 — 산출물은 프로젝트가 아니라 프로젝트에 *대한* 지식이다. 추측 없이 실제 트리만 반영. omp 4단계.
  Triggers: 문서 갱신, PROJECT.md 써줘, 프로젝트 문서, 개요 정리, STRUCTURE.md 갱신, 폴더 설명 써줘,
  document the project, update project docs, write PROJECT.md, refresh .omp docs
---

# omp-doc — 사람용 프로젝트 문서 생성·갱신 (omp 4단계)

<Purpose>
프로젝트를 처음 보는 사람(또는 미래의 나)이 한 화면에서 "이게 무슨 프로젝트이고, 폴더가 어떻게 짜여
있고, 어떻게 이름 붙이고, 데이터가 무엇인가"를 알 수 있게 하는 **사람용 .md 문서**를 만든다·갱신한다.

대상은 `.omp/`의 human 문서 4종 — `PROJECT.md` / `STRUCTURE.md` / `NAMING.md` / `DATASETS.md`.
이들은 모두 project-scanner 의 실제 폴더 인벤토리를 근거로 쓰여야 한다(추측 금지). readme-project 가
repo 루트의 README 를 만들 듯 omp-doc 은 같은 "코드베이스 정독 → 전문적 문서" 정신을 따르되, 산출물은
프로젝트 자체가 아니라 `<project>/.omp/` 안의 *프로젝트에 대한 지식*이다.

⚠️ **본질적 구분 — 사람용 .md ↔ 기계용 .json은 페어지만 권한이 다르다.** omp-doc 은 *사람용 .md* 의
서술(narrative)을 쓰는 스킬이다. `STRUCTURE.md`/`NAMING.md`의 강제 규칙 SSOT 는 `rules.json`이고 그건
`omp-codify`(rule-architect) 영역, `DATASETS.md`의 SSOT 는 `manifest.json`이고 그건 `omp-dataset`
(dataset-curator) 영역이다. omp-doc 은 **이미 확정된 .json 을 사람이 읽기 좋게 풀어쓰는 서술 갱신**을
하지, 규칙·인벤토리 자체를 새로 *결정*하지 않는다. 결정이 필요하면 codify/dataset 로 보낸다.
</Purpose>

<Use_When>
- `.omp/`가 이미 존재하고(=init 완료) 사람용 문서를 새로 쓰거나 최신화할 때
- 폴더가 한참 바뀌어 `STRUCTURE.md`/`PROJECT.md`가 현실과 어긋났을 때 ("문서 갱신해줘")
- 처음 보는 사람에게 "이 프로젝트가 뭔지" 한 화면 개요(`PROJECT.md`)가 필요할 때
- codify/dataset 가 `rules.json`/`manifest.json`을 바꾼 직후, 페어인 .md 서술을 동기화할 때
- 특정 문서만 콕 집어 ("`NAMING.md`만 다시 써줘")
</Use_When>

<Do_Not_Use_When>
- `.omp/`가 아직 없을 때 → `omp-init` 먼저 (부트스트랩이 PROJECT/STRUCTURE/NAMING 의 *초안*을 이미 깐다)
- 강제 규칙 자체를 바꾸려 할 때 → `omp-codify` (rule-architect, `rules.json` SSOT). omp-doc 은 규칙을
  *서술*만 하지 *결정*하지 않는다.
- dataset 을 등록·체크섬·split·lineage 추적할 때 → `omp-dataset` (dataset-curator, `manifest.json` SSOT).
  omp-doc 의 `DATASETS.md`는 manifest 의 사람용 뷰일 뿐, manifest 를 새로 쓰지 않는다.
- 규칙 위반을 탐지·재배치할 때 → `omp-audit`(탐지) → `omp-organize`(이동). omp-doc 은 파일을 옮기지 않는다.
- repo 루트의 배포용 README 가 목적이고 `.omp/` 지식과 무관할 때 → user-scope `readme-project` 스킬
  (omp 는 .omp/ 문서 중심이지 루트 README 생성기가 아니다. 다만 PROJECT.md 를 근거로 README 초안을
  뽑아달라는 요청이면 그 변환은 omp-doc 이 보조할 수 있다 — 단 출력은 .omp/ 가 SSOT.)
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **추측 금지 — 실제 트리만.** 모든 서술은 project-scanner 가 실측한 폴더·파일·확장자·명명 패턴에
  근거해야 한다. "보통 이런 프로젝트는…" 식 일반론으로 문서를 채우지 않는다. 인벤토리에 없는 폴더·역할을
  지어내면 그 문서는 거짓이 된다(readme-project 의 "코드베이스 정독" 원칙과 동일).
- ⚠️ **읽기전용 dispatch.** 이 단계가 부르는 project-scanner 는 read-only agent
  (`disallowedTools: [Write, Edit, NotebookEdit]`). 인벤토리만 받아오고, `.omp/*.md` 파일 *작성*은
  컨트롤러(이 스킬)가 한다. 사람용 .md 는 코드·데이터를 옮기지 않으므로 organizer 가 필요 없다.
- ⚠️ **.json 은 안 건드린다.** omp-doc 은 `rules.json`/`manifest.json`을 절대 수정하지 않는다(읽기만).
  .md 서술이 .json 과 어긋나 보이면 → .json 이 진실이므로 .md 를 .json 에 맞춰 갱신하거나, .json 쪽이
  틀렸다면 codify/dataset 로 핸드오프(여기서 .json 을 고치지 않는다). 페어 동기화 규칙은
  `references/output-layout.md` "Human .md ↔ Machine .json pairing" 절이 SSOT.
- **In-place 갱신 + 변경 요약.** 기존 .md 가 있으면 통째로 덮어쓰기 전에 무엇이 바뀌는지(추가/삭제된
  폴더, 새 명명 패턴 등) 한 줄 diff 요약을 사람에게 보여주고 진행. 사람용 문서는 사용자의 손글씨가
  섞여 있을 수 있으니 — 큰 구조 변경이면 확인을 받는다.
- **wiki 자동 누적(가벼운 채널).** 문서를 쓰다 발견한 비자명한 패턴·결정("이 repo 는 `tests/`가
  `src/` 미러 구조", "`legacy/`는 동결됨")은 `.omp/wiki/*.md`에 자동 append — 승인 게이트 없음,
  다음 세션 grep 회수용. 규칙으로 *승격*할 만한 관찰이면 자동 강제하지 말고 `.omp/learned.md`에 후보로
  적어 `omp-learn` 게이트로 넘긴다. 두 채널 구분은 `references/learning-protocol.md` 참조.
- **단일 dispatch.** 인벤토리는 여러 폴더를 한 번에 스캔하면 되므로 project-scanner 1 회 dispatch 로
  충분하다. 문서 4종을 따로 스캔하려고 병렬 fan-out 하지 않는다(같은 트리를 중복으로 읽을 뿐).
- **게이트 없음(판정 단계 아님).** omp-doc 은 사람용 문서를 쓰는 가벼운 단계로, 파일 이동·규칙 강제 같은
  위험 동작이 없어 승인 게이트가 없다(`omp-organize`/`omp-learn`과 대비). 단 큰 구조 변경 시의 위 확인은
  예의상의 한 줄 확인이지 정식 게이트가 아니다.
</Execution_Policy>

<Steps>
1. **대상 문서 확정.** 사용자가 어떤 문서를 원하는지 파악 — 전체 4종(`PROJECT.md`/`STRUCTURE.md`/
   `NAMING.md`/`DATASETS.md`) 갱신인지, 특정 하나인지. `.omp/`가 실재하는지 먼저 확인
   (없으면 `omp-init` 으로 안내하고 중단). 경로 규약은 `references/output-layout.md`가 SSOT.
2. **기존 SSOT 읽기.** `.omp/`의 기존 .md 4종 + 페어인 `.omp/rules.json`·`.omp/manifest.json`을 읽어
   현재 상태를 파악한다. 스키마는 `references/schemas/rules.schema.json`·
   `references/schemas/manifest.schema.json`. .md 서술은 이 .json 들과 *일치*해야 한다(.json 이 진실).
   `.omp/wiki/`도 grep 해 이전 세션이 남긴 패턴·결정을 회수한다.
3. **무엇이 바뀌었나 가설.** 기존 문서가 현실과 어긋난 지점을 짚는다(예: 문서엔 없는 새 폴더, 사라진
   디렉토리, 새 확장자 군집). 이 가설을 다음 스캔으로 검증한다 — 문서를 *고쳐쓰기* 전에 *무엇을* 고칠지부터.
4. **변경 요약 예고(기존 문서가 있을 때).** 통째로 덮어쓰기 전, 추가/삭제될 폴더·역할·명명 패턴을 한 줄
   diff 로 사용자에게 보여준다. 큰 구조 변경이면 진행 확인을 받는다(사람 손글씨 보호).
5. **문서 작성·갱신(컨트롤러가 .md write).** project-scanner 인벤토리를 근거로 .md 를 쓴다:
   - `PROJECT.md` — 한 화면 개요(무슨 프로젝트, 핵심 목적, 진입점). readme-project 의 hero/value-prop
     정신을 .omp/ 안으로 흡수: 스캔 가능성 > 완전성.
   - `STRUCTURE.md` — 폴더 트리 + 각 디렉토리 역할. `rules.json`의 구조 규칙을 사람용 서술로 풀어쓴다.
   - `NAMING.md` — 명명 규칙 + 실제 예시. `rules.json`의 naming 규칙과 일치시킨다.
   - `DATASETS.md` — `manifest.json` datasets[] 의 사람용 카탈로그 뷰(체크섬·split·lineage 요약).
   페어 .json 과 어긋나면 .json 에 맞춘다. 비자명 패턴은 `.omp/wiki/`에, 규칙 승격 후보는
   `.omp/learned.md`에 분리 기록(`references/learning-protocol.md`).
6. **Task dispatch (인벤토리 수집 — 항상 마지막 단계의 핵심).** 위 작성·갱신의 *근거*가 되는 실측
   인벤토리는 read-only `project-scanner`에게 위임한다. 이 스킬은 인벤토리를 받아 .md 를 쓰는 컨트롤러다:

   ```
   Task(
     subagent_type="oh-my-project:project-scanner",
     description="Inventory project tree for .omp human docs",
     prompt="""
     <project>의 폴더 트리·파일 인벤토리를 실측해 omp-doc 의 사람용 문서 작성 근거로 돌려줘.
     - 폴더 트리(깊이별 디렉토리 + 각 폴더의 대표 파일 군집·확장자 분포)
     - 명명 패턴 귀납(접두사/접미사/케이스/번호체계 — 실제 파일명에서만, 일반론 금지)
     - 진입점 후보(README/main/entrypoint/manifest 류 실재 파일)
     - 기존 .omp/rules.json·manifest.json 과 현실의 어긋남(문서엔 있으나 없는 폴더, 그 반대)
     - 비자명 구조 관찰(미러 구조, 동결 폴더, 데이터 디렉토리 위치 등)
     ⚠️ 추측 금지 — 실제 트리에 있는 것만. 없는 폴더·역할 지어내지 말 것.
     ⚠️ read-only — 파일을 만들거나 옮기지 말 것(.omp/*.md 작성은 omp-doc 컨트롤러가 한다).
     출력: 폴더별 역할 표 + 명명 패턴 목록 + 진입점 + .json↔현실 diff + 비자명 관찰.
     """
   )
   ```

   scanner 가 인벤토리를 돌려주면 → 5단계 작성을 수행하고, 페어 .json 과의 동기화·wiki 누적·learned 후보
   분리를 마친 뒤 산출 경로를 보고한다(omp-doc 자체는 PASS/FAIL 판정을 내지 않는다 — 그건 `omp-audit`).
</Steps>

<Output>
갱신·생성된 `.omp/` 사람용 .md 경로 목록(`PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md` 중
작업한 것) + 직전 대비 변경 요약(추가/삭제 폴더·명명 패턴) + 페어 .json 과의 동기화 결과(어긋남을
.md 쪽으로 맞췄는지, 또는 codify/dataset 로 핸드오프 필요한 .json 불일치) + `.omp/wiki/`에 새로 append
한 패턴(있으면) + `.omp/learned.md`에 적은 규칙 승격 후보(있으면, → `omp-learn` 게이트로). 경로 규약은
`references/output-layout.md`가 SSOT. 다음 단계 안내: 규칙을 강제하려면 `omp-codify`, 준수 검증은
`omp-audit`.
</Output>
