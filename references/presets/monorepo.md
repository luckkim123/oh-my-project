# Preset — `monorepo`

> 범용 시드 규칙 세트. 여러 패키지·앱·라이브러리를 **하나의 repo**에서 공유 tooling으로
> 관리하는 monorepo. omp-init이 실제 폴더 스캔(귀납)과 이 카드(연역)를 **합성**해 초안
> `rules.json`을 만든다. 이 카드는 모든 사용자에게 동일하게 배포되는 generic seed이며,
> 특정 프로젝트의 패키지 이름·도구 선택을 박지 않는다 — 그건 init의 귀납 스캔과 이후
> omp-learn 승격이 채운다.

`preset_origin`: `monorepo`

---

## 1. Canonical directory layout

monorepo의 본질은 **다수의 배포 단위(packages/apps/libs)를 한 repo가 품고, tooling은
root에서 공유**한다는 것. 두 가지 주류 배치가 있으며 omp-init은 스캔으로 어느 쪽인지 판별한다.

### Variant A — flat `packages/` (npm/pnpm/yarn workspaces, Turborepo, Nx 기본)

```
<repo root>/
├── packages/                 # 모든 배포 단위가 여기 평면 나열 (★ 핵심 경계)
│   ├── <pkg-a>/              # 독립 패키지 1개 = 1 디렉토리
│   │   ├── src/             # 패키지 소스
│   │   ├── tests/           # 패키지-스코프 테스트 (또는 __tests__/, *.test.ts 동거)
│   │   ├── package.json     # 패키지별 manifest (이름·버전·deps)
│   │   └── README.md
│   ├── <pkg-b>/
│   └── <pkg-c>/
├── apps/                     # (선택) 배포 가능한 앱 — 라이브러리(packages)와 구분
│   └── <app-name>/
├── tools/ | scripts/         # repo 전역 빌드·코드젠 스크립트
├── package.json              # root manifest — workspaces 선언, 공유 devDeps
├── pnpm-workspace.yaml | turbo.json | nx.json | lerna.json  # workspace 도구 설정
├── tsconfig.base.json        # 공유 tooling 설정 (root에서 상속)
├── .eslintrc | biome.json    # 공유 lint
└── .github/workflows/        # CI (보통 affected/changed 패키지만 빌드)
```

### Variant B — `apps/` + `libs/` 분리 (Nx 권장, Bazel/Gradle 다언어)

```
<repo root>/
├── apps/                     # 배포되는 application (end product)
│   └── <app-name>/{src,tests}/
├── libs/ | packages/         # 공유 라이브러리 (앱들이 의존)
│   └── <lib-name>/{src,tests}/
├── tools/                    # 빌드 플러그인·generator
├── BUILD | WORKSPACE | settings.gradle  # (Bazel/Gradle인 경우)
└── (root 공유 tooling 동일)
```

### 디렉토리별 역할 (role) — rules.json `structure.directories[]` 시드

| path | role | enforced |
|:---|:---|:---:|
| `packages/` (또는 `libs/`) | 공유·재사용 라이브러리. 각 하위 디렉토리 = 독립 패키지 경계. | true |
| `apps/` | 배포 가능한 application. libs에 의존하되 libs는 apps에 의존 금지. | true |
| `packages/<pkg>/src/` | 해당 패키지의 소스. 다른 패키지 src를 상대경로로 직접 import 금지(패키지 이름으로). | true |
| `packages/<pkg>/tests/` | 해당 패키지-스코프 테스트만. cross-package 테스트 금지. | true |
| `packages/<pkg>/package.json` | 패키지별 manifest. 패키지마다 1개 필수. | true |
| `tools/` \| `scripts/` | repo 전역 도구·코드젠. 패키지 로직 금지. | false |
| (root) `package.json` 등 workspace 설정 | 공유 tooling SSOT. 패키지 단위로 중복 선언 금지. | true |

> **합성 지침**: init 스캔이 `packages/`만 발견 → `structure.convention = "monorepo-flat"`.
> `apps/` + `libs/`(또는 `apps/`+`packages/`) 둘 다 발견 → `"monorepo-apps-libs"`.
> 실제 존재하는 디렉토리만 `directories[]`에 넣고, 카드의 나머지는 주석/learned 후보로 둔다
> (없는 폴더를 enforced로 박지 말 것 — audit이 전부 위반으로 띄운다).

---

## 2. Naming conventions

monorepo 명명의 핵심은 **package-scoped 식별** — 패키지 이름이 곧 import 경로·CI 필터·버전
태그의 단위가 된다.

| 대상 | 규칙 | 예시 (good / bad) |
|:---|:---|:---|
| 패키지 디렉토리 | `kebab-case`, 짧고 도메인 의미. | `auth-client`, `ui-tokens` / `AuthClient`, `pkg1` |
| 패키지 이름 (`package.json` name) | scoped: `@<org>/<pkg>`, 디렉토리명과 suffix 일치. | `@acme/auth-client` / `@acme/AuthClient` |
| 앱 디렉토리 | `kebab-case`, 제품/타깃 명시. | `web`, `admin-dashboard`, `mobile` / `App2` |
| 라이브러리 vs 앱 접두 (선택) | Nx 스타일 도메인-타입: `<domain>-<type>`. | `feature-checkout`, `util-formatters` |
| repo-전역 스크립트 | `kebab-case`, 동사로 시작. | `build-affected.ts`, `gen-types.mjs` |
| 버전 태그 (독립 배포 시) | `<pkg>@<semver>`. | `@acme/auth-client@1.4.0` |

### rules.json `naming.patterns[]` 시드 (Python regex, 실제 언어 맞춰 조정)

```jsonc
[
  {
    "applies_to": "packages/*/",
    "regex": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    "description": "패키지 디렉토리는 kebab-case",
    "severity": "warn"
  },
  {
    "applies_to": "apps/*/",
    "regex": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    "description": "앱 디렉토리는 kebab-case",
    "severity": "warn"
  },
  {
    "applies_to": "{packages,libs,apps}/*/package.json",
    "regex": "^package\\.json$",
    "description": "각 패키지·앱은 자체 manifest를 가진다(존재 검사는 audit이 디렉토리 단위로)",
    "severity": "error"
  }
]
```

> JS/TS 외 언어 monorepo면 manifest 이름이 다르다(`Cargo.toml`/`go.mod`/`pyproject.toml`/
> `pom.xml`/`BUILD.bazel`). init은 스캔으로 실제 manifest를 잡아 `applies_to`를 치환한다 —
> 카드의 `package.json`은 가장 흔한 기본값일 뿐.

---

## 3. Dataset conventions

monorepo는 일반적으로 **dataset-light** — 코드·라이브러리 중심이라 data/ 디렉토리가 없을 수
있다. 따라서 dataset 규칙은 **조건부**다(없으면 비워 둔다, 억지로 만들지 않는다).

- monorepo 안에 data 패키지가 있다면(`packages/<data-pkg>/` 또는 root `fixtures/`), 그 안의
  데이터는 해당 패키지 경계에 귀속 — cross-package에서 상대경로로 읽지 말 것.
- 테스트 fixture(`packages/<pkg>/tests/fixtures/`, `__fixtures__/`)는 데이터가 아니라 **테스트
  자산**으로 분류 — manifest dataset이 아니라 코드의 일부.
- 진짜 큰 dataset(학습 데이터 등)이 monorepo에 섞여 있으면 보통 anti-pattern(repo 비대) → omp는
  metadata-only로만 manifest에 기록하고 `.dvc/`·git-lfs 감지 시 위임(메타만 미러). 데이터 내용은
  **절대 이동·복사 안 함**(dataset-curator 불변 계약).

> 합성 지침: 스캔에서 `data/`·`*.parquet`·`*.csv` 등이 안 보이면 `manifest.datasets`는 빈 배열로
> 시작. DATASETS.md는 "이 monorepo는 dataset을 추적하지 않음(코드 중심)"으로 시드.

---

## 4. How omp-init maps a scanned folder onto this preset

rule-architect가 이 카드를 후보로 선택하는 **귀납 신호(scan signals)** → **합성 동작**:

| 스캔에서 이게 보이면 | monorepo 프리셋 신호 | 합성 동작 |
|:---|:---|:---|
| root `package.json`에 `workspaces` 키 / `pnpm-workspace.yaml` / `turbo.json` / `nx.json` / `lerna.json` | 강함 (확정에 가까움) | `preset_origin = "monorepo"`, workspace 도구를 PROJECT.md에 기록 |
| `packages/` 아래 2개 이상 디렉토리가 각자 `package.json`(또는 manifest) 보유 | 강함 | `convention = "monorepo-flat"`, 각 패키지를 `directories[]`에 등록 |
| `apps/` + (`libs/` 또는 `packages/`) 동시 존재 | 강함 | `convention = "monorepo-apps-libs"`, apps→libs 단방향 의존 규칙 시드 |
| 다언어 빌드 설정 (`WORKSPACE`/`BUILD.bazel`, `settings.gradle` 다중 모듈) | 중간 | monorepo로 매핑하되 manifest 이름·언어를 스캔값으로 치환 |
| root에만 `package.json` 하나, 하위 패키지 없음 | 약함 (오탐 주의) | monorepo 아님 → `web-app`/`python-ml`/`generic` 등 다른 프리셋 재검토 |

**합성 절차 (rule-architect):**
1. 위 신호로 monorepo 확신도 산정. 약하면 다른 프리셋과 비교해 best-match를 고른다.
2. 카드의 generic layout을 **스캔된 실제 트리로 투영** — 존재하는 디렉토리·패키지만 `structure.directories[]`에 넣는다(없는 폴더 enforce 금지).
3. 실제 manifest 파일명·실제 패키지 명명 패턴을 보고 `naming.patterns[]`의 `applies_to`/`regex`를 치환(예: kebab이 아니라 `snake_case`면 regex 교체).
4. `specificity = 0`으로 시작(순수 프리셋). 귀납으로 채운 부분이 많을수록 실질 특화도는 높지만, 명시적 specificity는 omp-learn 승격이 올린다.
5. 초안 `rules.json` + STRUCTURE.md/NAMING.md를 사람 게이트에 제시. 승인 후에만 `.omp/`에 기록.

**불확실하면**: 카드 규칙을 enforced로 박지 말고 `severity: "info"` 또는 learned.md 후보로
둔다 — monorepo는 팀마다 컨벤션 편차가 크므로 audit이 거짓 위반을 쏟지 않게 보수적으로 시드.

---

## 5. What omp-learn typically specializes here

monorepo에서 운영 중 가장 자주 프로젝트-고유 규칙으로 승격되는 관찰들(generic→specialized
대표 경로). omp-learn이 learned.md에 누적 → 사람 승인 → rules.json 강제 규칙으로 승격:

- **의존 방향 규칙**: "apps는 libs를 import하나 libs는 apps를 import 금지", "`util-*`는 어떤
  `feature-*`도 import 금지" 같은 **layer/boundary** 규칙. monorepo 특화의 핵심.
- **패키지 명명 도메인 사전**: 이 repo가 실제로 쓰는 접두/도메인(`feature-`/`util-`/`data-`/
  `ui-`) 집합을 enum으로 굳힘 → 새 패키지가 사전 밖 이름이면 audit warn.
- **공유 tooling 경계**: "tsconfig/eslint/jest 설정은 root에서만, 패키지가 재정의 금지" 또는
  반대로 "각 패키지가 자체 build 스크립트 보유" 중 이 repo의 실제 관습을 규칙화.
- **테스트 위치 관습**: `tests/` vs `__tests__/` vs `src` 동거(`*.test.ts`) 중 이 repo가
  실제로 쓰는 패턴 하나로 수렴 → 나머지 위치 warn.
- **release 단위**: 독립 버전 배포(packages별 semver) vs fixed 버전(lerna fixed) — 관찰된
  태그 패턴으로 `naming` 버전 규칙 특화.
- **신규 패키지 scaffold 규칙**: 새 패키지는 반드시 `src/` + `tests/` + `package.json` +
  `README.md`를 갖춘다 → 누락 시 audit error로 승격.

가벼운 채널(wiki/): "이 repo는 pnpm + turbo 사용", "affected 빌드만 CI에서 돈다",
"패키지 간 순환 의존 1건 발견(`auth`↔`session`)" 같은 패턴·결정은 게이트 없이 wiki에
자동 누적되어 다음 세션 grep으로 회수.
