---
name: omp-init
description: |
  1회 부트스트랩 — 프로젝트 폴더를 귀납 스캔하고 가장 맞는 프리셋을 매칭해 **합성**,
  `.omp/` SSOT 전체(PROJECT/STRUCTURE/NAMING/DATASETS.md + rules.json/manifest.json + learned.md + wiki/)를
  생성한다. 초안 rules.json은 사람 승인 게이트를 거쳐야 확정 — 범용으로 출발해 즉시 이 프로젝트에 특화된 시작점.
  이미 `.omp/`가 있으면 "재초기화?" 경고 후 멈춘다.
  Triggers: omp 초기화, 프로젝트 초기화, .omp 만들어, init, 부트스트랩, 폴더 스캔해줘,
  이 프로젝트 파악해, 프로젝트 세팅, omp init, project init, initialize project, scan this folder
---

# omp-init — 1회 부트스트랩 (폴더 스캔 + 프리셋 합성 → .omp/ 생성)

<Purpose>
프로젝트 폴더를 처음 만났을 때 단 한 번 돌리는 부트스트랩. 실제 폴더 트리를 **귀납적으로** 스캔(project-scanner)하고, 가장 맞는 범용 프리셋을 **매칭·합성**(rule-architect)해 `.omp/` SSOT 전체를 만든다. 핵심은 합성이다 — 프리셋만 복붙하면 범용에 머무르고, 귀납만 하면 시드가 없다. 둘을 합쳐 *배포 시엔 범용, 깔리는 순간 이 폴더에 특화된* rules.json 초안을 만든 뒤, 사람 승인 게이트를 통과시킨다. 이것이 omp의 "범용→특화" 비대칭의 출발점이다.
</Purpose>

<Use_When>
- 프로젝트 폴더에 아직 `.omp/`가 없고, omp로 관리를 시작할 때
- "이 프로젝트 파악해 / 폴더 스캔해 / omp 초기화" 같은 첫 진입
- `omp-pilot`이 `.omp` 부재를 감지해 init을 흡수 호출할 때 (그 경우 호출자가 이 skill로 진입)
</Use_When>

<Do_Not_Use_When>
- 이미 `.omp/`가 존재 → 재초기화는 기존 학습(learned.md·wiki·specificity)을 날린다. 규칙만 바꾸려면 → `omp-codify`, 관찰을 규칙으로 승격하려면 → `omp-learn`. (그래도 사용자가 의도적으로 재초기화를 원하면 아래 Steps의 재초기화 분기로.)
- 규칙은 그대로 두고 위반만 잡고 싶다 → `omp-audit`(탐지) / `omp-organize`(재배치)
- dataset만 등록 → `omp-dataset`
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **합성이 본질, 복붙 금지**: rules.json 초안은 (a) project-scanner의 실제 트리·확장자·명명 패턴 귀납 + (b) rule-architect의 프리셋 매칭, **둘의 합성**이어야 한다. 프리셋을 그대로 베끼면 `specificity`가 0에 멈춘다. 귀납으로 관측된 실제 구조가 프리셋 시드를 덮어쓰는 방향으로 합성한다. (진화 메커니즘 SSOT: `references/learning-protocol.md`, 채널 정의: `references/output-layout.md` §"Two learning channels".)
- ⚠️ **사람 승인 게이트는 자동 통과 금지**: 초안 rules.json은 *제안*이다. 사람이 proceed/revise/abort를 결정하기 전까지 `.omp/rules.json`을 확정 기록하지 않는다. 규칙은 파일 이동(organize)을 유발하는 무거운 결정이므로 게이트 필수.
- **`.omp` 존재 시 멈춤**: 첫 단계에서 `<project>/.omp/`를 검사. 있으면 즉시 멈추고 "이미 초기화됨 — 재초기화하면 학습 손실(learned.md/wiki/specificity)" 경고 + 사용자 명시 재확인을 받아야만 진행.
- **읽기 우선·쓰기 게이트 후**: project-scanner와 rule-architect는 둘 다 **read-only**(disallowedTools=[Write,Edit,NotebookEdit]) — init 단계에서 이들은 절대 파일을 쓰지 않는다. `.omp/` 실제 기록은 게이트 통과 후 호출 컨텍스트가 수행(또는 codify에 위임). self-approval 금지: 규칙을 설계한 rule-architect가 같은 패스에서 그 규칙을 승인·강제할 수 없다.
- **`specificity` 정직하게 기록**: 합성 직후 초안의 specificity는 보통 0.1–0.4(프리셋 골격 + 귀납 보정). 1로 부풀리지 말 것 — 진짜 특화는 운영 중 `omp-learn` 승격으로 올라간다.
- **메타데이터-only**: scanner는 dataset 후보(대용량·확장자)를 *식별*만 한다. SHA256·split·lineage 실제 기록은 `omp-dataset`(dataset-curator) 몫. init은 manifest.json에 빈/얕은 인벤토리만 시드.
- **크로스플랫폼**: 모든 경로는 상대경로 또는 `Path.cwd()` 기준. 절대경로·`~` 하드코딩 금지. 트리 스캔 시 `.git/**`·`node_modules/**`·`.omp/**`는 ignore 시드에 넣는다.
- **.gitignore 선택 1회 질문**: `references/output-layout.md` §".gitignore guidance"대로 `.omp/`를 커밋할지(`rules.json`/`*.md` 공유 권장, `wiki/`는 개인) init이 한 번 묻고 선택을 기록한다.
</Execution_Policy>

<Steps>
1. **`.omp` 존재 검사 (게이트 0)**: `<project>/.omp/`가 있으면 멈추고 경고 — "이미 초기화됨. 재초기화 시 learned.md·wiki/·specificity 손실. 정말 재초기화?" 사용자가 명시 동의해야만 계속(기존 학습 백업 권유: trash 경유 또는 `.omp.bak/`로 보존). 없으면 다음으로.
2. **스캔 범위 확인**: 프로젝트 루트 경로, 대략적 성격(사용자가 안다면), 무시할 거대 디렉토리(빌드 산출물 등)를 짧게 확인. 모르면 기본값(전체 스캔, 표준 ignore)으로 진행.
3. **귀납 스캔 (dispatch ①)**: project-scanner에게 폴더 인벤토리·구조 귀납·파일 분류를 위임 — 실제 트리·확장자 분포·명명 패턴·대용량/데이터 후보를 *관측된 사실로만* 산출(추측 금지). read-only. scanner 산출(인벤토리 보고서)은 합성 입력이므로 `.omp/work/scans/scan-{YYYY-MM-DD-HHMM}.json`에 기록해 둔다 — ⚠️ scanner는 read-only(자기 산출을 디스크에 못 씀)이므로 **이 기록은 호출 스킬(init)이** 수행한다(scanner read-only 불변 유지). 기록 후 `.omp/work/scans/`를 retention 정리: 최신 N=10개만 남기고 더 오래된 스캔은 trash 경유 prune(영구 `rm` 금지), "pruned X old scans" 한 줄 보고 — 기록한 이 스킬이 자기 subfolder를 trim. `references/output-layout.md` work layer.
4. **프리셋 매칭 + 합성 (dispatch ②)**: scanner 산출을 입력으로 rule-architect에게 위임 — `references/presets/*.md`(python-ml/web-app/research-lab/monorepo/johnny-decimal/generic) 중 가장 맞는 시드를 고르고, 귀납 결과로 보정해 **초안 rules.json**을 합성. 스키마는 `references/schemas/rules.schema.json` 준수(`omp_version`/`project`/`specificity`/`structure`/`naming` 필수, `preset_origin`에 선택한 프리셋 명시). manifest.json은 `references/schemas/manifest.schema.json`에 맞춰 얕게 시드(파일 인벤토리; dataset 엔트리는 후보 식별만). read-only — 디스크에 안 씀, 초안을 텍스트로 반환.
   ━━━ **GATE 1 (핵심): 초안 rules.json 승인 (human)** — proceed / revise / abort. 사람에게 매칭된 프리셋·합성된 structure/naming 규칙·추정 specificity를 제시하고 결정을 받는다. 자동 통과 없음. revise면 4로 되돌아 재합성. ━━━
5. **`.omp/` 기록 (게이트 통과 후에만)**: 승인된 초안으로 `references/output-layout.md`의 고정 구조대로 SSOT를 생성 —
   - `.omp/rules.json` (승인본), `.omp/manifest.json` (시드 인벤토리) — 두 .json 쓰기는 부분쓰기 손상을 막기 위해 `hooks/omp_atomic.py`의 atomic write를 경유한다(T20).
   - `.omp/STRUCTURE.md`·`.omp/NAMING.md` (rules.json의 사람용 narrative — .md↔.json 페어, 서로 어긋나지 않게)
   - `.omp/PROJECT.md` (이 프로젝트가 무엇인가, 한 화면), `.omp/DATASETS.md` (manifest dataset 뷰; init 시점엔 후보 목록 또는 빈 카탈로그)
   - `.omp/learned.md` (빈 관찰 로그, 승격 대기 채널), `.omp/wiki/` (빈 디렉토리, 자동 누적 채널)
   - .gitignore 선택을 기록(§Execution_Policy).
6. **확인 리포트**: 생성된 `.omp/` 경로 목록 + 선택된 `preset_origin` + 초안 `specificity` + "다음 단계 후보(codify로 규칙 다듬기 / dataset 등록 / audit 준수 확인)"를 사용자에게 보고. init은 1회 부트스트랩이므로 여기서 종료(루프 진입 아님).

> **dispatch 실체**: 4번까지의 두 위임은 read-only 진단 — 디스크 변경 0. 실제 `.omp/` 쓰기는 GATE 1 통과 후 5번에서만.
>
> ```
> # Step 3 — 귀납 스캔
> Task(
>   subagent_type="oh-my-project:project-scanner",
>   description="Inductive scan of the project folder",
>   prompt="<project root> 폴더를 read-only로 스캔. 실제 트리·확장자 분포·명명 패턴·"
>          "대용량/데이터 후보를 관측 사실로만 산출(추측 금지). ignore: .git/** node_modules/** .omp/**. "
>          "출력은 rule-architect가 프리셋 합성에 쓸 인벤토리."
> )
> # Step 4 — 프리셋 매칭 + 합성 (scanner 산출을 입력으로)
> Task(
>   subagent_type="oh-my-project:rule-architect",
>   description="Match preset and synthesize draft rules.json",
>   prompt="project-scanner 인벤토리를 입력으로 references/presets/*.md 중 best match를 고르고 "
>          "귀납 결과로 보정해 초안 rules.json 합성. references/schemas/rules.schema.json 준수, "
>          "preset_origin·specificity 정직 기록. read-only — 디스크에 쓰지 말고 초안 텍스트만 반환. "
>          "self-approve 금지(GATE 1은 사람)."
> )
> ```
</Steps>

<Output>
생성된 `.omp/` SSOT 전체 경로 목록(`PROJECT.md`/`STRUCTURE.md`/`NAMING.md`/`DATASETS.md` + `rules.json`/`manifest.json` + `learned.md` + `wiki/`) + 매칭된 `preset_origin` + 초안 `specificity`(0에 가까운 정직한 시작값) + GATE 1 결정 이력(proceed/revise/abort) + .gitignore 선택 기록 + 다음 단계 후보(codify/dataset/audit). `.omp` 이미 존재 시: 경고 메시지 + 재초기화 미진행(또는 사용자 명시 동의 시에만 진행)임을 명시. 게이트 통과 전엔 디스크에 아무것도 확정 기록하지 않았음을 보고(read-only 진단만 수행).
</Output>
