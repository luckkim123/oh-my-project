"""omp SessionEnd hook: append a mechanical journal stub + ledger session_end.

Once per session, bounded, NO LLM, NO cleanup/state management (this is what
distinguishes it from the backport-rejected "session/compaction state" row —
see docs/design/2026-07-11-omp-secretary-upgrade-plan.md §2.3 and
references/omc-backport-analysis.md amendment).
Fail-open; disable via OMP_SKIP_HOOKS=session_capture.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omp_secretary import find_omp_root, session_stub  # noqa: E402


def _skipped(token):
    return token in {t.strip() for t in os.environ.get("OMP_SKIP_HOOKS", "").split(",") if t.strip()}


def main() -> int:
    try:
        if _skipped("session_capture"):
            return 0
        data = json.load(sys.stdin)
        root = find_omp_root(data.get("cwd") or Path.cwd())
        if root is None:
            return 0  # not an omp project — secretary axis does not apply
        session_stub(root, str(data.get("session_id", "")), changed=[], last_stage=None)
        # ponytail: changed-files list needs session-start state we don't keep;
        # omp-log records real narratives — the stub is only "a session ended here".
    except Exception as e:  # noqa: BLE001 — fail-open is intentional
        sys.stderr.write("[omp_session_capture] swallowed: %r\n" % (e,))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
