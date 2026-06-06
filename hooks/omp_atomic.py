"""Atomic JSON write for .omp/ SSOT files (T20). stdlib only, cross-platform.

Closes the asymmetry where omp enforced safe-fileops.md (copy→verify→delete) for
*user file moves* but had no equivalent write-safety for writes to its *own state
files* (rules.json, manifest.json, versions/ snapshots). If the single source of
truth is corrupted by a crash mid-write, the whole harness dies — so write to a
temp file first, fsync, then atomic rename.

os.replace() guarantees an atomic same-volume rename on both POSIX and Windows
(Python 3.3+) — a partial-write state is never exposed at the target. No
third-party dependency.
"""
import json
import os
import tempfile
from pathlib import Path


def atomic_write_json(target, data) -> None:
    """Atomically write `data` (JSON-serializable) to the `target` path.

    Creates parent directories as needed (supports nested paths like work/versions/).
    Preserves non-ASCII (e.g. Korean) without escaping (.omp docs are often Korean).
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Initialize tmp to None: if mkstemp itself fails, tmp is never bound, so this
    # prevents an UnboundLocalError in the except block from masking the original
    # exception (disk full, permissions, etc.).
    tmp = None
    try:
        # The temp file must live in the same directory so os.replace is a
        # same-volume atomic rename.
        fd, tmp = tempfile.mkstemp(
            dir=str(target.parent), prefix=".omp-tmp-", suffix=".json"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)  # atomic — a partial-write state is never exposed
    except BaseException:
        # On failure, leave no temp file behind. Re-raise the original exception.
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise
