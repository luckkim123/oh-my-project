# Preset — johnny-decimal

> **Preset ID**: `johnny-decimal` · **specificity starting point**: `0.0` (pure preset)
> **This card is a _seed_**: omp-init **synthesizes** it with an actual inductive folder scan to produce a draft `rules.json`.
> Card ≠ final rules. The card is a general expectation of "for this project type, it usually looks like this,"
> while the real rules come from the user's actual tree. On conflict, **the measured tree wins**.

---

## §0. Projects this preset fits

**Johnny Decimal** is a personal / knowledge workspace organization method that groups an Area / Category / Item 3-tier hierarchy with two-digit numeric IDs. It applies not to code repos but to **folders where a person directly classifies and searches material themselves** (notes, presentation decks, assignments, documents, large output artifacts, etc.). This preset is a candidate if you see the following signals:

- Area folders at the top level with a **two-digit range + name** like `10-19_<AreaName>` / `20-29_<AreaName>`
  (Johnny Decimal standard examples: `10-19_Life-admin`, `20-29_Work`, `30-39_Projects`).
- Category folders inside an Area with a **two-digit ID + name** like `11_<CategoryName>` (e.g. `11_Finance`, `12_Travel`).
- ID-prefixed Item folders inside a Category, in the form `11.01_<item>` (dot notation) or `01_<item>` (shorthand notation).
- A folder index (README / INDEX) maintaining the "list of IDs currently in use" as the authoritative source.
- Expressions like "two-click rule" or "reserved empty numbers" appearing in docs or CLAUDE.md.

> If code / build artifacts (`src/`, `package.json`, `requirements.txt`, `node_modules/`) are central, this is **not** the preset
> → consider `python-ml` / `web-app` / `monorepo` / `generic`. Johnny Decimal is for *material storage*.

---

## §1. Canonical directory layout (structure rules)

Johnny Decimal's invariant skeleton. `rules.json.structure.convention = "johnny-decimal"`.

```
<project root>/
├── 00-09_Meta/              # AREA 00-09 : workspace's own meta (index, templates, decisions, plans)
│   ├── 00_Index/            #   CATEGORY 00 : folder index — authoritative source (SSOT) for ID assignment
│   ├── 01_Templates/        #   CATEGORY 01 : reusable templates
│   └── 02_Decisions/        #   CATEGORY 02 : decision records
├── 10-19_<AreaName>/        # AREA 10-19 : first topic area (e.g. Academic)
│   ├── 11_<Category>/       #   CATEGORY 11 : first classification within the area
│   │   ├── 11.01_<item>/    #     ITEM 11.01 : a work unit bundling multiple files
│   │   └── 11.02_<item>/    #     ITEM 11.02
│   └── 13_<Category>/       #   CATEGORY 13 : (12 may be intentionally left empty)
├── 20-29_<AreaName>/        # AREA 20-29 : second topic area
├── 90-99_Inbox_Archive/     # AREA 90-99 : pre-classification temp + inactive archive (conventional last Area)
│   ├── 91_Inbox/            #   CATEGORY 91 : temp before classification (emptied regularly)
│   └── 99_Archive/          #   CATEGORY 99 : inactive storage
```

### Role of each tier (codified as rules.json `structure.directories[]`)

| Tier | ID format | `id` field | Role (`role`) | `enforced` default |
|:---|:---|:---|:---|:---:|
| **Area** | `AA-BB_Name` (e.g. `10-19_Academic`) | `"10-19"` | Top-level topic area grouped by a range of 10. Holds no material directly, only Categories | `true` |
| **Category** | `BB_Name` (e.g. `11_Coursework`) | `"11"` | A single classification within one Area. The two digits fall within the parent Area range (`11`∈`10-19`) | `true` |
| **Item** | `BB.CC_name` or `CC_name` | `"11.01"` | The actual work-unit folder bundling multiple files. ID may be omitted for a single file | `false` (advisory) |
| **Index** | `00_Index/` (convention) | `"00"` | Authoritative source for the list of IDs in use. Consult it before placing a new folder | `true` |
| **Inbox** | `91_Inbox/` (convention) | `"91"` | Pre-classification temp. Emptied periodically | `false` |

> **Two-click rule** (structural health indicator, audit reports as `info`): any material should be reachable at a depth of two folders, `Area → Category`. An Item folder (the third click) is a work unit, so it's OK. Anything deeper inside it is a signal to reassign IDs.
>
> **Empty numbers are intentional reservations** (audit must never "tidy" them): empty slots like `12`, `25`, `43` are deliberately left for later. They are not a continuity defect, so **do not treat a gap as a violation**. New material receives the next empty number *in the order it was added*, with no alphabetical enforcement.

---

## §2. Naming rules (naming rules + regex)

Codified as `rules.json.naming.patterns[]`. The regex uses Python `re` syntax and matches on **basename**.

| Target (`applies_to`) | Meaning | regex (`regex`) | severity |
|:---|:---|:---|:---|
| Area folder (direct child of root) | `AA-BB_Name` — range + name | `^[0-9]0-[0-9]9_[A-Za-z0-9][A-Za-z0-9_]*$` | `warn` |
| Category folder | `BB_Name` — two digits + name | `^[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$` | `warn` |
| Item folder (dot notation) | `BB.CC_name` — Category.Item | `^[0-9]{2}\.[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$` | `info` |
| Item folder (shorthand notation) | `CC_name` — just two digits within a Category | `^[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$` | `info` |

### The notation style must be consistent, one of the two (determined inductively)

Johnny Decimal Items have two common notations, and **a single project uses only one consistently**:

- **Dot notation** (orthodox): `11.01_robotics_final_project` — connects Category and Item with a dot, globally unique.
- **Shorthand notation**: inside a Category folder (`11_Coursework`), `01_machine_learning`, `02_dynamic_programming` —
  since the parent Category gives context, the Item uses just two digits.

> omp-init **counts which notation is dominant** in the measured scan, marks only the dominant side's regex as `error`/`warn`, and leaves the rest as `info` or removes it. If the two are mixed, that is the first organize candidate.

### Examples (Good / Bad)

```
Good (Area):       10-19_Academic/    40-49_Reference/    90-99_Inbox_Archive/
Good (Category):   11_Coursework/     13_Lab_Research/    91_Inbox/
Good (Item·dot):   11.01_kalman_homework/    13.02_krit/
Good (Item·short): 01_machine_learning/      04_mobile_robotics/

Bad:  Academic/                  → Area but no ID range
Bad:  1_Coursework/              → Category not two digits (one digit)
Bad:  11_coursework_final.pptx   → file in a Category slot (should be an Item folder / single file)
Bad:  13_Lab_Research/sub/deep/x → two-click-rule violation (arbitrary nesting under an Item)
```

---

## §3. Dataset conventions (usually not applicable)

Johnny Decimal is a **material-storage workspace**, so the ML-style train/val/test dataset concept barely exists. Defaults: `manifest.json.datasets = []`, `managed_by_external.tool = "none"`.

That said, the real pitfall of this type is large output artifacts (accumulated PPT copies, mp4, large PDFs) causing **version bloat**. Candidates the dataset-curator might record in the manifest:

- A large single artifact (>50MB presentation video, data dump) → `source: "internal"`, no `split`, lineage optional.
- Files on a sync medium such as iCloud/exFAT → if too large to hash cheaply, `sha256: "UNHASHED"` (track size+mtime).
- **The actual data is never moved** (metadata-only). Since the sync medium (iCloud/Drive) handles syncing, the manifest only knows "what is where and whether it changed."

> If you need ML-style split/lineage, that's a `python-ml` signal, not johnny-decimal.

---

## §4. omp-init mapping guide (scan → this preset → draft rules.json)

The procedure by which rule-architect **synthesizes** project-scanner's inductive results with this card.

1. **Confirm convention**: if root has ≥1 `AA-BB_Name` Area folder + a Category (`BB_Name`) is visible, set
   `structure.convention = "johnny-decimal"`, `project.preset_origin = "johnny-decimal"`.
2. **Fill directories[]**: bake the scanned actual Areas/Categories directly into `directories[]` entries.
   `path` = actual relative path, `id` = the extracted two digits (or range), `role` = the sentence from the index README's "purpose" column
   if it exists, otherwise a one-liner inferred from the folder name. Areas are `enforced:true`; Items are usually not registered.
3. **Index README first**: if `00_Index/README.md` (or `INDEX.md` / root README) holds the "list of IDs in use,"
   **adopt it as authoritative** — reflect its `role` sentences and empty-number reservations verbatim.
   This is johnny-decimal's core specialization point (a human-authored SSOT that code repos lack).
4. **Confirm naming notation**: count dot-notation vs shorthand-notation frequency, activate only the dominant side's regex, adopt from the §2 table.
5. **Fill ignore**: put `.git/**`, `.omp/**`, OS noise (`.DS_Store`, `.Trash/**`, `*.nosync`, `Icon?`),
   and sync-conflict byproducts (`* (1).*`, `*conflicted*`) into `ignore` to block audit noise.
6. **specificity**: don't hammer in a value — *compute* it with the formula in `learning-protocol.md` §4 — the weighted ratio of each rule's `origin`
   (`preset`/`inductive`/`learned`). The `directories[]` baked from the measured directories are
   `origin: inductive`; naming rules left as the bare preset skeleton are `origin: preset`. A pure preset is 0.0,
   inductive correction mixed in pushes it >0 by that much. Each learn promotion raises it toward 1.
7. **Human gate**: show the synthesized draft rules.json + STRUCTURE.md/NAMING.md to the user for approval.
   "Is this empty number a reservation or a mistake?", "Is the canonical Item notation dot or shorthand?" — settle these here.

### Draft rules.json sketch (scaffold; slots to be filled by measurement are `<…>`)

```json
{
  "omp_version": "<current omp version>",
  "project": { "name": "<folder name>", "preset_origin": "johnny-decimal", "initialized": "<ISO date>" },
  "specificity": 0.0,
  "structure": {
    "convention": "johnny-decimal",
    "directories": [
      { "path": "00-09_<Meta>",          "id": "00-09", "role": "<the purpose sentence if an index exists, else inferred from folder name>", "origin": "inductive", "enforced": true },
      { "path": "00-09_<Meta>/00_Index", "id": "00",    "role": "authoritative index for ID assignment",                            "origin": "inductive", "enforced": true },
      { "path": "90-99_<Archive>/91_Inbox", "id": "91", "role": "temp before classification (emptied regularly)",                        "origin": "inductive", "enforced": false }
    ]
  },
  "naming": {
    "patterns": [
      { "applies_to": "*/",   "regex": "^[0-9]0-[0-9]9_[A-Za-z0-9][A-Za-z0-9_]*$", "description": "Area folder (direct child of root) is AA-BB_Name (range+name)", "origin": "preset", "severity": "warn" },
      { "applies_to": "*/*/", "regex": "^[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$",       "description": "Category folder (one level down) is BB_Name",        "origin": "preset", "severity": "warn" }
    ]
  },
  "ignore": [".git/**", ".omp/**", "**/.DS_Store", "**/*.nosync", "**/* (1).*"]
}
```

> The directories[] above are just an **example of 3 lines** — in reality, all scanned Areas/Categories go in.
> Empty numbers (`12`, `25`) are **not put** into directories[] (non-existent folders). Reservations are written only in the human-facing STRUCTURE.md
> document as "intentional reservations," and audit does not treat a gap as a violation.

---

## §5. What omp-learn specializes for this type (observation → rule promotion candidates)

Patterns that learn frequently promotes the more you use a Johnny Decimal workspace. All pass through a human approval gate.

- **Classification boundary rules**: project-specific classification principles like "which Area a piece of material belongs to by
  *context / identity / purpose* rather than by *word*." When the same misclassification is repeatedly observed, promote it to a rule (e.g. when two Areas
  share similar keywords, codify a discriminating criterion that is not the keyword).
- **Extension → location rules**: version-bloat prevention rules like "in this workspace, keep only the latest version of a `.pptx` copy; old versions go to trash"
  (the signature pitfall of this type — copy accumulation of decks and large artifacts).
- **Hardening the canonical notation**: converge on one of dot notation vs shorthand notation → promote the rest to `error`.
- **Recording the meaning of empty numbers**: accumulate in wiki/ whether a given empty number is "reserved" or "awaiting activation" (light channel).
- **Index synchronization rule**: enforce updating `00_Index/README.md` when a new Category is added (prevents authoritative-source drift).
- **Sync-medium pitfall**: renaming a folder on iCloud/Drive triggers original-restore conflicts → make "avoid rename; verify residue after mv"
  an organize rule (this type often delegates to sync rather than git).

> The above is a **general candidate list**, not enforced rules. Actual promotion enters rules.json only when observation repeats in that project and
> a human approves, and specificity rises toward 1 each time.

---

## §6. Anti-patterns (what omp must NOT do in this preset)

- **Do not "tidy" empty numbers** — they are intentional reservations. A gap is not a violation.
- **Do not forcibly unify Item notation** — keep it as `info` only until the user's canonical choice is confirmed at the gate.
- **Do not assume git** — Johnny Decimal workspaces commonly delegate to iCloud/Drive sync.
  Don't treat the absence of `.git/` as a defect; on a sync medium, be more conservative about rename and concurrent deletion.
- **Do not view material as code** — don't rule it "an unfinished project" just because there's no `src/`/lockfile.
- **Do not ignore the index** — a human-authored `00_Index` always takes precedence over folder names / automatic inference.
