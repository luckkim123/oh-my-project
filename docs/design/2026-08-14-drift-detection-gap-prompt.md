# 인수인계 — omp 가 놓친 드리프트 부류 (2026-08-14 vault 사건)

> 이 문서는 **설계 입력**이지 설계 결과가 아니다. 다음 세션이 여기서 시작해
> `superpowers:brainstorming` → `writing-plans` 를 거쳐 실제 계획을 만든다.
> 파일명이 형제 문서의 `-plan.md` 가 아니라 `-prompt.md` 인 이유가 이것이다.

## 요청자 목적 (원문 그대로)

> 그리고 지금한 작업들이 사실은 내가 이 vault에서 작업을 할때 omp가 그때그때 알아서 잘
> 진행해서 애초부터 이런 문제가 없었어야하는 거 아닌가 싶은데 어떻게 생각해? 동의 한다면
> 다른 세션에서 omp를 좀 업데이트하게 prompt를 만들어줄 수 있어? 아니면 다른 하네스라던지
> 말이야. 내가 만든 om* 시리즈 하네스나 claudebase 중에 말이야

**이 문장이 판정 기준이다.** 아래 모든 제안은 "그때그때 알아서 진행됐다면 이 사건이
안 일어났을까" 에 답해야 한다. 목적을 다시 쓰지 말 것.

## 사건 요약 — 무엇이 3개월간 방치됐나

대상: Obsidian vault `~/ksm_Obsidian` (omp 0.9.0, preset `para`, specificity 0.731,
init 2026-05-31). 사용자가 **직접 "구분이 안 된다" 고 말하기 전까지 아무 신호도 없었다.**

정리에 든 것: 커밋 7건, 파일 이동 286건 / 1,001 MB, vault git tracked 1,804 → 705 MB.

| # | 결함 | 규모 | 방치 |
|:--|:---|---:|:---|
| D1 | `0_Project/README.md` 가 없는 폴더 3개(`stonefish`·`kmrts`·`agent_albc`)를 선언 | — | 3개월+ |
| D2 | `albc/README.md` 가 "Phase 1 RL 이론학습 Ch3 진행중" 에서 정지 | — | 7개월 |
| D3 | `pkrc/README.md` 가 선언한 6폴더 중 5개가 이미 `completed/` 로 이동됨 | — | 미상 |
| D4 | `completed/` 5개 중 4개에 README 부재 → 폴더 정체 불명 | — | 미상 |
| D5 | `albc/references/` 가 실은 **IROS 2024 제출본 일체**(rejected, ID 634) | 179파일 345 MB | 3개월 |
| D6 | `3_Archive/etc/attachments/` 의 82.5% 가 어떤 노트도 참조 안 함 | 148파일 686 MB | 미상 |
| D7 | 하네스 산출물(omx wiki 초안·세션 프롬프트)이 노트 트리에 혼재 | 28건 | 1개월+ |
| D8 | git 인덱스 `KROC/` vs 디스크 `kroc/` 대소문자 불일치 | 8건 | 미상 |

## 핵심 진단 — 3층으로 갈린다

### 층위 1. 검사 항목이 없어서 못 봤다

`hooks/omp_content_audit.py` 가 노출하는 검사는 넷뿐이다 —
`check_content_rule` · `find_dead_links` · `scan_structure_drift` · `lint_wiki`.

| 결함 | 가장 가까운 기존 검사 | 왜 안 걸렸나 |
|:---|:---|:---|
| D1 D2 D3 | `scan_structure_drift(root, rules)` | `rules.json.structure.directories[].path` 와 `STRUCTURE.md`/`DATASETS.md` 의 backtick 경로만 본다. **프로젝트 README 는 스캔 대상이 아니다** |
| D4 | 없음 | `rules.json` 의 role 산문에 "각 프로젝트는 자체 Kanban.md + README.md" 라 써 있으나 **강제 검사가 아니다** |
| D5 | 없음 | 폴더명과 그 폴더 README 의 자기 선언을 대조하는 검사가 없다. `references/README.md` 첫 줄이 `IROS 2024 Reference Materials / Status: Rejected / Submission ID 634` 였다 |
| D6 | `find_dead_links` | 링크 → 대상 **한 방향만** 본다. 자산 → 참조 역방향(아무도 안 쓰는 파일)이 없다 |
| D7 | 없음 | "이 파일은 다른 하네스(omx) 소관" 을 판별할 근거가 없다 |
| D8 | 없음 | 경로 대소문자 검사 없음. macOS 가 대소문자를 구분하지 않아 조용하다 |

### 층위 2. 규칙은 있었는데 재부상하지 않았다 — 이쪽이 더 중요하다

`.omp/wiki/paper-work-split.md` 에 **2026-05-31 자로 이렇게 적혀 있었다**:

```
### 미결 (omp-organize 별도 세션 대상)
사용자가 "논문 작업물 전부 workspace 로 옮겨줘" 요청. init 범위 밖이라 미실행. 이동 대상 후보:
- 0_Project/in_progress/albc/paper/ …
- 0_Project/in_progress/pkrc/paper_works/ …
```

**3개월간 아무도 이 문장을 다시 보지 않았다.** `lint_wiki` 가 orphan/stale/oversized/
broken-ref/stuck_candidate/ready_to_promote/contradiction 7종을 잡지만, **산문 안의
"미결" 액션 아이템은 status 필드가 아니라 잡히지 않는다.** `omp-brief` 의 BRIEF.md 도
`learned.md` 의 OBS 블록만 싣고 wiki 의 미결은 싣지 않는다 (사건 당일 BRIEF 실물 확인).

즉 **omp 는 자기가 적어둔 숙제를 자기가 못 읽는다.**

### 층위 3. 발동 계기가 없다

omp 의 stage 는 전부 명시적 호출이다 — audit 도, review 도. 요청자가 원한 "그때그때
알아서" 는 stage 로는 성립하지 않는다. 이건 **훅 레이어**의 문제다.

## 동의하지 않는 부분 — 설계 시 반드시 반영

**규칙 품질은 문제가 아니었다.** `paper-work-split.md` 의 분류 원칙
("순수 산출물(manuscript·figure·video·results·review)만 workspace, code·references·
methodology 는 vault") 은 정확했고, 2026-08-14 에 그대로 적용해 215파일을 옳게 갈랐다.

따라서 **고칠 곳은 `rules.json` 이 아니라 audit 함수 · BRIEF · 훅이다.**
"규칙을 더 쓰자" 는 방향으로 가면 이 사건을 오독한 것이다.

## 후보 변경 — 결정하지 말고 검토할 것

아래는 **후보이지 결론이 아니다.** 각각 omp 의 기존 관용구(detection ≠ execution,
warn-default, 사람 승인 게이트, "audit 은 고치지 않는다")를 지키는지 따로 판단해야 한다.

**A. 감지 확장 (`omp_content_audit.py`)**
- `scan_readme_drift(root, rules)` — 각 프로젝트 폴더 `README.md` 가 언급한 하위 경로 ↔ 디스크 대조. **주의**: 표 셀 안의 상대 이름(`background/` 가 `paper/background/` 를 뜻함)과 workspace 경로(vault 에 없는 게 정상)를 오탐으로 잡지 않아야 한다 — 이번 세션에서 검증 스크립트가 실제로 그렇게 틀렸다.
- `scan_orphan_assets(root, rules)` — 참조되지 않는 바이너리 자산. `find_dead_links` 의 역방향. 판정이 파일명 문자열 등장 여부이므로 **"미참조 ≠ 무가치"** 를 finding 문구에 담아야 한다(원본 실험 영상은 노트에 안 박혀 있어도 증거 가치가 있다).
- `scan_identity_mismatch(root)` — 폴더명과 그 폴더 `README.md` 의 자기 선언 대조. LLM 판단이 필요한 영역이라 **기계 검사로 어디까지 가능한지**가 설계 쟁점.
- `scan_path_case(root)` — `git ls-files` 경로 ↔ 디스크 실제 대소문자. **macOS NFD ↔ git NFC 정규화 차이로 한글 파일명이 전부 오탐이 된다** — `os.path.exists` 재확인 단계 필수.
- README 필수 규칙의 강제화 — 지금은 role 산문. `structure.directories[].requires: ["README.md"]` 같은 필드가 후보.

**B. 재부상 (`omp_session_brief.py` / `lint_wiki`)**
- wiki 산문의 "미결"·"TODO"·"별도 세션 대상" 패턴을 `lint_wiki` 의 8번째 종류로 추가하고, 30일 이상 방치 시 BRIEF 의 "다음 세션" 에 싣는다.
- 이게 층위 2 의 직접 해법이고 **비용 대비 효과가 가장 크다** — 이번 사건은 감지가 아니라 재부상만 됐어도 3개월이 아니라 1주일이면 끝났다.

**C. 발동 (훅)**
- SessionStart 에서 마지막 audit 시각을 보고 N일 경과 시 한 줄 넛지. **주의**: `.omp/work/audits/` 는 gitignored 이므로 머신 간 이동 시 "한 번도 안 함" 으로 보인다.
- 훅 주입 상한이 **문자 단위**라 한국어는 바이트 예산을 통과하며 문자 상한만 넘긴다
  (claudebase auto-memory `machine_hook_context_limit_is_chars`). 넛지는 짧아야 한다.

**D. claudebase (omp 아님 — 별건)**
- 이 세션에서 **작업자 커밋 2건이 병렬 세션의 작업을 삼켰다** (`796eb55d` 24건, `927e2296` 33건).
  원인은 `git add <경로> && git commit` 에서 **경로 인자가 `add` 에만 걸리고 `commit` 은
  인덱스 전체를 커밋**한다는 것. user-scope CLAUDE.md 의 "Multi-session git: isolate,
  don't negotiate" 는 worktree 분리를 말하지만 이 구체 함정을 담고 있지 않다.
- 후보: 그 operational limit 에 "공유 트리에서는 커밋 직전 `git diff --cached --name-only`
  가 비었는지 확인하거나 `git commit -- <경로>` 를 쓴다" 한 줄 추가.

## 명시적 비목표

- **rules.json 에 규칙을 더 넣는 방향 금지.** 위 "동의하지 않는 부분" 참조.
- **audit 이 고치게 만들지 말 것.** detection ≠ execution 은 omp 의 구조적 불변식이다.
- **새 검사를 error 로 승격하지 말 것.** Docker/secretary/governance/code-graph 축이 전부
  warn-default 인 이유와 같다 — 오탐 가능성이 있는 축이 PASS 를 막으면 게이트가 무력화된다.
- **`tokensave` CLI 실행 금지** (읽기처럼 보이는 verb 가 `~/.claude/settings.json` 을 덮어쓴다).

## 이 사건의 부수 교훈 (설계 시 함정으로 참고)

이번 정리에서 **검증 스크립트가 5회 틀렸다** — `ls -d` 다인자 종료코드, `awk '/^[ADMR]/'` 가
커밋 헤더 `Author:`/`Date:` 를 집계, `split('---')` 가 마크다운 표 구분선에서 절단, 소문자
경로 `git ls-files` 실패를 "미추적" 으로 오판, `os.listdir` 문자열 비교가 NFD/NFC 차이로 실패.

**새 audit 함수를 쓸 때 같은 부류를 반복하기 쉽다.** 특히 A 안의 네 함수는 전부 문자열
매칭 기반이라, 각 함수에 **오탐 케이스를 담은 테스트를 먼저** 두는 편이 안전하다.

## 검증 기준 — 무엇이 되면 성공인가

이 사건을 재현 데이터로 삼는다. 구현 후 vault 를 사건 이전 상태(`e408b7fd`)로 체크아웃하고
audit 을 돌렸을 때 **D1~D8 중 몇 개가 finding 으로 뜨는가**가 유일한 지표다.
"검사를 추가했다" 는 성공이 아니다.

---

# 부록 — krit 정리 세션이 덧붙임 (2026-08-14, 두 번째 세션)

> 같은 날 `krit/` 를 정리한 병렬 세션이 독립적으로 같은 의뢰서를 쓰다가, 본 문서가 먼저
> 있고 더 정확함을 확인하고 **고유분만 여기 접어 넣었다**(중복 사본 폐기). 아래는 위 본문에
> 없는 것만이다.

## 정정 — 두 번째 세션이 틀렸던 것

내 초안은 `scan_structure_drift` 가 결함 A(프로젝트 README 의 유령 경로 선언)를 "정확히 잡는
함수" 라고 썼다. **틀렸다.** 소스 실측(`hooks/omp_content_audit.py`) 결과 그 함수는
`rules.json structure.directories[].path` 와 `.omp/STRUCTURE.md`·`DATASETS.md` 의 백틱 경로만
읽고 **프로젝트 README 를 열지 않는다**. 본문 층위 1 의 D1·D2·D3 판정이 맞다.

또 나는 "진입점 문서(README/SYSTEM)의 structure_drift 는 FAIL 로 승격" 을 제안했으나,
본문의 명시적 비목표 **"새 검사를 error 로 승격하지 말 것"** 이 더 옳다 — 오탐 가능한 축이
PASS 를 막으면 게이트가 무력화된다. 제안 철회한다.

## 층위 1 을 굳히는 추가 증거 — 명시 호출조차 못 잡았다

`krit/simulator/README.md` 는 **오늘 `omp-organize` 가 실제로 돈 뒤에도** 결함이 남았다.

- `61c74885 [프로젝트] 논문 작업물 vault→workspace 이주 (omp-organize, 406파일)` — 오늘 실행.
- 같은 날 `krit/README.md` 는 omp-organize 감사로 구조 절이 **고쳐졌다**(그 파일이 자백: "최종
  수정 2026-08-14 (omp-organize 감사 — 프로젝트 구조 절을 디스크 실측으로 정정)").
- 그런데 **한 단계 아래 `simulator/README.md` 의 유령 경로 6건·깨진 링크 3건은 그대로였다.**

즉 감지 공백은 "스킬을 안 쳤다" 로만 설명되지 않는다. **쳤는데도 중첩 하위 폴더의 README 가
스캔 범위 밖이었다.** `scan_readme_drift` 후보(본문 A안)를 설계할 때 **재귀 범위**를 명시적
쟁점으로 둘 것.

## 새 결함 부류 — 외부 정본(external SSOT) 격차 (본문 D1~D8 에 없음)

본문의 D1~D8 은 전부 **vault 내부** 드리프트다. krit 정리에서 나온 것은 성격이 다르다:
**vault 문서가 vault 밖 정본의 사본인데 대조가 끊긴** 부류다.

| # | 결함 | 방치 |
|:--|:--|:--|
| D9 | `krit/README.md` 의 "Recent Activities (**Last 7 Days**)" 가 2025-11-25 | **262일** |
| D10 | `krit/Kanban.md` 최종 항목 2026-03. 그 사이 Notion 작업현황에 2026-07~08 항목 6건이 쌓였고 그중 실해역 실험 마감이 **이틀 뒤**였다 | 약 150일 |
| D11 | 2026-08-10 Notion 로드맵의 **범위 축소 결정 3건**(목표물 기반 위치인식·목표물 3D 복원·광학 3D 복원 → 수행 안 함)이 vault 어디에도 없음. 설계 문서는 여전히 개발 예정으로 서술 | 4일 |

이 vault 의 실제 정본 구조:

| 무엇 | 정본 | vault 측 사본 |
|:--|:--|:--|
| 일정·작업 현황 | Notion 「국기연 과제 통합 관리」 | `krit/Kanban.md` |
| 시뮬레이터 빌드 절차 | GitHub `HERO-Lab-POSTECH/stonefish_bringup` | `krit/simulator/README.md` |
| 시뮬레이터·SLAM 코드 | GitHub `stonefish_sim`/`stonefish_slam` | `simulator/` 하위 clone(gitignored) |

`secretary.sources[]` 는 **vault 안** 읽기 대상만 등록한다. 밖에 정본이 있다는 사실을 적을
자리가 없다. D9~D11 은 그 공백 하나에서 나온 세 증상이다.

### 후보 E — `rules.json` 에 `external_ssot[]` (본문 A~D 에 이어지는 다섯 번째)

```jsonc
"external_ssot": [
  { "authority": "notion",
    "ref": "https://app.notion.com/p/3a58e4e9fd2781c9aa09dc49eca3c3b0",
    "what": "국기연 과제 일정·작업 현황",
    "mirrors": ["0_Project/in_progress/krit/Kanban.md"],
    "reconcile_budget_days": 30 },
  { "authority": "github",
    "ref": "HERO-Lab-POSTECH/stonefish_bringup",
    "what": "시뮬레이터 빌드 절차",
    "mirrors": ["0_Project/in_progress/krit/simulator/README.md"],
    "reconcile_budget_days": 90 }
]
```

- **omp 는 외부를 읽지 않는다.** `mirrors[]` 의 mtime(또는 마지막 대조 기록)과 예산일만으로
  "N일간 대조 안 됨" 을 판정한다. 그 이상을 약속하면 지킬 수 없다.
- 이건 본문 **층위 2(재부상)** 의 외부판이다 — 감지가 아니라 재부상만 됐어도 D10 은
  이틀 전이 아니라 5개월 전에 걸렸다. 비용 대비 효과가 B 안과 같은 이유로 크다.
- 등록은 `omp-codify` 사람 게이트(= `secretary.sources[]` 와 동일 취급).
- ⚠️ 이건 본문의 "rules.json 에 규칙을 더 넣지 말 것" 과 충돌하는 것처럼 보이나 다르다 —
  **행동 규칙을 추가하는 게 아니라 세계의 사실(정본이 밖에 있다)을 등록**하는 것이다.
  그래도 쟁점이므로 설계 시 명시적으로 다툴 것.

## 두 번째 회귀 픽스처 (본문 `e408b7fd` 와 병용)

본문 픽스처는 vault 전역 D1~D8 용이다. README 재귀 스캔(A안)만 좁게 검증하려면 더 싼 것이 있다:

```bash
cd ~/ksm_Obsidian
git worktree add /tmp/omp-fixture-krit c19cf274
#   ghost path ≥6  @ 0_Project/in_progress/krit/simulator/README.md:31-38
#   dead link  ≥3  @ 0_Project/in_progress/krit/simulator/README.md:250-252
#     (그 링크 대상 0_Project/in_progress/stonefish/ 는 c19cf274 시점 매칭 파일 수 0 — 실측)
git worktree remove /tmp/omp-fixture-krit
```

오탐 회귀도 같이 볼 것: **현재 HEAD 에서 krit 의 깨진 링크는 0건이어야 한다.** 단
Kanban 의 daily-note 규약 `[[2026-08-16]]` 22건은 정상이므로 오탐으로 세면 안 된다
(`find_dead_links` 가 이미 이걸 어떻게 다루는지 먼저 확인할 것).

## 릴리스 관례 (누락되기 쉬움)

- 버전 bump 는 `.claude-plugin/plugin.json` (현재 `0.9.0`). **bump 안 하면 push 해도 no-op** —
  플러그인 갱신은 버전으로 해석된다(claudebase auto-memory `machine_plugin_update_resolves_by_version`).
- `CHANGELOG.md` 헤더는 산문 한 문장 관례다 (`0.9.0 — the house style was never written down`,
  `0.8.0 — a graph is not coverage`, `0.7.0 — absence is not health`).
  이번 건 후보: *"the check existed; nobody pulled the trigger"*.

---

# 부록 2 — vault ownership-gap 세션이 덧붙임 (2026-08-14, 세 번째 세션)

> 같은 날 vault 쪽 의뢰서(`1_Area/2026-08-14-harness-ownership-gap-prompt.md`)를 실행한
> 세션이다. 본문·부록 1 과 겹치지 않는 것만, 그리고 **위 서술 중 이미 낡은 것만** 적는다.
> 형식은 부록 1 의 선례를 따른다.

## 낡은 사실 정정 — omp 는 이제 0.9.0 이 아니다

부록 1 의 "릴리스 관례" 가 `현재 0.9.0` 이라 쓰는데, 같은 날 두 건이 더 들어갔다.

| 버전 | 무엇 |
|:---|:---|
| **0.9.1** (`88eb5b4`, 태그 `v0.9.1`) | `인덱스 정합` 경고가 레인과 무관하게 걸리도록 `CHECKPOINT` 수정 |
| `[Unreleased]` (`7e47718`) | `tests/conftest.py` — 앰비언트 킬스위치 격리 (테스트 전용) |

**0.9.1 은 본문 층위 3(발동)의 일부를 이미 처리했다.** `인덱스 정합` 경고는 원래
*"프로젝트 관리 작업이 아니면 이 블록 전체 무시"* 로 닫히는 블록 안에 있어서, 정작 그게
필요한 턴(실험·코드 세션이 지나가며 폴더를 리네임하는 턴)이 명시적으로 버리라는 지시를
받고 있었다. 닫는 줄이 이제 경고 3개를 이름으로 예외 처리한다.

그 과정에서 나온 기계 사실 하나 — **`omp_route_emit.py` 의 관련성 게이트는 레인 게이트가
아니다.** `is_omp_related()` 가 `.omp/` 존재만으로 True 를 반환하므로(그 함수의 첫 분기
`if not _omp_missing(): return True` — 줄번호는 `CHECKPOINT` 가 자라며 밀리니 함수로 찾을 것), 초기화된
프로젝트에서는 `OMP_ROUTE_GATE` 값과 무관하게 매 프롬프트 주입된다. 억제는 훅이 아니라
**모델이 닫는 줄을 읽고 따르는 한 층 위**에서 일어난다. 층위 3 을 설계할 때 "훅을 새로
달아야 한다" 로 가기 전에 이걸 먼저 볼 것 — 주입은 이미 되고 있다.

## 후보 E 에는 선례가 있다 — 그리고 죽었다

부록 1 의 후보 E(`external_ssot[]`)가 짚은 공백은 실재한다. 독립적으로 같은 결론에 닿은
증거가 있다: 이 vault 의 `rules.json` 에 **`secretary.external_sources[]` 가 이미 있었다.**

- 2026-08-10 커밋 `8ea53bd7` "omp secretary external_sources 신설 — 원격 constrained-albc
  현황 2건(ssh read-map) 등록". `name`/`transport`/`host`/`path`/`kind`/`convention` 형태로,
  후보 E 의 `authority`/`ref`/`what`/`mirrors` 와 사실상 같은 축이다.
- **아무도 안 읽었다.** `~/oh-my-project` 전체에서 `external_sources` 참조 0건 — 스키마에도,
  훅에도, 스킬 문서에도 없다. `derive_status`/`load_secretary_sources` 는 `sources[]` 만 본다.
- **스키마 위반이었다.** `secretary` 는 `additionalProperties: false` 에 `sources`/`surfaces`
  두 키만 허용한다. 이 필드 하나 때문에 vault 의 `rules.json` **전체가 jsonschema INVALID**
  였고 4일간 아무도 몰랐다. 제거하니 VALID.
- 2026-08-14 제거하고 내용은 `.omp/wiki/remote-state-sources.md` 로 옮겼다(복사 아님).

**두 가지가 동시에 참이다.** (1) 두 세션이 서로 모른 채 같은 공백을 짚었으니 공백은 실재한다.
(2) 그러나 **등록 자리만 만들고 소비자를 안 만들면 죽은 설정 + 스키마 위반이 된다**는 것이
이미 실증됐다. 후보 E 를 설계한다면 스키마 필드보다 **`omp-audit` 축과 `omp-brief` 열거를
같은 변경 안에서** 넣어야 한다 — CHANGELOG 0.9.0 이 말하는 "4곳 정합(schema+codify+learn+audit)"
비용이 이 축에도 그대로 붙는다.

참고로 `secretary.sources[]` 로는 못 옮긴다. 거기도 `additionalProperties: false` 라
`transport`/`host` 를 담을 자리가 없고, `path` 가 "relative path" 로 정의돼 있어 원격 경로를
넣으면 존재하지 않는 로컬 경로가 read-map 에 실린다. 새 축이 필요하다는 부록 1 의 판단은 맞다.

## 후보 B 는 기각됐다 — E 의 근거 한 줄이 영향받는다

부록 1 은 E 를 정당화하며 *"비용 대비 효과가 B 안과 같은 이유로 크다"* 고 쓴다. **그 B 는
같은 날 실측으로 기각됐다** — `docs/design/2026-08-14-resurfacing-detector-measurement.md`
(`f63f6a3`). 두 줄 요약:

- **mtime 은 항목 방치의 신호가 아니다.** 3개월 묵은 "미결" 이 든 `paper-work-split.md` 의
  mtime 이 사건 당일 **0.0d** 였다(같은 날 다른 절이 추가됨). 30일 게이트면 동기 사례가 안 잡힌다.
- **산문 마커에 해소 상태가 없다 — 오탐 3/7.** 해소를 선언하는 제목("1차 미결 전부 해소")과
  파일명 `RL-ALBC - TODO.md` 가 걸린다. 열림과 해소를 잇는 기계 판독 가능한 연결이 없다.

**E 가 자동으로 같이 죽지는 않는다.** B 의 mtime 은 *파일 안의 한 항목*이 얼마나 묵었는지를
물었고, E 의 `mirrors[]` mtime 은 *그 파일이 언제 마지막으로 손대졌는지*를 묻는다 — 후자는
파일 단위 질문이라 mtime 이 맞는 신호다(기존 `stale` kind 가 같은 이유로 유효하다).
다만 **"대조했다" 와 "편집됐다" 는 다르다**: 오늘 vault 에서 여러 세션이 문서를 만지는 동안
Notion 과 대조한 세션은 없었고 mtime 만 갱신됐다. E 를 설계한다면 mtime 이 아니라 **명시적
대조 기록**(마지막 reconcile 날짜를 사람이 적는 필드)이 필요한지부터 다툴 것 — 이게 B 기각의
진짜 전이 가능한 교훈이다.

## 진단은 셋 다 같은 곳을 가리킨다

본문 층위 2, 부록 1 의 D9~D11, vault 의뢰서의 P2 — 셋이 독립적으로 **"규칙·판정은 있었는데
재부상하지 않았다"** 에 닿았다. vault 쪽 사례는 `.omp/learned.md` 의 OBS-0002 로, 승격 조건
(evidence 3 · counter 0 · 사용자 결정)을 **전부 만족한 채 71일**을 candidate 로 있었다.
`omp-brief` 가 `ready_to_promote` 로 표시하고는 있었다 — **표시가 행동이 되지 않은 것**이다.
층위 2 를 설계할 때 "표시를 추가한다" 가 아니라 "표시를 행동으로 바꾸는 게 무엇인가" 를
질문으로 둘 것. (그 OBS 는 2026-08-14 `rejected` 로 종결했다 — 승격이 아니라 종결이 답이었다.
근거는 vault 커밋 `23a4ce3e`.)

## 본문 D안(claudebase git 함정)에 대한 독립 확증

본문이 지목한 함정을 이 세션도 **독립적으로 밟았다**. 내 `git mv` 리네임 12건이 병렬 세션의
커밋 `8677d1d6`("albc PLAN wiki 이관")에 통째로 흡수됐다 — 파일은 온전하나 이력 귀속이 어긋났고
에러는 없었다. 워킹트리 공유 = **인덱스 공유**가 원인이다.

방어로 확인된 것: `git commit -F msg -- <내 경로>` 는 부분 커밋이라 남의 staged 항목(당시
`D kmrts/Kanban.md` 등 4건)을 딸려가지 않는다 — 실측 확인. 본문 D안에 이 형태를 명시할 것.
다만 **이미 스테이징된 뒤에는 늦다** — `git mv` 는 커밋 직전에 몰아서 해야 한다.
