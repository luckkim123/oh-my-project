# OMP 2.0 — Secretary-Axis Upgrade Plan (OMC v4.15.2 흡수 + 외부 조사)

| Field | Value |
|:--|:--|
| Subject harness | oh-my-project 0.3.0 (`main` @ 76f519d) |
| Reference harness | oh-my-claudecode v4.15.2 — `claudebase/docs/reference/omc-deep-analysis-v4.15.2/` (24 files) 경유 |
| Document precedent | omx `docs/2026-07-05-omc-v4.15.2-alignment-audit.md` (판정 taxonomy) + omx `docs/design/2026-05-30-omx-experiment-harness-design.md` (design 골격) |
| Prior decisions honored | `references/omc-backport-analysis.md` — T1–T25 채택, 재분석에서 반박된 45후보, §5 형제전파 0건. **본 문서는 이를 재논의하지 않는다**; 단 하나의 개정(T24)만 §4.3에서 명시적으로 논증한다. |
| External research | 2026-07-11 웹 조사 2계통: (a) AI-PM assistant 지형 2025–26, (b) 지식노동 방법론 + agentic-memory 아키텍처. 출처는 본문 인라인. |
| Date | 2026-07-11 |
| Status | **APPROVED** (2026-07-11 사용자 승인 "ㄱㄱ" — 본문 가정 채택: omp-log/brief/review 명명·BRIEF 명시 호출·init 기본 생성·0.4.0·journal 태그·PreToolUse 게이트 보류) — 구현 진행 |
| Deep analysis (v2) | 2026-07-11 ultracode 2-workflow(50 agents): ① 계획 5렌즈 감사(OMC 커버리지·omp 코드 정합·기존 결정 준수·설계 비판·웹 인용 검증 — 24 findings 중 19 생존), ② OMC 24문서 8클러스터 import 감사(검증 생존 후보 11). 적대 검증 생존분만 반영; 잠긴 결정을 건드리는 것은 §1.1 개정 대기 블록으로 분리(자동 반영 금지). |

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
| D2 | **Pull, never push.** 브리핑은 세션 시작 시 로드되는 파일이지, 사용자를 부르는 알림이 아니다. cron digest·외부 notification 없음. | 4.4초 인터럽션이 순차 오류를 3배로 만든다(2.8초=2배) — Altmann, Trafton & Hambrick (2014, *J. Exp. Psychol.: General*); "복구 23분"은 Gloria Mark 계열의 통속화 수치(원논문 미확정으로 표기); unsolicited AI help는 self-threat을 유발해 기피된다 ([arXiv:2509.09309](https://arxiv.org/html/2509.09309v1)); 알림 일 3–5건 상한은 실무 관찰 heuristic ([notification budget](https://tianpan.co/blog/2026-05-13-background-agents-notification-budget-attention-economy), 비피어리뷰 — 참고용). |
| D3 | **Correction over creation.** 비서 파일은 자동 초안이 기본이고 사용자는 고치기만 한다. 수동 기입을 요구하는 순간 이탈한다. | todo-app abandonment 연구: "모니터링/업데이트가 부담이면 시스템을 버린다" ([Zapier](https://zapier.com/blog/why-you-hate-every-to-do-list-app/)); 참고: 현재 PM 워크플로우의 AI 자동화 침투율은 5.2%로 낮다 ([Chief of Staff Network 2026](https://www.chiefofstaff.network/blog/ai-era-chief-of-staff-chief-of-ai-2026) — 현황 통계, 이탈 인과의 근거는 아님). |
| D4 | **회상은 결정론적 grep만.** 기존 불변식(learning-protocol §6.A)이 비서 축에도 그대로 적용된다. 임베딩·유사도 검색 영구 금지. | 실증적으로도 충분: Claude Code auto-memory·Karpathy LLM wiki 모두 no-embedding으로 작동 ([Claude Code Memory docs](https://code.claude.com/docs/en/memory), [LLM wiki](https://aaif.io/blog/karpathys-llm-wiki-as-agent-memory/)). |
| D5 | **저장은 `<project>/.omp/secretary/` 한 곳, 코드는 python3 stdlib 순수함수.** CLI 바이너리를 만들지 않는다(omp는 순수 플러그인 유지). 기계 로직은 `hooks/omp_secretary.py`에 — `omp_content_audit.py`가 확립한 "hook 파일 = 순수함수 라이브러리" 관용구 그대로. | omx는 CLI가 정체성이지만 omp는 처음부터 plugin-only였고 0.3.0까지 그 형태로 67 tests가 지킨다. 형태 변경은 이 계획의 목적(기능 추가)과 무관한 리스크. |
| D6 | **Journal은 append-only, 실패가 일급 콘텐츠다.** git 커밋 로그는 성공만 남긴다 — "시도했지만 안 된 것"의 캡처가 이 축의 차별점. | engineering daybook 관행 ([ntietz](https://ntietz.com/blog/using-an-engineering-notebook/)); wiki append-only 규율(§5, 0.2.0)과 동일 계열. |
| D7 | **비서 상태의 writer는 도메인 분할.** 서사·판단 콘텐츠(journal 본문·decisions·todo·raid·BRIEF)의 유일한 *LLM writer*는 신규 agent `chronicler`(write scope `.omp/secretary/**`), 기계 append(ledger.jsonl·journal 세션 스텁)는 훅이 소유한다. 두 writer는 라인 단위 disjoint — 훅=append-only 스텁 라인만, chronicler=서사 블록만, 기존 라인 truncate 금지. | organizer(이동)·dataset-curator(manifest)의 "도메인당 LLM-writer 1" 계보 + 탐지≠실행 분리. 검증은 기존 auditor가 새 축으로(author≠reviewer). hook+agent 공동 소유는 omp 최초라 경계를 라인 단위로 명문화(§1.1 개정 반영). |
| D8 | **진행률은 쓰지 않고 파생시킨다.** "몇 % 완료"를 LLM이 추정해 적는 것을 금지 — 지표는 `ledger.jsonl`/`todo.txt` 카운트에서 코드가 계산한다. | OMC 분석의 실증 함정: marketplace가 "28 agents"라 광고하나 실제 19 — 손으로 쓴 수치는 반드시 drift한다. hallucinated-status 실패 모드의 직접 차단. |
| D9 | **닫는 건 사람이다.** blocker·risk·task의 완료 처리는 자동으로 하지 않는다. 자동은 "닫아도 될 것 같다" flag까지만. | Motion/Asana의 risk-flag 업계 관행(1차 출처 미확인) + hallucinated-completion 회피를 위한 human sign-off 권고 ([Galileo failure modes](https://galileo.ai/blog/agent-failure-modes-guide)). |

### 1.1 잠긴 결정 개정 (ultracode 검증발 — **2026-07-11 사용자 승인, D-표 반영 완료**)

**[D7 문구 재정의 후보]** D7("비서 상태의 single-writer는 chronicler 1개")은 두 지점에서 자기 설계와 마찰한다: (1) §4.1이 journal을 "세션 스텁 + 서사"로 명시하는데 스텁은 SessionEnd 훅(LLM 없음)이, 서사는 chronicler가 같은 파일에 쓴다. (2) SSOT의 single-writer는 동시-쓰기 경합 해소 장치이고 기존 3개 도메인(T20)은 전부 agent만 쓰는 토폴로지였다 — hook+agent 공동 소유는 이 계획이 처음이라 "3번째 사례"는 부정확하다. **제안 재정의**: "chronicler는 서사·판단 콘텐츠(journal 본문, decisions, todo, raid, BRIEF)의 유일한 *LLM writer*이고, 기계 append(ledger.jsonl, journal 스텁)는 훅이 소유한다 — 두 writer는 라인 단위 disjoint(훅=append-only 스텁 라인만, chronicler=서사 블록만, 기존 라인 truncate 금지)." 승인 시 D7 문구와 §4.1에 ledger=훅-owned, journal=훅(스텁)+chronicler(서사) 공동임을 명시한다.

**[D2/D3/D9 인용 정정]** 외부 검증에서 근거 열의 인용 3건이 원문과 어긋남이 확인됐다. 결정 방향은 유지하되 근거를 다음과 같이 정정한다 (승인 시 D-표 반영):
- **D2**: "복구 평균 23분, 5초 인터럽션 에러율 3배"는 arXiv:2509.09309가 보고하지 않는 수치. 정정 → 23분은 Gloria Mark(UC Irvine) 계열의 통속화 수치(원논문 미확정으로 표기), 순차오류 배증은 Altmann, Trafton & Hambrick (2014, *J. Exp. Psychol.: General* — 4.4초 인터럽션에 3배, 2.8초에 2배). arXiv:2509.09309는 "unsolicited AI help의 self-threat 유발" 주장에만 인용.
- **D2**: "일 3–5건 알림 상한"(tianpan.co)은 비피어리뷰 블로그의 저자 휴리스틱 — "실무 관찰 heuristic, 재검증 필요"로 격하 표기.
- **D3**: "AI-native 실사용률 5.2%"는 오독 — 원문 5.2%는 PM 워크플로우의 *자동화 침투율*이지 사용률 격차가 아님. Zapier(todo-app abandonment) 인용만으로 D3 논거는 충분하므로 이 통계는 삭제 또는 "현재 PM 자동화 침투율 5.2%"로 재서술.
- **D9**: Galileo 블로그에는 "risk-flag" 패턴이 없음 — 인용 범위를 "hallucinated-completion 회피를 위한 human sign-off 권고"로 좁히고, risk-flag는 Motion/Asana 업계 관행(1차 출처 미확인)으로 표기.

---

## 2. OMC 흡수 — skill / agent / hook / MCP 축별 판정

각 항목: **메커니즘 — OMC 소스 — 판정 — omp 이식 스케치.** ADOPT는 재구현(코드 import 없음)이며, 전부 python3-stdlib + 파일 기반으로 번역된다.

### 2.1 Skills에서 흡수

**notepad 3계층 (Priority / Working / MANUAL) — ADAPT — 비서 축의 뼈대.**
OMC `.omc/notepad.md`: Priority Context(≤500자, 매 세션 주입, REPLACE), Working Memory(타임스탬프 append, 7일 TTL prune), MANUAL(영구). omp 번역: Priority→`BRIEF.md`(브리핑, 재생성), Working→`journal/YYYY-MM-DD.md`(일지, append-only·prune 없음 — D6이 TTL을 기각), MANUAL→`decisions/`(ADR, 영구). 3계층의 *역할 분리*는 채택하되 단일 파일이 아니라 파일 분리로 — grep 대상이 명확해지고 append-only와 REPLACE 규율이 파일 단위로 갈린다. 또한 이 매핑은 T11로 이미 채택된 Priority Context(압축-생존 채널)를 대체하지 않는다 — **BRIEF.md와 T11은 병존하며 목적이 다르다**: T11=*세션 중* 컨텍스트 압축 생존, BRIEF=*세션 간* 인수인계 브리핑(파생 뷰). 이 역할 경계도 learning-protocol.md 경계 §에 명시한다.

**ultragoal 이원 구조 (`goals.json` 스냅샷 + `ledger.jsonl` 불변 이벤트 로그) — ADOPT — 진행 추적의 원형.**
가변 스냅샷과 append-only 이벤트 로그의 분리가 "지금 상태"와 "언제 무엇이 막혔나(감사)"를 동시에 준다. omp 번역: `todo.txt`(스냅샷) + `secretary/ledger.jsonl`(이벤트: `task_added|task_done|blocker_opened|blocker_closed|decision_recorded|gate_passed|session_start|session_end`, 각 이벤트에 선택적 `stage` 필드 `init|codify|organize|dataset|env|doc|null`). omp-pilot이 게이트 통과 시 `gate_passed{stage, decision}`을 남기면(§4.2 통합점) omp-brief가 "지난 세션은 organize GATE 2에서 끝남 → dataset부터 재개" 같은 구체적 재개 제안을 derive_status에서 파생할 수 있다 — §0이 지적한 "게이트 이력이 턴 Output에만 남는다"는 갭을 ledger가 실제로 메우는 지점. 이미 omp에 있는 사람.md↔기계.json 페어링 규율(STRUCTURE.md↔rules.json)의 시간축 판박이.

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

**agent frontmatter ↔ 실제 배선 정합성 회귀 테스트 — ADOPT (예방적).**
OMC 12-agents-catalog §Divergences는 선언↔구현 drift가 방치된 실증(존재하지 않는 `preamble.ts`/`vision.ts` 참조, frontmatter opus vs SDK 레지스트리 sonnet)을 기록한다. omp는 별도 컴파일 레지스트리가 없어 model-티어 drift는 구조적으로 부재하지만, SKILL.md의 `subagent_type="oh-my-project:<name>"` 참조가 실재 `agents/<name>.md`와 1:1인지는 현재 아무도 검사하지 않는다 — `test_plugin_integrity.py`의 3-way sync가 agent(디렉토리-관례 discovery)에는 미치지 않는 갭이고, chronicler로 5→6 확장하는 이 시점이 정확히 그 갭이다. 이식: pytest 1개 — (1) `agents/*.md` frontmatter model이 `opus|sonnet|haiku`인지, (2) `subagent_type` 참조↔agents 파일 양방향 대응인지 grep 검증. stdlib만.

### 2.3 Hooks에서 흡수 — T24 개정 논증

**SessionEnd 캡처 스텁 훅 — ADOPT (T24 일부 개정).**
**SessionStart 브리핑 주입 훅 — ADOPT (동일 개정).**

T24는 OMC의 훅 3종 번들(directory-readme-injector, pre-compact, posttool-capture)을 "경량성 훼손"으로 기각했다. 그 논거의 실체는 *per-tool-use·per-prompt 훅의 상시 비용*이었다 — posttool은 도구 호출마다, injector는 프롬프트마다 돈다. 이번에 추가하는 2개는 **세션당 정확히 1회** 실행되고(시작/종료), 각각 bounded(≤3초, 출력 ≤30줄)·fail-open·stdlib이다. 세션당 상수 비용은 T24가 지키려던 것을 훼손하지 않는다. 기각 자체를 뒤집는 게 아니라 적용 범위를 정밀화하는 개정이며, `omc-backport-analysis.md`에 개정 기록을 남긴다(silent violation 금지 — 불변식 C와 같은 정신).

**두 번째 기각 행도 함께 개정한다.** `omc-backport-analysis.md`의 45-반박 exclude 표에는 T24와 별개로 "session/compaction state" 행(L127)이 있고, 그 근거는 상시 비용이 아니라 "a new PreCompact/SessionEnd hook would dilute the lightweight identity"다. 이 행이 `session-end cleanup`을 명시 지목하므로, 이 행을 재논의 대상에 넣지 않으면 SSOT상 여전히 기각된 메커니즘을 구현하는 셈이 된다. 개정 논거를 이 행에 한정해 정밀화하면: 이 행이 우려한 것은 *cleanup 목적의 상태 관리 훅*(형제 세션 상태 정리·pre-compact 체크포인트)이고, 본 계획의 SessionEnd 훅은 cleanup을 하지 않는다(기계 스텁 append 1회, 상태 정리·삭제 없음, LLM 없음) — 정체성 희석의 실체인 상태 관리 로직의 상시 유지 부담이 발생하지 않는다. 로드맵 #11의 개정 기록에 T24와 이 행 **둘 다**를 남긴다.

- `omp_session_brief.py` (SessionStart): `.omp/secretary/BRIEF.md` 존재 시 그 내용(≤30줄)을 additionalContext로 주입. 없으면 침묵. **advisory-only — 자동 재개 절대 없음** (OMC SessionStart 복원의 검증된 원칙).
- `omp_session_capture.py` (SessionEnd): 기계적 스텁만 append — timestamp, session id(정규식 `^[A-Za-z0-9][A-Za-z0-9_-]{0,255}$` 살균 — OMC omha 갭의 경로 트래버설 교훈), 세션 중 `.omp/` 변경 파일 목록. **LLM 호출 없음**; 서사화는 다음 세션 `omp-log`가 curate.

**Stop-hook persistent loop — NA_JUSTIFIED (기각 재확인).** freeze 전례(`OMC post-tool freeze pattern`)와 파일 이동 사람 승인 원칙 때문에 이전 기각 그대로. 비서 축에 루프는 없다.

**킬스위치 — ADOPT.** `OMP_SKIP_HOOKS=route,verify,session_brief,session_capture` 콤마 토큰 개별 비활성 — 신규 훅 2개만이 아니라 **기존 거버넌스 훅 2개(route/verify)까지 하나의 공통 게이트로 통일**한다(현재는 route_emit 오탐·verify_emit 소음 시 plugin.json에서 훅을 통째로 빼는 것 외 비활성 수단이 전무). OMC `OMC_SKIP_HOOKS` 관용구 그대로, main() 진입부 3~4줄.

**PreToolUse 경로-스코프 게이트 (chronicler write-scope 하네스 강제) — 검토 필요 (별도 T24 개정 논증 선행, 이번 로드맵 제외).**
OMC 19-delegation-enforcement-gate의 패턴: PreToolUse가 Write/Edit 호출을 가로채 `permissionDecision:'deny'` + continue로 agent의 쓰기 경로를 하네스 레벨에서 강제(deny해도 세션은 안 죽고 agent가 고쳐 재시도, fail-open). 레버리지는 실재한다 — chronicler의 `.omp/secretary/**` 한정은 "부분 허용 write scope"라 `disallowedTools`(전면 차단)로 표현 불가능하고, 프롬프트 신뢰 외 강제 수단이 없어 오작동·prompt-injection 시 `.omp/rules.json`을 고쳐도 못 막는다(§4.3). 그러나 이 훅은 **per-tool-use로 돌아 §2.3이 T24를 연 근거("세션당 1회")를 정확히 벗어난다.** 채택하려면 "경량성 vs 불변식 보호"의 별도 개정 논증 + chronicler 1개 agent 한정 최소 게이트 + subagent 식별 선행이 전제 — 사용자 승인 전 로드맵에 넣지 않는다.

### 2.4 MCP에서 흡수

**자체 MCP 서버 — NA_JUSTIFIED (기각 유지).** T7이 이미 "파일 기본, MCP는 선택적 accelerant"로 결정했다. 비서 파일 전부 grep/Read로 충분한 크기(BRIEF ≤30줄, todo.txt 수십 줄, journal 일 단위 분할)라 persistent 서버의 이득이 없다. OMC `t` 서버의 notepad_*·wiki_*가 하는 일은 omp에선 순수함수 + 파일 규약이 대신한다. 단, OMC 툴 어휘(`notepad_read`/`wiki_query`류)는 **미래에 MCP를 붙일 때의 교체점 이름**으로 §5.1 함수명에 반영해 둔다 — T10의 "wiki_query는 미래 교체점" 결정과 같은 배려.

### 2.5 기타 크로스커팅 흡수

| 메커니즘 | 판정 | 이식처 |
|:--|:--|:--|
| managed-marker + content hash (wholesale 덮어쓰기 전 사람 수정 감지 — OMC 분석이 지적한 omp 갭#4) | ADOPT | `BRIEF.md` 헤더에 `<!-- omp-managed: sha256:... -->` — 재생성 전 해시 비교, 불일치면 STOP하고 사람에게 |
| atomic write (`omp_atomic.py`) | HAS(atomic_write_json) + PARTIAL(append 프리미티브 신규 필요) | `todo.txt`/`done.txt` **전체 재작성**에만 `atomic_write_json`(tempfile→fsync→os.replace) 사용. `ledger.jsonl` append는 이 함수로 못 한다 — 전체 교체 방식이라 append 의미와 어긋나고 동시 writer 시 한쪽 배치를 조용히 덮어쓴다. §4.4 `append_ledger` 참조 |
| 로그-경계 시크릿 마스킹 (`redactTokens()` 중앙화 — 13-hud §2.3, issue #1162) | ADOPT | `redact_secrets(text)` 순수함수(stdlib `re`) — Bearer/`sk-ant-api`/`ghp_`류/`AKIA`/`xoxb-` 형태를 journal·ledger **쓰기 직전** 마스킹. append-only 영구 파일에 커밋 메시지·스택트레이스 속 API 키가 박제되는 경로가 계획 안에 이미 존재(omp-log의 git 서사, SessionEnd 스텁)하므로 쓰기 전 마스킹이 유일한 방어선 (§4.4) |
| 완료 증거 기반 정리 (형제 세션 상태를 완료 증거 파일 있을 때만 정리) | DEFER | omp 비서는 세션별 상태 파일을 두지 않으므로(journal은 append-only) 당장 불필요; 멀티세션 충돌이 관측되면 재검토 |
| HUD/statusline·notification 데몬 | NA_JUSTIFIED | D2(pull-only)와 정면 충돌; omp에 데몬 없음 |
| trace/session_search (JSONL replay) | REJECT | ledger.jsonl이 비서 수준의 타임라인을 이미 제공; 도구 수준 replay는 실행 하네스의 것 |

**iCloud 등 sync 폴더에서 ledger append 방어** (safe-fileops의 iCloud rename 실패 계보): (1) 각 이벤트를 완결 JSON 한 줄+개행으로만 `O_APPEND` write(POSIX 줄 단위 append는 원자적 — 부분줄 방지), (2) `derive_status`/`scan_stale` 파서는 JSON 파싱 실패 줄을 "스킵 + stderr 1줄 경고"로 관용(오염 1줄이 D8 파생지표 전체를 죽이지 않게), (3) `scan_stale`이 `secretary/` 안의 `NAME N.ext` conflict-copy 패턴(예: `ledger 2.jsonl`)을 stale 위생 항목으로 탐지·경고. §5의 멀티세션 DEFER는 "경고까지는 지금, 잠금은 관측 후"로 정밀화.

### 2.6 거버넌스 축 개선 후보 (OMC 재정독 부산물 — 비서 축과 분리)

비서 축(시간)과 무관하게 기존 공간 축(폴더 거버넌스)의 미흡점을 채우는 흡수분. 전부 read-only 감사 finding·pytest·기존 훅 편승이라 새 훅·agent·서브시스템이 없고, 상당수가 비서 축 순수함수(`brief_hash_check`·`scan_stale`·`find_dead_links`)를 재사용하므로 **secretary 축 이후 착수**가 싸다. 판정 어휘·warn-default 선례는 docker 축(0.3.0)과 동일.

| 메커니즘 | OMC 소스 | 판정 | omp 이식처 |
|:--|:--|:--|:--|
| **wiki/learned.md 6종 기계적 lint** (orphan/stale/broken-ref/oversized/stuck-candidate/structural-contradiction, report-only) | 11-knowledge-lifecycle §"Lint" | ADAPT | §2.1의 비서 lint는 `.omp/secretary/**`만 스코프 — 정작 원 대상인 거버넌스축 `wiki/*.md`·`learned.md`는 `find_dead_links` 하나뿐. `omp_content_audit.py`에 5종 추가(broken-ref는 기존 재사용): stale(last-seen>N일), orphan(피링크 0), oversized, stuck-candidate(`status:candidate` 장기 미승격), contradiction(동일 glob에 상충 path_constraint). 자동 승격·삭제 없음, warn-default |
| **구조 경로 drift 감지** | v4.15.0 `workflow-drift-guard`(18-delta) — Stop-hook이 아닌 감사 finding으로 재구성 | ADOPT | `scan_structure_drift`: `rules.json.structure.directories[].path` + STRUCTURE.md/DATASETS.md 인용 경로를 `Path.exists()` 순회, 사라진/개명 경로=warn. CHANGELOG 2회 기록된 최다 실전 실패(맨손 mv 후 인덱스 유령 경로)를 산문 리마인더→기계 WARN으로 전환. auditor의 기존 축은 manifest 경로만 보고 rules.json 구조 경로 자체는 안 봄 — 정확히 그 갭 |
| **STRUCTURE/NAMING/PROJECT.md managed-marker + hash** (governance 절반) | omp 갭#4 (gaps/oh-my-project.md) | ADOPT | §2.5가 BRIEF.md에만 채택한 marker를 원 대상에도: omp-doc/omp-codify가 통째 재생성 직전 `work/versions/`의 "omp 최종본" 해시와 현재 파일 해시 비교, 불일치 시 침묵 덮어쓰기 대신 "사람이 손댔음 — overwrite/merge/skip?" 1줄 게이트. `brief_hash_check` 패턴·기존 롤백층 재사용 |
| **verify_emit content-hash advisory throttle** | 02-hooks §"advisory throttle" | ADAPT | `omp_verify_emit.py`는 stateless라 organizer 배치 mv 시 동일 리마인더가 매번 재출력. reason 해시별 last_emitted를 세션 스코프 JSON에 기록, 쿨다운(5분) 내 스킵. IO 실패는 fail-open 재출력(안전 신호를 침묵시키지 않음) |

**skill 파이프라인 frontmatter 계약** — SKILL.md에 선택적 `pipeline`/`next-skill`/`handoff` 필드를 두고, `test_plugin_integrity.py`에 "모든 `next-skill` 값이 실재 skill 디렉토리로 resolve"를 assert하는 pytest 1개(16-skills-authoring `parseSkillPipelineMetadata`). omp의 실제 stage chain(omp-pilot의 init-absorb→codify→organize→dataset→doc, 이번의 brief-at-pilot-end)이 전부 SKILL.md 산문에만 살아 있어 rename·10→13 확장 후 stage/handoff 실재를 아무도 검사하지 않는 갭 — 로드맵 #10이 필요로 하는 바로 그 chaining. 순수 메타데이터+테스트, 훅 0.

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
| journal 인라인 이벤트 태그 (`[BLOCKER:<raid-id>]`/`[LESSON:<slug>]`/`[DECISION:<adr-id>]`) + 추출 정규식 병기 | OMC 09-research evidence-tag grammar | ADAPT | journal은 기본이 자유서술(D6)이고 태그는 뒤에 붙이는 **선택적 grep 훅**일 뿐(강제 아님). `scan_journal_tags`가 grep해 "반복 실패 태그"를 종합, omp-review가 wiki 승격 후보로 *제시*(자동 승격 아님 — D9). raid.md는 이미 R/A/I/D 4섹션 헤더가 grep 가능한 분류라 별도 category 필드는 추가하지 않음. 대안 경로는 Open item 5 |

---

## 4. Architecture — 비서 축의 형태

### 4.1 `.omp/secretary/` 레이아웃 (output-layout.md에 §로 추가)

```
<project>/.omp/secretary/
├── BRIEF.md              # 상시 로드 인덱스 (≤30줄 그리고 ≤2000자, 재생성, omp-managed 마커+해시)
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
- **BRIEF.md 크기 상한은 줄 수와 문자 수 둘 다**: ≤30줄 *그리고* ≤2000자(OMC Zod 하드캡과 동일 — 매 SessionStart 상시 주입 컨텍스트 예산 보호, `priorityMaxChars` 소프트캡 선례). 줄 수만으로는 각 줄이 임의로 길어져 예산이 무력화된다.
- **초과 시 절단 우선순위**(구현자 자의 절단 방지): top5 task → top3, open blocker → 개수만, decisions 요약 → 참조 경로만. `derive_status` 반환 카운트를 그대로 써서 truncate하며, 필수 3줄(managed 마커 / 신호등+근거 / State-of-play 1줄)은 절대 자르지 않는다.

### 4.2 신규 skill 3개 (10→13)

| Skill | 역할 | 게이트 | dispatch |
|:--|:--|:--|:--|
| **omp-log** | 만능 캡처: 사건→journal, 할일→todo, 막힘·위험→raid, 결정→decisions/ADR, 규칙 관찰→learned.md로 *이관*. git 있으면 커밋을 서사 재료로(optional). SessionEnd 스텁의 curate(서사화)도 여기서 | 없음 (light 캡처; 단 learned.md행은 기존 관찰 포맷 준수) | chronicler |
| **omp-brief** | ledger/todo/raid/journal 최근분 → `BRIEF.md` 재생성. 신호등 + State of play + top 5 task + open blockers + 다음 세션 goal 제안 | managed-hash 불일치 시 STOP | chronicler (생성) — auditor 아님(브리핑은 판정이 아니라 종합) |
| **omp-review** | 주간(또는 온디맨드) 리뷰: BuJo migration(항목별 재평가), stale 스캔, done.txt 이관, raid 재확인 질문, GTD get-current | **재평가 판정마다 사람 확인** (migrate/strike는 삭제성 — D9) | chronicler + auditor(위생 리포트) |

기존 skill 통합점: `omp-init`이 secretary/ 스켈레톤을 기본 생성(GATE 1에 한 줄 포함), `omp-audit`에 비서 위생 축(warn-default), `omp-pilot` 마지막에 omp-brief 1회, `omp-doctor`에 신규 훅 등록 점검 추가. route hook의 STAGE 열거에 `log|brief|review` 3개 verb 추가 — 이때 **두 하드코딩 지점을 동시에 갱신해야 한다**: `hooks/omp_route_emit.py`의 CHECKPOINT 상수 문자열 *그리고* `tests/test_plugin_integrity.py`의 `ROUTE_STAGES` 튜플(카탈로그↔`skills/omp-<stage>/` 폴더 1:1 왕복 검증 테스트). 후자를 빠뜨리면 "기존 67 tests 무회귀" 완료 조건이 반드시 깨진다. 신규 skill 3개는 `.claude-plugin/plugin.json`의 `skills[]`에도 등록해야 registered↔dir 왕복 테스트를 통과한다. (omha `cards/omp.json` 동기 갱신은 별도 repo 커밋.)

### 4.3 신규 agent 1개 + hook 2개

§2.2–2.3에서 논증 완료. 요약: `chronicler`(sonnet, write=`.omp/secretary/**`만, Final_Response_Contract, self-approve 금지) / `omp_session_brief.py`(SessionStart, ≤30줄 주입, advisory-only) / `omp_session_capture.py`(SessionEnd, 기계 스텁 append, ≤3초, LLM 없음). 둘 다 fail-open + `OMP_SKIP_HOOKS` 킬스위치. plugin.json hooks 배열 2건 추가.

**chronicler write-scope는 도구 강제가 아니라 프롬프트 서술 제약이다.** organizer·dataset-curator와 마찬가지로 omp에는 "특정 경로 서브트리에만 쓰기 허용"을 강제하는 tool-level 메커니즘이 없다(`disallowedTools`는 도구 *전면* 차단이지 경로 스코핑이 아님). chronicler의 `.omp/secretary/**` 한정은 frontmatter가 아니라 Role/프롬프트 텍스트 수준이며, 하네스 레벨 강제 후보(PreToolUse 스코프 게이트)는 §2.3의 검토 항목이다.

**훅의 secretary root 해석 규칙**: 두 훅은 payload(`json.load(sys.stdin)`)의 `cwd`에서 시작해 `.omp/`를 만날 때까지 상향 탐색(ascend)하되, safe-fileops의 realpath-inside-root 가드를 재사용하고 홈 디렉토리에서 정지한다. `.omp/`를 못 찾으면 **no-op**(비-omp 세션은 비서 축 대상 아님) + fail-open 침묵. cwd에서 `.omp` 존재만 보는 route_emit 방식을 그대로 쓰면 서브디렉토리 시작 시 브리핑 소실, 멀티 프로젝트에서 잘못된 BRIEF 주입이 생긴다.

### 4.4 순수함수 라이브러리 `hooks/omp_secretary.py`

`omp_content_audit.py` 관용구(순수함수 + pytest)를 따르는 단일 모듈:

```python
parse_todo_line(line) -> TodoItem | None      # todo.txt 스키마 파서 (우선순위/날짜/+project/@context/key:value)
append_ledger(root, event: dict) -> None       # O_APPEND 직접(완결 JSON 1줄+개행, flush+fsync) — omp_atomic 경유 아님. atomic_write_json은 todo/done 전체 재작성 전용
derive_status(root) -> Status                  # ledger+todo+raid 카운트 → 신호등/지표 (D8 유일 계산처). 파싱 실패 줄은 skip+stderr 경고
brief_hash_check(path) -> "clean"|"dirty"      # omp-managed 마커 해시 비교
session_stub(root, session_id, changed, last_stage=None) -> None # SessionEnd 스텁 (id 살균 + 선택적 stage)
scan_stale(root, now) -> list[Finding]         # stale task>30d, blocker>14d, BRIEF drift, conflict-copy(`NAME N.ext`) — audit 축 정본
redact_secrets(text) -> str                    # 로그-경계 시크릿 마스킹 (§2.5) — journal/ledger 쓰기 직전 통과
scan_journal_tags(root) -> list[TagRef]        # journal 인라인 태그([BLOCKER:/LESSON:/DECISION:]) grep 추출 (§3 규약)
```

함수명이 미래 MCP 교체점 어휘(§2.4)를 겸한다. 전부 stdlib(json, re, hashlib, datetime, pathlib). `redact_secrets`·`scan_journal_tags`의 정규식은 `secretary-protocol.md`에 파서와 나란히 명시한다(OMC evidence-tag grammar 관례 — 문법과 추출기가 한 문서에).

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
| 0 | `hooks/omp_secretary.py` + tests | 전 기능의 기계 기반 — 파서·ledger·파생지표·마스킹·태그추출이 없으면 나머지는 산문뿐 | §4.4 함수 8개(`redact_secrets`·`scan_journal_tags` 포함), `test_secretary.py` (스키마 왕복·살균·해시·마스킹·태그 grep) |
| 1 | `references/secretary-protocol.md` + output-layout.md §추가 | 파일 계약의 SSOT — skill들이 인용할 정본 | 레이아웃(§4.1)+lifecycle(§5)+todo.txt 스키마 명세 |
| 2 | `agents/chronicler.md` | single-writer 확립 — 이후 skill이 전부 이 위에 | sonnet, write scope 명시, Final_Response_Contract |
| 3 | `omp-log` skill | 캡처가 없으면 브리핑할 원천이 없다 — 최초의 사용자 가치 | 5목적지 라우터, git enrichment는 `if .git exists` 분기, journal/ledger 쓰기 직전 `redact_secrets` 통과, 선택적 인라인 태그 규약 |
| 4 | `omp_session_capture.py` (SessionEnd) + plugin.json | 자동 캡처 — D3의 "사용자는 고치기만"이 여기서 시작 | 스텁 append ≤3초, 살균, fail-open, 킬스위치 |
| 5 | `omp-brief` skill | 축의 얼굴 — "지금 어디까지 왔나"에 답함 | derive_status + 핸드오프 필드 + top5 + 신호등 |
| 6 | `omp_session_brief.py` (SessionStart) + plugin.json | pull 브리핑 완성 — 세션 시작이 곧 인수인계 | BRIEF 존재 시 ≤30줄 주입, advisory-only |
| 7 | `omp-review` skill | 부패 방지 — 이게 없으면 stale의 무덤(GTD의 교훈) | BuJo migration + done.txt 이관 + `scan_journal_tags`로 반복 실패 태그 종합→wiki 승격 후보 *제시* + 사람 확인 게이트 |
| 8 | `omp-audit` 비서 위생 축 | 검증 없는 캡처는 자기만족 — auditor가 감시 | `scan_stale` 소비, warn-default (docker 축 선례) |
| 8b | `omp-audit` 거버넌스 위생 축 (§2.6) | secretary 함수 재사용으로 기존 wiki/구조 갭을 저비용 충당 | wiki/learned.md 6종 lint + `scan_structure_drift`(`Path.exists()` 순회), 전부 warn-default, `omp_content_audit.py`에 얹음 |
| 8c | agent 정합성 회귀 테스트 (§2.2) | chronicler 5→6 확장 시점 — 선언↔배선 drift 예방 | `test_agent_integrity.py`: frontmatter model 정적 검증 + `subagent_type` 양방향 grep |
| 9 | route hook STAGE 확장 + omha `cards/omp.json` | 발견 가능성 — 라우팅에 없는 stage는 없는 기능 | `log\|brief\|review` 추가, 카드 동기 (별도 repo) |
| 10 | `omp-init`/`omp-pilot`/`omp-doc`/`omp-codify`/`omp-doctor` 통합 | 신규 프로젝트가 비서를 공짜로 얻음 + 거버넌스 SSOT 재생성 보호 | init 스켈레톤 생성, pilot 말미 brief + 게이트별 `gate_passed` ledger 기록, doctor 훅 점검, omp-doc/omp-codify 재생성 직전 managed-hash로 사람 수정 감지(§2.6), skill 파이프라인 frontmatter 계약 + pytest(§2.6) |
| 11 | `omc-backport-analysis.md` 개정 기록 + learning-protocol.md 경계 § | silent violation 방지 — 결정 문서가 현실과 일치 | §2.3 논거를 **T24 그리고 45-반박 표 "session/compaction state" 행(L127)** 둘 다의 개정 항목으로; **secretary 축의 형제(oms/omd) 전파 판단도 §5 형식으로 기록**(예상: 도메인 비대칭으로 전파 0 — oms/omd는 산출물 단위 생성 파이프라인이라 daybook/세션 저널 개념이 없음) |
| 12 | README + CHANGELOG + version 0.4.0 | 릴리스 규율 (0.3.0 관례) | Removed/Added/Changed/Verification/Notes |

**기존 항목 편승(신규 항목 아님):** `OMP_SKIP_HOOKS` 4훅 통일은 #4·#6의 plugin.json 훅 작업에 3~4줄로, verify_emit content-hash throttle은 그 verify_emit 편집에 함께 편승한다(§2.6).

전 항목이 skill prose·agent .md·python3-stdlib 순수함수·훅 2개·읽기전용 감사 검사·pytest·문서이며 — **CLI 바이너리, MCP 서버, 임베딩, Node 런타임, 자동 승격, 데이터 이동을 하나도 만들지 않는다.** 신규 훅 2개는 세션당 1회 실행으로 T24 개정 범위 안이고, §2.6 항목은 전부 감사 finding·테스트라 훅 수를 늘리지 않는다.

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
2. **BRIEF 재생성 트리거**: omp-log 캡처 시마다 자동 재생성 vs omp-brief 명시 호출만 — 본문은 명시 호출 가정(단순 우선). ⚠️ **write-only 함정 주의**: 캡처(journal/ledger 스텁)는 SessionEnd 훅으로 자동·전 세션 누적되지만 유일한 상시 read 경로는 SessionStart의 BRIEF 주입이다. 명시 호출이 기본값이면 omp-brief를 부르지 않는 세션마다 BRIEF가 stale/부재 → SessionStart 침묵 → 캡처만 쌓이고 read 경로가 죽는다(상용 도구의 수동-업데이트 이탈 실패 모드 그대로). 대안(SessionEnd에서 derive_status로 신호등+top5 한 줄 기계 재생성)은 T24 개정 논거(훅=단일 목적)·managed-hash 계약과 충돌하므로 채택하려면 그 두 제약의 재논증이 필요 — 이 저울이 이 항목의 실제 결정 내용이다.
3. **secretary 스켈레톤을 omp-init 기본 생성**으로 할지 opt-in으로 할지 — 본문은 기본 생성 가정(빈 파일 비용 ≈ 0).
4. **버전**: 0.4.0(축 추가) vs 1.0.0(정체성 확장 선언) — 본문은 0.4.0 가정.
5. **journal 인라인 태그 vs ledger 이벤트 확장**: §3은 journal 서사에 선택적 grep 태그(`[BLOCKER:]`/`[LESSON:]`/`[DECISION:]`)를 채택했지만, 같은 목적을 이미 계획된 `append_ledger`에 `lesson_recorded` 등 이벤트 타입을 추가하는 쪽으로 흡수하면 파서가 하나 줄고 "지표 파생 SSOT=ledger" 원칙(D4·§4.1 페어링)과 더 정합적이다. 태그(서사 친화, 파서 +1) vs ledger 확장(SSOT 단일, 캡처 시 명시 이벤트 필요) 중 택일 — 본문은 태그를 가정하되 구현 착수 전 확정 요망.
6. **PreToolUse 경로-스코프 게이트 (§2.3 검토 항목)**: chronicler write-scope의 하네스 강제 vs 훅 경량성(per-tool-use는 T24 원 논거의 정중앙) — 채택하려면 별도 T24 개정 논증이 선행돼야 한다. 이 저울(무결성 강제 vs 경량성)은 사용자 승인 사항.
7. ~~**§1.1 잠긴 결정 개정 대기**~~ — 2026-07-11 사용자 승인으로 D-표 반영 완료 (§1.1은 개정 이력으로 보존).
