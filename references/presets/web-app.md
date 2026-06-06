# Preset — `web-app`

> Generic seed rule card. `omp-init`/`rule-architect` **synthesizes** this card with an
> **inductive scan of the actual folder** to produce a draft `rules.json`. This card itself is a
> generic artifact distributed identically to every user (specificity starting point = 0).
> Specialization is raised by `omp-learn` after init synthesis.
>
> `preset_origin` value: **`web-app`**
> Target schema: `references/schemas/rules.schema.json` (every item in this card is translated
> literally into that schema's `structure.directories[]` / `naming.patterns[]` / `ignore[]`.)

---

## 0. When this preset matches (rule-architect detection signals)

When `project-scanner`'s inductive result has enough of the signals below, treat `web-app` as the
best match. Don't decide on a single signal alone — judge by the **co-occurrence of 2 or more**.

- **Root manifest**: `package.json` exists at the root (strongest signal)
- **Framework traces**: one of `next.config.*` / `vite.config.*` / `vue.config.*` / `svelte.config.*` /
  `angular.json` / `remix.config.*` / `astro.config.*`
- **Source directory**: `src/` exists and contains two or more of `components/`·`pages/`(or `routes/`)·`lib/`·`api/`
- **Static assets**: a `public/` (or `static/`, `assets/`) directory
- **Test directory**: a group of `tests/`·`__tests__/`·`*.test.*`·`*.spec.*` files
- **Extension distribution**: `.ts`/`.tsx`/`.js`/`.jsx`/`.vue`/`.svelte` predominate

**Misclassification guard** — review another preset first when:
- `pyproject.toml`/`requirements.txt` + `.ipynb`/`.parquet` predominate → `python-ml`
- multiple `package.json` at the root (workspaces) + `packages/`·`apps/` → `monorepo`
- a two-digit ID (`10-19_*`, `11_*`) folder system → `johnny-decimal`
- all of the above signals are weak → `generic`

> **Single-signal limit**: if only `package.json` exists with no `src/` and no framework trace, do
> not conclude web-app. It may be a CLI tool or a library package. In that case use `generic` +
> inductive predominance.

---

## 1. Canonical directory layout (→ `structure.directories[]`)

Real-world convention for web applications. Names diverge by ecosystem (Next.js/Vite/SvelteKit etc.),
so **roles are fixed, paths are confirmed by the scan**. The below are seed defaults; put only
directories that actually exist in the folder into `directories[]` (do not force paths that do not exist).

`structure.convention` = `"src-layout"` (the convention of gathering source under `src/`. If the
actual folder places source directly at the root, correct to `"flat"`).

| path (seed) | role | enforced | notes |
|:---|:---|:---:|:---|
| `src/` | Root of the application source. All build-target code lives here. | true | If the framework-specific location is `app/` etc., substitute that path |
| `src/components/` | Reusable UI components. Presentation units not tied to a route. | true | |
| `src/pages/` or `src/routes/` | Routing entry points (pages/views). Next=`pages/`·`app/`, SvelteKit=`routes/`. | true | Register only whichever of the two actually exists |
| `src/lib/` | Framework-agnostic domain logic·utilities·client. Reusable code that is not UI. | true | |
| `src/api/` | API routes·server handlers·backend endpoints. | false(warn) | May move to `app/api/`·`server/` depending on framework |
| `public/` | Static assets served as-is without a build (favicons·images·`robots.txt`). | true | Vite uses `public/`, some use `static/`·`assets/` |
| `tests/` | Tests. Or may co-locate beside the source (`*.test.tsx`). | false(warn) | If co-located, don't force a directory; manage via naming |
| (root) | Config files are placed flat at the root (§1.1 below). | n/a | A group of files, not a directory — not put into `directories[]` |

**Role boundaries (what audit treats as a violation):**
- route·server-only code in `components/` → violation (role mixing)
- React/Vue components (`.tsx` UI) in `lib/` → must go to `components/` (warn)
- source code (`.ts`/`.js`) in `public/` → violation (only static assets should appear)
- business logic directly in `pages/` → recommend extracting to `lib/` (info)

### 1.1 Root config files (not a directory — handled only by naming/ignore)

By web-app convention, configs are normally placed **flat at the root** (do not flag this as a
violation). `package.json`, `package-lock.json`/`pnpm-lock.yaml`/`yarn.lock`,
`tsconfig.json`, `.eslintrc.*`/`eslint.config.*`, `.prettierrc.*`,
`vite.config.*`/`next.config.*` etc., `.env*`, `Dockerfile`, `README.md`.
→ These are not `structure.directories[]`; they are used as a root allow-list — a whitelist for audit
when it judges "root clutter".

---

## 2. Naming rules (→ `naming.patterns[]`, regex = Python `re`)

The web ecosystem has **no single standard**. Even within one project, React=component PascalCase
and SvelteKit/file-routing=kebab-case coexist. So the seed lays down only **conservative
non-conflicting rules**, and the scan measures the actual predominant pattern and corrects it. Most
severities are `warn` (respecting ecosystem variance).

| applies_to (seed glob) | regex (basename) | description | severity |
|:---|:---|:---|:---|
| `src/components/**/*.{tsx,jsx,vue}` | `^[A-Z][A-Za-z0-9]*\.(tsx\|jsx\|vue)$` | React/Vue component files are PascalCase. | warn |
| `src/{lib,api,utils}/**/*.{ts,js}` | `^[a-z][a-z0-9]*([-.][a-z0-9]+)*\.(ts\|js)$` | Non-component modules are kebab-case (or dotted). | warn |
| `src/pages/**/*` or `src/routes/**/*` | `^[a-z0-9\[\]._-]+$` | File-routing paths are lowercase kebab + dynamic segment `[id]`. | warn |
| `public/**/*` | `^[a-z0-9._-]+$` | Static assets are lowercase kebab (URL-safe). | warn |
| `**/*.{test,spec}.{ts,tsx,js,jsx}` | `^[A-Za-z0-9.-]+\.(test\|spec)\.(ts\|tsx\|js\|jsx)$` | Tests use the `<name>.test.*`/`.spec.*` suffix. | info |
| (env) `.env*` | `^\.env(\.[a-z]+)?$` | Env files take the form `.env`·`.env.local`·`.env.production`. | info |

**Rule synthesis guidance (for rule-architect):**
- If the scan measures a **component-predominant case (PascalCase vs kebab)**, correct the regex to
  follow that predominance. E.g., if it's a file-routing framework so components are also kebab,
  demote/remove the PascalCase rule.
- If the two cases are **mixed** (common), don't enforce via regex; leave only an observation at
  `severity: info` and let `omp-learn` promote it from repeated observations (no premature error).
- Treat barrel files like `index.{ts,tsx}` and framework-reserved filenames like
  `_app`/`_document`/`+page`/`+layout` as **exceptions** and exclude them from PascalCase/kebab checks.

---

## 3. Dataset convention (web-app = lightweight)

A web app is not an ML project. **Lightweight dataset tracking** is the default.

- Most web-apps have no "dataset" to track → `omp-dataset` is usually recommended **inactive**.
- Cases worth tracking: seed data (`prisma/seed.*`, `db/seeds/`), fixtures
  (`tests/fixtures/`, `__fixtures__/`), static content data (`content/`·`data/*.json`/`*.md`).
  → Register these as **metadata-only** (SHA256·size·lineage in manifest.json) only. The actual files
  are not moved.
- Image/media bundles in `public/` are not datasets but **static assets** (STRUCTURE domain). Do not
  put them in the manifest.
- DVC/git-lfs traces are rare in web-app, but on detecting `.dvc/`·`.gitattributes`(lfs) the
  delegation principle is the same (the manifest mirrors metadata only).

> Summary: the web-app preset **keeps the dataset slot open but OFF by default**. Turn it on only when
> seeds/fixtures actually exist.

---

## 4. How omp-init maps this preset onto the scan (synthesis procedure)

`omp-init` **does not use this card as-is.** It goes through the synthesis below to produce a draft
`rules.json`.

1. **Existence intersection** — among this card's seed directories, put **only those that actually
   exist in the folder** into `structure.directories[]`. Do not include nonexistent `api/`·`tests/`,
   or leave them at `enforced:false` (merely not there yet, not a violation).
2. **Path substitution** — match seed paths to actual paths via framework signals.
   Next.js App Router → `pages/` to `app/`, `api/` to `app/api/`. SvelteKit → `pages/` to
   `routes/`. Plain Vite → `pages/` may not exist (remove).
3. **Confirm convention** — `"src-layout"` if `src/` exists, `"flat"` if source is placed directly at the root.
4. **Naming measurement correction** — correct the §2 seed regexes by the predominant case the scan
   measured. If mixed, demote to `info`.
5. **ignore seed** — inject §5 below into `ignore[]`.
6. **specificity = 0** — right after synthesis it's the preset starting point. `project.preset_origin = "web-app"`.
   `project.name` is the `name` field of `package.json` or the root folder name.
7. **Human gate** — show the draft `rules.json` + STRUCTURE.md/NAMING.md to the human and get
   approval. No automatic enforcement.

**Handling scan ↔ preset conflicts:** if the actual folder differs from the preset (e.g., root-direct
placement without `src/`, or a `features/`-based structure), **the scan wins.** The preset only
provides a *naming·role vocabulary*; it does not force a structure that does not exist. Record the
conflict in STRUCTURE.md in one line ("this project uses the `app/` router instead of the preset
default `src/pages/`").

---

## 5. ignore seed (→ `rules.json.ignore[]`)

Globs that audit should always skip in web-app (noise suppression):

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

> `.env*` is both an ignore and a §2 naming observation target (the double listing is intentional —
> scan secrets but exclude them from the audit clutter judgment).

---

## 6. What omp-learn typically specializes in web-app

Typical observations that accumulate in `learned.md` during operation and get promoted (candidates
that raise specificity 0→1):

- **Fix the component location rule** — "this project feature-groups components into
  `src/components/<feature>/`" → replace the seed's flat `components/` with a feature-directory rule.
- **Fix the naming case** — when a previously mixed PascalCase/kebab converges to one side, promote
  `info`→`warn`/`error` and fix the regex.
- **Fix the router kind** — among `pages/` vs `app/` vs `routes/`, leave only the one actually used as
  enforced and remove the remaining seed candidates.
- **Test placement rule** — if "tests always co-locate beside the source as `*.test.tsx`" vs "always
  separated in `tests/`" is consistent 3+ times, fix one of the two as the project rule.
- **Shared code boundary** — unify on whichever of `lib/` vs `utils/` vs `shared/` this team uses.
- **Asset path** — fix to the actually-used path among `public/` vs `static/` vs `assets/`.

Each promotion goes through a human approval gate, and on promotion leaves the source observation ID
in `learned_refs[]` for traceability.

---

## 7. Synthesis result example (draft rules.json skeleton — for reference)

A synthesized draft (abbreviated) for when the scan finds Next.js App Router + TypeScript + `src/`
layout:

```json
{
  "omp_version": "0.2.1",
  "project": { "name": "my-web-app", "preset_origin": "web-app", "initialized": "2026-05-30" },
  "specificity": 0,
  "structure": {
    "convention": "src-layout",
    "directories": [
      { "path": "src", "role": "Application source root", "enforced": true },
      { "path": "src/components", "role": "Reusable UI components", "enforced": true },
      { "path": "src/app", "role": "App Router route entry points", "enforced": true },
      { "path": "src/app/api", "role": "Server API route handlers", "enforced": false },
      { "path": "src/lib", "role": "Framework-agnostic domain logic·utilities", "enforced": true },
      { "path": "public", "role": "Static assets served as-is", "enforced": true }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "src/components/**/*.tsx",
        "regex": "^[A-Z][A-Za-z0-9]*\\.tsx$",
        "description": "Components are PascalCase", "severity": "warn" },
      { "applies_to": "src/lib/**/*.ts",
        "regex": "^[a-z][a-z0-9]*([-.][a-z0-9]+)*\\.ts$",
        "description": "lib modules are kebab-case", "severity": "warn" }
    ]
  },
  "ignore": ["node_modules/**", ".next/**", "dist/**", ".env*", ".git/**", ".omp/**"]
}
```

> This example is a **reference skeleton**. The actual init confirms paths·regex·listed directories
> against the scan result via the §4 synthesis procedure above. Never copy this example verbatim.
