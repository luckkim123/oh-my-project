# omp × 코드그래프 — 등록 축 (registry axis) 계획

> 상태: **구현 완료** — v0.8.0, 브랜치 `feat/code-graph-registry` (2026-08-10).
> 로드맵 1–7단계 전부 반영, pytest 205 passed / 1 skipped (신규 graph 축 16건 포함).
> 이 문서는 구현 후에도 설계 근거(§2 실측·§3 잠긴 결정)의 기록으로 남긴다.

---

## 0. 요청자 목표 (원문 그대로 — 이 문서의 모든 판정은 이 문장에 대해 논증한다)

> "graphify랑 code review graph를 omp에 통합하는건 어때? 결과물도 .omp에 넣고
> omp-init을 할때 두 개도 돌리고 omp 하네스가 해당 플러그인을 적극적으로 사용하는
> 느낌으로 말이야. 그리고 코드 수정 작업을할때도 omp 하네스랑 적극적으로 협력해서
> 진행하는 느낌으로 말이야."

> "내가 생각하는 omp는 말그대로 프로젝트 폴더를 총괄 관리하는 느낌인데 아닌가?
> 폴더 구조부터 시작해서 프로젝트에 관한 모든걸 관리하는 느낌이어서 통합을 말한거긴했어."

> "단순히 폴더 구조만 검사하는 하네스가 아니라 말이야"

목표는 **omp가 이 프로젝트의 코드그래프를 아는 것**이다. 아래 모든 설계는 이 문장에
대해 "이게 목표를 채우나"로 판정한다. 목표를 재정의하지 않는다.

---

## 1. Executive verdict

원 제안 4개 중 **3개 채택, 1개 형태 변경**. 유일한 제약은 축이 아니라 실행 경계다.

| 원 제안 | 판정 | 형태 |
|:---|:---|:---|
| 결과물을 `.omp/`에 | **채택, 방식 변경** | 아티팩트를 옮기지 않고 **등록**한다. `manifest.json`의 dataset과 동일한 관계 |
| omp-init이 두 개 실행 | **형태 변경** | init이 외부 바이너리를 실행하지 않는다. 빌드 명령을 **제안**하고 결과를 등록 (`omp-env`의 not-a-build-runner와 같은 형태) |
| omp 하네스가 적극 사용 | **채택** | audit(stale·커버리지) + organize(이동 전 참조) 2축 |
| 코드 수정 때 협력 | **채택, 방향 반전** | omp가 코드를 고치지 않는다. `omp-handoff`가 코드 작업 레인에 그래프 지식을 전수 |

**omp의 불변 경계**: omp는 프로젝트에 관한 사실을 등록·검증하되 그 대상을 실행하지
않는다. dataset은 메타만(데이터 안 옮김), env는 not-a-build-runner(`docker build` 안 함),
auditor는 detection-only(안 고침), secretary는 사람이 닫음. 코드그래프도 같다 —
**등록하고 검증하되, 빌드하지 않는다.**

이 경계 하나만 지키면 나머지는 전부 omp가 이미 하는 일의 확장이며, 새 축의 도입이 아니다.

---

## 2. 조사로 확정된 사실 (2026-08-10 실측)

계획의 근거. 추정 없음, 전부 실행 결과.

### 2.1 세 도구 모두 CLI가 있다 — MCP 전용이 아니다

`~/.local/bin/{graphify,code-review-graph,tokensave}` 전부 실행 가능. 즉 omp의
`python3 stdlib + subprocess` 제약 안에서 질의할 수 있다. MCP 전용이었다면 audit·organize
칸은 성립하지 않았다.

CRG는 필요한 서브커맨드를 전부 갖는다: `status`(통계), `query`(관계), `impact`(blast
radius), `detect-changes`(변경 영향).

### 2.2 `code-review-graph status`는 커버리지 판정에 충분하다

이 vault에서 실측:

```
Nodes: 21865   Edges: 142416   Files: 101
Languages: bash, python, javascript, cpp, objc
Last updated: 2026-07-29T16:17:12
Built on branch: main   Built at commit: 6cb80302ff8a
```

같은 저장소의 실제 규모는 `git ls-files` 기준 **2277 파일(md 828, py 55)**이다. 즉 이 그래프는
전체의 **4.4%**만 담았고, 그것도 `.obsidian/plugins`의 벤더 JS이며 노트 828개는 **0노드**다.
HEAD는 `45fa74e5300a`, 그래프는 `6cb80302ff8a`에서 빌드됨 — stale도 확정.

**이 함정이 `status` 출력만으로 기계 판정된다**는 것이 등록 축의 핵심 근거다:

| 판정 | 신호 |
|:---|:---|
| 커버리지 거짓 | `Languages:`에 프로젝트 주 언어 부재, `Files:` ≪ `git ls-files \| wc -l` |
| stale | `Built at commit` ≠ `git rev-parse HEAD`, 또는 `Last updated` 경과 |

지금 이 사실은 `<project>/.claude/rules/*.md` 산문에만 있고 **기계가 읽을 곳이 없다.**
등록 축이 채우는 공백이 정확히 여기다.

### 2.3 ⚠️ `tokensave` CLI는 조회 명령에 부작용이 있다 — 1급 제약

`tokensave status`(순수 조회로 보이는 명령)를 실행하자 `✔ Wrote ~/.claude/settings.json`을
출력하고 **렌더된 settings.json에 자기 훅 2개를 주입**했다 (UserPromptSubmit, Stop).
mtime으로 확인: 실행 시각과 파일 수정 시각이 일치.

결과는 **훅 중복 실행**이다 — 래퍼로 이미 배선된 훅이 있으면 매 프롬프트마다 두 번 돈다.

| 도구 | 조회 명령 부작용 |
|:---|:---|
| `code-review-graph status` | 없음 (실측: settings mtime 무변화) |
| `graphify` (path/explain/diagnose) | 없음 (`install`만 설정을 건드리고, `--project` 필수) |
| **`tokensave status`** | **있음 — 에이전트 통합을 재설치** |

**결정 D3 (아래)**: omp는 tokensave CLI를 호출하지 않는다. 이 제약을 모른 채 audit에
`tokensave status`를 넣었다면, omp audit이 돌 때마다 사용자의 훅 설정이 조용히 오염된다.

### 2.4 `secretary.sources[]`가 등록 스키마의 완성된 모델이다

`references/schemas/rules.schema.json`의 기존 섹션이 그대로 대응한다:

- 구조: `path` + `kind`(enum) + `convention`(사람용 1줄)
- 의미: "existing state surfaces registered as **READ** targets" — 복제가 아니라 읽기 지도
- 게이트: "Registered only via the omp-codify human gate — **never auto-registered**"
- kind별 차등: `todo|schedule`은 카운트 기여, `journal|status`는 read-map 전용

코드그래프 등록은 이 패턴의 복제다. 새 관용구를 발명하지 않는다.

`rules.schema.json`은 최상위가 `additionalProperties: false`이므로 새 섹션은 **스키마 개정이
필수**다. 조용한 drift가 불가능하다는 뜻이라, 이는 제약이 아니라 안전장치다.

### 2.5 audit은 축(axis) 단위로 확장돼 왔고, 새 축은 전부 warn-default였다

선례 3개: Docker anti-pattern(0.3.0), secretary hygiene(0.4.0), governance hygiene(0.4.0).
전부 **"findings do NOT block an overall PASS"**. 검사 로직은 `hooks/omp_*_audit.py`의
순수함수이고 `auditor` 에이전트가 호출한다. 코드그래프 축도 같은 idiom을 따른다.

### 2.6 organize에는 이미 "이동 전 참조 검사" 슬롯이 있다

`skills/omp-organize/SKILL.md` §"wikilink inbound 카운트 (para preset 한정 — Release 2)":
dry-run 계획서 각 이동 행에 `inbound [[links]]: N`을 병기하고, N>0인 이동은 링크 깨짐으로
경고한다. **코드 프로젝트의 등가물이 `importers_of`다.** preset별 분기 구조가 이미 있으므로
새 메커니즘이 아니라 같은 슬롯의 두 번째 언어판이다.

### 2.7 handoff의 4요소 중 하나가 정확히 코드그래프 자리다

`omp-handoff`의 패킷 4요소 중 **"Tool·source guidance (어디를 읽어라)"**의 현재 원천은
`PROJECT.md 1줄 + wiki grep + derive_status read-map`이다. 여기에 등록된 그래프의
커버리지 한 줄을 추가하면 된다. **새 요소를 만들지 않는다.**

---

## 3. 이 계획에서 잠그는 결정 (구현 중 재논의 금지)

- **D1 — 등록만, 소유하지 않는다.** 그래프 아티팩트(`graphify-out/`, `.tokensave/`, CRG DB)는
  제자리에 둔다. `.omp/`로 복사·이동하지 않는다. 근거: 이들은 빌드 아티팩트(한 vault에서
  수백 MB 관측)이고 `.omp/`는 커밋 후보 SSOT다(omp-init이 gitignore 여부를 사용자에게 묻는다).
  dataset이 실제 데이터를 안 옮기는 것과 같은 이유.
- **D2 — omp는 그래프를 빌드하지 않는다.** init/codify는 빌드 명령을 **제안**하고, 사용자가
  실행하며, omp는 결과를 등록한다. `omp-env`의 not-a-build-runner 경계를 그대로 승계.
  근거: 외부 바이너리 의존은 `python3 stdlib only + fail-open + cross-platform` 불변식과
  충돌하고, 도구 미설치 머신에서 init이 깨진다.
- **D3 — tokensave CLI를 호출하지 않는다.** §2.3의 부작용 때문. tokensave는 *등록 대상*으로만
  기록하고(경로·커버리지·갱신 명령은 사람이 codify 게이트에서 입력), 질의는 세션의 MCP 툴이
  한다. omp 코드에서 `tokensave` 바이너리를 실행하는 경로를 만들지 않는다.
- **D4 — 자동 등록 금지, codify 게이트 경유.** `secretary.sources[]`와 동일. 그래프의 존재를
  탐지해 조용히 등록하지 않는다. 탐지는 제안까지만.
- **D5 — 새 축은 warn-default.** 코드그래프 findings는 전체 PASS를 막지 않는다. §2.5 선례.
- **D6 — 커버리지는 등록 시점의 선언이 아니라 검증 대상이다.** 등록된 `covers`와 `status`
  실측이 어긋나면 audit이 findings를 낸다. 사람이 "md도 색인됨"이라 잘못 써두면 그게 잡혀야
  한다 — 안 그러면 등록 축이 §2.2의 함정을 재생산한다.

---

## 4. 설계

### 4.1 `rules.json` 새 섹션 — `code_graphs`

`secretary`와 같은 위치(최상위, optional). `rules.schema.json` 개정 동반.

```jsonc
"code_graphs": {
  "indexes": [
    {
      "tool": "code-review-graph",        // enum: code-review-graph | graphify | tokensave
      "path": ".crg/",                     // 아티팩트 위치 (프로젝트 상대). 등록만, 소유 X
      "covers": ["python", "cpp"],         // 이 그래프가 실제로 담는 언어/확장자
      "excludes": [".obsidian/**"],        // 색인에서 뺀 경로 (벤더 트리 등)
      "refresh": "code-review-graph update",  // 사람이 실행할 갱신 명령 (omp는 실행 X)
      "convention": "노트(.md)는 이 그래프에 없다 — 산문 질의는 tokensave로"
    }
  ]
}
```

`convention` 필드가 §2.2의 함정을 사람 언어로 담는 자리다 — 지금 `.claude/rules/*.md`
산문에만 있는 지식이 여기로 온다.

### 4.2 새 audit 축 — `hooks/omp_graph_audit.py`

순수함수 2개. `auditor` 에이전트가 호출, warn-default.

| 함수 | 판정 | 근거 |
|:---|:---|:---|
| `check_graph_stale(root, entry)` | `Built at commit` ≠ HEAD, 또는 `Last updated` 경과 | §2.2 |
| `check_graph_coverage(root, entry)` | 등록된 `covers` ∌ `status`의 `Languages`, 또는 `Files` ≪ 트래킹 파일 수 | §2.2, D6 |

finding kinds: `graph_stale`, `graph_coverage_mismatch`, `graph_missing`(등록됐는데 아티팩트 부재).

**CRG만 CLI로 질의한다** (D3). graphify는 `graph.json` mtime + 파일 존재로 판정(파싱 불필요).
tokensave는 등록 정보만 사용, 실행하지 않음.

### 4.3 `omp-organize` — 코드 preset의 이동 전 참조 검사

para preset의 `inbound [[links]]: N`과 같은 자리에, 코드 파일 이동 시
`inbound imports: N` 열을 병기한다. 출처는 `code-review-graph query importers_of <path>`.
N>0인 이동은 para와 동일하게 경고 표시.

**CRG를 쓴다, graphify가 아니다.** graphify는 incremental update가 없어 이동 직전 시점에
stale이고, stale한 "0 importers"는 잘못된 초록불이다.

### 4.4 `omp-handoff` — Tool·source guidance에 원천 1줄 추가

§2.7. 패킷의 해당 요소에 등록된 그래프의 `tool`/`covers`/`convention`을 붙인다. 이것이
원 요청 4번("코드 수정 작업 때 협력")의 실현 형태다 — omp가 코드를 고치는 게 아니라,
고치러 가는 레인이 "이 프로젝트엔 CRG가 있고 .md는 안 덮는다"를 들고 출발한다.

### 4.5 `omp-init` / `omp-codify` — 탐지 → 제안 → 등록

init은 스캔 중 그래프 아티팩트의 존재를 **관찰 사실로** 보고한다(project-scanner는 read-only).
없으면 프로젝트 구성에 맞는 빌드 명령을 **제안**한다(실행 X, D2). 등록 자체는 codify의
사람 게이트(D4).

---

## 5. 로드맵

| 단계 | 산출물 | 검증 |
|:---|:---|:---|
| 1 | `rules.schema.json`에 `code_graphs` + `tests/test_schemas.py` | 스키마 검증 통과, 기존 rules.json 무영향 |
| 2 | `hooks/omp_graph_audit.py` + `tests/test_omp_graph_audit.py` | 이 vault의 CRG(21865노드/101파일/12일 stale)로 두 finding 모두 재현 |
| 3 | `omp-audit` SKILL에 축 추가, `auditor.md` 갱신 | warn-default 확인 — 전체 PASS를 안 막음 |
| 4 | `omp-codify` 등록 게이트, `omp-init` 탐지·제안 | 자동 등록이 일어나지 않음을 확인(D4) |
| 5 | `omp-organize` 코드 preset inbound imports | dry-run 계획서에 열 표시, N>0 경고 |
| 6 | `omp-handoff` 원천 추가 | 패킷에 커버리지 줄이 실림 |
| 7 | 릴리스 — v0.8.0 + CHANGELOG + README | ⚠️ **버전을 올려야 플러그인 update가 반영된다** (버전 미상승 시 push해도 no-op) |

1→2가 선행이다. 등록 스키마가 없으면 audit이 읽을 데가 없다.

---

## 6. 채택하지 않는 것 (경계 확정)

- **`.omp/`에 그래프 아티팩트 저장** — D1
- **omp가 그래프를 빌드** — D2
- **tokensave CLI 호출** — D3, §2.3
- **graphify를 organize 참조 검사에 사용** — incremental update 부재(§4.3)
- **코드그래프를 rules 승격(learn) 대상으로** — 등록 정보는 관찰이 아니라 사실 선언이다.
  learned.md → rules 승격 경로와 섞지 않는다.
- **omp가 코드 수정 레인에 개입** — 방향은 handoff 한 방향(§4.4). omha의 LANE 판정은 불변.

---

## 7. 사용자 결정 필요 (본 계획을 막지는 않음)

1. **범위**: 1–3단계(등록+audit)만 먼저 낼지, 7단계 전부를 한 릴리스로 낼지.
2. **`tool` enum에 tokensave를 넣을지**: D3에 따라 omp가 실행하지 않으므로 등록만 가능하다.
   "실행 못 하는 도구를 등록만 하는 것"이 유용한지는 사용자 판단.
3. **계획서 커밋 여부**: 이 문서는 배포되는 공개 저장소에 있다. 기존
   `2026-07-11-omp-secretary-upgrade-plan.md` 선례는 커밋돼 있다.

---

## 8. 미해결 / 확인 안 한 것

- CRG `query importers_of <target>`은 실재하고 `target`이 "Node name, qualified name, or
  **file path**"를 받는 것까지 확인했다(§4.3에 필요한 형태). 다만 **출력 형식(텍스트/JSON)은
  미실측** — 5단계 착수 전 파싱 방식 확정 필요.
- graphify `graph.json`의 커버리지 필드 유무 미확인 — 현재 설계는 mtime + 존재 판정만
  가정한다.
- omp 자신은 코드 저장소이므로 이 축의 첫 사용자가 될 수 있다. 도그푸딩 여부 미결정.
