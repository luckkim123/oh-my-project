---
name: omp-organize
description: |
  규칙 위반 탐지 → 안전 재배치 — auditor가 .omp/rules.json 기준으로 위반을 탐지하고,
  organizer가 mv→검증→삭제 안전 프로토콜로 파일을 옮긴다. 이동 전 사람 승인 + dry-run 강제.
  탐지(auditor read-only) ≠ 실행(organizer write) 분리. 파일을 옮기는 유일한 stage.
  Triggers: 정리해줘, 규칙대로 정리, 재배치, 파일 옮겨, 위반 정리, 폴더 정리,
  organize, reorganize, move files, 제자리에 놓아줘, 어긋난 파일, tidy up
---

# omp-organize — 규칙 위반 탐지 → 안전 재배치

<Purpose>
`.omp/rules.json`에 성문화된 구조·명명 규칙을 어긴 파일을 찾아, 규칙에 맞는 자리로 안전하게 옮긴다. 두 lane으로 갈린다: **auditor(read-only)가 위반을 탐지**하고, **organizer(write)가 이동을 실행**한다. omp 전체에서 파일을 실제로 옮기는 유일한 stage이므로, `references/safe-fileops.md`의 mv→검증→삭제 프로토콜·trash 경유·rename 지양·사람 승인·dry-run을 절대 우회하지 않는다. "정리"가 파일을 잃어버리면 omp의 가치가 통째로 무너진다 — 이 stage의 모든 안전장치는 그 한 가지를 막기 위함이다.
</Purpose>

<Use_When>
- codify로 규칙을 갱신한 뒤 기존 파일을 그 규칙에 맞춰 재배치하고 싶을 때
- audit이 위반 목록을 냈고, 이제 그 위반을 실제로 고치고 싶을 때
- "이 폴더 규칙대로 정리해줘" — 흩어진 파일을 STRUCTURE/NAMING 규칙대로 제자리에 놓을 때
- 잘못된 디렉토리에 있는 산출물·데이터·문서를 옮기되, 안전하게 옮기고 싶을 때
</Use_When>

<Do_Not_Use_When>
- 규칙 준수 여부 **판정만** 필요하면 (이동 없이 PASS/FAIL) → `omp-audit`
- 규칙 자체를 바꾸거나 새로 만들 거라면 → `omp-codify` (먼저 규칙을 고치고 organize)
- dataset 메타데이터 등록·추적이면 → `omp-dataset` (organizer는 데이터를 옮기지 않음, dataset-curator는 메타만)
- `.omp/`가 아직 없으면 → `omp-init` 먼저 (규칙이 없으면 위반을 정의할 수 없음)
- 관찰을 규칙으로 승격하는 거라면 → `omp-learn`
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **탐지 ≠ 실행 분리 (불변)**: auditor는 위반을 **탐지만** 하고 절대 파일을 옮기지 않는다(disallowedTools=[Write,Edit,NotebookEdit]). 이동은 organizer만 한다. 같은 context가 탐지하고 자기 판단으로 실행하는 self-approval은 금지 — oms의 "inspector(비평) ≠ drafter(생성)" 분리를 계승.
- ⚠️ **safe-fileops.md 강제**: organizer의 모든 이동/삭제는 `references/safe-fileops.md`를 절대 규약으로 따른다.
  - **Move = copy-verify-delete**: `mv`/copy → 목적지를 `find`/`ls`로 검증(개수 + 중요 파일은 SHA-256 비교) → **검증 통과 후에만** 원본 삭제. 같은 호흡에 원본 `rm` 금지 (iCloud/Drive sync lag, exFAT AppleDouble 잔여로 파일 유실).
  - **Delete = trash 경유**: OS 분기 — macOS `trash`(없으면 `~/.Trash`) / Linux `gio trash`·`trash-cli` / Windows PowerShell 휴지통. 휴지통 없는 환경(Docker/CI)은 **STOP** → 다른 곳에 복사본 존재 확인 + 사용자의 명시적 "영구 삭제" 승인 후에만 `rm`. git repo면 `git rm`+commit도 복구 가능 경로.
  - **Rename 지양**: sync 폴더에서 폴더 rename은 sync 엔진이 원본 이름을 복원해 반쪽본+원본 공존 위험. rename 후 옛 경로 삭제 전 `diff -rq old new`로 새 경로가 옛 경로의 **superset**임을 확인.
- ⚠️ **dry-run first**: 모든 batch 이동/삭제는 먼저 dry-run으로 전체 plan(from → to, 위반 규칙 인용)과 *실행될* 검증 명령을 **0 mutation**으로 출력한다. 실제 실행은 dry-run 출력을 사람에게 보이고 승인받은 뒤에만 진입.
- ⚠️ **사람 승인 게이트 (이동 전)**: organizer는 절대 auto-move 하지 않는다. move plan을 제시하고 사람이 승인해야 한 건이라도 파일시스템을 건드린다.
- 모든 경로는 `pathlib` 기준, OS 중립. 절대경로·`~` 하드코딩 금지(`Path.home()`/`Path.cwd()`).
- 진행 중 발견한 가벼운 패턴(예: "이 확장자는 늘 이 폴더로 모임")은 `references/learning-protocol.md`의 light 채널대로 `.omp/wiki/`에 자동 append(승인 불필요). 규칙으로 굳힐 무거운 관찰은 `.omp/learned.md`에 후보로만 적고 → `omp-learn` 게이트로 넘긴다(여기서 직접 rules.json 안 고침).
</Execution_Policy>

<Steps>
1. **대상·범위 확인**: 정리할 프로젝트 루트와 `.omp/rules.json`·`.omp/STRUCTURE.md`·`.omp/NAMING.md`의 존재 확인. 범위(전체 트리 / 특정 하위 폴더)와 severity 필터(error만 / error+warn)를 정한다. `.omp/`가 없으면 즉시 중단하고 `omp-init`을 안내.
2. **탐지 lane 위임 (auditor, read-only)**: `Task(subagent_type="oh-my-project:auditor", ...)`로 위반 탐지를 위임한다.
   - 입력: 프로젝트 루트, `.omp/rules.json`(기계 규칙 SSOT), `references/schemas/rules.schema.json`(스키마), 범위, severity 필터.
   - 지시: rules.json의 `structure.directories[].enforced`·`naming.patterns[].regex`(Python re)·`ignore` glob에 따라 실제 트리를 검사. 각 위반에 대해 {위반 파일 경로, 어긴 규칙(structure/naming + 규칙 id), severity(error/warn/info), 제안 목적지(어느 규칙이 어디로 요구하는지)}를 낸다. **파일은 옮기지 않는다 — 탐지만**.
3. **위반 목록 수령 + move plan 초안**: auditor 산출을 받아 severity별로 집계하고, 각 위반을 `from → to`(위반 규칙 인용 포함) move plan으로 정리한다. 모호한 목적지(규칙이 한 자리를 특정 못 함)는 이동 후보가 아니라 **사람 질문 항목**으로 분리.
4. **dry-run 제시 (0 mutation)**: organizer에게 dry-run을 요청해 전체 move plan + *실행될* 검증 명령(`find`/`ls`/SHA-256 비교)·삭제 경로(trash 분기)를 출력한다. 이 단계는 사용자 파일시스템을 건드리지 않는다. dry-run plan(from→to + 위반 규칙 인용 + 검증 명령)은 `.omp/work/plans/organize-{YYYY-MM-DD-HHMM}.md`에 기록해 undo provenance로 남긴다(`references/output-layout.md` work layer — 이 기록은 사용자 파일이 아닌 omp 자체 작업장 쓰기다). 기록 후 `.omp/work/plans/`를 retention 정리: 최신 N=10개만 남기고 더 오래된 plan은 trash 경유 prune(영구 `rm` 금지), "pruned X old plans" 한 줄 보고 — 기록한 이 스킬이 자기 subfolder를 trim.
5. ━━━ **GATE: 이동 승인 (human)** — dry-run plan을 사람에게 보이고 결정받는다: proceed(전체) / 일부 선택 / revise(목적지 수정) / abort. **승인 없이는 단 한 건도 실행하지 않는다.**
6. **실행 lane 위임 (organizer, write)**: 승인된 plan에 대해서만 `Task(subagent_type="oh-my-project:organizer", ...)`로 실제 이동을 위임한다.
   - 입력: 승인된 move plan(from→to + 규칙 인용), `references/safe-fileops.md`(절대 규약), 대상 OS 정보.
   - 지시: 각 이동을 **copy-verify-delete** 순서로 — mv/copy → 목적지 `find`/`ls`+SHA-256 검증 → 통과 후에만 원본 trash 경유 삭제. rename 지양, sync 폴더는 superset 확인. 한 건이라도 검증 실패하면 그 건은 **롤백 가능 상태로 STOP**하고 보고(나머지 진행 여부는 사람에게).
7. **사후 검증 + 기록**: 이동 후 `omp-audit`(또는 auditor 재탐지)로 위반이 실제로 해소됐는지 확인(잔류 위반 0 목표). 정리 중 드러난 가벼운 패턴은 `.omp/wiki/`에 append, 규칙화할 무거운 관찰은 `.omp/learned.md`에 후보로 적어 `omp-learn`으로 넘긴다.
8. **인덱스 동기화 (구조를 바꿨으면 필수)**: 이동/리네임이 **rules.json `structure.directories[].path`나 STRUCTURE.md 트리에 이름으로 등장하는 폴더의 이름·계층·존재 자체를 바꿨다면**, 그 변경은 인덱스를 *어긋나게* 만든다 — `.omp/STRUCTURE.md`·`rules.json`(+ 경로가 적힌 경우 `DATASETS.md`)이 옛 경로를 가리키게 된다(drift). 이 동기화는 **organize 완료 정의의 일부**다: 별도 사용자 요청 없이 organize 안에서 끝낸다(사용자가 "인덱스도 고쳐"라고 다시 말하게 만들면 실패). 판별 — *방금 옮긴/이름 바꾼 폴더가 rules.json·STRUCTURE.md에 이름으로 적혀 있나?* **아니오**(파일을 규칙대로 제자리에 옮겼을 뿐, 구조 정의 불변) → no-op, 인덱스는 이미 맞다. **예** → 단순 path 문자열 치환이면 직접 Edit로 동기화, `enforced`·`role`·구획 신설처럼 규칙 *의미*가 바뀌면 `omp-codify` 게이트로 넘긴다(rule-architect 제안 → 사람 승인). 동기화한 파일과 옛→새 경로를 Output에 명시.

> **순서 불변**: auditor(탐지) → move plan → dry-run → **사람 승인** → organizer(실행) → 사후 audit → **인덱스 동기화**. 어떤 경우에도 탐지 context가 그대로 실행하거나, 승인·dry-run을 건너뛰지 않는다. **구조를 바꾼 이동은 인덱스 동기화까지가 한 작업** — 옛 경로가 인덱스에 남은 채 다음 작업으로 넘어가지 않는다.
</Steps>

<Output>
- 위반 목록 (위반 파일 · 어긴 규칙(structure/naming + id) · severity · 제안 목적지) + severity별 카운트
- move plan (from → to, 위반 규칙 인용) — dry-run 출력(0 mutation)으로 먼저 제시
- 사람 승인 결정 이력 (proceed/일부/revise/abort)
- 실행 결과: 각 이동의 copy-verify-delete 검증 증거(개수·SHA-256 일치), trash 경유 삭제 경로, 실패·롤백 건(있으면)
- 사후 audit 결과(잔류 위반 수) + 모호 목적지로 분리된 사람 질문 항목
- **인덱스 동기화 결과**: 구조를 바꿨으면 갱신한 `.omp/` 파일(STRUCTURE.md·rules.json·DATASETS.md)과 옛→새 경로 / 구조 불변이면 "인덱스 동기화 불필요(no-op)" 명시
- `.omp/wiki/` 자동 append 내역 / `.omp/learned.md` 승격 후보(→ omp-learn 안내)
- ⚠️ 승인 없이 실행한 이동 없음 / safe-fileops.md 우회 없음 명시
</Output>
