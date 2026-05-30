# Preset — `web-app`

> 범용 시드 규칙 카드. `omp-init`/`rule-architect`가 **실제 폴더 귀납 스캔**과 이 카드를
> **합성**해 초안 `rules.json`을 만든다. 이 카드 자체는 모든 사용자에게 동일하게 배포되는
> 범용물(specificity 출발점 = 0). 특화는 init 합성 이후 `omp-learn`이 올린다.
>
> `preset_origin` 값: **`web-app`**
> 대상 스키마: `references/schemas/rules.schema.json` (이 카드의 모든 항목은 그 스키마의
> `structure.directories[]` / `naming.patterns[]` / `ignore[]` 로 직역된다.)

---

## 0. 언제 이 프리셋이 매칭되나 (rule-architect 판별 신호)

`project-scanner`의 귀납 결과가 아래 신호를 충분히 가지면 `web-app`을 최적 매칭으로 본다.
하나만으로 단정하지 말고 **2개 이상**의 동시 출현으로 판별한다.

- **루트 manifest**: `package.json`이 루트에 존재 (가장 강한 신호)
- **프레임워크 흔적**: `next.config.*` / `vite.config.*` / `vue.config.*` / `svelte.config.*` /
  `angular.json` / `remix.config.*` / `astro.config.*` 중 하나
- **소스 디렉토리**: `src/`가 있고 그 안에 `components/`·`pages/`(또는 `routes/`)·`lib/`·`api/`
  중 둘 이상
- **정적 자산**: `public/`(또는 `static/`, `assets/`) 디렉토리
- **테스트 디렉토리**: `tests/`·`__tests__/`·`*.test.*`·`*.spec.*` 파일군
- **확장자 분포**: `.ts`/`.tsx`/`.js`/`.jsx`/`.vue`/`.svelte`가 우세

**오분류 가드** — 다음이면 다른 프리셋을 우선 검토:
- `pyproject.toml`/`requirements.txt` + `.ipynb`/`.parquet` 우세 → `python-ml`
- 루트에 여러 `package.json`(워크스페이스) + `packages/`·`apps/` → `monorepo`
- 두 자리 ID(`10-19_*`, `11_*`) 폴더 체계 → `johnny-decimal`
- 위 신호가 모두 약하면 → `generic`

> **단일 신호 한계**: `package.json` 하나만 있고 `src/`도 프레임워크 흔적도 없으면 web-app으로
> 단정하지 말 것. CLI 도구·라이브러리 패키지일 수 있다. 그 경우 `generic` + 귀납 우세.

---

## 1. 정규 디렉토리 레이아웃 (→ `structure.directories[]`)

웹 애플리케이션의 실세계 관례. 생태계(Next.js/Vite/SvelteKit 등)마다 이름이 갈리므로
**역할(role)은 고정, 경로(path)는 스캔이 확정**한다. 아래는 시드 기본값이며, 실제 폴더에
존재하는 디렉토리만 `directories[]`에 넣는다(존재하지 않는 경로를 강제하지 말 것).

`structure.convention` = `"src-layout"` (소스를 `src/` 아래에 모으는 관례. 실제 폴더가 루트
직배치면 `"flat"`로 교정).

| path (시드) | role | enforced | 비고 |
|:---|:---|:---:|:---|
| `src/` | 애플리케이션 소스의 루트. 빌드 대상 코드는 모두 여기. | true | 프레임워크별 위치(`app/` 등)면 그 경로로 치환 |
| `src/components/` | 재사용 UI 컴포넌트. 라우트에 묶이지 않은 표현 단위. | true | |
| `src/pages/` 또는 `src/routes/` | 라우팅 진입점(페이지/뷰). Next=`pages/`·`app/`, SvelteKit=`routes/`. | true | 둘 중 실재하는 쪽만 등록 |
| `src/lib/` | 프레임워크 비종속 도메인 로직·유틸·클라이언트. UI가 아닌 재사용 코드. | true | |
| `src/api/` | API 라우트·서버 핸들러·백엔드 엔드포인트. | false(warn) | 프레임워크에 따라 `app/api/`·`server/`로 이동 가능 |
| `public/` | 빌드 없이 그대로 서빙되는 정적 자산(파비콘·이미지·`robots.txt`). | true | Vite는 `public/`, 일부는 `static/`·`assets/` |
| `tests/` | 테스트. 또는 소스 옆 동거(`*.test.tsx`)일 수 있음. | false(warn) | 동거 패턴이면 디렉토리 강제 X, naming으로 관리 |
| (루트) | 설정 파일은 루트에 평탄 배치(아래 §1.1). | n/a | 디렉토리 아닌 파일군 — `directories[]`에 넣지 않음 |

**역할 경계(audit가 위반으로 보는 것):**
- `components/`에 라우트·서버 전용 코드 → 위반(역할 혼입)
- `lib/`에 React/Vue 컴포넌트(`.tsx` UI) → `components/`로 가야 함(warn)
- `public/`에 소스 코드(`.ts`/`.js`) → 위반(정적 자산만 와야 함)
- 비즈니스 로직이 `pages/`에 직접 → `lib/`로 추출 권고(info)

### 1.1 루트 설정 파일 (디렉토리 아님 — naming/ignore로만 다룸)

웹앱 관례상 설정은 **루트 평탄 배치**가 정상이다(이를 위반으로 잡지 말 것).
`package.json`, `package-lock.json`/`pnpm-lock.yaml`/`yarn.lock`,
`tsconfig.json`, `.eslintrc.*`/`eslint.config.*`, `.prettierrc.*`,
`vite.config.*`/`next.config.*` 등, `.env*`, `Dockerfile`, `README.md`.
→ 이들은 `structure.directories[]`가 아니라, 루트 허용 목록으로 audit가 "루트 잡동사니"를
판별할 때의 화이트리스트로 쓴다.

---

## 2. 명명 규칙 (→ `naming.patterns[]`, regex = Python `re`)

웹 생태계는 **단일 표준이 없다**. 같은 프로젝트도 React=컴포넌트 PascalCase,
SvelteKit/파일라우팅=kebab-case가 공존한다. 따라서 시드는 **충돌하지 않는 보수적 규칙**만
깔고, 실제 우세 패턴은 스캔이 측정해 교정한다. severity는 대부분 `warn`(생태계 편차 존중).

| applies_to (시드 glob) | regex (basename) | description | severity |
|:---|:---|:---|:---|
| `src/components/**/*.{tsx,jsx,vue}` | `^[A-Z][A-Za-z0-9]*\.(tsx\|jsx\|vue)$` | React/Vue 컴포넌트 파일은 PascalCase. | warn |
| `src/{lib,api,utils}/**/*.{ts,js}` | `^[a-z][a-z0-9]*([-.][a-z0-9]+)*\.(ts\|js)$` | 비컴포넌트 모듈은 kebab-case(또는 dotted). | warn |
| `src/pages/**/*` 또는 `src/routes/**/*` | `^[a-z0-9\[\]._-]+$` | 파일라우팅 경로는 소문자 kebab + 동적 세그먼트 `[id]`. | warn |
| `public/**/*` | `^[a-z0-9._-]+$` | 정적 자산은 소문자 kebab(URL 안전). | warn |
| `**/*.{test,spec}.{ts,tsx,js,jsx}` | `^[A-Za-z0-9.-]+\.(test\|spec)\.(ts\|tsx\|js\|jsx)$` | 테스트는 `<name>.test.*`/`.spec.*` 접미사. | info |
| (env) `.env*` | `^\.env(\.[a-z]+)?$` | 환경파일은 `.env`·`.env.local`·`.env.production` 형태. | info |

**규칙 합성 지침 (rule-architect에게):**
- 스캔이 **컴포넌트 우세 케이스(PascalCase vs kebab)** 를 측정하면 그 우세를 따라 regex를 교정.
  예: 파일라우팅 프레임워크라 컴포넌트도 kebab이면 PascalCase 규칙을 강등/삭제.
- 두 케이스가 **혼재**하면(흔함) regex로 강제하지 말고 `severity: info`로 관찰만 남기고,
  반복 관찰을 `omp-learn`이 승격하도록 둔다(섣부른 error 금지).
- `index.{ts,tsx}` 같은 배럴 파일, `_app`/`_document`/`+page`/`+layout` 같은 프레임워크
  예약 파일명은 **예외**로 두고 PascalCase/kebab 검사에서 제외.

---

## 3. Dataset 관례 (web-app = 경량)

웹앱은 ML 프로젝트가 아니다. **dataset 추적은 가벼움**이 기본.

- 대부분의 web-app은 추적할 "dataset"이 없다 → `omp-dataset`는 보통 **비활성** 권고.
- 추적할 가치가 있는 경우: 시드 데이터(`prisma/seed.*`, `db/seeds/`), 픽스처
  (`tests/fixtures/`, `__fixtures__/`), 정적 콘텐츠 데이터(`content/`·`data/*.json`/`*.md`).
  → 이들은 **메타데이터-only**(manifest.json에 SHA256·크기·lineage)로만 등록. 실제 파일 불이동.
- `public/`의 이미지/미디어 번들은 dataset이 아니라 **정적 자산**(STRUCTURE 영역). manifest에
  넣지 말 것.
- DVC/git-lfs 흔적은 web-app에서 드물지만 `.dvc/`·`.gitattributes`(lfs) 감지 시 위임 원칙 동일
  (manifest는 메타만 미러).

> 요약: web-app 프리셋은 dataset 슬롯을 **열어두되 기본 OFF**. 시드/픽스처가 실재할 때만 켠다.

---

## 4. omp-init이 이 프리셋을 스캔에 매핑하는 법 (합성 절차)

`omp-init`은 이 카드를 **그대로 쓰지 않는다.** 아래 합성을 거쳐 초안 `rules.json`을 만든다.

1. **존재 교집합** — 이 카드의 시드 디렉토리 중 **실제 폴더에 존재하는 것만**
   `structure.directories[]`에 넣는다. 존재하지 않는 `api/`·`tests/`는 넣지 않거나
   `enforced:false`로 둔다(아직 없을 뿐 위반은 아님).
2. **경로 치환** — 프레임워크 신호로 시드 경로를 실제 경로에 맞춘다.
   Next.js App Router → `pages/`를 `app/`로, `api/`를 `app/api/`로. SvelteKit → `pages/`를
   `routes/`로. Vite 순수 → `pages/` 없을 수 있음(제거).
3. **convention 확정** — `src/`가 있으면 `"src-layout"`, 소스가 루트 직배치면 `"flat"`.
4. **naming 측정 교정** — §2 시드 regex를 스캔이 잰 우세 케이스로 교정. 혼재면 `info`로 강등.
5. **ignore 시드** — 아래 §5를 `ignore[]`에 주입.
6. **specificity = 0** — 합성 직후엔 프리셋 출발점. `project.preset_origin = "web-app"`.
   `project.name`은 `package.json`의 `name` 필드 또는 루트 폴더명.
7. **사람 게이트** — 초안 `rules.json` + STRUCTURE.md/NAMING.md를 사람에게 보여주고 승인받는다.
   자동 강제 없음.

**스캔 ↔ 프리셋 충돌 처리:** 실제 폴더가 프리셋과 다르면(예: `src/` 없이 루트 직배치, 또는
`features/` 기반 구조) **스캔이 이긴다.** 프리셋은 *이름·역할 어휘*를 제공할 뿐, 실재하지 않는
구조를 강요하지 않는다. 충돌은 STRUCTURE.md에 한 줄로 기록("프리셋 기본 `src/pages/` 대신
이 프로젝트는 `app/` 라우터 사용").

---

## 5. ignore 시드 (→ `rules.json.ignore[]`)

web-app에서 audit가 항상 건너뛰어야 하는 글롭(노이즈 억제):

```
node_modules/**
.next/**
.nuxt/**
.svelte-kit/**
dist/**
build/**
out/**
coverage/**
.turbo/**
.vercel/**
.netlify/**
*.log
.env*
.git/**
.omp/**
```

> `.env*`는 ignore이자 §2의 naming 관찰 대상(이중 등재 의도적 — 비밀은 스캔하되 audit
> 잡동사니 판정에선 제외).

---

## 6. omp-learn이 web-app에서 전형적으로 특화하는 것

운영하며 `learned.md`에 쌓이고 승격되는 전형 관찰(specificity를 0→1로 올리는 후보):

- **컴포넌트 위치 규칙 확정** — "이 프로젝트는 컴포넌트를 `src/components/<feature>/`로
  feature-grouped한다" → 시드의 평탄 `components/`를 feature 디렉토리 규칙으로 대체.
- **명명 케이스 확정** — 혼재였던 PascalCase/kebab이 한쪽으로 수렴하면 `info`→`warn`/`error`로
  승격하고 regex를 고정.
- **라우터 종류 고정** — `pages/` vs `app/` vs `routes/` 중 실제 쓰는 하나만 enforced로 남기고
  나머지 시드 후보 제거.
- **테스트 배치 규칙** — "테스트는 항상 소스 옆 `*.test.tsx` 동거" vs "항상 `tests/` 분리"가
  3회 이상 일관되면 둘 중 하나를 프로젝트 규칙으로 고정.
- **공유 코드 경계** — `lib/` vs `utils/` vs `shared/` 중 이 팀이 쓰는 어휘로 통일.
- **자산 경로** — `public/` vs `static/` vs `assets/` 실제 사용 경로로 고정.

각 승격은 사람 승인 게이트를 거치며, 승격 시 `learned_refs[]`에 출처 관찰 ID를 남겨 추적한다.

---

## 7. 합성 결과 예시 (초안 rules.json 골격 — 참고용)

스캔이 Next.js App Router + TypeScript + `src/` 레이아웃을 발견했을 때의 합성 초안(축약):

```json
{
  "omp_version": "0.1.0",
  "project": { "name": "my-web-app", "preset_origin": "web-app", "initialized": "2026-05-30" },
  "specificity": 0,
  "structure": {
    "convention": "src-layout",
    "directories": [
      { "path": "src", "role": "애플리케이션 소스 루트", "enforced": true },
      { "path": "src/components", "role": "재사용 UI 컴포넌트", "enforced": true },
      { "path": "src/app", "role": "App Router 라우트 진입점", "enforced": true },
      { "path": "src/app/api", "role": "서버 API 라우트 핸들러", "enforced": false },
      { "path": "src/lib", "role": "프레임워크 비종속 도메인 로직·유틸", "enforced": true },
      { "path": "public", "role": "그대로 서빙되는 정적 자산", "enforced": true }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "src/components/**/*.tsx",
        "regex": "^[A-Z][A-Za-z0-9]*\\.tsx$",
        "description": "컴포넌트는 PascalCase", "severity": "warn" },
      { "applies_to": "src/lib/**/*.ts",
        "regex": "^[a-z][a-z0-9]*([-.][a-z0-9]+)*\\.ts$",
        "description": "lib 모듈은 kebab-case", "severity": "warn" }
    ]
  },
  "ignore": ["node_modules/**", ".next/**", "dist/**", ".env*", ".git/**", ".omp/**"]
}
```

> 이 예시는 **참고용 골격**이다. 실제 init은 위 §4 합성 절차로 스캔 결과에 맞춰 경로·regex·
> 등재 디렉토리를 확정한다. 절대 이 예시를 그대로 복사하지 말 것.
