# Preset — para

> **Preset ID**: `para` · **specificity starting point**: `0.0` (pure preset)
> **This card is a _seed_**: omp-init synthesizes it with an actual inductive folder scan to produce a draft `rules.json`.
> Card ≠ final rules. The card is a general expectation of "if it's this project type, this is usually how it looks,"
> and the real rules come from the user's actual tree. On conflict, **the measured tree wins**.

---

## §0. Projects this preset fits

**PARA** (Projects / Areas / Resources / Archives) is Tiago Forte's information organization method, classifying material
into 4 tiers by *actionability* — work you're trying to finish now (Projects) → ongoing areas of
responsibility (Areas) → future reference material (Resources) → inactive storage (Archives). It is used not for a code repo but for a **workspace where a person
directly classifies and accumulates notes and knowledge** (Obsidian vault, Notion, digital garden, research notes). This preset is a candidate when you see the following signals:

- 4 actionability folders at the top level — `Projects` / `Areas` / `Resources` / `Archives`, or
  with order prefixes `0_Project` / `1_Area` / `2_Resource` / `3_Archive` (a common Obsidian PARA variant).
- **status subfolders** inside Projects, like `in_progress/` / `done/` — a lifecycle where completed projects are
  moved to Archives or marked done.
- Topic-based classification inside Resources — **knowledge type folders** like `concepts/` / `papers/` / `references/`.
- `.md` notes dominate, and notes are linked to each other via `[[wikilink]]` (Zettelkasten / Obsidian).
- An `.obsidian/` directory, vault operations notes like `Dashboard.md` · `Kanban.md`, and `YYYY-MM-DD.md` date files
  in `daily_notes/`.
- Expressions like "PARA", "Projects/Areas/Resources/Archives", "actionability" appear in CLAUDE.md or README.

> If code/build artifacts (`src/`, `package.json`, `requirements.txt`, `node_modules/`) are central, this is **not**
> the preset → consider `python-ml` / `web-app` / `monorepo` / `generic`. PARA is for *knowledge/material organization*.
>
> **Distinguishing PARA vs johnny-decimal** (both are PKM workspaces, so they get confused):
> - If two-digit numeric IDs (`10-19_`, `11_`, `11.01_`) form the folder skeleton and `00_Index` is the ID authority,
>   → `johnny-decimal` (searchability / number-based).
> - If the **4 actionability categories** (Projects/Areas/Resources/Archives) form the skeleton and material is classified by "are you acting on it now"
>   → `para` (actionability-based). Order prefixes `0_`/`1_`/`2_`/`3_` are for sorting, not JD
>   range IDs.
> - If the two are mixed (e.g., JD-style numbered folders inside the 4 PARA categories), use `para` as the origin and correct the numbering pattern
>   via an inductive naming rule.

---

## §1. Canonical directory layout (structure rules)

PARA's invariant skeleton is the **4 actionability categories**. `rules.json.structure.convention = "para"`.

```
<project root>/
├── 0_Project/               # PROJECTS : current in-progress work with a deadline/goal
│   ├── in_progress/         #   in progress (status subfolder is a common variant)
│   │   └── <project_name>/   #     individual project work folder (notes + dependent code/docs)
│   └── done/                #   completed — periodically moved to Archives
├── 1_Area/                  # AREAS : areas of responsibility maintained ongoing without a deadline (health/finance/research field)
│   └── <area_name>/
├── 2_Resource/              # RESOURCES : topic-based reference material for future use
│   ├── concepts/            #   concept notes (Zettelkasten)
│   └── papers/              #   paper review notes
├── 3_Archive/               # ARCHIVES : inactive — storage for things finished in the 3 categories above
│   └── calendar/daily_notes/   #   date notes etc. (YYYY-MM-DD.md)
├── Dashboard.md             # vault operations note (outside PARA categories, allowed directly under root)
└── Kanban.md
```

> The prefix notation is **consistently one of two** (determined inductively): the order-prefix variant (`0_Project`/`1_Area`/
> `2_Resource`/`3_Archive`, common in Obsidian) or the plain variant (`Projects`/`Areas`/`Resources`/`Archives`).
> A single vault uses only one.

### Role of each category (codified in rules.json `structure.directories[]`)

| Category | Folder example | `role` | Actionability | `enforced` default |
|:---|:---|:---|:---|:---:|
| **Projects** | `0_Project/` · `Projects/` | Work *you're trying to finish now* with a deadline/goal. When done, to Archives | Highest | `true` |
| **Areas** | `1_Area/` · `Areas/` | Areas of responsibility *maintained ongoing* without a deadline (maintaining roles/standards) | Ongoing | `true` |
| **Resources** | `2_Resource/` · `Resources/` | Topic-based material for *future reference*. Not acted on now | Low | `true` |
| **Archives** | `3_Archive/` · `Archives/` | Storage for things *deactivated* from the 3 categories above | None | `true` |
| **status sub** | `Projects/in_progress/` · `/done/` | Lifecycle marker inside Projects (variant) | — | `false` (advisory) |
| **type sub** | `Resources/concepts/` · `/papers/` | Knowledge type classification inside Resources (variant) | — | `false` |

> **Actionability flow** (structural health indicator, audit reports as `info`): as actionability drops, material moves
> in the direction Projects → Areas/Resources → Archives. If completed projects keep piling up in `0_Project/`,
> that's a signal to move to Archives (not a violation, a health hint).
>
> **Root-level operations note exception**: it is **normal** for vault operations notes that belong to none of the 4 categories,
> like `Dashboard.md`·`Kanban.md`·`changelog.md`·`README.md`·`CLAUDE.md`, to sit at root — not a violation.

---

## §2. Naming rules (naming rules + regex)

Codified in `rules.json.naming.patterns[]`. regex is Python `re` syntax, matched against the **basename**.

| Applies to (`applies_to`) | Meaning | regex (`regex`) | severity |
|:---|:---|:---|:---|
| Top-level PARA category (order-prefix variant) | `N_Singular` (e.g., `0_Project`) | `^[0-3]_[A-Z][A-Za-z]+$` | `warn` |
| Top-level PARA category (plain variant) | `Plural` (e.g., `Projects`) | `^(Projects\|Areas\|Resources\|Archives)$` | `warn` |
| daily note file | `YYYY-MM-DD.md` | `^\d{4}-\d{2}-\d{2}\.md$` | `info` |
| concept/paper note | note naming (determined inductively) | `<dominant pattern from the scan>` | `info` |

> omp-init **counts which is dominant — the order-prefix variant or the plain variant — in the measured scan**, and leaves
> only the dominant side's regex as `warn`, while leaving the rest as `info` or removing them. Note file naming (concepts/papers)
> varies wildly per vault, so the preset does not enforce it and leaves it to induction/learn.

### Examples (Good / Bad)

```
Good (category, prefix):  0_Project/   1_Area/   2_Resource/   3_Archive/
Good (category, plain):  Projects/    Areas/    Resources/    Archives/
Good (status sub):  0_Project/in_progress/   0_Project/done/
Good (type sub):  2_Resource/concepts/   2_Resource/papers/
Good (daily):      3_Archive/calendar/daily_notes/2026-05-31.md
Good (operations note):   Dashboard.md   Kanban.md   (directly under root OK)

Bad:  0_Projects/              → the prefix variant is singular (0_Project); only the plain variant is plural
Bad:  4_Inbox/                 → PARA is the four categories 0–3 (Inbox is a separate convention, not PARA)
Bad:  2_Resource/random.pptx   → an unclassified file directly under Resource (put it under concepts/papers etc.)
```

---

## §3. Dataset conventions (usually not applicable)

PARA is a **knowledge/material organization workspace**, so it almost never has the ML-style train/val/test dataset concept.
Defaults: `manifest.json.datasets = []`, `managed_by_external.tool = "none"`.

That said, the real pitfall of this type is **dependent code repos / large artifacts inside Projects folders** (notes are
the body, but a project folder drags along code, data, and media). Candidates that dataset-curator might record in the manifest:

- Embedded code repos (clone / submodule) inside a project folder → usually gitignored. The manifest only knows their
  location (not a dataset). If clone-management files like `.gitmodules`·`CLONES.md` exist, those are the SSOT.
- Large single artifacts (>50MB mp4·PPT copies·PDF dumps, in Archives or project attachments) →
  `source: "internal"`, no `split`. If too large to hash, `sha256: "UNHASHED"` (track size+mtime).
- Temporary folders awaiting migration to external HDD/iCloud → usually gitignored. Not data, not put in the manifest.
- **Actual data is never moved** (metadata-only).

> If ML-style split/lineage is needed, that's a `python-ml` signal, not para (if a python-ml structure exists
> *inside* a project folder, only that subtree can be judged separately as python-ml).

---

## §4. omp-init mapping guide (scan → this preset → draft rules.json)

The procedure by which rule-architect **synthesizes** project-scanner's inductive results with this card.

1. **Determine convention**: if the 4 actionability categories (`0_Project`/`1_Area`/`2_Resource`/`3_Archive`
   or `Projects`/`Areas`/`Resources`/`Archives`) appear directly under root, set `structure.convention = "para"`,
   `project.preset_origin = "para"`. (If a two-digit ID skeleton is dominant, it's `johnny-decimal`, not para.)
2. **Fill directories[]**: bake the scanned actual PARA categories + the status/type subfolders observed under them directly into
   `directories[]` entries. `path` = actual relative path, `role` = if there's a description in the README/CLAUDE.md,
   that sentence; otherwise a one-line inference from the category. The 4 categories are `enforced:true`; status/type subs are usually
   `enforced:false` (advisory). origin: measured categories are `inductive`, preset skeleton expectations are `preset`.
3. **Operations note whitelist**: root-level vault operations notes like `Dashboard.md`·`Kanban.md`·`changelog.md`·`README.md`·
   `CLAUDE.md` are outside the 4 PARA categories but normal — put them in `ignore` or the allowlist of `structure`
   so audit doesn't flag them as "unclassified files".
4. **Determine naming notation**: count the frequency of the order-prefix variant vs plain variant, activate only the dominant side's regex,
   adopting from the §2 table. Add daily note/concept note naming as `info` if the pattern is clear in the scan, otherwise omit.
5. **Fill ignore**: put `.git/**`, `.omp/**`, `.obsidian/**` (Obsidian settings), `.smart-env/**`,
   OS noise (`.DS_Store`, `*.tmp`, `*.backup`), gitignored embedded repos, and large folders awaiting external HDD migration
   into `ignore` to block audit noise / scan bloat. If a `.gitignore` exists, reflect its entries
   first (the ignore list the user has already declared).
6. **specificity**: don't slap a number on; *compute* it with the `learning-protocol.md` §4 formula — the `origin`-weighted
   ratio of each rule. The `directories[]` baked from measured categories/subs are `origin: inductive`, naming rules that stay as the preset
   skeleton are `origin: preset`. A pure preset is 0.0; with inductive corrections mixed in, it's >0 by that amount.
   It rises toward 1 with each learn promotion.
7. **Human gate**: show the synthesized draft rules.json + STRUCTURE.md/NAMING.md to the user for approval.
   "Which is canonical for prefix notation — order-prefix or plain", "should status subs (in_progress/done) be enforced or
   advisory only", "which root notes to whitelist as operations notes" are settled here.

### Draft rules.json sketch (scaffold; slots to be filled by measurement are `<…>`)

```json
{
  "omp_version": "<current omp version>",
  "project": { "name": "<folder name>", "preset_origin": "para", "initialized": "<ISO date>" },
  "specificity": 0.0,
  "structure": {
    "convention": "para",
    "directories": [
      { "path": "0_Project",  "role": "<current in-progress work with deadline/goal; the README sentence if present>", "origin": "inductive", "enforced": true },
      { "path": "1_Area",     "role": "<area of responsibility maintained ongoing without a deadline>",                        "origin": "inductive", "enforced": true },
      { "path": "2_Resource", "role": "<topic-based material for future reference>",                                  "origin": "inductive", "enforced": true },
      { "path": "3_Archive",  "role": "<inactive storage>",                                            "origin": "inductive", "enforced": true },
      { "path": "0_Project/in_progress", "role": "in-progress project (status sub)",                    "origin": "inductive", "enforced": false }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "*/", "regex": "^[0-3]_[A-Z][A-Za-z]+$", "description": "top-level PARA category is N_Singular (order-prefix variant)", "origin": "preset", "severity": "warn" }
    ]
  },
  "ignore": [".git/**", ".omp/**", ".obsidian/**", "**/.DS_Store", "**/*.tmp", "**/*.backup"]
}
```

> The directories[] above is just an **example** — in reality every scanned category/sub goes in.
> Root operations notes (Dashboard.md etc.) go in ignore/allowlist, not directories[] — they're files,
> not folders, and they're the vault's own operational material, not classification targets.

---

## §5. What omp-learn specializes for this type (observation → rule promotion candidates)

Patterns that learn frequently promotes the more you use a PARA workspace. All go through a human approval gate.

- **Actionability classification boundary rules**: PARA's core judgment, like "is this material a Project (acting now) or a Resource (future reference)",
  solidifies differently per vault. If the same misclassification is repeatedly observed, codify the discrimination criterion
  (e.g., "notes with a deadline are always 0_Project; without one, 1_Area/2_Resource").
- **Completed → Archives lifecycle rule**: PARA's signature operations rule, like "a project marked done moves to 3_Archive after N days"
  (preventing Projects-folder bloat — this type's pitfall).
- **Resource type classification**: the `concepts/` vs `papers/` vs `references/` boundary converges into a vault-specific rule
  (e.g., "code snippets go in a separate snippets/, not concepts").
- **Note naming / tag conventions**: if concept note/daily note naming or a tag hierarchy (`Concepts/`, `Papers/`) is
  repeatedly observed, promote it to a naming rule.
- **Embedded repo location rule**: if the location / gitignore pattern of code clones inside project folders is consistent
  (e.g., "all clones live under `<project>/code/`, managed by CLONES.md"), make it a rule.
- **Settling canonical prefix notation**: converging on one of order-prefix vs plain → promote the other to `error`.
- **wikilink integrity**: accumulate notes with broken `[[link]]` (dead links) in wiki/ as health hints (light channel).

> The above is a **general candidate list**, not enforced rules. Actual promotion enters rules.json only when observations
> repeat in that vault and a human approves, and each time specificity rises toward 1.

---

## §6. Anti-patterns (what omp must not do under this preset)

- **Do not create a 5th category** — PARA is exactly 4 actionability categories. If you see `Inbox`/`Meta` etc.,
  that's a PARA variant or a johnny-decimal mix, not a new PARA category.
- **Do not view notes as code** — don't rule something an "unfinished project" just because there's no `src/`/lockfile. PARA is
  a knowledge workspace.
- **Do not rule a completed project's non-move to Archives a violation** — it's a lifecycle health hint (`info`), not an
  enforced violation. The user may intentionally keep it in 0_Project.
- **Do not flag root operations notes as "unclassified files"** — Dashboard.md·Kanban.md·changelog.md being
  outside the 4 PARA categories is normal (whitelist §4-3).
- **Do not view an embedded repo as vault material** — code clones inside a project folder are often gitignored
  and managed by a separate SSOT (`CLONES.md`/`.gitmodules`). Audit must not sweep their interior with PARA rules
  (put it in ignore).
- **Do not touch `.obsidian/`** — the Obsidian settings directory is vault operations infrastructure, not material.
  Always ignore.
- **Do not forcibly unify prefix notation** — only `info`/`warn` until the user's canonical choice is confirmed at the gate.
  If order-prefix and plain are mixed, that's a first organize candidate (no automatic change).
