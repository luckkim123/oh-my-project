# Safe File Operations — organizer's hard protocol

This card is the SSOT the **organizer** agent must obey whenever it moves, renames,
or deletes a file. It is derived from hard-won failures (iCloud rename sync
conflicts, exFAT cross-volume move residue, accidental permanent deletion).
omp's whole value collapses if a "reorganize" step loses a file.

## Core rule

> **Avoid irreversible loss.** The rule is not "always run `trash`" — it is
> "never let a file disappear silently." Use the safest path the environment offers.

## Move = copy-verify-delete, never a bare `mv` across volumes

1. `mv` (or copy) source → destination.
2. **Verify the destination actually has the files**: `find`/`ls` the destination,
   compare count and (for important files) SHA-256 against the source.
3. **Only then** remove the source. NEVER `rm` the source in the same breath as the
   move — sync lag (iCloud / Google Drive) or cross-volume copy (exFAT AppleDouble)
   can leave files behind, and a same-breath delete then loses them.

## Boundary check: every move target must stay inside the project root (T22)

Before *any* mutation, organizer resolves the destination's real path (following
symlinks) and confirms it is still inside the managed project root. On synced folders
(iCloud/Drive) a path can be a symlink that escapes the root; moving a file "out" of
the project is silent data loss from the user's point of view.

```python
from pathlib import Path
def target_inside_root(target, project_root) -> bool:
    t = Path(target).resolve()       # resolve symlinks
    r = Path(project_root).resolve()
    return t == r or r in t.parents  # equivalent to t.is_relative_to(r) (py3.9+)
# If False → REFUSE the move, surface it as a violation (hand off to auditor),
# and mutate nothing. A target escaping the root is never auto-corrected.
```

This is a guard, not a mover: it only decides go/no-go. It composes with
copy-verify-delete below — boundary check first, then the safe move sequence.

## Delete = recycle bin, not permanent erase

Cross-platform branch (organizer detects OS via `platform`/`os.name`):

| OS | Preferred trash | Fallback |
|:---|:---|:---|
| macOS | `trash` CLI if present, else move into `~/.Trash` | — |
| Linux desktop | `gio trash`, else `trash-cli` (`trash-put`) | — |
| Windows | PowerShell recycle (`Shell.Application` namespace 10) | — |
| No trash (Docker/CI/minimal) | **STOP.** Confirm a copy exists elsewhere AND get the user's explicit "this is permanent" approval before any `rm`. | — |

In a git repo, `git rm` + commit is itself recoverable — acceptable if the repo is committed.

## Rename: prefer NOT to, on sync folders

On iCloud/Drive-synced folders, a folder `mv` rename can make the sync engine restore
the original name, leaving a half-synced copy **alongside** the original. Before
deleting any "old" path after a rename, run `diff -rq old new` (or hash-compare) and
confirm the new path is a **superset** of the old. Only delete when the subset check passes.

## Always propose before executing

organizer NEVER auto-moves. It produces a move plan (from → to, with the violated rule
cited), and a human approves before any filesystem mutation. This mirrors oms's
"detection (auditor) ≠ execution (organizer)" split.

## Dry-run first

Every batch move/delete supports a dry-run that prints the full plan and the verify
commands that *would* run, with zero mutation. The real run is only entered after the
dry-run output is shown and approved.
