---
name: omp-audit
description: |
  프로젝트 폴더를 .omp/rules.json·manifest.json 대비 기계적으로 검사하는 summative 게이트 —
  구조 위반·명명 위반·dataset 체크섬 drift·split 누수·lineage/orphan을 read-only PASS/FAIL로 판정한다.
  코드의 "CI". 증거 기반(fresh 해시·grep·트리워크)으로만, 비평·조언·자기 수정 없음.
  위반은 직접 고치지 않고 organizer(이동)·dataset-curator(재등록) 핸드오프 목록으로만 넘긴다.
  Triggers: 감사해줘, 규칙 준수 확인, audit, 위반 검사, PASS 판정, 체크섬 확인, drift 검사,
  split 누수, 구조 위반 찾아, omp audit, 규칙 어긴 거 찾아, 게이트 확인
---

# omp-audit — 규칙 준수 summative 게이트 (read-only PASS/FAIL)

<Purpose>
프로젝트 폴더가 `.omp/rules.json`·`.omp/manifest.json`이 선언한 규칙을 실제 디스크에서 지키는지 기계적으로 검사한다. `oh-my-project:auditor`(opus, read-only)에게 단일 위임해 구조 위반·명명 위반·dataset 체크섬 drift·split 누수·lineage/orphan을 항목별 PASS/FAIL + 증거로 판정한다. 코드의 "CI"에 해당 — 객관 증거(파일:줄·기대 vs 실제 해시·grep 결과)로만 판정하고 비평·조언·개선 제안은 하지 않는다.

⚠️ **자기 수정 안 함.** 위반을 감지해도 한 바이트도 옮기거나 고치지 않는다. 파일 이동은 omp 전체에서 `organizer`만, manifest 재등록은 `dataset-curator`만 한다. auditor는 그들이 소비할 핸드오프 목록만 산출한다.
⚠️ **비평·조언이 목적이면 audit이 아니다.** "이 구조를 이렇게 바꾸면 좋겠다"는 `omp-codify`(rule-architect)의 영역이다. 여기서 나오는 것은 항목별 PASS/FAIL과 증거뿐이다.
</Purpose>

<Use_When>
- `omp-organize`로 파일을 옮긴 *직후* 디스크가 규칙에 부합하는지 객관 재검증이 필요할 때 (조직화 결과의 독립 reviewer pass)
- `omp-codify`/`omp-learn`으로 rules.json이 바뀐 뒤 실제 폴더가 새 규칙을 지키는지 확인할 때
- dataset이 등록 후 바뀌었는지(체크섬 drift), train/val/test 사이에 누수가 없는지 기계적으로 검사할 때
- manifest에 등록됐으나 디스크에 없는 orphan 엔트리·끊긴 lineage를 찾을 때
- `omp-pilot` 루프 안에서 organize/dataset 단계 결과를 게이트로 통과/반려할 때
</Use_When>

<Do_Not_Use_When>
- 규칙을 *설계·갱신*하고 싶으면 → `omp-codify` (rule-architect). audit은 현 rules.json 대비 위반만 판정한다.
- 위반을 *고치고/옮기고* 싶으면 → `omp-organize` (auditor 탐지 → organizer 이동). audit은 탐지만 한다.
- 체크섬 drift를 manifest에 반영(재등록)하고 싶으면 → `omp-dataset` (dataset-curator). audit은 manifest를 안 고친다.
- 아직 `.omp/`가 없으면 (init 안 됨) → `omp-init` 먼저. rules.json 없이는 검사 기준이 없다.
- "논리·문체 같은 정성 개선점"이 목적이면 audit이 아니다 — audit은 기계적 PASS/FAIL만 낸다.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **fresh 증거만** — "should/probably/seems/아마도/잘 정리된 듯" 금지. dataset 체크섬은 `manifest.json.datasets[].sha256` 기록값을 믿지 않고 `hashlib` SHA-256 **재계산** 결과로만 판정한다. 검사 실행 못 한 항목은 PASS가 아니라 "검사 미실행 — 수동 확인 필요"로 표기.
- ⚠️ **자동 수정·자동 이동 절대 금지** — 구조 위반을 감지해도 `mv` 안 하고, 체크섬 drift를 감지해도 manifest의 sha256을 새 값으로 덮어쓰지 않으며, 명명 위반을 감지해도 rename 안 한다. 감지 항목은 **organizer 처리 필요**(이동) 또는 **dataset-curator 재등록 필요**(메타데이터) 목록으로만 넘긴다.
- ⚠️ **self-approval 3중 금지** — (a) auditor frontmatter `disallowedTools: Write, Edit, NotebookEdit`로 파일 수정 차단, (b) audit은 규칙을 codify하거나 파일을 organize한 *같은 active context*가 아닌 **분리된 reviewer pass**다, (c) auditor의 NOT-responsible에 "재배치(organizer)·규칙 설계(rule-architect)·manifest 작성(dataset-curator)"이 명시 — 그 역할을 겸하면 게이트 독립성이 사라진다. 이 skill을 호출하는 context가 직접 audit을 흉내내지 말고 fresh `oh-my-project:auditor` subagent에 위임한다.
- **DVC/git-lfs 존중** — `manifest.json.managed_by_external.tool`이 `dvc`/`git-lfs`이거나 `.dvc/`·lfs `.gitattributes` 흔적이 보이면 데이터 콘텐츠 drift는 외부 도구 소관이므로 critical FAIL이 아닌 "외부 관리 — manifest는 메타만 미러" 경고로 강등한다 (citation-safe의 dataset판).
- **스냅샷 식별자에 판정을 묶는다** — 모든 PASS/FAIL은 그 회차에 실제 검증한 대상의 스냅샷 식별자(`.omp/rules.json`·`.omp/manifest.json` 내용 해시 + 검사한 dataset 파일 SHA-256/mtime + 다룬 위반ID 집합)에 묶는다. `omp-organize`가 파일을 옮기거나 `omp-codify`가 규칙을 바꾸면 식별자가 달라지므로, audit→organize→재audit 멀티라운드에서 stale PASS를 재사용하지 않는다.
- 전체 PASS는 모든 error-severity 항목이 PASS일 때만. `naming.patterns[].severity`의 warn/info 위반은 전체 FAIL을 유발하지 않되 보고서에 집계한다.
- 경로는 전부 프로젝트 루트 기준 상대(`pathlib`) — 절대경로·`~` 하드코딩 금지. `rules.json.ignore[]` glob(`.git/**`, `node_modules/**`, `.omp/**` 등)은 검사에서 제외.
</Execution_Policy>

<Steps>
1. **대상·SSOT 확인**: 프로젝트 루트와 `.omp/rules.json`·`.omp/manifest.json` 존재를 확인한다.
   - `.omp/`가 없으면 audit 불가 → 호출자에게 "`omp-init` 필요"를 보고하고 종료 (검사 기준 없음).
   - rules.json/manifest.json JSON이 깨졌으면 전체 FAIL로 표기하고 "`omp-codify`/`omp-dataset`로 SSOT 복구 필요" 보고.
2. **검사 축 확정**: 이번 회차가 다룰 축을 명시한다 — 구조 위반(`rules.json.structure.directories[].enforced`), 명명 위반(`naming.patterns[]` Python regex + severity), dataset 체크섬 drift(`manifest.datasets[].sha256` SHA-256 재계산), split 누수(`split.group` 내 동일 hash/path), lineage·orphan 무결성, specificity 정합(정보). 호출 맥락이 한 축만 요청해도 dataset 축과 구조/명명 축은 서로 독립적으로 수행 — 한 축 FAIL이 다른 축 검사를 건너뛰게 하지 않는다.
3. **참조 카드 적재 (위임 입력)**: auditor에게 넘길 SSOT·카드 경로를 모은다 —
   - `.omp/rules.json` + `references/schemas/rules.schema.json` (규칙 스키마 SSOT: 필수 필드 `omp_version/project/specificity/structure/naming`)
   - `.omp/manifest.json` + `references/schemas/manifest.schema.json` (인벤토리 스키마 SSOT: 필수 `omp_version/generated/datasets`, sha256 `^[a-f0-9]{64}$|^UNHASHED$`)
   - `.omp/STRUCTURE.md`·`.omp/NAMING.md`·`.omp/DATASETS.md` (사람용 .md — 기계 .json과 페어, 참고용)
   - `references/output-layout.md` (`.omp/` 경로 규약·"Two learning channels" SSOT)
   - `references/safe-fileops.md` (organizer 핸드오프 시 인용할 mv→검증→삭제·trash·dry-run·승인 프로토콜 — auditor는 흉내내지 않고 핸드오프 목록에 인용만)
   - `references/learning-protocol.md` (heavy/light 2채널·specificity 승격 게이트 SSOT — `rules.json.specificity`·`learned_refs[]` 정합 확인의 기준)
   - `references/presets/*.md` (`project.preset_origin`이 가리키는 시드 — specificity 정합 참고)
4. **검사 결과 수령**: auditor의 항목별 PASS/FAIL + 증거(파일 경로·행·어긴 규칙 ID/regex·기대 해시 vs 재계산 해시·중복 path)를 취합한다. 증거 없는 PASS·"검사 미실행"은 PASS로 카운트하지 않는다.
5. **핸드오프 분류**: FAIL 위반을 처리 주체별로 나눈다 — **organizer 처리 필요**(구조/명명 위반 파일: 위반 경로 + 어긴 rules.json 규칙 + 제안 목적지 후보) / **dataset-curator 재등록 필요**(체크섬 drift·orphan·미등록: 데이터 콘텐츠는 안 건드리고 메타만). audit 자신은 이들을 직접 dispatch하지 않는다 — 핸드오프 목록만 산출하고, 실제 호출은 `omp-organize`/`omp-dataset`/`omp-pilot`이 사람 승인 게이트를 거쳐 한다.
6. **스냅샷 식별자 부착 + 리포트 기록**: 판정을 검증 대상 스냅샷 식별자에 묶어, organize/codify 후 stale PASS 재사용을 차단한다. 그리고 항목별 PASS/FAIL + 증거 + 스냅샷 식별자를 `.omp/work/audits/audit-{YYYY-MM-DD-HHMM}.json`에 기록해 drift 이력(시계열 비교)을 남긴다. ⚠️ **이 기록은 read-only auditor가 아니라 컨트롤러인 이 스킬이 쓴다** — auditor는 산출(텍스트)만 내고, work/audits 기록은 호출 스킬의 몫이다(auditor의 read-only 불변·탐지≠실행 분리 유지). `references/output-layout.md` work layer.
7. **Task 위임 (단일, read-only)**: 위 입력을 묶어 auditor에 단일 위임한다. read-only 게이트이므로 자동 검사의 독립성을 위해 **단일 dispatch** (검사 항목을 여러 agent로 쪼개지 않는다 — 한 auditor가 전 축을 결정론적으로 본다):
   ```
   Task(
     subagent_type="oh-my-project:auditor",
     description="omp 규칙 준수 audit (read-only PASS/FAIL)",
     prompt="""
     프로젝트 루트: <project root 절대경로>
     SSOT: .omp/rules.json, .omp/manifest.json
     스키마 카드: references/schemas/rules.schema.json, references/schemas/manifest.schema.json
     경로 규약·2채널: references/output-layout.md
     organizer 핸드오프 시 인용: references/safe-fileops.md (auditor는 흉내내지 말 것)
     학습 2채널·specificity 게이트: references/learning-protocol.md
     preset 시드(specificity 정합 참고): references/presets/<preset_origin>.md

     지시: 아래 축을 각각 fresh 증거로 PASS/FAIL + 증거 출력. 조언·비평·자동수정 없음.
     dataset 체크섬은 manifest 기록값을 믿지 말고 hashlib SHA-256 재계산으로만 판정.
       - 스키마 유효성 (rules.json·manifest.json 필수 필드)
       - 구조 위반 (structure.directories[] 중 enforced:true role 위반)
       - 명명 위반 (naming.patterns[] applies_to glob × regex, severity별 집계)
       - dataset 체크섬 drift (manifest.datasets[].sha256 vs hashlib 재계산; UNHASHED는 size+mtime 폴백)
       - split 누수 (같은 split.group 내 train↔val↔test 동일 SHA-256 또는 중복 path)
       - lineage·orphan (derived_from·by 실재; manifest path 디스크 실재; 미등록 파일 경고)
       - specificity 정합 (rules.json.specificity ↔ learned_refs[] 일관성, 경고만)
     DVC/git-lfs(managed_by_external·.dvc/·lfs .gitattributes) 감지 시 데이터 drift는 경고로 강등.
     rules.json.ignore[] glob은 검사 제외. 경로는 프로젝트 루트 기준 상대(pathlib).
     위반은 organizer/dataset-curator 핸드오프 목록으로만 — 직접 mv/rm/manifest 수정 절대 금지.
     판정을 스냅샷 식별자(rules/manifest 내용 해시 + dataset SHA-256/mtime + 위반ID)에 묶어라.
     출력: 항목별 PASS/FAIL 표 + FAIL 증거 블록 + organizer/dataset-curator 핸드오프 목록 + 실행 명령어 + 스냅샷 식별자.
     """
   )
   ```
</Steps>

<Output>
- **항목별 결과표**: 스키마 유효 / 구조 위반 / 명명 위반(error·warn·info) / dataset 체크섬 drift / split 누수 / lineage 무결성 / manifest path 실재(orphan·미등록) / specificity 정합 — 각 PASS·FAIL·WARN + 비고.
- **FAIL 항목 증거**: 위반 파일 경로·행·어긴 rules.json 규칙 ID/regex·기대 해시 vs `hashlib` 재계산 해시·중복 path — 재현 가능한 형태.
- **organizer 처리 필요 목록** (자동 이동 안 함): 위반 경로 + 어긴 규칙 + 제안 목적지 후보. `references/safe-fileops.md`(mv→find 잔류0 검증→삭제·trash 경유·dry-run·사람 승인) 프로토콜로 `omp-organize`가 처리 — audit은 인용만 하고 직접 옮기지 않음.
- **dataset-curator 재등록 필요 목록** (자동 갱신 안 함): drift·orphan·미등록 — 데이터 콘텐츠는 안 건드리고 `omp-dataset`이 메타데이터만 재등록.
- **외부 관리 표기**: DVC/git-lfs 감지 시 데이터 drift는 경고로 강등됨을 명시.
- **실행 명령어** (재현용 read-only 명령 목록) + **스냅샷 식별자** (rules/manifest 내용 해시 + dataset SHA-256/mtime + 위반ID).
- **최종 판정**: **PASS** (전 error-severity 항목 통과) 또는 **FAIL** (N개 항목 실패). FAIL 시 다음 단계 — 이동 필요 → `omp-organize`, 재등록 필요 → `omp-dataset`, 규칙 자체 손질 필요 → `omp-codify`. 모두 사람 승인 게이트를 거치고, 처리 후 **재audit**(fresh 스냅샷)으로 닫는다. self-approve 안 함 명시.
</Output>
