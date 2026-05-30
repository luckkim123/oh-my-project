# oh-my-project (omp)

> Multi-agent orchestration harness for **project-folder management & evolution** — a second brain that knows your local directory. Ships **generic**, specializes to **your** project the more you use it.

계보: [`oh-my-claudecode`](https://github.com/Yeachan-Heo/oh-my-claudecode) (omc) → `oh-my-docs` (omd) → `oh-my-scholar` (oms) → **`oh-my-project` (omp)**

## 철학 — 폴더 ≈ 살아있는 지식

oms/omd가 **매번 새 산출물을 만드는** 생성 파이프라인이라면, omp는 **하나의 살아있는 `.omp/`를 계속 갱신하는** 관리 루프다. `claude /init`이 1회성 스냅샷을 뱉는다면, omp는 쓸수록 그 폴더에 특화되는 비서다.

| 일반 init | omp |
|:---|:---|
| 1회 스캔 → 정적 문서 | 1회 스캔 → 살아있는 `.omp/` → 쓸수록 진화 |
| 모든 프로젝트 동일 | 배포는 범용, 사용은 특화 |
| 구조만 | 구조 + 명명 규칙 + dataset 추적 |

## 핵심 비대칭 — 배포 가능 + 특화 동시 만족

```
하네스 로직 (스킬·에이전트)   = 범용·불변   (모든 사용자 동일)
범용 프리셋 (references/presets) = 범용 시드   (하네스가 제공)
특화 SSOT  (<프로젝트>/.omp/)   = 프로젝트별 발산 (쓸수록 특화)
```

로직은 범용으로 고정, 산출물(`.omp/`)만 프로젝트별로 발산한다. 이 비대칭이 "배포 + 특화"를 동시에 만족시킨다.

## Stage 골격 (관리 루프)

```
  omp-init      1회 부트스트랩 — 폴더 스캔(귀납) + 프리셋 매칭 합성 → .omp/ 생성
       ━━━ GATE: 초안 rules.json 승인 ━━━
  omp-codify    구조·명명 규칙 성문화 (rules.json + STRUCTURE/NAMING.md)
  omp-organize  규칙 위반 탐지 → 안전 재배치 (mv→검증→삭제, trash 경유)
  omp-dataset   dataset 등록·SHA256·split·lineage (manifest.json) — 메타데이터-only
  omp-doc       사람용 문서 생성·갱신 (PROJECT.md 등)
  omp-learn     관찰 → 규칙 승격 (사람 승인 게이트) ← 진화의 핵심
  omp-audit     규칙 준수 검증 (read-only PASS/FAIL)
  omp-pilot     통째 오케스트레이션 (.omp 없으면 init 흡수)
```

## "범용→특화" 진화 — 2채널

obsidian이 두 번째 뇌인 것처럼, omp는 누적된 컨텍스트를 grep으로 회수한다.

- **무거운 채널 (규칙)**: `learned.md` 관찰 누적 → `omp-learn` 승격 판단 → **사람 승인** → `rules.json` 진화 (`specificity` 0→1 상승)
- **가벼운 채널 (패턴/결정)**: `.omp/wiki/*.md` 자동 누적 → 다음 세션 grep 회수 (승인 불필요)

무거운 건 게이트, 가벼운 건 자동 — oms/omd의 wiki(자동) vs 게이트(승인) 분리를 계승.

## `.omp/` SSOT (사람용 .md + 기계용 .json 이중)

```
<프로젝트>/.omp/
├── PROJECT.md     STRUCTURE.md   NAMING.md   DATASETS.md   ← 사람이 읽음
├── rules.json     manifest.json                            ← audit hook이 읽음
├── learned.md                                              ← 승격 대기 관찰
└── wiki/                                                   ← 자동 누적 (grep 회수)
```

## Agents (5)

| agent | model | 권한 | 역할 |
|:---|:---|:---|:---|
| project-scanner | sonnet | read-only | 폴더 인벤토리·구조 귀납 |
| rule-architect | opus | read-only | 규칙 설계·프리셋 합성·승격 판단 |
| organizer | sonnet | write | **유일한 파일 이동 agent** (안전 프로토콜 강제) |
| dataset-curator | sonnet | write(manifest) | 체크섬·split·lineage (데이터 안 옮김) |
| auditor | opus | read-only | 규칙 준수 검증 (탐지만, 이동 안 함) |

**불변 계약**: 파일 이동은 organizer만 (쓰기 단일 집중). 탐지(auditor) ≠ 실행(organizer) 분리. dataset은 메타데이터-only (DVC/git-lfs 감지 시 위임).

## 라우팅

omp는 **도메인 처리기**(프로젝트 관리 도메인)다. 작업방식 레인(SP/OMC) 판정은 [`oh-my-heroacademia`](https://github.com/luckkim123/oh-my-heroacademia)(omha)가 담당 — omp는 레인을 정하지 않는다. omha가 레인을 잡은 뒤, omp의 UserPromptSubmit hook(`omp_route_emit.py`)이 프로젝트 도메인 안에서 어느 **STAGE**(init/codify/organize…)인지 매 턴 `STAGE(project) → …` 한 줄로 선언한다. PostToolUse hook(`omp_verify_emit.py`)은 `.omp/` 편집·파일 이동 후 무결성 리마인더를 주입한다 (자동 수정·freeze 안 함).

## 크로스플랫폼

Mac / Linux / Windows. 모든 hook은 **python3 stdlib only + fail-open** (에러 시 세션 안 막음), 모든 경로는 `pathlib` (OS 중립), 삭제는 OS별 trash 경유.

## Status

v0.2.1 — 9 skill + 5 agent + 6 preset + 4 reference card + 4 hook(route/verify/atomic/`__init__`) + 스키마 구현. 0.2.0에서 `content_conventions[]` 규칙 타입(노트 본문 컨벤션: present/absent × body/frontmatter)과 content·wikilink audit 축 추가. 0.2.1에서 `find_dead_links`의 Obsidian 테이블 이스케이프 파이프 `[[Note\|alias]]` 거짓 양성 수정. 훅·스키마·content/link 순수함수는 pytest로 검증(49 passed). **runtime end-to-end 실측 완료** (plugin reload 세션에서 route/verify hook·init→codify→organize→audit 흐름·work/ 분리 실동작 확인). 자세한 내역은 [CHANGELOG](CHANGELOG.md).
