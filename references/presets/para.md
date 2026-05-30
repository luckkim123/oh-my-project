# Preset — para

> **Preset ID**: `para` · **specificity 시작점**: `0.0` (순수 프리셋)
> **이 카드는 _시드_**: omp-init 이 실제 폴더 귀납 스캔과 **합성**해 초안 `rules.json` 을 만든다.
> 카드 ≠ 최종 규칙. 카드는 "이 프로젝트 타입이면 보통 이렇다" 는 범용 기대값이고,
> 진짜 규칙은 사용자의 실제 트리에서 나온다. 충돌하면 **실측 트리가 이긴다**.

---

## §0. 이 프리셋이 맞는 프로젝트

**PARA** (Projects / Areas / Resources / Archives) 는 Tiago Forte 의 정보 조직법으로, 자료를
*행동가능성(actionability)* 으로 4계층 분류한다 — 지금 끝내려는 일(Projects) → 지속 책임
영역(Areas) → 미래 참고자료(Resources) → 비활성 보관(Archives). 코드 repo 가 아니라 **사람이
직접 노트·지식을 분류·축적하는 워크스페이스**(Obsidian vault, Notion, 지식 정원, 연구 노트)에
쓰인다. 다음 신호가 보이면 이 프리셋이 후보다:

- 최상위에 4개의 행동가능성 폴더 — `Projects` / `Areas` / `Resources` / `Archives`, 또는
  순서 접두를 붙인 `0_Project` / `1_Area` / `2_Resource` / `3_Archive` (Obsidian PARA 흔한 변형).
- Projects 안에 `in_progress/` / `done/` 같은 **상태(status) 하위 폴더** — 완료된 프로젝트는
  Archives 로 옮기거나 done 으로 표시하는 lifecycle.
- Resources 안에 주제별 분류 — `concepts/` / `papers/` / `references/` 같은 **knowledge type 폴더**.
- `.md` 노트가 압도적이고, 노트끼리 `[[wikilink]]` 로 연결 (Zettelkasten / Obsidian).
- `.obsidian/` 디렉토리, `Dashboard.md` · `Kanban.md` 같은 vault 운영 노트, `daily_notes/` 의
  `YYYY-MM-DD.md` 날짜 파일.
- CLAUDE.md 나 README 에 "PARA", "Projects/Areas/Resources/Archives", "행동가능성" 표현이 등장.

> 코드·빌드 산출물(`src/`, `package.json`, `requirements.txt`, `node_modules/`)이 중심이면 이 프리셋이
> **아니다** → `python-ml` / `web-app` / `monorepo` / `generic` 후보. PARA 는 *지식·자료 조직*용.
>
> **PARA vs johnny-decimal 구분** (둘 다 PKM 워크스페이스라 헷갈림):
> - **두 자리 숫자 ID** (`10-19_`, `11_`, `11.01_`)가 폴더 골격이고 `00_Index` 가 ID 권위본이면
>   → `johnny-decimal` (검색성·번호 기반).
> - **4개 행동가능성 범주**(Projects/Areas/Resources/Archives)가 골격이고 자료가 "지금 행동하는가"
>   로 분류되면 → `para` (행동가능성 기반). 순서 접두 `0_`/`1_`/`2_`/`3_` 는 정렬용이지 JD 의
>   범위 ID 가 아니다.
> - 둘이 섞여 있으면(예: PARA 4범주 안에 JD 식 번호 폴더) `para` 를 origin 으로 하고 번호 패턴은
>   귀납 naming 규칙으로 보정.

---

## §1. Canonical 디렉토리 레이아웃 (구조 규칙)

PARA 의 불변 골격은 **4개 행동가능성 범주**. `rules.json.structure.convention = "para"`.

```
<project root>/
├── 0_Project/               # PROJECTS : 마감/목표가 있는 현재 진행 중인 일
│   ├── in_progress/         #   진행 중 (상태 하위 폴더는 흔한 변형)
│   │   └── <project_name>/   #     개별 프로젝트 작업 폴더 (노트 + 종속 코드/문서)
│   └── done/                #   완료 — 정기적으로 Archives 로 이동
├── 1_Area/                  # AREAS : 마감 없이 지속 유지하는 책임 영역 (건강·재무·연구분야)
│   └── <area_name>/
├── 2_Resource/              # RESOURCES : 미래에 쓸 주제별 참고자료
│   ├── concepts/            #   개념 노트 (Zettelkasten)
│   └── papers/              #   논문 리뷰 노트
├── 3_Archive/               # ARCHIVES : 비활성 — 위 3범주에서 끝난 것들의 보관소
│   └── calendar/daily_notes/   #   날짜 노트 등 (YYYY-MM-DD.md)
├── Dashboard.md             # vault 운영 노트 (PARA 범주 밖, root 직속 허용)
└── Kanban.md
```

> 접두 표기는 **둘 중 하나로 일관** (귀납으로 확정): 순서 접두 변형(`0_Project`/`1_Area`/
> `2_Resource`/`3_Archive`, Obsidian 흔함) 또는 평문 변형(`Projects`/`Areas`/`Resources`/`Archives`).
> 한 vault 는 하나만 쓴다.

### 각 범주의 역할 (rules.json `structure.directories[]` 로 성문화)

| 범주 | 폴더 예 | `role` | 행동가능성 | `enforced` 기본 |
|:---|:---|:---|:---|:---:|
| **Projects** | `0_Project/` · `Projects/` | 마감·목표가 있는 *지금 끝내려는* 일. 끝나면 Archives 로 | 가장 높음 | `true` |
| **Areas** | `1_Area/` · `Areas/` | 마감 없이 *지속 유지*하는 책임 영역 (역할·표준 유지) | 지속 | `true` |
| **Resources** | `2_Resource/` · `Resources/` | *미래 참고*용 주제별 자료. 지금 행동 안 함 | 낮음 | `true` |
| **Archives** | `3_Archive/` · `Archives/` | 위 3범주에서 *비활성화*된 것의 보관소 | 없음 | `true` |
| **상태 하위** | `Projects/in_progress/` · `/done/` | Projects 내부 lifecycle 표시 (변형) | — | `false` (조언) |
| **type 하위** | `Resources/concepts/` · `/papers/` | Resources 내부 knowledge type 분류 (변형) | — | `false` |

> **행동가능성 흐름** (구조 건강성 지표, audit 가 `info` 로): 자료는 행동가능성이 떨어지면
> Projects → Areas/Resources → Archives 방향으로 이동한다. 완료 프로젝트가 `0_Project/` 에
> 계속 쌓여 있으면 Archives 이동 신호(위반은 아니고 health hint).
>
> **root 직속 운영 노트 예외**: `Dashboard.md`·`Kanban.md`·`changelog.md`·`README.md`·`CLAUDE.md`
> 처럼 4범주 어디에도 안 속하는 vault 운영 노트가 root 에 있는 것은 **정상** — 위반 아님.

---

## §2. 명명 규칙 (naming 규칙 + regex)

`rules.json.naming.patterns[]` 로 성문화. regex 는 Python `re` 문법, **basename** 매칭.

| 적용 대상 (`applies_to`) | 의미 | regex (`regex`) | severity |
|:---|:---|:---|:---|
| 최상위 PARA 범주 (순서 접두 변형) | `N_Singular` (예: `0_Project`) | `^[0-3]_[A-Z][A-Za-z]+$` | `warn` |
| 최상위 PARA 범주 (평문 변형) | `Plural` (예: `Projects`) | `^(Projects\|Areas\|Resources\|Archives)$` | `warn` |
| daily note 파일 | `YYYY-MM-DD.md` | `^\d{4}-\d{2}-\d{2}\.md$` | `info` |
| concept/paper 노트 | 노트 명명 (귀납으로 확정) | `<스캔에서 우세한 패턴>` | `info` |

> omp-init 은 실측 스캔에서 **순서 접두 변형 vs 평문 변형 중 어느 쪽이 우세한지 세고**, 우세한
> 쪽 regex 만 `warn` 으로, 나머지는 `info` 로 남기거나 제거한다. 노트 파일 명명(concepts/papers)은
> vault 마다 천차만별이라 프리셋이 강제하지 않고 귀납·learn 에 맡긴다.

### 예시 (Good / Bad)

```
Good (범주·접두):  0_Project/   1_Area/   2_Resource/   3_Archive/
Good (범주·평문):  Projects/    Areas/    Resources/    Archives/
Good (상태 하위):  0_Project/in_progress/   0_Project/done/
Good (type 하위):  2_Resource/concepts/   2_Resource/papers/
Good (daily):      3_Archive/calendar/daily_notes/2026-05-31.md
Good (운영 노트):   Dashboard.md   Kanban.md   (root 직속 OK)

Bad:  0_Projects/              → 접두 변형은 단수 (0_Project), 평문 변형만 복수
Bad:  4_Inbox/                 → PARA 는 0~3 네 범주 (Inbox 는 별도 컨벤션이지 PARA 아님)
Bad:  2_Resource/random.pptx   → Resource 직속에 분류 안 된 파일 (concepts/papers 등 하위로)
```

---

## §3. Dataset 관례 (대개 해당 없음)

PARA 는 **지식·자료 조직 워크스페이스**라 ML 식 train/val/test dataset 개념이 거의 없다.
기본값: `manifest.json.datasets = []`, `managed_by_external.tool = "none"`.

다만 이 타입의 실제 함정은 **Projects 폴더 안에 종속된 코드 repo·대용량 산출물**이다 (노트가
본체지만 프로젝트 폴더에 코드·데이터·미디어가 딸려옴). dataset-curator 가 manifest 에 기록할 만한
후보:

- 프로젝트 폴더 내 임베디드 코드 repo (clone / submodule) → 보통 gitignored. manifest 는 위치만
  안다(데이터셋 아님). `.gitmodules`·`CLONES.md` 같은 clone 관리 파일이 있으면 그것이 SSOT.
- 대용량 단일 산출물(>50MB mp4·PPT 사본·PDF 덤프, Archives 나 프로젝트 attachments) →
  `source: "internal"`, `split` 없음. 너무 커서 해시 비싸면 `sha256: "UNHASHED"` (size+mtime 추적).
- 외장HDD/iCloud 이주 대기 임시 폴더 → 보통 gitignored. 데이터 아님, manifest 에 안 넣음.
- **실제 데이터는 절대 안 옮긴다** (메타데이터-only).

> ML 스타일 split/lineage 가 필요하면 그건 para 가 아니라 `python-ml` 신호다 (프로젝트 폴더
> *안에* python-ml 구조가 있으면 그 하위만 python-ml 로 별도 판단 가능).

---

## §4. omp-init 매핑 가이드 (스캔 → 이 프리셋 → 초안 rules.json)

project-scanner 의 귀납 결과를 rule-architect 가 이 카드와 **합성**하는 절차.

1. **convention 확정**: root 직속에 4개 행동가능성 범주(`0_Project`/`1_Area`/`2_Resource`/`3_Archive`
   또는 `Projects`/`Areas`/`Resources`/`Archives`)가 보이면 `structure.convention = "para"`,
   `project.preset_origin = "para"`. (두 자리 ID 골격이 우세하면 para 가 아니라 `johnny-decimal`.)
2. **directories[] 채우기**: 스캔된 실제 PARA 범주 + 그 아래 관측된 상태/type 하위 폴더를 그대로
   `directories[]` 엔트리로 굽는다. `path` = 실제 상대경로, `role` = README/CLAUDE.md 의 설명이
   있으면 그 문장을, 없으면 범주에서 추론한 한 줄. 4범주는 `enforced:true`, 상태/type 하위는 보통
   `enforced:false`(조언). origin: 실측 범주는 `inductive`, 프리셋 골격 기대값은 `preset`.
3. **운영 노트 화이트리스트**: root 직속 `Dashboard.md`·`Kanban.md`·`changelog.md`·`README.md`·
   `CLAUDE.md` 등 vault 운영 노트는 PARA 4범주 밖이지만 정상 — `ignore` 또는 `structure` 의
   허용 목록에 넣어 audit 가 "분류 안 된 파일" 로 잡지 않게 한다.
4. **naming 표기 확정**: 순서 접두 변형 vs 평문 변형 빈도를 세어 우세한 쪽 regex 만 활성, §2 표에서
   채택. daily note·concept note 명명은 스캔에서 패턴이 뚜렷하면 `info` 로 추가, 아니면 생략.
5. **ignore 채우기**: `.git/**`, `.omp/**`, `.obsidian/**`(Obsidian 설정), `.smart-env/**`,
   OS 노이즈(`.DS_Store`, `*.tmp`, `*.backup`), gitignored 임베디드 repo·외장HDD 이주 대기
   대용량 폴더를 `ignore` 에 넣어 audit 노이즈·스캔 부풀음 차단. `.gitignore` 가 있으면 그 항목을
   우선 반영(사용자가 이미 선언한 무시 목록).
6. **specificity**: 박지 말고 `learning-protocol.md` §4 공식으로 *계산*한다 — 각 규칙의 `origin`
   가중 비율. 실측 범주·하위를 구워 넣은 `directories[]`는 `origin: inductive`, 프리셋 골격
   그대로인 naming 규칙은 `origin: preset`. 순수 프리셋이면 0.0, 귀납 보정이 섞이면 그만큼 >0.
   learn 승격마다 1 쪽으로 상승.
7. **사람 게이트**: 합성된 초안 rules.json + STRUCTURE.md/NAMING.md 를 사용자에게 보여 승인.
   "접두 표기는 순서접두/평문 중 무엇이 정본인가", "상태 하위(in_progress/done)를 강제할 것인가
   조언만 할 것인가", "어떤 root 노트를 운영 노트로 화이트리스트할 것인가" 를 여기서 확정.

### 초안 rules.json 스케치 (스캐폴드, 실측으로 채워질 자리는 `<…>`)

```json
{
  "omp_version": "<현재 omp 버전>",
  "project": { "name": "<폴더명>", "preset_origin": "para", "initialized": "<ISO date>" },
  "specificity": 0.0,
  "structure": {
    "convention": "para",
    "directories": [
      { "path": "0_Project",  "role": "<마감/목표 있는 현재 진행 일; README 설명 있으면 그 문장>", "origin": "inductive", "enforced": true },
      { "path": "1_Area",     "role": "<마감 없이 지속 유지하는 책임 영역>",                        "origin": "inductive", "enforced": true },
      { "path": "2_Resource", "role": "<미래 참고용 주제별 자료>",                                  "origin": "inductive", "enforced": true },
      { "path": "3_Archive",  "role": "<비활성 보관소>",                                            "origin": "inductive", "enforced": true },
      { "path": "0_Project/in_progress", "role": "진행 중 프로젝트 (상태 하위)",                    "origin": "inductive", "enforced": false }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "*/", "regex": "^[0-3]_[A-Z][A-Za-z]+$", "description": "최상위 PARA 범주는 N_Singular (순서 접두 변형)", "origin": "preset", "severity": "warn" }
    ]
  },
  "ignore": [".git/**", ".omp/**", ".obsidian/**", "**/.DS_Store", "**/*.tmp", "**/*.backup"]
}
```

> 위 directories[] 는 **예시**일 뿐 — 실제로는 스캔된 모든 범주·하위가 들어간다.
> root 운영 노트(Dashboard.md 등)는 directories[] 가 아니라 ignore/허용목록에 — 폴더가 아니라
> 파일이고, 분류 대상이 아니라 vault 자체 운영물이다.

---

## §5. omp-learn 이 이 타입에서 특화하는 것 (관찰 → 규칙 승격 후보)

PARA 워크스페이스를 쓸수록 learn 이 자주 승격하는 패턴들. 모두 사람 승인 게이트 경유.

- **행동가능성 분류 경계 규칙**: "이 자료가 Project(지금 행동)인가 Resource(미래 참고)인가" 같은
  PARA 의 핵심 판단이 vault 마다 다르게 굳는다. 같은 오분류가 반복 관찰되면 판별 기준을 명문화
  (예: "마감일 있는 노트는 항상 0_Project, 없으면 1_Area/2_Resource").
- **완료 → Archives lifecycle 규칙**: "done 으로 표시된 프로젝트는 N일 후 3_Archive 로 이동" 같은
  PARA 의 대표 운영 규칙 (Projects 폴더 부풀음 방지 — 이 타입의 함정).
- **Resource type 분류**: `concepts/` vs `papers/` vs `references/` 경계가 vault 고유 규칙으로
  수렴 (예: "코드 스니펫은 concepts 아닌 별도 snippets/").
- **노트 명명·태그 컨벤션**: concept note·daily note 명명, 태그 계층(`Concepts/`, `Papers/`)이
  반복 관찰되면 naming 규칙으로 승격.
- **임베디드 repo 위치 규칙**: 프로젝트 폴더 내 코드 clone 의 위치·gitignore 패턴이 일관되면
  (예: "모든 clone 은 `<project>/code/` 아래, CLONES.md 로 관리") 규칙으로.
- **접두 표기 정본 굳히기**: 순서 접두 vs 평문 중 하나로 수렴 → 나머지를 `error` 로 승격.
- **wikilink 무결성**: `[[link]]` 가 깨진 노트(dead link)를 health hint 로 wiki/ 에 누적(가벼운 채널).

> 위는 **범용 후보 목록**이지 강제 규칙이 아니다. 실제 승격은 해당 vault 에서 관찰이 반복되고
> 사람이 승인할 때만 rules.json 으로 들어가며, 그때마다 specificity 가 1 쪽으로 오른다.

---

## §6. 안티패턴 (이 프리셋에서 omp 가 하지 말아야 할 것)

- **5번째 범주를 만들지 마라** — PARA 는 정확히 4개 행동가능성 범주다. `Inbox`/`Meta` 등이 보이면
  그건 PARA 의 변형이거나 johnny-decimal 혼합이지, 새 PARA 범주가 아니다.
- **노트를 코드처럼 보지 마라** — `src/`/lockfile 이 없다고 "미완성 프로젝트" 판정 금지. PARA 는
  지식 워크스페이스다.
- **완료 프로젝트의 Archives 미이동을 위반으로 단정 마라** — lifecycle health hint(`info`)이지
  강제 위반이 아니다. 사용자가 일부러 0_Project 에 둘 수 있다.
- **root 운영 노트를 "분류 안 된 파일" 로 잡지 마라** — Dashboard.md·Kanban.md·changelog.md 는
  PARA 4범주 밖이 정상이다(화이트리스트 §4-3).
- **임베디드 repo 를 vault 자료로 보지 마라** — 프로젝트 폴더 안 코드 clone 은 gitignored 인
  경우가 많고 별도 SSOT(`CLONES.md`/`.gitmodules`)로 관리된다. audit 가 그 안을 PARA 규칙으로
  훑지 말 것 (ignore 에 넣음).
- **`.obsidian/` 을 건드리지 마라** — Obsidian 설정 디렉토리는 vault 운영 인프라지 자료가 아니다.
  항상 ignore.
- **접두 표기를 강제로 통일하지 마라** — 사용자 정본을 게이트에서 확인하기 전까지 `info`/`warn`
  로만. 순서 접두와 평문이 섞여 있으면 그것이 첫 organize 후보다(자동 변경 금지).
