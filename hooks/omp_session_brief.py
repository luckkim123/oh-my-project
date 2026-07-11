"""omp SessionStart hook: inject BRIEF.md (pull-style briefing). Advisory-only —
never auto-resumes work (spec D2/§2.3). <=30 lines and <=2000 chars injected.
Fail-open; disable via OMP_SKIP_HOOKS=session_brief.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omp_secretary import find_omp_root  # noqa: E402

MAX_LINES, MAX_CHARS = 30, 2000


def _skipped(token):
    return token in {t.strip() for t in os.environ.get("OMP_SKIP_HOOKS", "").split(",") if t.strip()}


def main() -> int:
    try:
        if _skipped("session_brief"):
            return 0
        data = json.load(sys.stdin)
        root = find_omp_root(data.get("cwd") or Path.cwd())
        if root is None:
            return 0
        brief = root / ".omp" / "secretary" / "BRIEF.md"
        if not brief.is_file():
            return 0  # pull model: nothing prepared, stay silent (no nag)
        text = brief.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()[:MAX_LINES]
        body = "\n".join(lines)[:MAX_CHARS]
        ctx = ("[omp secretary brief — advisory only, do NOT auto-resume; "
               "user decides]\n" + body)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}))
    except Exception as e:  # noqa: BLE001 — fail-open is intentional
        sys.stderr.write("[omp_session_brief] swallowed: %r\n" % (e,))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
