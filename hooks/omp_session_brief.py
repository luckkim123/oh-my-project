"""omp SessionStart hook: inject BRIEF.md (pull-style briefing) and report the
store gate. Advisory-only — never auto-resumes work (spec D2/section 2.3).
<=30 lines and <=2000 chars injected. Fail-open; disable via
OMP_SKIP_HOOKS=session_brief.

P3 added the four-state gate (store-spec.md section 6). This hook is omp's
SessionStart surface, so it is where a project announces which store it is on:

  off      not an omp project              silent, exit 0
  legacy   legacy store, no anchor         one warn line prepended to the brief
  normal   anchor present and parseable    brief only, as before
  corrupt  anchor present, unparseable     stderr + exit 2

Row 2 is the reason the gate is a pair and not a single marker. "Legacy store
present, not yet migrated" is the most dangerous state of the whole migration,
and a three-state design sends it into the quiet `off` branch where a hook that
silently stopped looks exactly like one that correctly had no work.

Row 4 is the one place omp's blanket fail-open does not apply. A corrupt anchor
is not an absent one, and reading it as absent is how a migration loses a store
quietly. SessionStart cannot block a session, so exit 2 here is as loud as this
surface gets — which is the intent (section 6: "never silent", not "always
effective").
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omp_paths import GATE_CORRUPT, GATE_LEGACY, brief_md, gate_state  # noqa: E402
from omp_secretary import find_omp_root  # noqa: E402

LEGACY_WARN = (
    "[omp store] 이 프로젝트는 아직 통합 스토어로 이주하지 않았다 — 구 스토어는 "
    "있는데 `.hq/.anchor` 가 없다. 지금은 읽기 fallback 으로 정상 동작하지만, "
    "이 상태는 '기능 꺼짐'이 아니라 '이주 미완'이다 (store-spec.md section 6 row 2)."
)

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
        state = gate_state(root)
        if state == GATE_CORRUPT:
            # not swallowed, deliberately — see the module docstring
            sys.stderr.write(
                "[omp store] CORRUPT: %s/.hq/.anchor exists but does not parse. "
                "A corrupt store is not an absent one; fix or remove the anchor "
                "before writing any harness state here.\n" % root)
            return 2
        prefix = LEGACY_WARN + "\n\n" if state == GATE_LEGACY else ""
        brief = brief_md(root)
        if not brief.is_file():
            if not prefix:
                return 0  # pull model: nothing prepared, stay silent (no nag)
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": LEGACY_WARN}}))
            return 0
        text = brief.read_text(encoding="utf-8", errors="replace")
        # the gate warn counts against the same budget — MAX_LINES is a promise
        # about the whole injection, not about the brief body alone
        budget = MAX_LINES - len(prefix.splitlines())
        lines = text.splitlines()[:budget]
        body = "\n".join(lines)[:MAX_CHARS]
        ctx = (prefix + "[omp secretary brief — advisory only, do NOT auto-resume; "
               "user decides]\n" + body)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}))
    except Exception as e:  # noqa: BLE001 — fail-open is intentional
        sys.stderr.write("[omp_session_brief] swallowed: %r\n" % (e,))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
