# Preset — johnny-decimal

> **Preset ID**: `johnny-decimal` · **specificity 시작점**: `0.0` (순수 프리셋)
> **이 카드는 _시드_**: omp-init 이 실제 폴더 귀납 스캔과 **합성**해 초안 `rules.json` 을 만든다.
> 카드 ≠ 최종 규칙. 카드는 "이 프로젝트 타입이면 보통 이렇다" 는 범용 기대값이고,
> 진짜 규칙은 사용자의 실제 트리에서 나온다. 충돌하면 **실측 트리가 이긴다**.

---

## §0. 이 프리셋이 맞는 프로젝트

**Johnny Decimal** 은 Area / Category / Item 3계층을 두 자리 숫자 ID 로 묶는 개인·지식 워크스페이스
조직법이다. 코드 repo 가 아니라 **사람이 직접 자료를 분류·검색하는 폴더**(노트·발표자료·과제·문서·
대용량 산출물 등)에 쓰인다. 다음 신호가 보이면 이 프리셋이 후보다:

- 최상위에 `10-19_<AreaName>` / `20-29_<AreaName>` 같은 **두 자리 범위 + 이름** Area 폴더
  (Johnny Decimal 표준 예: `10-19_Life-admin`, `20-29_Work`, `30-39_Projects`).
- Area 안에 `11_<CategoryName>` 같은 **두 자리 ID + 이름** Category 폴더 (예: `11_Finance`, `12_Travel`).
- Category 안에 `11.01_<item>` (점 표기) 또는 `01_<item>` (단축 표기) 식 **ID 접두 Item** 폴더.
- 폴더 인덱스(README / INDEX)가 "현재 사용 중인 ID 목록" 을 권위본으로 관리.
- "두 클릭 룰", "빈 번호 예약" 같은 표현이 문서·CLAUDE.md 에 등장.

> 코드·빌드 산출물(`src/`, `package.json`, `requirements.txt`, `node_modules/`)이 중심이면 이 프리셋이
> **아니다** → `python-ml` / `web-app` / `monorepo` / `generic` 후보. Johnny Decimal 은 *자료 보관*용.

---

## §1. Canonical 디렉토리 레이아웃 (구조 규칙)

Johnny Decimal 의 불변 골격. `rules.json.structure.convention = "johnny-decimal"`.

```
<project root>/
├── 00-09_Meta/              # AREA 00-09 : 워크스페이스 자체 메타 (인덱스·템플릿·결정·계획)
│   ├── 00_Index/            #   CATEGORY 00 : 폴더 인덱스 — ID 부여의 권위본(SSOT)
│   ├── 01_Templates/        #   CATEGORY 01 : 재사용 템플릿
│   └── 02_Decisions/        #   CATEGORY 02 : 결정 기록
├── 10-19_<AreaName>/        # AREA 10-19 : 첫 주제 영역 (예: Academic)
│   ├── 11_<Category>/       #   CATEGORY 11 : 영역 내 첫 분류
│   │   ├── 11.01_<item>/    #     ITEM 11.01 : 여러 파일이 묶이는 작업 단위
│   │   └── 11.02_<item>/    #     ITEM 11.02
│   └── 13_<Category>/       #   CATEGORY 13 : (12 는 의도적으로 비워둘 수 있음)
├── 20-29_<AreaName>/        # AREA 20-29 : 둘째 주제 영역
├── 90-99_Inbox_Archive/     # AREA 90-99 : 분류 전 임시 + 비활성 아카이브 (관례적 마지막 Area)
│   ├── 91_Inbox/            #   CATEGORY 91 : 분류 전 임시 (정기 비우기)
│   └── 99_Archive/          #   CATEGORY 99 : 비활성 보관
```

### 각 계층의 역할 (rules.json `structure.directories[]` 로 성문화)

| 계층 | ID 형식 | `id` 필드 | 역할 (`role`) | `enforced` 기본 |
|:---|:---|:---|:---|:---:|
| **Area** | `AA-BB_Name` (예: `10-19_Academic`) | `"10-19"` | 10단위 범위로 묶인 최상위 주제 영역. 자료를 직접 담지 않고 Category 를 담는다 | `true` |
| **Category** | `BB_Name` (예: `11_Coursework`) | `"11"` | 한 Area 안의 단일 분류. 두 자리는 부모 Area 범위 안 (`11`∈`10-19`) | `true` |
| **Item** | `BB.CC_name` 또는 `CC_name` | `"11.01"` | 여러 파일이 묶이는 실제 작업 단위 폴더. 단일 파일이면 ID 생략 가능 | `false` (조언) |
| **Index** | `00_Index/` (관례) | `"00"` | 사용 중인 ID 목록의 권위본. 새 폴더 배치 전 먼저 참조 | `true` |
| **Inbox** | `91_Inbox/` (관례) | `"91"` | 분류 전 임시. 정기적으로 비움 | `false` |

> **두 클릭 룰** (구조 건강성 지표, audit 가 `info` 로): 어떤 자료든 `Area → Category` 두 폴더 깊이로
> 도달. Item 폴더(셋째 클릭)는 작업 단위라 OK. 그 안에서 더 깊어지면 ID 재배치 신호.
>
> **빈 번호는 의도된 예약** (audit 가 절대 "정리"하지 않음): `12`, `25`, `43` 처럼 비어 있는 자리는
> 나중을 위해 비워둔 자리다. 연속성 결손이 아니므로 **gap 을 위반으로 보지 말 것**. 새 자료는 알파벳
> 강제 없이 *추가된 순서대로* 다음 빈 번호를 받는다.

---

## §2. 명명 규칙 (naming 규칙 + regex)

`rules.json.naming.patterns[]` 로 성문화. regex 는 Python `re` 문법, **basename** 매칭.

| 적용 대상 (`applies_to`) | 의미 | regex (`regex`) | severity |
|:---|:---|:---|:---|
| Area 폴더 (root 직속) | `AA-BB_Name` — 범위 + 이름 | `^[0-9]0-[0-9]9_[A-Za-z0-9][A-Za-z0-9_]*$` | `warn` |
| Category 폴더 | `BB_Name` — 두 자리 + 이름 | `^[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$` | `warn` |
| Item 폴더 (점 표기) | `BB.CC_name` — Category.Item | `^[0-9]{2}\.[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$` | `info` |
| Item 폴더 (단축 표기) | `CC_name` — Category 안에서 두 자리만 | `^[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$` | `info` |

### 표기 방식은 둘 중 하나로 일관 (귀납으로 확정)

Johnny Decimal Item 에는 두 흔한 표기가 있고, **한 프로젝트는 하나만 일관되게** 쓴다:

- **점 표기** (정통): `11.01_robotics_final_project` — Category·Item 을 점으로 연결, 전역 유일.
- **단축 표기**: Category 폴더(`11_Coursework`) 안에서 `01_machine_learning`, `02_dynamic_programming` —
  부모 Category 가 맥락을 주므로 Item 은 두 자리만.

> omp-init 은 실측 스캔에서 **어느 표기가 우세한지 세고**, 우세한 쪽 regex 만 `error`/`warn` 으로,
> 나머지는 `info` 로 남기거나 제거한다. 둘이 섞여 있으면 그것이 첫 organize 후보다.

### 예시 (Good / Bad)

```
Good (Area):      10-19_Academic/    40-49_Reference/    90-99_Inbox_Archive/
Good (Category):  11_Coursework/     13_Lab_Research/    91_Inbox/
Good (Item·점):   11.01_kalman_homework/    13.02_krit/
Good (Item·단축): 01_machine_learning/      04_mobile_robotics/

Bad:  Academic/                  → Area 인데 ID 범위 없음
Bad:  1_Coursework/              → Category 두 자리 아님 (한 자리)
Bad:  11_coursework_final.pptx   → Category 자리에 파일 (Item 폴더/단일파일이어야)
Bad:  13_Lab_Research/sub/deep/x → 두 클릭 룰 위반 (Item 아래 임의 중첩)
```

---

## §3. Dataset 관례 (대개 해당 없음)

Johnny Decimal 은 **자료 보관용 워크스페이스**라 ML 식 train/val/test dataset 개념이 거의 없다.
기본값: `manifest.json.datasets = []`, `managed_by_external.tool = "none"`.

다만 대용량 산출물(PPT 사본 누적, mp4, 대용량 PDF)이 **버전 부풀음**을 일으키는 게 이 타입의 실제
함정이다. dataset-curator 가 manifest 에 기록할 만한 후보:

- 대용량 단일 산출물(>50MB 발표 영상·데이터 덤프) → `source: "internal"`, `split` 없음, lineage 선택.
- iCloud/exFAT 등 sync 매체 위 파일 → 너무 커서 해시 비싸면 `sha256: "UNHASHED"` (size+mtime 추적).
- **실제 데이터는 절대 안 옮긴다** (메타데이터-only). sync 매체(iCloud/Drive) 가 sync 를 맡으므로
  manifest 는 "무엇이 어디 있나·바뀌었나" 만 안다.

> ML 스타일 split/lineage 가 필요하면 그건 johnny-decimal 이 아니라 `python-ml` 신호다.

---

## §4. omp-init 매핑 가이드 (스캔 → 이 프리셋 → 초안 rules.json)

project-scanner 의 귀납 결과를 rule-architect 가 이 카드와 **합성**하는 절차.

1. **convention 확정**: root 직속에 `AA-BB_Name` Area 폴더가 ≥1 개 + Category(`BB_Name`)가 보이면
   `structure.convention = "johnny-decimal"`, `project.preset_origin = "johnny-decimal"`.
2. **directories[] 채우기**: 스캔된 실제 Area/Category 를 그대로 `directories[]` 엔트리로 굽는다.
   `path` = 실제 상대경로, `id` = 추출한 두 자리(또는 범위), `role` = 인덱스 README 의 "용도" 열이
   있으면 그 문장을, 없으면 폴더명에서 추론한 한 줄. Area 는 `enforced:true`, Item 은 보통 미등록.
3. **인덱스 README 우선**: `00_Index/README.md`(또는 `INDEX.md`·root README) 가 "사용 중인 ID 목록"
   을 가지면 그것을 **권위본으로 채택** — 거기 적힌 `role` 문장과 빈 번호 예약을 그대로 반영.
   이게 johnny-decimal 의 핵심 특화 지점이다(코드 repo 엔 없는 사람 작성 SSOT).
4. **naming 표기 확정**: 점 표기 vs 단축 표기 빈도를 세어 우세한 쪽 regex 만 활성, §2 표에서 채택.
5. **ignore 채우기**: `.git/**`, `.omp/**`, OS 노이즈(`.DS_Store`, `.Trash/**`, `*.nosync`, `Icon?`),
   sync 충돌 부산물(`* (1).*`, `*conflicted*`) 을 `ignore` 에 넣어 audit 노이즈 차단.
6. **specificity**: 박지 말고 `learning-protocol.md` §4 공식으로 *계산*한다 — 각 규칙의 `origin`
   (`preset`/`inductive`/`learned`) 가중 비율. 실측 디렉토리를 구워 넣은 `directories[]`는
   `origin: inductive`, 프리셋 골격 그대로인 naming 규칙은 `origin: preset`. 순수 프리셋이면 0.0,
   귀납 보정이 섞이면 그만큼 >0. learn 승격마다 1 쪽으로 상승.
7. **사람 게이트**: 합성된 초안 rules.json + STRUCTURE.md/NAMING.md 를 사용자에게 보여 승인.
   "이 빈 번호는 예약인가 실수인가", "Item 표기는 점/단축 중 무엇이 정본인가" 를 여기서 확정.

### 초안 rules.json 스케치 (스캐폴드, 실측으로 채워질 자리는 `<…>`)

```json
{
  "omp_version": "<현재 omp 버전>",
  "project": { "name": "<폴더명>", "preset_origin": "johnny-decimal", "initialized": "<ISO date>" },
  "specificity": 0.0,
  "structure": {
    "convention": "johnny-decimal",
    "directories": [
      { "path": "00-09_<Meta>",          "id": "00-09", "role": "<인덱스가 있으면 그 용도 문장, 없으면 폴더명 추론>", "origin": "inductive", "enforced": true },
      { "path": "00-09_<Meta>/00_Index", "id": "00",    "role": "ID 부여의 권위본 인덱스",                            "origin": "inductive", "enforced": true },
      { "path": "90-99_<Archive>/91_Inbox", "id": "91", "role": "분류 전 임시 (정기 비우기)",                        "origin": "inductive", "enforced": false }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "*/",   "regex": "^[0-9]0-[0-9]9_[A-Za-z0-9][A-Za-z0-9_]*$", "description": "Area 폴더(root 직속)는 AA-BB_Name (범위+이름)", "origin": "preset", "severity": "warn" },
      { "applies_to": "*/*/", "regex": "^[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$",       "description": "Category 폴더(한 단계 아래)는 BB_Name",        "origin": "preset", "severity": "warn" }
    ]
  },
  "ignore": [".git/**", ".omp/**", "**/.DS_Store", "**/*.nosync", "**/* (1).*"]
}
```

> 위 directories[] 는 **예시 3줄**일 뿐 — 실제로는 스캔된 모든 Area/Category 가 들어간다.
> 빈 번호(`12`, `25`)는 directories[] 에 **넣지 않는다**(존재하지 않는 폴더). 예약은 STRUCTURE.md
> 사람용 문서에만 "의도적 예약" 으로 적고, audit 는 gap 을 위반으로 보지 않는다.

---

## §5. omp-learn 이 이 타입에서 특화하는 것 (관찰 → 규칙 승격 후보)

Johnny Decimal 워크스페이스를 쓸수록 learn 이 자주 승격하는 패턴들. 모두 사람 승인 게이트 경유.

- **분류 경계 규칙**: "어떤 자료가 *단어*가 아니라 *맥락·신분·목적* 으로 어느 Area 에 속하는가" 같은
  프로젝트 고유 분류 원칙. 같은 오분류가 반복 관찰되면 규칙으로 승격 (예: 두 Area 가 비슷한 키워드를
  공유할 때, 키워드가 아닌 판별 기준을 명문화).
- **확장자 → 위치 규칙**: "이 워크스페이스에서 `.pptx` 사본은 최신 버전 하나만, 구버전은 trash" 같은
  버전 부풀음 방지 규칙 (이 타입의 대표 함정 — 발표자료·대용량 산출물의 사본 누적).
- **표기 정본 굳히기**: 점 표기 vs 단축 표기 중 하나로 수렴 → 나머지를 `error` 로 승격.
- **빈 번호 의미 기록**: 어떤 빈 번호가 "예약"인지 "활성화 대기"인지를 wiki/ 에 누적(가벼운 채널).
- **인덱스 동기화 규칙**: 새 Category 추가 시 `00_Index/README.md` 갱신을 강제(권위본 drift 방지).
- **sync 매체 함정**: iCloud/Drive 위에서 폴더 rename 시 원본 복원 충돌 → "rename 지양, mv 후
  잔류 검증" 을 organize 규칙으로(이 타입은 git 이 아니라 sync 에 위임하는 경우가 많음).

> 위는 **범용 후보 목록**이지 강제 규칙이 아니다. 실제 승격은 해당 프로젝트에서 관찰이 반복되고
> 사람이 승인할 때만 rules.json 으로 들어가며, 그때마다 specificity 가 1 쪽으로 오른다.

---

## §6. 안티패턴 (이 프리셋에서 omp 가 하지 말아야 할 것)

- **빈 번호를 "정리"하지 마라** — 의도된 예약. gap 은 위반이 아니다.
- **Item 표기를 강제로 통일하지 마라** — 사용자 정본을 게이트에서 확인하기 전까지 `info` 로만.
- **git 을 가정하지 마라** — Johnny Decimal 워크스페이스는 iCloud/Drive sync 에 위임하는 경우가
  흔하다. `.git/` 이 없다고 결함으로 보지 말고, sync 매체 위라면 rename·동시 삭제를 더 보수적으로.
- **자료를 코드처럼 보지 마라** — `src/`/lockfile 이 없다고 "미완성 프로젝트" 로 판정 금지.
- **인덱스를 무시하지 마라** — 사람이 쓴 `00_Index` 가 폴더명·자동 추론보다 항상 우선한다.
