# Preset Card — generic

> **What this is**: A data file, not a skill. `omp-init`/`rule-architect` read this card and
> **synthesize** it with an inductive scan of the real folder (`project-scanner`) into a draft
> `rules.json`. This is the **fallback seed** — used when no richer preset (python-ml / web-app /
> research-lab / monorepo / johnny-decimal) confidently matches the scanned folder. It carries only
> **minimal sane defaults**; `omp-learn` specializes it over time as the project reveals its real
> shape. Do not duplicate this knowledge into agent files — point at this card. `preset_origin` in
> `rules.json` becomes `"generic"`.

## 정체성 (when this preset wins)

이 프리셋은 **"잘 모르겠을 때의 안전한 기본값"** 이다. 폴더가 특정 프로젝트 타입의 시그니처
(예: `pyproject.toml`+`src/`, `package.json`+`src/`, `data/raw`+`notebooks/`, `XX-YY_` Johnny-Decimal
ID, monorepo `packages/`) 를 충분히 보이지 **않을 때** rule-architect 가 이걸 고른다.

핵심은 **과소 명세(under-specification)** 다. 모르는 것을 지어내지 않는다. 강제 규칙은 거의 없고,
대부분 `info`/`warn` 수준의 부드러운 권고만 둔다. `specificity: 0` 으로 출발해서, 실제 사용 중
드러난 패턴을 `omp-learn` 이 승격시키며 점점 진짜 규칙으로 굳힌다. 즉 generic 은 **목적지가 아니라
출발점** — 시간이 지나면 거의 모든 generic 프로젝트가 자기만의 규칙으로 발산한다.

## (1) Canonical directory layout

generic 은 특정 레이아웃을 강요하지 않는다. 거의 모든 프로젝트가 공유하는 **최소 골격만** 시드로 둔다.
실제 디렉토리는 inductive scan 이 채운다 (아래 §4).

| path | role | id | enforced | 비고 |
|:---|:---|:---|:---|:---|
| `.` (root) | 프로젝트 진입점. README·라이선스·최상위 설정만. 떠도는 산출물 금지. | — | `true` | root 청결이 generic 의 유일한 강한 규칙 |
| `docs/` | 사람용 문서·노트 (있을 때) | — | `false` | 스캔으로 발견되면 추가, 없으면 강제 안 함 |
| `src/` 또는 코드 루트 | 소스 코드 (스캔으로 추정) | — | `false` | 이름은 스캔이 결정 (`src`/`lib`/`app`/프로젝트명) |
| `data/` | 데이터 파일 (있을 때) | — | `false` | 존재하면 등록, 하위 구조는 강제 안 함 |
| `scripts/` 또는 `bin/` | 실행 스크립트·도구 (있을 때) | — | `false` | |
| `tests/` | 테스트 (있을 때) | — | `false` | |

**핵심 규칙 — root 청결 (root hygiene)**: generic 의 단 하나의 강한(enforced) 구조 규칙은
"**루트에 떠도는 잡파일을 두지 않는다**" 이다. 루트에는 README, 라이선스, 최상위 설정 파일
(`pyproject.toml`/`package.json`/`Makefile`/`.gitignore` 등), 그리고 1급 서브디렉토리만 허용.
임시 파일·산출물·일회성 스크립트가 루트에 쌓이면 audit 이 플래그한다. **나머지 디렉토리는 모두
`enforced: false`** — 존재가 확인되면 역할을 기록하되, 거기 뭐가 들어가야 하는지는 강제하지 않는다
(아직 모르므로).

> **합성 규칙**: 위 표의 디렉토리 중 **스캔으로 실제 존재가 확인된 것만** `rules.json.structure.directories[]`
> 에 들어간다. 존재하지 않는 디렉토리를 미리 만들거나 규칙에 박지 않는다 (generic 은 청사진을 강요하지
> 않는다). `structure.convention` 은 `"flat"` 으로 둔다 (명명된 레이아웃 없음). 단 하나 항상 들어가는
> 엔트리는 root (`path: "."`, `enforced: true`).

## (2) Naming conventions

generic 의 명명 규칙은 **일관성(consistency)** 한 가지다 — 특정 케이스를 강요하기보다,
"이 프로젝트가 이미 쓰는 케이스를 계속 써라" 를 권고한다.

| applies_to | regex (Python `re`) | description | severity |
|:---|:---|:---|:---|
| `*` (모든 새 파일/폴더) | `^[A-Za-z0-9._-]+$` | 공백·특수문자 없는 이름 (이식성·셸 안전) | `warn` |
| `*` | (스캔이 채움 — 아래) | 프로젝트의 지배적 케이스와 일관 (예: 전부 `snake_case` 면 `kebab-case` 신규 파일은 warn) | `info` |
| `README*` | `^README(\.[a-z]+)?$` | 루트 README 는 표준 이름 | `info` |

**케이스 일관성 (스캔이 결정)**: generic 은 `snake_case`/`kebab-case`/`camelCase`/`PascalCase`
중 무엇을 강요하지 않는다. 대신 `project-scanner` 가 **기존 파일들의 지배적 케이스를 귀납**하고,
rule-architect 가 그걸 `info` 규칙으로 박는다. 예: 기존 파일 80% 가 `snake_case` 면
"신규 파일은 `snake_case` 권장" 규칙이 생긴다. 처음부터 한 케이스를 박지 않는 이유 — generic 은
프로젝트가 이미 정한 관습을 존중하지, 새 관습을 강요하지 않는다.

**예시 (Good/Bad)**:
- Good: `data_loader.py`, `user-profile.tsx`, `README.md`, `2026-05-30-notes.md`
- Bad: `data loader.py` (공백), `final FINAL (2).docx` (공백+괄호), `Untitled.md` (의미 없는 이름)

> **합성 규칙**: 위 1행 (공백/특수문자 금지) 은 항상 들어간다 (전 OS 안전). 2행 (케이스 일관성) 은
> 스캔이 지배적 케이스를 ≥60% 신뢰도로 찾았을 때만 `info` 로 들어간다 — 못 찾으면 생략 (지어내지 말 것).
> 모든 generic 명명 규칙은 `error` 가 아니라 `warn`/`info` — 강제 이동을 유발하지 않는 부드러운 권고.

## (3) Dataset conventions

generic 은 dataset 중심 프로젝트가 **아닐 수도** 있다고 가정한다. 따라서 dataset 규칙은 **조건부**다.

- 스캔이 `data/`·`datasets/`·대용량 바이너리(`.parquet`/`.csv`/`.npz`/`.h5`/`.pkl`) 를 **발견하면**:
  `omp-dataset` 가 `manifest.json` 에 메타데이터-only 로 등록 (SHA256·크기·행수). 실제 데이터는
  **절대 안 옮긴다** (`dataset-curator` 계약 — `references/manifest.schema.json` 참조).
- **발견하지 못하면**: dataset 규칙을 비워 둔다. 강제로 `data/` 를 만들지 않는다.
- `.dvc/`·`.git/lfs`·`.gitattributes`(lfs filter) 감지 시: "이미 DVC/git-lfs 관리 중 — manifest 는
  메타만 미러" 로 위임. generic 은 기존 데이터 관리 도구를 존중한다.

> generic 에는 데이터 split/lineage 명명 규약이 시드로 없다 (프로젝트 타입을 모르므로). 데이터가
> 실제로 보이고 사용자가 split 추적을 원하면 `omp-dataset` 이 그때 manifest 스키마대로 채운다.

## (4) How omp-init maps a scanned folder onto this preset

`omp-init` 의 합성 = **(a) inductive scan + (b) generic seed → draft rules.json**. generic 에선
귀납(scan)이 시드(preset)보다 **우세**하다 — 시드가 거의 비어 있으므로 스캔이 실질을 채운다.

1. **루트 인벤토리**: `project-scanner` 가 루트의 파일·1급 디렉토리를 나열. README 존재 여부 확인.
2. **디렉토리 역할 귀납**: 발견된 각 1급 디렉토리에 대해 내용물로 역할 추정
   (코드 비중 높음 → 소스 루트, `.csv`/`.parquet` 비중 → 데이터, `.md` 비중 → docs, 테스트 파일 → tests).
   추정 가능한 것만 `directories[]` 에 넣고, 불확실하면 `role` 에 "스캔 추정 — 확인 필요" 표기.
3. **케이스 귀납**: 기존 파일명들의 지배적 케이스 집계 → ≥60% 면 `info` 명명 규칙 생성.
4. **데이터 감지**: §3 조건부 규칙 적용.
5. **ignore 시드**: `rules.json.ignore[]` 에 항상 `.git/**`, `.omp/**`, `node_modules/**`,
   `__pycache__/**`, `.venv/**`, `*.pyc`, `.DS_Store` 를 넣는다 (전 타입 공통 노이즈).
6. **specificity = 0**: 순수 프리셋 출발점임을 명시. preset_origin = `"generic"`.
7. **사람 게이트**: 합성된 draft rules.json 을 사람에게 제시. "이게 너 프로젝트 맞아?" 확인 후 확정.

> **합성의 자세**: generic 에서 init 의 임무는 "규칙을 많이 만드는 것" 이 아니라 "지금 확실히 아는
> 최소만 박고, 나머지는 learn 에 미루는 것" 이다. 의심스러우면 규칙을 **넣지 말고** wiki/learned 에
> 관찰만 남긴다. 잘못된 강제 규칙(파일을 엉뚱하게 옮기게 함)이 빈 규칙보다 훨씬 해롭다.

## (5) What omp-learn typically specializes here

generic 은 발산이 가장 큰 프리셋이다 (시작이 거의 비어 있으므로). `omp-learn` 이 흔히 승격시키는 것:

- **디렉토리 역할 확정**: "`scratch/` 에는 항상 임시 노트만" 같은 관찰 3회 반복 → `enforced: true`
  구조 규칙으로 승격. specificity 상승.
- **확장자 ↔ 위치 규칙**: "이 프로젝트에서 `.pkl` 은 항상 `outputs/models/`" → 명명/구조 규칙 신설.
- **케이스 고정**: init 때 `info` 였던 케이스 일관성이, 위반이 거의 없음을 확인하면 `warn` 으로 격상.
- **프리셋 재분류 신호**: 스캔/사용 중 특정 타입 시그니처가 누적되면 (예: `pyproject.toml` 추가됨)
  rule-architect 가 "이제 python-ml 프리셋으로 재초기화하는 게 낫지 않나?" 를 사람에게 제안.
  generic 은 더 구체적인 프리셋으로 **졸업**할 수 있다.

> 모든 승격은 `learned.md` → 사람 승인 게이트를 거친다 (heavy 채널). 승격된 규칙은 `rules.json`
> 의 `learned_refs[]` 에 출처를 남긴다. 가벼운 패턴·결정은 `.omp/wiki/` 에 자동 누적 (승인 불필요).

## Draft rules.json skeleton (generic seed)

`rule-architect` 가 합성 시 시작점으로 쓰는 골격. **대괄호 부분은 inductive scan 이 채운다** —
스캔이 못 채우면 그 엔트리는 생략한다 (지어내지 말 것). `rules.schema.json` 준수.

```json
{
  "omp_version": "0.2.1",
  "project": {
    "name": "[scan: 루트 폴더명 또는 manifest/pyproject 의 name]",
    "preset_origin": "generic",
    "initialized": "[ISO date]"
  },
  "specificity": 0,
  "structure": {
    "convention": "flat",
    "directories": [
      { "path": ".", "role": "프로젝트 루트 — README·라이선스·최상위 설정·1급 디렉토리만. 떠도는 산출물 금지.", "enforced": true }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "*", "regex": "^[A-Za-z0-9._-]+$", "description": "공백·특수문자 없는 이식성 안전 이름.", "severity": "warn" }
    ]
  },
  "ignore": [".git/**", ".omp/**", "node_modules/**", "__pycache__/**", ".venv/**", "*.pyc", ".DS_Store"],
  "learned_refs": []
}
```

> `directories[]` 에는 스캔으로 확인된 1급 디렉토리가 append 되고, `naming.patterns[]` 에는 케이스
> 일관성 규칙(스캔이 ≥60% 신뢰도로 찾았을 때)이 append 된다. 위 골격은 **항상 참인 최소항만** 담은
> 보수적 출발점이다 — generic 의 핵심 철학 그대로 "확실한 것만, 나머지는 learn 에게".
