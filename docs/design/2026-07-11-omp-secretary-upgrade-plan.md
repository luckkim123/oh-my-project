# OMP 2.0 — Secretary-Axis Upgrade Plan (OMC v4.15.2 흡수 + 외부 조사)

| Field | Value |
|:--|:--|
| Subject harness | oh-my-project 0.3.0 (`main` @ 76f519d) |
| Reference harness | oh-my-claudecode v4.15.2 — `claudebase/docs/reference/omc-deep-analysis-v4.15.2/` (24 files) 경유 |
| Document precedent | omx `docs/2026-07-05-omc-v4.15.2-alignment-audit.md` (판정 taxonomy) + omx `docs/design/2026-05-30-omx-experiment-harness-design.md` (design 골격) |
| Prior decisions honored | `references/omc-backport-analysis.md` — T1–T25 채택, 재분석에서 반박된 45후보, §5 형제전파 0건. **본 문서는 이를 재논의하지 않는다**; 단 하나의 개정(T24)만 §4.3에서 명시적으로 논증한다. |
| External research | 2026-07-11 웹 조사 2계통: (a) AI-PM assistant 지형 2025–26, (b) 지식노동 방법론 + agentic-memory 아키텍처. 출처는 본문 인라인. |
| Date | 2026-07-11 |
| Status | **PLAN** — 구현 착수 전 사람 승인 게이트 대기 |

이 문서는 세 입력을 합성한다: OMC 심층분석(메커니즘 카탈로그), omp 현재 상태 인벤토리(부재 확인 포함), 외부 조사(도구 지형 + 방법론). 판정 어휘는 omx 선례를 따른다 — 상태축 `HAS / PARTIAL / ABSENT / NA_JUSTIFIED`, 채택축 `ADOPT / ADAPT / REJECT / DEFER`.

---

## 0. Executive verdict

**omp는 오늘 "공간 축" 하네스다 — 이 계획은 "시간 축"을 추가한다.** 현재 10 skill × 5 agent × 2 hook은 전부 폴더 구조·명명·데이터셋·환경 거버넌스(공간: 무엇이 어디 있어야 하나)에 속한다. 비서 기능 — 진행 추적, 세션 저널, TODO/blocker, 결정 기록, 상태 브리핑(시간: 무엇이 어디까지 왔고 다음은 무엇인가) — 은 전수 grep으로 **부재 확인(ABSENT verified)** 됐다. `omp-pilot`의 게이트 이력은 그 턴의 Output에만 남고, `learned.md`는 규칙 후보만 다루며, wiki는 구조 관찰 노트이지 작업 로그가 아니다.

**새 메커니즘은 전부 기존 4대 불변식과 정합하도록 설계했다** — 결정론적 grep(임베딩 영구 금지), 사람 게이트 승격, 도메인별 single-writer, fail-open python3-stdlib. 이전 backport에서 영구 REJECT된 것(Stop-hook 강제 루프, 임베딩, 자동 승격, 데이터 실물 이동)은 하나도 되살리지 않는다. 유일한 개정은 T24(훅 추가 억제)로, SessionStart/SessionEnd 2개 훅에 한해 §4.3에서 논증한다.

**외부 조사의 한 줄 결론: 비서는 "묻지 않고 추론하되, 끼어들지 않고 준비해 둔다."** 상용 AI-PM 도구의 실패 모드(수동 업데이트 이탈, 알림 피로, hallucinated status)와 interruption-cost 문헌이 가리키는 설계는 push가 아니라 pull — 세션 시작 시 2분 스캔 가능한 브리핑을 *미리 준비*해 두고, 사용자 개입은 "새로 입력"이 아니라 "자동 초안의 확인/수정"으로 좁힌다.

### Scorecard — 비서 5기능 × omp 현황

| 기능 | 현황 | 이 계획의 대응 |
|:--|:--|:--|
| 진행 추적 (progress) | ABSENT | `ledger.jsonl` 이벤트 로그 + 카운트 파생 지표 (§5.2) |
| 세션 저널 (journal) | ABSENT | append-only daybook + SessionEnd 캡처 스텁 (§5.3) |
| TODO / blocker | ABSENT | `todo.txt` 스키마 + RAID 파일, 사람만 닫음 (§5.4) |
| 결정 기록 (decisions) | PARTIAL (wiki에 구조 결정만 산발) | ADR `NNNN-slug.md` 정식 채널 (§5.5) |
| 상태 브리핑 (briefing) | ABSENT | `BRIEF.md` pull형, SessionStart 주입 (§5.6) |

---

## 1. Decisions locked in this plan (구현 전 재확인, 구현 중 재논의 금지)

| # | 결정 | 근거 |
|:--|:--|:--|
| D1 | **비서 = 두 번째 축이지 새 하네스가 아니다.** 기존 거버넌스 stage는 손대지 않고, secretary stage 3개를 *추가*한다. | omp 정체성 = "rules.json을 반복 재검사하는 관리 루프". 비서도 같은 루프 위에 얹는다 — 별도 도구로 쪼개면 `.omp/` SSOT가 이원화된다. |
| D2 | **Pull, never push.** 브리핑은 세션 시작 시 로드되는 파일이지, 사용자를 부르는 알림이 아니다. cron digest·외부 notification 없음. | interruption 복구 평균 23분, 5초 인터럽션도 에러율 3배 ([arXiv:2509.09309](https://arxiv.org/html/2509.09309v1)); unsolicited AI update는 일 3–5건이 실질 상한 ([notification budget](https://tianpan.co/blog/2026-05-13-background-agents-notification-budget-attention-economy)). |
| D3 | **Correction over creation.** 비서 파일은 자동 초안이 기본이고 사용자는 고치기만 한다. 수동 기입을 요구하는 순간 이탈한다. | todo-app abandonment 연구: "모니터링/업데이트가 부담이면 시스템을 버린다" ([Zapier](https://zapier.com/blog/why-you-hate-every-to-do-list-app/)); AI-native 실사용률 5.2% 격차 ([Chief of Staff Network 2026](https://www.chiefofstaff.network/blog/ai-era-chief-of-staff-chief-of-ai-2026)). |
| D4 | **회상은 결정론적 grep만.** 기존 불변식(learning-protocol §6.A)이 비서 축에도 그대로 적용된다. 임베딩·유사도 검색 영구 금지. | 실증적으로도 충분: Claude Code auto-memory·Karpathy LLM wiki 모두 no-embedding으로 작동 ([Claude Code Memory docs](https://code.claude.com/docs/en/memory), [LLM wiki](https://aaif.io/blog/karpathys-llm-wiki-as-agent-memory/)). |
| D5 | **저장은 `<project>/.omp/secretary/` 한 곳, 코드는 python3 stdlib 순수함수.** CLI 바이너리를 만들지 않는다(omp는 순수 플러그인 유지). 기계 로직은 `hooks/omp_secretary.py`에 — `omp_content_audit.py`가 확립한 "hook 파일 = 순수함수 라이브러리" 관용구 그대로. | omx는 CLI가 정체성이지만 omp는 처음부터 plugin-only였고 0.3.0까지 그 형태로 67 tests가 지킨다. 형태 변경은 이 계획의 목적(기능 추가)과 무관한 리스크. |
| D6 | **Journal은 append-only, 실패가 일급 콘텐츠다.** git 커밋 로그는 성공만 남긴다 — "시도했지만 안 된 것"의 캡처가 이 축의 차별점. | engineering daybook 관행 ([ntietz](https://ntietz.com/blog/using-an-engineering-notebook/)); wiki append-only 규율(§5, 0.2.0)과 동일 계열. |
| D7 | **비서 상태의 single-writer는 신규 agent `chronicler` 1개.** write scope를 `.omp/secretary/**`로 한정한다. organizer(파일 이동)·dataset-curator(manifest)와 같은 "도메인당 writer 1" 패턴의 세 번째 사례. | 탐지≠실행 분리 불변식. 검증은 기존 auditor가 새 축으로 맡는다(author≠reviewer). |
| D8 | **진행률은 쓰지 않고 파생시킨다.** "몇 % 완료"를 LLM이 추정해 적는 것을 금지 — 지표는 `ledger.jsonl`/`todo.txt` 카운트에서 코드가 계산한다. | OMC 분석의 실증 함정: marketplace가 "28 agents"라 광고하나 실제 19 — 손으로 쓴 수치는 반드시 drift한다. hallucinated-status 실패 모드의 직접 차단. |
| D9 | **닫는 건 사람이다.** blocker·risk·task의 완료 처리는 자동으로 하지 않는다. 자동은 "닫아도 될 것 같다" flag까지만. | Motion/Asana의 risk-flag 패턴 + hallucinated-completion 회피 ([Galileo failure modes](https://galileo.ai/blog/agent-failure-modes-guide)). |

---

## 2. OMC 흡수 — skill / agent / hook / MCP 축별 판정

각 항목: **메커니즘 — OMC 소스 — 판정 — omp 이식 스케치.** ADOPT는 재구현(코드 import 없음)이며, 전부 python3-stdlib + 파일 기반으로 번역된다.

### 2.1 Skills에서 흡수

**notepad 3계층 (Priority / Working / MANUAL) — ADAPT — 비서 축의 뼈대.**
OMC `.omc/notepad.md`: Priority Context(≤500자, 매 세션 주입, REPLACE), Working Memory(타임스탬프 append, 7일 TTL prune), MANUAL(영구). omp 번역: Priority→`BRIEF.md`(브리핑, 재생성), Working→`journal/YYYY-MM-DD.md`(일지, append-only·prune 없음 — D6이 TTL을 기각), MANUAL→`decisions/`(ADR, 영구). 3계층의 *역할 분리*는 채택하되 단일 파일이 아니라 파일 분리로 — grep 대상이 명확해지고 append-only와 REPLACE 규율이 파일 단위로 갈린다.

**ultragoal 이원 구조 (`goals.json` 스냅샷 + `ledger.jsonl` 불변 이벤트 로그) — ADOPT — 진행 추적의 원형.**
가변 스냅샷과 append-only 이벤트 로그의 분리가 "지금 상태"와 "언제 무엇이 막혔나(감사)"를 동시에 준다. omp 번역: `todo.txt`(스냅샷) + `secretary/ledger.jsonl`(이벤트: `task_added|task_done|blocker_opened|blocker_closed|decision_recorded|session_start|session_end`). 이미 omp에 있는 사람.md↔기계.json 페어링 규율(STRUCTURE.md↔rules.json)의 시간축 판박이.

**remember 라우터 (4목적지 분류, 묻지마 덤프 금지) — ADAPT — 캡처 skill의 내부 로직.**
OMC remember는 순수 프롬프트 라우터로 기록 요청을 project-memory/notepad/docs로 분류한다. omp 번역: 신규 `omp-log` skill이 캡처 하나로 받아 journal(사건)/todo(할 일)/raid(blocker·risk)/decisions(결정)/learned.md(규칙 후보 — **기존 heavy 채널로 넘김, 비서 축이 가로채지 않음**) 5목적지로 라우팅. "불확실하면 불확실하다고 표시" 원칙 유지.

**capture-then-curate (SessionEnd 스텁 → 다음 세션 승격 판단) — ADOPT — 자동 저널링의 핵심.**
저렴하고 bounded된(≤3초 예산) 기계적 스텁을 훅이 쓰고, 품질 판단(서사화·승격)은 다음 세션의 LLM이 한다. 자동 캡처와 게이트된 승격의 분리 — omp의 wiki(light)/learn(heavy) 2채널 철학과 동일 구조. 서드파티 clerk도 같은 패턴을 실증 ([clerk](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87)).

**wiki 6종 기계적 lint (stale/orphan/broken-ref 등, report-only) — ADAPT — 비서 위생 감사로.**
lint 항목을 비서 파일에 맞게 번역해 `omp-audit`의 새 축으로: todo.txt 스키마 위반, stale task(>30일 무변동), 미해결 blocker(>14일), BRIEF↔ledger drift, decisions 죽은 `[[링크]]`(기존 `find_dead_links` 재사용). docker 축(0.3.0)이 확립한 **warn-default** 선례 그대로 — 비서 위생은 전체 audit FAIL을 막지 않는다.

**autopilot/ralph/ultrawork/team 루프·병렬 실행 — NA_JUSTIFIED (기각 유지).**
이전 backport에서 Stop-hook 강제·병렬 실행·모호성 정량화가 전부 기각됐고(freeze 위험, detect≠execute 충돌), 비서 축은 그 판단을 바꿀 이유가 없다 — 비서는 관리 루프지 실행 루프가 아니다.

### 2.2 Agents에서 흡수

**author≠reviewer 이중 강제 (프롬프트 + `disallowedTools`) — ADOPT.**
신규 `chronicler`(sonnet, write scope `.omp/secretary/**` — organizer·dataset-curator에 이은 3번째 scoped writer)가 쓰고, 기존 `auditor`(opus, read-only)가 검증한다. chronicler frontmatter에 "자기 산출물 PASS 선언 금지" 명시 + auditor는 write 차단 유지. 신규 agent는 1개뿐 — 5→6.

**3티어 모델 라우팅 (탐색 haiku / 실행 sonnet / 판단 opus) — HAS (이미 준수).**
현행 5 agent가 이미 이 경제학을 따른다(scanner·organizer·curator=sonnet, rule-architect·auditor=opus). chronicler=sonnet — 캡처·서사화는 기계적이고, 판단(승격·검증)은 opus 몫이라는 기존 배치와 정합.

**Final_Response_Contract (마지막 메시지 = 산출물, "done"으로 끝내기 금지) — ADOPT (프롬프트 수준).**
chronicler·auditor 프롬프트에 계약 문구를 넣는다. OMC처럼 유닛테스트로 강제하는 것은 DEFER — omp 테스트는 훅·순수함수 대상이고 agent .md 계약 테스트 인프라가 없다. 텍스트 계약만으로 시작.

### 2.3 Hooks에서 흡수 — T24 개정 논증

**SessionEnd 캡처 스텁 훅 — ADOPT (T24 일부 개정).**
**SessionStart 브리핑 주입 훅 — ADOPT (동일 개정).**

T24는 OMC의 훅 3종 번들(directory-readme-injector, pre-compact, posttool-capture)을 "경량성 훼손"으로 기각했다. 그 논거의 실체는 *per-tool-use·per-prompt 훅의 상시 비용*이었다 — posttool은 도구 호출마다, injector는 프롬프트마다 돈다. 이번에 추가하는 2개는 **세션당 정확히 1회** 실행되고(시작/종료), 각각 bounded(≤3초, 출력 ≤30줄)·fail-open·stdlib이다. 세션당 상수 비용은 T24가 지키려던 것을 훼손하지 않는다. 기각 자체를 뒤집는 게 아니라 적용 범위를 정밀화하는 개정이며, `omc-backport-analysis.md`에 개정 기록을 남긴다(silent violation 금지 — 불변식 C와 같은 정신).

- `omp_session_brief.py` (SessionStart): `.omp/secretary/BRIEF.md` 존재 시 그 내용(≤30줄)을 additionalContext로 주입. 없으면 침묵. **advisory-only — 자동 재개 절대 없음** (OMC SessionStart 복원의 검증된 원칙).
- `omp_session_capture.py` (SessionEnd): 기계적 스텁만 append — timestamp, session id(정규식 `^[A-Za-z0-9][A-Za-z0-9_-]{0,255}$` 살균 — OMC omha 갭의 경로 트래버설 교훈), 세션 중 `.omp/` 변경 파일 목록. **LLM 호출 없음**; 서사화는 다음 세션 `omp-log`가 curate.

**Stop-hook persistent loop — NA_JUSTIFIED (기각 재확인).** freeze 전례(`OMC post-tool freeze pattern`)와 파일 이동 사람 승인 원칙 때문에 이전 기각 그대로. 비서 축에 루프는 없다.

**킬스위치 — ADOPT.** `OMP_SKIP_HOOKS=session_brief,session_capture` 콤마 토큰 개별 비활성. OMC `OMC_SKIP_HOOKS` 관용구 그대로 — 신규 훅이 문제를 일으키면 삭제 아닌 스위치로 끈다.

### 2.4 MCP에서 흡수

**자체 MCP 서버 — NA_JUSTIFIED (기각 유지).** T7이 이미 "파일 기본, MCP는 선택적 accelerant"로 결정했다. 비서 파일 전부 grep/Read로 충분한 크기(BRIEF ≤30줄, todo.txt 수십 줄, journal 일 단위 분할)라 persistent 서버의 이득이 없다. OMC `t` 서버의 notepad_*·wiki_*가 하는 일은 omp에선 순수함수 + 파일 규약이 대신한다. 단, OMC 툴 어휘(`notepad_read`/`wiki_query`류)는 **미래에 MCP를 붙일 때의 교체점 이름**으로 §5.1 함수명에 반영해 둔다 — T10의 "wiki_query는 미래 교체점" 결정과 같은 배려.

### 2.5 기타 크로스커팅 흡수

| 메커니즘 | 판정 | 이식처 |
|:--|:--|:--|
| managed-marker + content hash (wholesale 덮어쓰기 전 사람 수정 감지 — OMC 분석이 지적한 omp 갭#4) | ADOPT | `BRIEF.md` 헤더에 `<!-- omp-managed: sha256:... -->` — 재생성 전 해시 비교, 불일치면 STOP하고 사람에게 |
| atomic write (`omp_atomic.py`) | HAS | `ledger.jsonl` append와 `todo.txt` 재작성에 그대로 사용 |
| 완료 증거 기반 정리 (형제 세션 상태를 완료 증거 파일 있을 때만 정리) | DEFER | omp 비서는 세션별 상태 파일을 두지 않으므로(journal은 append-only) 당장 불필요; 멀티세션 충돌이 관측되면 재검토 |
| HUD/statusline·notification 데몬 | NA_JUSTIFIED | D2(pull-only)와 정면 충돌; omp에 데몬 없음 |
| trace/session_search (JSONL replay) | REJECT | ledger.jsonl이 비서 수준의 타임라인을 이미 제공; 도구 수준 replay는 실행 하네스의 것 |

---

## 3. 외부 조사 흡수 — 방법론·도구 패턴 판정

웹 조사 2계통에서 나온 패턴 중 채택분. 전부 D1–D9와 교차 검증됨.

| 패턴 | 출처 | 판정 | omp 반영 |
|:--|:--|:--|:--|
| 2-tier memory (인덱스 상시 로드 + 토픽 파일 온디맨드) | [Claude Code auto-memory](https://code.claude.com/docs/en/memory) | ADOPT | `BRIEF.md`=인덱스(상시), journal/decisions=온디맨드. 실전 검증된 no-embedding 구조 |
| ADR 5필드 (Title/Status/Context/Decision/Consequences) + 번호 prefix | [Nygard 2011](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | ADOPT | `decisions/NNNN-slug.md`. "significant한 결정만" 필터: 사소한 선택은 journal에, 되돌리기 힘든 것만 ADR |
| RAID log (Risks/Assumptions/Issues/Dependencies, owner+priority+status) | [monday.com](https://monday.com/blog/project-management/raid-project-management-template/) | ADAPT | `raid.md` 단일 파일 4섹션. "해결해야 할 것"(RAID) vs "할 일"(todo) 분리 |
| todo.txt 줄 스키마 + `key:value` 확장 | [todo.txt spec](https://github.com/todotxt/todo.txt/blob/master/README.md) | ADOPT | `(A) 2026-07-11 본문 +project @context due:… blocked-by:…` — 한 줄=한 태스크, 전 필드 grep 가능 |
| Bullet Journal migration = 재평가 (단순 carry-over 금지) | [bulletjournal.com](https://bulletjournal.com/blogs/faq/what-is-rapid-logging-understand-rapid-logging-bullets-and-signifiers) | ADOPT | `omp-review`의 핵심 스텝: 미완료 항목마다 "아직 유효한가"를 명시적으로 판정(migrate/strike/done) |
| GTD weekly review (Get Clear/Current/Creative) + AI는 종합만, 판단은 사람 | [Asian Efficiency](https://www.asianefficiency.com/productivity/gtd-weekly-review/), [Capable](https://www.dearflow.ai/blog/getting-things-done-gtd-in-the-age-of-ai) | ADAPT | `omp-review` = 사실 종합 리포트 생성까지; 우선순위 재배열은 제안 아닌 질문으로 |
| 세션 핸드오프 필드 (Goal/State of play/Key decisions/Blockers/Artifacts-참조만) | [AgentPatterns](https://www.agentpatterns.ai/agent-design/handoff-skill-context-transfer/) | ADOPT | `BRIEF.md` 섹션 구조가 곧 이것. "2분 내 스캔·복붙 금지·경로만" 원칙 |
| OKR 신호등 (green/yellow/red + 한 줄 근거) | [Mooncamp](https://mooncamp.com/blog/okr-check-in) | ADOPT | BRIEF 최상단 프로젝트 상태 한 줄. 색은 ledger 파생 규칙으로 결정(D8) — blocker open>0 = red 등 |
| commit → narrative journal (DevLog 패턴) | [DevLog](https://dev.to/zeshama/devlog-i-built-an-ai-powered-developer-journal-that-turns-git-commits-into-stories-3fdl) | ADAPT | **optional enrichment로만.** omp 대상엔 git 없는 폴더가 많다(workspace 등) — git 있으면 `omp-log`가 커밋을 서사 재료로 쓰고, 없으면 세션 스텁만으로 동작 |
| code churn = blocker proxy | [CodeScene](https://codescene.io/docs/guides/technical/code-churn.html) | DEFER | 신호 가치는 있으나 git 의존 + 오탐 위험. raid 수동 기록이 자리잡은 뒤 재검토 |
| batch digest, not push | [Height 사례](https://www.marktechpost.com/2025/01/06/meet-height-an-autonomous-project-management-platform-leading-the-next-wave-of-ai-tools/) | ADOPT | D2 그 자체. Height 서비스 종료(2025-09)는 "패턴 참고, 구현 참고 아님" |
| task-scale ceiling (5+ workstream에서 중앙 시스템 붕괴) | [Todoist 사례](https://zapier.com/blog/why-you-hate-every-to-do-list-app/) | ADOPT | 전역 대시보드 금지(프로젝트별 `.omp/` 격리 유지) + BRIEF 노출 태스크 상한(top 5) |
| access-count decay frontmatter (`last_accessed`/`access_count`) | [Vectorize consolidation](https://hindsight.vectorize.io/blog/2026/05/21/agent-memory-consolidation) | REJECT (now) | 읽기마다 쓰기가 발생해 single-writer·append-only 규율과 마찰. weekly review의 명시적 재평가가 같은 문제를 사람 게이트로 푼다 |
| `superseded_by:` frontmatter (결정 대체 추적 — Zep bi-temporal의 grep 번역) | [arXiv:2501.13956](https://arxiv.org/abs/2501.13956) | ADOPT | ADR Status 필드 + `superseded_by: NNNN` — "이 결정이 뒤집혔나"가 grep 한 번 |

---

## 4. Architecture — 비서 축의 형태

### 4.1 `.omp/secretary/` 레이아웃 (output-layout.md에 §로 추가)

```
<project>/.omp/secretary/
├── BRIEF.md              # 상시 로드 인덱스 (≤30줄, 재생성, omp-managed 마커+해시)
├── todo.txt              # todo.txt 스키마, 한 줄=한 태스크 (done은 review 때 done.txt로)
├── done.txt              # 완료 태스크 아카이브 (todo.txt 관례)
├── raid.md               # Risks/Assumptions/Issues/Dependencies — 사람만 닫음
├── ledger.jsonl          # append-only 이벤트 로그 (기계, 지표 파생의 SSOT)
├── journal/
│   └── YYYY-MM-DD.md     # daybook — append-only, 실패 일급, 세션 스텁 + 서사
└── decisions/
    └── NNNN-slug.md      # ADR 5필드, superseded_by 추적, [[wikilink]] 허용
```

- SSOT layer 소속(재생성 가능한 work layer 아님) — 단 `BRIEF.md`만은 "재생성되는 SSOT"라는 특수 지위: 원천은 ledger/todo/raid/journal이고 BRIEF는 그 파생 뷰. 그래서 managed-marker가 필수다(사람이 BRIEF를 직접 고쳤으면 파생 재생성이 그걸 덮으면 안 됨).
- 사람.md↔기계 페어링: `BRIEF.md`↔`ledger.jsonl`, `todo.txt`(단일 파일이 양쪽 겸— 사람이 읽고 기계가 파싱).
- 기존 `wiki/`·`learned.md`와의 경계: **비서 파일은 규칙 채널이 아니다.** 구조·명명에 대한 관찰은 지금처럼 learned.md(heavy)/wiki(light)로 — `omp-log`가 라우팅으로 이 경계를 지킨다(§2.1 remember). learning-protocol.md에 경계 § 추가.

### 4.2 신규 skill 3개 (10→13)

| Skill | 역할 | 게이트 | dispatch |
|:--|:--|:--|:--|
| **omp-log** | 만능 캡처: 사건→journal, 할일→todo, 막힘·위험→raid, 결정→decisions/ADR, 규칙 관찰→learned.md로 *이관*. git 있으면 커밋을 서사 재료로(optional). SessionEnd 스텁의 curate(서사화)도 여기서 | 없음 (light 캡처; 단 learned.md행은 기존 관찰 포맷 준수) | chronicler |
| **omp-brief** | ledger/todo/raid/journal 최근분 → `BRIEF.md` 재생성. 신호등 + State of play + top 5 task + open blockers + 다음 세션 goal 제안 | managed-hash 불일치 시 STOP | chronicler (생성) — auditor 아님(브리핑은 판정이 아니라 종합) |
| **omp-review** | 주간(또는 온디맨드) 리뷰: BuJo migration(항목별 재평가), stale 스캔, done.txt 이관, raid 재확인 질문, GTD get-current | **재평가 판정마다 사람 확인** (migrate/strike는 삭제성 — D9) | chronicler + auditor(위생 리포트) |

기존 skill 통합점: `omp-init`이 secretary/ 스켈레톤을 기본 생성(GATE 1에 한 줄 포함), `omp-audit`에 비서 위생 축(warn-default), `omp-pilot` 마지막에 omp-brief 1회, `omp-doctor`에 신규 훅 등록 점검 추가. route hook의 STAGE 열거에 `log|brief|review` 3개 verb 추가(+ omha `cards/omp.json` 동기 갱신 — 별도 repo 커밋 필요).

### 4.3 신규 agent 1개 + hook 2개

§2.2–2.3에서 논증 완료. 요약: `chronicler`(sonnet, write=`.omp/secretary/**`만, Final_Response_Contract, self-approve 금지) / `omp_session_brief.py`(SessionStart, ≤30줄 주입, advisory-only) / `omp_session_capture.py`(SessionEnd, 기계 스텁 append, ≤3초, LLM 없음). 둘 다 fail-open + `OMP_SKIP_HOOKS` 킬스위치. plugin.json hooks 배열 2건 추가.

### 4.4 순수함수 라이브러리 `hooks/omp_secretary.py`

`omp_content_audit.py` 관용구(순수함수 + pytest)를 따르는 단일 모듈:

```python
parse_todo_line(line) -> TodoItem | None      # todo.txt 스키마 파서 (우선순위/날짜/+project/@context/key:value)
append_ledger(root, event: dict) -> None       # omp_atomic 경유 JSONL append, ts 자동
derive_status(root) -> Status                  # ledger+todo+raid 카운트 → 신호등/지표 (D8: 유일한 진행률 계산처)
brief_hash_check(path) -> "clean"|"dirty"      # omp-managed 마커 해시 비교
session_stub(root, session_id, changed) -> None # SessionEnd 스텁 (id 살균 포함)
scan_stale(root, now) -> list[Finding]         # stale task>30d, blocker>14d, BRIEF drift — audit 축 정본
```

함수명이 미래 MCP 교체점 어휘(§2.4)를 겸한다. 전부 stdlib(json, re, hashlib, datetime, pathlib).

---

## 5. Lifecycle 규칙 (decay / promotion / 경계)

| 파일 | 쓰기 규율 | 소멸/이관 | 승격 |
|:--|:--|:--|:--|
| journal/ | append-only (truncate 영구 금지) | 없음 — daybook은 안 지운다. BRIEF는 최근 7일만 읽음 | 규칙 관찰 발견 시 learned.md로 **재작성** 이관(복사 아님 — 채널 규율) |
| todo.txt | 재작성 허용(스냅샷) — 단 atomic write | done → review 때 done.txt | 없음 |
| raid.md | append + status 갱신 | 닫힘은 사람만(D9); stale>14d는 BRIEF에 노출 | issue가 반복 패턴이면 wiki 노트로 |
| decisions/ | 생성 후 불변 — 뒤집을 땐 새 ADR + `superseded_by` | 삭제 없음 | 없음 (ADR이 이미 최종 형태) |
| ledger.jsonl | append-only, 기계만 씀 | 없음 (일 단위 이벤트 수십 건 규모 — 캡 불필요, 관측 후 재평가) | 없음 |
| BRIEF.md | omp-brief만 재생성 (managed-hash) | 매 재생성이 곧 갱신 | 없음 (파생 뷰) |

---

## 6. Consolidated roadmap

구현은 이 순서의 단일 리스트로 (omx 관례 — phase 없음, #0이 최우선). 각 항목이 독립 커밋 단위이고, 전 항목 공통 완료 조건: pytest 추가 + 기존 67 tests 무회귀.

| # | Item | Leverage | Idiom sketch |
|:--|:--|:--|:--|
| 0 | `hooks/omp_secretary.py` + tests | 전 기능의 기계 기반 — 파서·ledger·파생지표가 없으면 나머지는 산문뿐 | §4.4 함수 6개, `test_secretary.py` (스키마 왕복·살균·해시) |
| 1 | `references/secretary-protocol.md` + output-layout.md §추가 | 파일 계약의 SSOT — skill들이 인용할 정본 | 레이아웃(§4.1)+lifecycle(§5)+todo.txt 스키마 명세 |
| 2 | `agents/chronicler.md` | single-writer 확립 — 이후 skill이 전부 이 위에 | sonnet, write scope 명시, Final_Response_Contract |
| 3 | `omp-log` skill | 캡처가 없으면 브리핑할 원천이 없다 — 최초의 사용자 가치 | 5목적지 라우터, git enrichment는 `if .git exists` 분기 |
| 4 | `omp_session_capture.py` (SessionEnd) + plugin.json | 자동 캡처 — D3의 "사용자는 고치기만"이 여기서 시작 | 스텁 append ≤3초, 살균, fail-open, 킬스위치 |
| 5 | `omp-brief` skill | 축의 얼굴 — "지금 어디까지 왔나"에 답함 | derive_status + 핸드오프 필드 + top5 + 신호등 |
| 6 | `omp_session_brief.py` (SessionStart) + plugin.json | pull 브리핑 완성 — 세션 시작이 곧 인수인계 | BRIEF 존재 시 ≤30줄 주입, advisory-only |
| 7 | `omp-review` skill | 부패 방지 — 이게 없으면 stale의 무덤(GTD의 교훈) | BuJo migration + done.txt 이관 + 사람 확인 게이트 |
| 8 | `omp-audit` 비서 위생 축 | 검증 없는 캡처는 자기만족 — auditor가 감시 | `scan_stale` 소비, warn-default (docker 축 선례) |
| 9 | route hook STAGE 확장 + omha `cards/omp.json` | 발견 가능성 — 라우팅에 없는 stage는 없는 기능 | `log\|brief\|review` 추가, 카드 동기 (별도 repo) |
| 10 | `omp-init`/`omp-pilot`/`omp-doctor` 통합 | 신규 프로젝트가 비서를 공짜로 얻음 | init 스켈레톤 생성, pilot 말미 brief, doctor 훅 점검 |
| 11 | `omc-backport-analysis.md` T24 개정 기록 + learning-protocol.md 경계 § | silent violation 방지 — 결정 문서가 현실과 일치 | §2.3 논증 요약을 개정 항목으로 |
| 12 | README + CHANGELOG + version 0.4.0 | 릴리스 규율 (0.3.0 관례) | Removed/Added/Changed/Verification/Notes |

전 항목이 skill prose·agent .md·python3-stdlib 순수함수·훅 2개·문서이며 — **CLI 바이너리, MCP 서버, 임베딩, Node 런타임, 자동 승격, 데이터 이동을 하나도 만들지 않는다.** 신규 훅 2개는 세션당 1회 실행으로 T24 개정 범위 안이다.

구현 방식 권장: 항목이 독립적이고 spec이 이 문서로 명확하므로 subagent-driven-development(태스크별 fresh implementer + spec-compliance/quality reviewer)가 적합 — release-grade 변경의 기존 관례.

---

## 7. Deliberately not adopting (스코프 경계 확정)

- **Stop-hook persistent loop / 자율 실행 루프** — freeze 전례 + 파일 조작 사람 승인 원칙 정면 충돌. 비서는 관리 루프다 (기존 기각 재확인).
- **임베딩·유사도 회상** — learning-protocol §6.A 영구 금지. 비서의 "예전에 이런 일 있었나?"도 grep이다.
- **push 알림·cron digest·외부 messenger 연동** — D2 위반. 브리핑은 파일이고, 읽는 시점은 사용자가 정한다.
- **blocker/task 자동 close** — D9 위반. hallucinated-completion의 문이다.
- **LLM이 쓰는 진행률 %** — D8 위반. 수치는 전부 `derive_status` 파생.
- **전역 크로스 프로젝트 대시보드** — task-scale ceiling 붕괴 사례 + `.omp/` per-project 격리 원칙. 여러 프로젝트 종합은 사용자가 각 BRIEF를 여는 것으로 충분.
- **git 신호 필수화** — omp 대상엔 git 없는 폴더(iCloud workspace 등)가 많다. git은 enrichment, 전제 아님.
- **CLI 바이너리 / 자체 MCP 서버** — D5·T7. omp는 순수 플러그인으로 남는다.
- **notepad TTL prune의 journal 적용** — daybook은 지우지 않는다(D6). TTL은 BRIEF의 "최근 7일 읽기"로 대체 — 데이터는 남고 뷰만 좁힌다.
- **access-count decay frontmatter** — 읽기가 쓰기를 유발해 append-only·single-writer와 마찰. weekly review의 명시적 재평가가 사람 게이트 버전의 같은 답.

## 8. Open items (구현 전 사용자 결정 필요 — 본 계획을 막지 않음)

1. **skill 명명**: `omp-log`/`omp-brief`/`omp-review` vs `omp-journal`/`omp-status`/`omp-weekly` — 본문은 전자 가정.
2. **BRIEF 재생성 트리거**: omp-log 캡처 시마다 자동 재생성 vs omp-brief 명시 호출만 — 본문은 명시 호출 가정(단순 우선), 사용 후 불편하면 자동화.
3. **secretary 스켈레톤을 omp-init 기본 생성**으로 할지 opt-in으로 할지 — 본문은 기본 생성 가정(빈 파일 비용 ≈ 0).
4. **버전**: 0.4.0(축 추가) vs 1.0.0(정체성 확장 선언) — 본문은 0.4.0 가정.
