# Preset — `monorepo`

> A generic seed rule set. A monorepo manages multiple packages/apps/libraries in **one repo**
> with shared tooling. omp-init **synthesizes** the actual folder scan (induction) with this card
> (deduction) to produce a draft `rules.json`. This card is a generic seed distributed identically
> to all users; it does not hardcode any specific project's package names or tool choices — those
> are filled in by init's inductive scan and later omp-learn promotions.

`preset_origin`: `monorepo`

---

## 1. Canonical directory layout

The essence of a monorepo is that **one repo holds many deployable units (packages/apps/libs),
with tooling shared at the root**. There are two mainstream layouts, and omp-init determines which
one via the scan.

### Variant A — flat `packages/` (npm/pnpm/yarn workspaces, Turborepo, Nx default)

```
<repo root>/
├── packages/                 # all deployable units listed flat here (★ key boundary)
│   ├── <pkg-a>/              # one independent package = one directory
│   │   ├── src/             # package source
│   │   ├── tests/           # package-scoped tests (or __tests__/, *.test.ts colocated)
│   │   ├── package.json     # per-package manifest (name·version·deps)
│   │   └── README.md
│   ├── <pkg-b>/
│   └── <pkg-c>/
├── apps/                     # (optional) deployable apps — distinct from libraries (packages)
│   └── <app-name>/
├── tools/ | scripts/         # repo-wide build·codegen scripts
├── package.json              # root manifest — declares workspaces, shared devDeps
├── pnpm-workspace.yaml | turbo.json | nx.json | lerna.json  # workspace tool config
├── tsconfig.base.json        # shared tooling config (inherited from root)
├── .eslintrc | biome.json    # shared lint
└── .github/workflows/        # CI (usually builds only affected/changed packages)
```

### Variant B — split `apps/` + `libs/` (Nx recommended, Bazel/Gradle polyglot)

```
<repo root>/
├── apps/                     # deployed applications (end product)
│   └── <app-name>/{src,tests}/
├── libs/ | packages/         # shared libraries (apps depend on these)
│   └── <lib-name>/{src,tests}/
├── tools/                    # build plugins·generators
├── BUILD | WORKSPACE | settings.gradle  # (if Bazel/Gradle)
└── (same root shared tooling)
```

### Role per directory — rules.json `structure.directories[]` seed

| path | role | enforced |
|:---|:---|:---:|
| `packages/` (or `libs/`) | Shared·reusable libraries. Each subdirectory = an independent package boundary. | true |
| `apps/` | Deployable applications. May depend on libs, but libs must not depend on apps. | true |
| `packages/<pkg>/src/` | The package's source. Do not directly import another package's src by relative path (use the package name). | true |
| `packages/<pkg>/tests/` | Only that package-scoped tests. No cross-package tests. | true |
| `packages/<pkg>/package.json` | Per-package manifest. Exactly one required per package. | true |
| `tools/` \| `scripts/` | Repo-wide tools·codegen. No package logic. | false |
| (root) `package.json` etc. workspace config | Shared tooling SSOT. Do not duplicate declarations per package. | true |

> **Synthesis guidance**: If the init scan finds only `packages/` → `structure.convention = "monorepo-flat"`.
> If it finds both `apps/` + `libs/` (or `apps/`+`packages/`) → `"monorepo-apps-libs"`.
> Put only directories that actually exist into `directories[]`, and leave the rest of the card as
> comment/learned candidates (don't hardcode nonexistent folders as enforced — audit would flag
> them all as violations).

---

## 2. Naming conventions

The crux of monorepo naming is **package-scoped identification** — the package name becomes the
unit of the import path, CI filter, and version tag.

| target | rule | example (good / bad) |
|:---|:---|:---|
| package directory | `kebab-case`, short with domain meaning. | `auth-client`, `ui-tokens` / `AuthClient`, `pkg1` |
| package name (`package.json` name) | scoped: `@<org>/<pkg>`, suffix matches the directory name. | `@acme/auth-client` / `@acme/AuthClient` |
| app directory | `kebab-case`, names the product/target. | `web`, `admin-dashboard`, `mobile` / `App2` |
| library vs app prefix (optional) | Nx-style domain-type: `<domain>-<type>`. | `feature-checkout`, `util-formatters` |
| repo-wide scripts | `kebab-case`, starts with a verb. | `build-affected.ts`, `gen-types.mjs` |
| version tag (when independently released) | `<pkg>@<semver>`. | `@acme/auth-client@1.4.0` |

### rules.json `naming.patterns[]` seed (Python regex, adjust to the actual language)

```jsonc
[
  {
    "applies_to": "packages/*/",
    "regex": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    "description": "package directory is kebab-case",
    "severity": "warn"
  },
  {
    "applies_to": "apps/*/",
    "regex": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    "description": "app directory is kebab-case",
    "severity": "warn"
  },
  {
    "applies_to": "{packages,libs,apps}/*/package.json",
    "regex": "^package\\.json$",
    "description": "each package/app has its own manifest (audit checks existence per directory)",
    "severity": "error"
  }
]
```

> For monorepos in languages other than JS/TS, the manifest name differs (`Cargo.toml`/`go.mod`/`pyproject.toml`/
> `pom.xml`/`BUILD.bazel`). init catches the actual manifest via scan and substitutes `applies_to` —
> the card's `package.json` is just the most common default.

---

## 3. Dataset conventions

A monorepo is generally **dataset-light** — being code/library-centric, it may have no data/
directory. So dataset rules are **conditional** (leave them empty if absent; don't force them).

- If there is a data package inside the monorepo (`packages/<data-pkg>/` or root `fixtures/`), the
  data within belongs to that package boundary — don't read it from another package by relative path.
- Test fixtures (`packages/<pkg>/tests/fixtures/`, `__fixtures__/`) are classified as **test
  assets**, not data — part of the code, not a manifest dataset.
- If a truly large dataset (training data, etc.) is mixed into the monorepo, it's usually an
  anti-pattern (repo bloat) → omp records it in the manifest as metadata-only and, upon detecting
  `.dvc/`·git-lfs, delegates (mirroring metadata only). The data content is **never moved or copied**
  (dataset-curator invariant contract).

> Synthesis guidance: If the scan shows no `data/`·`*.parquet`·`*.csv` etc., start `manifest.datasets`
> as an empty array. Seed DATASETS.md with "this monorepo does not track datasets (code-centric)".

---

## 4. How omp-init maps a scanned folder onto this preset

The **inductive signals (scan signals)** by which rule-architect selects this card as a candidate
→ **synthesis action**:

| if the scan shows this | monorepo preset signal | synthesis action |
|:---|:---|:---|
| `workspaces` key in root `package.json` / `pnpm-workspace.yaml` / `turbo.json` / `nx.json` / `lerna.json` | strong (near-certain) | `preset_origin = "monorepo"`, record the workspace tool in PROJECT.md |
| two or more directories under `packages/` each holding a `package.json` (or manifest) | strong | `convention = "monorepo-flat"`, register each package in `directories[]` |
| `apps/` + (`libs/` or `packages/`) both present | strong | `convention = "monorepo-apps-libs"`, seed the apps→libs one-way dependency rule |
| polyglot build config (`WORKSPACE`/`BUILD.bazel`, multi-module `settings.gradle`) | medium | map to monorepo but substitute manifest names·language with scanned values |
| only a single `package.json` at root, no sub-packages | weak (beware false positive) | not a monorepo → re-examine other presets such as `web-app`/`python-ml`/`generic` |

**Synthesis procedure (rule-architect):**
1. Estimate monorepo confidence from the signals above. If weak, compare against other presets and pick the best match.
2. **Project the card's generic layout onto the scanned actual tree** — put only directories·packages that exist into `structure.directories[]` (don't enforce nonexistent folders).
3. Look at the actual manifest filename·actual package naming pattern and substitute `applies_to`/`regex` in `naming.patterns[]` (e.g., if it's `snake_case` rather than kebab, swap the regex).
4. Start with `specificity = 0` (pure preset). The more you fill via induction, the higher the effective specialization; but explicit specificity is raised by omp-learn promotion.
5. Present the draft `rules.json` + STRUCTURE.md/NAMING.md at the human gate. Write to `.omp/` only after approval.

**When uncertain**: Don't hardcode card rules as enforced; leave them as `severity: "info"` or
learned.md candidates — monorepos vary widely in convention across teams, so seed conservatively
so audit doesn't spew false violations.

---

## 5. What omp-learn typically specializes here

The observations most often promoted to project-specific rules during monorepo operation
(representative generic→specialized paths). omp-learn accumulates them in learned.md → human
approval → promotion to enforced rules in rules.json:

- **Dependency-direction rules**: **layer/boundary** rules such as "apps import libs but libs must
  not import apps", "`util-*` must not import any `feature-*`". The heart of monorepo specialization.
- **Package naming domain dictionary**: Solidify the set of prefixes/domains this repo actually uses
  (`feature-`/`util-`/`data-`/`ui-`) into an enum → if a new package has a name outside the
  dictionary, audit warns.
- **Shared tooling boundary**: Codify this repo's actual habit — either "tsconfig/eslint/jest config
  lives only at root, packages must not redefine it", or conversely "each package holds its own build
  script".
- **Test location habit**: Converge on the one pattern this repo actually uses among `tests/` vs
  `__tests__/` vs colocated in `src` (`*.test.ts`) → warn on the other locations.
- **Release unit**: Independent versioned releases (per-package semver) vs fixed version (lerna
  fixed) — specialize the `naming` version rule from the observed tag pattern.
- **New-package scaffold rule**: A new package must have `src/` + `tests/` + `package.json` +
  `README.md` → promote to audit error when missing.

Light channel (wiki/): patterns·decisions such as "this repo uses pnpm + turbo", "CI runs only
affected builds", "found 1 circular dependency between packages (`auth`↔`session`)" accumulate
automatically into the wiki without a gate, recoverable via grep in the next session.
