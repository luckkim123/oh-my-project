"""om-core shared atomic-write primitive (function form) — vendored verbatim into
consumer repos; edit only in om-core.

Provides a crash-safe write to a target file: write to a same-dir temp file,
fsync, then atomically `os.replace` onto the target. On any failure the temp
file is cleaned up and the original exception re-raised — the target is never
left partially written.

os.replace() guarantees an atomic same-volume rename on both POSIX and Windows
(Python 3.3+) — a partial-write state is never exposed at the target. No
third-party dependency.
"""
import json
import os
import tempfile
from pathlib import Path


def _atomic_write(target, write_fn) -> None:
    """Shared core: write to a same-dir temp file via `write_fn(fileobj)`, fsync,
    then atomically replace `target`. Cleans up the temp file on any failure.

    Creates parent directories as needed (supports nested paths like .oms/<slug>/).
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Initialize tmp to None: if mkstemp itself fails, tmp is never bound, so this
    # prevents an UnboundLocalError in the except block from masking the original
    # exception (disk full, permissions, etc.).
    tmp = None
    try:
        # The temp file must live in the same directory so os.replace is a
        # same-volume atomic rename. suffix mirrors the target's own extension
        # (".json" for json targets, ".yaml" for yaml, etc.) — unchanged behavior
        # for existing .json callers, generalized for any target.
        fd, tmp = tempfile.mkstemp(
            dir=str(target.parent), prefix=".om-tmp-", suffix=target.suffix
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            write_fn(f)
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


def atomic_write_json(target, data) -> None:
    """Atomically write `data` (JSON-serializable) to the `target` path.

    Creates parent directories as needed (supports nested paths like .oms/<slug>/).
    Preserves non-ASCII (e.g. Korean) without escaping (.oms notes are often Korean).
    """
    _atomic_write(target, lambda f: json.dump(data, f, ensure_ascii=False, indent=2))


def atomic_write_text(target, text: str) -> None:
    """Atomically write `text` (already-composed text, e.g. YAML) to `target`.

    Same guarantees as `atomic_write_json`: parent mkdir, same-dir mkstemp, fsync,
    os.replace, temp cleanup on failure, UTF-8, non-ASCII (Korean) preserved as-is.
    """
    _atomic_write(target, lambda f: f.write(text))
