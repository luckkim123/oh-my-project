# OMC Backport Analysis — oh-my-project (omp)

omp 의 init 스코핑 게이트·consensus 레이어·organize 루프·자가학습 누적(wiki/notepad/
verifier 토큰)은 **oh-my-claudecode (OMC)** 의 검증된 패턴을 프로젝트 폴더 관리·진화 도메인으로
옮겨온 것이다. OMC 가 업데이트되면 *무엇이 바뀌었고 omp 를 갱신해야 하는지* 판단할 영속 기준이
필요하다. OMC 는 CHANGELOG 가 없고(GitHub commit/release 만 존재) 개별 파일 버전도 없으므로,
"diff 기준"을 이 문서가 자체 보관한다.

> **이 문서는 배포 plugin 의 references/ 라 개인 환경에 비의존이다.** OMC 경로는 *공개 plugin
> 내부 구조*(상대 표현)로만 적는다. 특정 머신의 절대경로·작업 메모·사용자 조직 체계는 박지 않는다.

> **도메인 비대칭 주의**: oms/omd 는 "매번 새 산출물을 만드는 생성 파이프라인"이고, omp 는
> "하나의 살아있는 `.omp/` 를 계속 갱신하는 관리 루프"다. OMC 패턴을 옮길 때 *단계=생성 step*
> 이 아니라 *단계=관리 루프 phase* 로 재해석한다. 이 차이가 아래 채택/제외의 근거를 가른다.

---

## §1. OMC 4.14.4 구조 스냅샷 — backport 원천 컴포넌트

OMC plugin 은 **이중 구조**다: `skill-bodies/<name>/SKILL.md` 가 전체 로직이고,
`skills/<name>/SKILL.md` 는 시작 컨텍스트를 가볍게 유지하기 위한 *compact 참조 shim*
(본문을 `skill-bodies/` 에서 로드). backport 의 원천은 항상 `skill-bodies/` 쪽이다.

| 원천 (OMC 4.14.4 내부 경로) | 무엇을 가져왔나 |
|:---|:---|
| `skill-bodies/deep-interview/SKILL.md` | Round 0 topology · 차원별 모호성 판정 · challenge agents(contrarian/simplifier/ontologist) · soft limits · 3-point injection → **omp-init** 의 스코핑 게이트 골격(폴더 정체·구조 의도·명명 컨벤션·dataset 경계의 모호성 해소) |
| `skill-bodies/plan/SKILL.md`, `skill-bodies/ralplan/SKILL.md` | RALPLAN-DR consensus(Principles/Drivers/Options≥2/steelman/tradeoff/ADR) · 순차 강제(병렬 금지) 프롬프트 규율 → **rule-architect** 의 규칙 변경 합의(큰 rules.json 변경·learn 승격이 파일 이동을 유발할 때) |
| `skill-bodies/autopilot/SKILL.md` | brief→완성 단계 오케스트레이션 + 게이트 골격 → **omp-pilot** (`.omp` 없으면 init 흡수 → codify→organize→dataset→doc) |
| `skill-bodies/ralph/SKILL.md` | 결함=PRD·passes:true 게이트까지 fix/verify 루프·no scope reduction → **omp-organize** 가 omp-audit PASS 까지 도는 루프(위반 탐지→재배치→재감사) |
| `agents/analyst.md` | 사전 진단·요구 분석 사상 → init 스코핑의 폴더 정체 판정 |
| `agents/architect.md` | steelman/antithesis/tradeoff → **rule-architect 에 흡수**(별도 consensus agent 신설 안 함) |
| `agents/planner.md` | 구조 설계·역할 분해 → rule-architect 의 STRUCTURE/NAMING 설계 |
| `agents/critic.md` | pre-commitment · assumption(VERIFIED/REASONABLE/FRAGILE) · pre-mortem · self-audit → **auditor 의 위반 판정 기법** |
| OMC MCP 도구 서버 (`wiki_*`/`notepad_*`/`shared_memory_*`/`state_*`) | 누적·압축생존·핸드오프 *사상*. ⚠️ omp 는 **.md degrade 가 기본**이고 MCP 는 선택 가속 — Node MCP 를 새로 넣지 않는다 |

---

## §2. 분석 기준 버전 + diff 기준

- **분석 기준 snapshot = OMC 4.14.4.** 이 문서가 backport 원천을 읽을 때 본 OMC 버전이다
  (당시 plugin 의 `package.json`·`.claude-plugin/plugin.json`·`.claude-plugin/marketplace.json`
  세 곳 모두 `"version": "4.14.4"`). **이것은 *분석 시점의 스냅샷*이지 런타임 핀이 아니다** —
  `~/.claude/settings.json` 의 omc marketplace 선언(`repo: Yeachan-Heo/oh-my-claudecode`)에는
  버전·commit-SHA 가 없어 **OMC 는 항상 marketplace 최신을 자동 추종**한다. oms/omd/omp 어디에도
  OMC 를 특정 버전으로 묶는 핀은 없다. 따라서 OMC 업그레이드에 별도 작업이 필요 없고,
  아래 diff 기준은 *backport 채택/제외 결정이 여전히 유효한지* 재검토하기 위한 것일 뿐이다.
- **diff 기준**: OMC 는 CHANGELOG 가 없다(GitHub commit/release 만). 다음 OMC 업데이트 시,
  위 §1 원천 파일들(`skill-bodies/{deep-interview,plan,ralplan,autopilot,ralph}/SKILL.md`,
  `agents/{analyst,architect,planner,critic}.md`)의 diff 를 직접 보고 omp 갱신 여부를 판단한다.
- 판단 규칙: OMC 업데이트가 **§3 의 *채택* 영역**을 바꾸면 → 대응 backport 갱신 검토.
  **§3 의 *제외* 영역**을 새로 건드리면 → 제외 결정이 여전히 유효한지 재검토.

---

## §3. 채택·제외 매핑 (내부 backport 작업 ID = Tn)

> Tn 은 이 repo 의 내부 backport 작업 식별자(니모닉)다. 각 행은 *무엇이 바뀌었나*로
> 자족 기술하므로 외부 plan 문서 없이도 읽힌다. oms(논문)·omd(문서)와 동형이되 도메인만 다르다.

### 채택 (adopt)

| Tn | OMC 패턴 | omp 적용 (실제 변경) |
|:---|:---|:---|
| T1 | deep-interview/ralplan 의 단계 경계 | init↔codify↔organize 경계 규약. 별도 scoping·consensus agent **신설 안 함**(init 스킬·rule-architect 로 흡수). 단계=관리 루프 phase 로 재해석(생성 step 아님) |
| T2 | critic 4기법 | `agents/auditor.md` 가 critic 의 *정신*을 채택(명칭·기법 라벨은 박지 않음 — omp 어휘로 재구현). pre-mortem("어떤 재배치가 데이터를 깰까")은 `<Why_This_Matters>`의 drift 사고 서사로, self-audit(LOW confidence→사람 확인)은 `<Constraints>` "should/probably/seems 금지 + 검사 미실행 표기"로, assumption 검증은 **loud-fail 평가계약**(파싱실패·필수필드누락=즉시 전체 FAIL, broken≠empty 구분)으로 흡수 — critic 4기법보다 정밀하나 `pre-commitment`/`VERIFIED-REASONABLE-FRAGILE` 라벨 자체는 미삽입 |
| T4 | ralplan RALPLAN-DR + architect steelman | `agents/rule-architect.md` 가 RALPLAN-DR 의 *합의 규율*을 채택(`<Consensus_RALPLAN_DR_Protocol>` XML 블록·steelman/ADR 라벨은 박지 않음 — omp 어휘로 재구현). "큰 rules.json 변경·learn 승격이 파일 이동을 유발하므로 보수적 합의가 필요하다"는 정신을 **evidence-trace 강제**(모든 규칙이 scan/learned/preset 출처 추적, 추측 규칙 금지) + **one-way ratchet conservative promotion**(반복·반례0 증거 바 미달이면 candidate 로만 hold) + **human approval gate**(proposal-only, 자기채택 3중 금지)로 구현. RALPLAN-DR 의 Options≥2/steelman/Deliberate-Short 모드 구분은 별도 프로토콜로 분리하지 않고 "fewer, evidenced rules" 단일 보수 규율로 단순화 |
| T5 | ralplan 순차 합의 | `skills/omp-codify/SKILL.md` 가 규칙 변경 시 순차 강제(병렬 금지) — 규칙은 파일 이동을 유발하므로 동시 변경 금지. consensus 산출 = `.omp/` 안 별도 파일(아래 T7) |
| T7 | shared_memory 핸드오프 | 단계 간 전달 = `.omp/` 파일이 **기본**(learned.md·wiki/·consensus 노트), MCP 는 선택 미러(부재 시 .md degrade) |
| T8 | deep-interview 게이트 | `skills/omp-init/SKILL.md` 스코핑 게이트 — Round 0 topology + 4차원 **정성** 판정(폴더 정체/구조 의도/명명 컨벤션/dataset 경계, 수치화 0) + challenge 3종 + soft limits + 사람 승인(초안 rules.json 게이트). data-fragile flag(이동 위험 폴더 표시) |
| T8b | autopilot wiring | `skills/omp-pilot/SKILL.md` `<Steps>` 에 `.omp` 부재 시 init 흡수 분기 + 큰 규칙 변경 시 codify --consensus 분기 삽입 — 엔진이 pilot 경로에서 실제 발동(죽은 코드 방지) |
| T10 | wiki 누적 (가벼운 채널) | `<project>/.omp/wiki/*.md` + 결정론적 grep 이 **기본**, `wiki_query(category)` 는 추상 함수(미래 MCP 교체점). 패턴·결정 자동 append(승인 불필요) — "범용→특화" 진화의 가벼운 채널 |
| T11 | notepad 압축생존 | omp-pilot 진입 시 `.omp/notepad.md`(또는 learned.md `## Priority Context`)에 safe-fileops 3원칙(mv→검증→삭제, trash 경유, rename 지양) + 게이트 기록(.md 기본) |
| T12 | verifier request-id | `agents/auditor.md` 에 스냅샷 상관 토큰(rules.json mtime·해시 + manifest SHA256 + 위반ID) — organize 루프 multi-round 의 stale-PASS 재사용 차단. checksum 상관이 manifest SHA256 과 직접 맞물림 |
| T13 | ralph regression 사상 | `skills/omp-organize/SKILL.md` 에 재배치 후 **구조-regression**(rules.json 위반 0 + manifest 경로 정합 + dataset SHA256 불변) 전수 재audit — 파일이 깨지지 않았음을 기계 검증 |
| T14 | (omp 자체 라우팅) | `hooks/omp_route_emit.py` STAGE 카탈로그 = 8단계(init/codify/organize/dataset/doc/learn/audit/omp-pilot) 열거 |
| T15 | state 경로 | SSOT = `<project>/.omp/` 고정(`.omp/specs`·`sessions/{sid}` 미검증 세그먼트 없음). 30s state-MCP 트랩은 *미래 대비 메모만* |
| T16 | (계약 이력) | `CHANGELOG.md` 신설 — commit-SHA 버저닝 유지하되 hook·rules.schema 계약 변경을 명문 기록(oms/omd 톤 통일) |
| T17 | (omp 고유) wiki 가벼운 채널 ↔ learn 무거운 채널 분리 | OMC wiki(자동)/게이트(승인) 분리를 **2채널 진화**로 구체화: wiki/ 자동 누적(grep) vs learned.md→omp-learn→rule-architect 승격→사람 승인→rules.json. specificity 0→1 추적 |
| T18 | OMC `REFERENCE.md` artifact-first 핸드오프 + descriptor(kind/path/contentHash/producer) | `.omp/work/{scans,versions,plans,audits,tmp}` 가 이 정신 — 큰 중간물(스캔 인벤토리·이동 계획·감사 리포트)을 control plane 에 복붙하지 않고 파일로 두고 경로로 참조. SSOT(.omp 상단)와 work layer 분리(output-layout.md) |
| T19 | OMC Platform Support (Windows=native 미지원, tmux 의존 → WSL2 권장) | omp 는 **tmux·Node 의존 없음** — hook=python3 stdlib + 경로=pathlib + 삭제=OS별 trash 분기. 따라서 **omp 는 OMC 보다 Windows 친화적**(WSL 불요). 크로스플랫폼은 omp 의 의도적 강점이지 OMC 흉내가 아님 |

#### 채택 — OMC 4.14.4 심층 재분석 (2026-05-30, 60후보→45반증/7생존)

> 권위문서 §5 의 6패턴을 넘어 OMC 원본(19 agents+40 skills+dist/{lib·hooks·features}+docs24)을 5영역 병렬
> 정독→후보별 적대 반증(author≠review)→opus 종합(workflow wf_11040f52, 58 agents, 2.7M tokens). 생존 7건은
> 전부 "런타임 무관 + python stdlib 10줄 이하"(포팅이 아닌 *정신만* 채택). 반증 45건은 아래 제외 표 참조.

| Tn | OMC 패턴 (원천) | omp 적용 (실제 변경) |
|:---|:---|:---|
| T20 | `dist/lib/atomic-write.js` (tempfile→fsync→rename) | `hooks/omp_atomic.py` (`atomic_write_json`, stdlib `tempfile`+`os.fsync`+`os.replace`). omp-codify/learn 의 rules.json 쓰기·versions/ 스냅샷을 이 헬퍼 경유로 강제 — 부분쓰기로 SSOT 손상 방지. (must: omp 는 *사용자 파일 이동*엔 safe-fileops 강제하나 *자기 상태 파일* 쓰기엔 보호 없던 비대칭 해소) |
| T21 | `skill-bodies/omc-doctor/` 설치 자가진단 | `skills/omp-doctor/SKILL.md` — hooks 설치·python3 가용성·reference 카드 존재 진단(omp-audit 이 가정하는 *.omp 존재 이전*의 설치 gap). ⚠️ rules.json 스키마 검증은 omp-audit 소관이라 doctor 에서 제외(중복 회피) |
| T22 | `dist/lib/worktree-cleanup-safety.js` `validateWorktreeRemovalTarget` | `references/safe-fileops.md`+`agents/organizer.md` 에 경계 검증 — 이동 target realpath(symlink 해소)가 project root 안인지 확인, 밖이면 거부. iCloud symlink 탈출 가드. stdlib 5줄(포팅 아님) |
| T23 | `dist/lib/swallowed-error.js` `logSwallowedError` | 두 hook 의 bare `except` 에 stderr 1줄(에러 맥락) — fail-open 유지하며 디버그 가능. except 당 1줄(모듈 포팅 아님) |
| T25 | OMC hook non-blocking 재주입 철학(매 턴 주입하되 차단 안 함) | `hooks/omp_route_emit.py` **init 발견성** — cwd 에 `.omp/` 부재 시 STAGE 줄 다음 "아직 .omp/가 없다 — omp-init 먼저" 힌트(부재 전용 마커, 존재 시 억제=false nag 방지). best-effort+fail-open, cwd 상대(sub-dir false-neg 무해). 사용자가 init 필요를 *모를* 발견성 gap 해소이지 자동 실행 아님. 사용자 런타임 제안(2026-05-30) |

> **T24 = 의도적 no-add**: directory-readme-injector / pre-compact / posttool-capture 3종은 각각 가치는
> 있으나 전부 hook 수를 2→3 으로 늘려 경량 정체성(T19)을 희석 → 단일 묶음으로 **추가 안 함**. 실증 필요
> 발현 시 단일 통합 hook 으로 재검토.

### 제외 (exclude — 사유 포함)

| OMC 패턴 | 제외 사유 |
|:---|:---|
| scoping-agent / consensus-agent 류 **신설** | init 스킬·rule-architect 와 중복 → 확장으로 흡수 |
| **임베딩 검색 / 의미 검색** | 파일·규칙 매칭은 **결정론적 grep 만**. 임베딩은 "비슷해 보이는" 오탐으로 잘못된 폴더에 파일을 옮길 위험 — organize 가 데이터를 망가뜨림. 현재도 미래도 영구 금지 |
| **state MCP 실호출** | 관리 루프 철학에 과잉. `.omp/` (.md) 가 압축생존·세션 간 핸드오프 더 잘함. 30s 트랩은 문서화만 |
| **ambiguity 수치화**(가중합·threshold·stability_ratio) | 정성 게이트 채택 — magic number 근거 약함. "이 폴더가 무엇인가"는 정성 판정이 정직 |
| persistent-mode **Stop-hook 강제** | freeze 위험 + 파일 이동은 사람 승인이 필수라 자동 루프 위험. organize 의 audit-PASS 루프로 충분. 보류 |
| **multi-perspective / realist / adversarial escalation** | pre-mortem·self-audit 와 중복, auditor "탐지만 하고 멈춤"(탐지≠실행 분리)과 충돌 |
| 코드 전용 런타임 15+ (comment-checker·code-simplifier·ast/lsp·python_repl·ultragoal·loop_authority 등) | 도메인 무관. 단 lsp/ast 는 미래 omp-doc 의 코드 인벤토리 보조로 *재검토 여지만* 메모 |
| **dataset 실데이터 이동/remote push 자동화** | dataset-curator 는 메타데이터-only(SHA256·split·lineage). DVC/git-lfs 감지 시 위임. 실데이터 이동은 iCloud/exFAT 함정 + 누수 위험 — 영구 금지 |

#### 제외 — OMC 4.14.4 심층 재분석 반증 45건 (2026-05-30)

> 공통 원칙: **OMC 가 throughput·병렬 Node 런타임으로 푸는 것을 omp 는 더 높은 레벨(단일 writer + 인간
> 게이트 + 결정론적 grep)에서 *설계로 제거*했다.** 그래서 가져올 경쟁 조건·런타임 전제가 omp 엔 없다.
> "OMC 에 X 가 있는데 omp 엔 왜 없나"의 방어 근거가 이 표다(누락 아닌 의도된 부재).

| 제외 카테고리 | 대표 OMC 패턴 (반증된 후보) | 반증 사유 |
|:---|:---|:---|
| 동시성·잠금 인프라 | file-lock, session-isolation, project-memory-merge, mode-state-io `_meta` | omp 는 단일 writer(organizer)+인간 게이트(learn/codify)로 동시 쓰기 경쟁이 구조적으로 부재 → 잠금/merge 가 풀 문제가 없음 |
| Node 런타임 전제 hook | context-injector, keyword-detector, codebase-map(+SKIP_DIRS), rules-injector | stateless python subprocess 에서 실행 불가 또는 ~150–300줄 인프라 신설 필요 → stdlib 2훅 경량 강점 파괴. (codebase-map 은 project-scanner 가, rules-injector 는 verify hook+audit 이 이미 커버) |
| 경로/페이로드 인프라 | worktree-paths(785줄), payload-limits, truncate-prompt | 진짜 필요분은 10줄 stdlib util 이지 모듈 포팅이 아님. payload guard 는 dataset-curator 아키텍처 제약이 이미 처리. truncate 는 omp 가 프롬프트를 재주입하지 않아 전제 부재 |
| 실행 파이프라인 어휘 | task-decomposer, model-routing, deepinit(전체) | 생성/실행 도메인 전용 — 관리 루프(폴더·명명·dataset)와 직교 |
| 이미 omp 에 존재 | learner(↔omp-learn), learner skill injector(↔wiki+route_emit), project-memory learner | 관찰→규칙 승격은 omp-learn+learned.md+wiki 가 이미 2채널로 커버. 자동 passive 수집의 좁은 조각은 route_emit regex 몇 줄로 흡수 가능(새 훅 불필요) |
| 세션/컴팩션 상태 | pre-compact checkpoint, session-end cleanup, project-memory pre-compact | omp 훅은 stateless(정리할 세션 state 자체가 없음). compaction 생존은 T11(notepad Priority Context)이 이미 담당. 새 PreCompact/SessionEnd 훅은 경량 정체성 희석 |

---

**Analysis snapshot**: OMC 4.14.4 (런타임 핀 아님 — marketplace 최신 자동 추종, §2) · **isomorphic sibling**: oh-my-scholar `references/omc-backport-analysis.md`(논문 도메인) · oh-my-docs `references/omc-backport-analysis.md`(문서 도메인)
