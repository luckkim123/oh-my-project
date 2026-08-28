"""omp PostToolUse hook: inject an integrity reminder after risky operations.

Stdlib only (a test enforces this). Fires on Edit/Write/MultiEdit/Bash. Reminds
(does NOT auto-fix, does NOT freeze) when:
  - a file under .omp/ was edited (rules/manifest may need re-validation), or
  - a move/delete command ran (organize safety: verify residue == 0 before delete)

Critically does NOT use the phrase "fix before continuing" (that wording is known
to freeze the model — see OMC post-tool-verifier freeze pattern). Reminder tone
only; the session decides whether to act. Fail-open: any error returns 0.

Content-hash advisory throttle (§2.6): organizer batch mv can re-trigger the same
reason repeatedly; a sha256(reason) key in `.omp/state/verify-throttle.json` records
the last-emitted timestamp and suppresses re-emission within COOLDOWN_S. State IO
failure re-emits (fail-open must not silence a safety signal) — only a successful
"already emitted recently" read suppresses. Disable via OMP_SKIP_HOOKS=verify.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omp_atomic import atomic_write_json  # noqa: E402
from omp_paths import is_inside_store, verify_throttle_json  # noqa: E402
from omp_paths import verify_throttle_json_write  # noqa: E402
from omp_paths import rules_json as omp_rules_json  # noqa: E402
from omp_secretary import find_omp_root  # noqa: E402

COOLDOWN_S = 300

# Bash command substrings that imply a move/delete (organize safety relevant).
# Only checked at a command boundary (start of command, or right after && ; |) —
# a bare substring test would false-positive on commands that merely MENTION a
# risky verb, e.g. `grep -c "mv the file" notes.md` or `echo "do not rm this"`.
RISKY_CMD_MARKERS = ("mv ", "rm ", "trash ", "gio trash", "rmdir ", "Remove-Item")
# Commands whose whole job is to inspect/print text — never treat their
# arguments as an invocation of the risky verb they happen to quote.
SAFE_INVOKED_CMDS = ("grep", "rg", "sed", "awk", "echo")
_CMD_SPLIT_RE = re.compile(r"&&|\|\||;|\||\n")
WRITE_TOOLS = ("Edit", "Write", "MultiEdit")


def _invoked_cmd(segment: str) -> str:
    """First whitespace token of a command segment, basename only (strip a path)."""
    first = segment.split(None, 1)[0] if segment.split(None, 1) else ""
    return first.rsplit("/", 1)[-1]


def _extract_command_substitutions(cmd: str) -> list:
    """Inner text of every $(...) (balanced-paren, handles nesting) and
    `...` command substitution, so a risky verb hidden inside a subshell
    is still reachable by the boundary check instead of only the outer line."""
    found = []
    i = 0
    while True:
        start = cmd.find("$(", i)
        if start == -1:
            break
        depth = 1
        j = start + 2
        while j < len(cmd) and depth > 0:
            if cmd[j] == "(":
                depth += 1
            elif cmd[j] == ")":
                depth -= 1
            j += 1
        inner = cmd[start + 2:j - 1]
        found.append(inner)
        found.extend(_extract_command_substitutions(inner))  # nested $(...)
        i = j
    found.extend(re.findall(r"`([^`]*)`", cmd))
    return found


def _is_risky_segment(segment: str) -> bool:
    seg = segment.lstrip()
    if not seg or _invoked_cmd(seg) in SAFE_INVOKED_CMDS:
        return False
    return any(seg.startswith(marker) for marker in RISKY_CMD_MARKERS)


def build_reminder(reason: str) -> str:
    return (
        f"[omp integrity reminder] {reason}\n"
        "- 규칙 준수가 깨지지 않았는지 omp-audit로 확인할 것(read-only PASS/FAIL).\n"
        "- ⚠️ 파일 이동/삭제는 mv→find 잔류0 검증→삭제 순서, trash 경유. "
        "rm 직접·iCloud 폴더 rename은 지양(원본 복원 충돌).\n"
        "- ⚠️ 구조를 바꾼 이동·리네임이었다면(폴더 이름·계층·존재 변경) "
        ".omp/STRUCTURE.md·rules.json(+경로 적힌 경우 DATASETS.md) 갱신은 "
        "이 작업의 일부 — 옛 경로가 인덱스에 남지 않게 다음 작업으로 넘어가기 전에 동기화한다.\n"
        "- .omp/rules.json·manifest.json을 손댔으면 스키마 정합을 확인."
    )


def _skipped(token):
    return token in {t.strip() for t in os.environ.get("OMP_SKIP_HOOKS", "").split(",") if t.strip()}


def _throttle_path(root):
    return verify_throttle_json(root)


def _throttle_path_write(root):
    return verify_throttle_json_write(root)


def should_throttle(root, reason: str, now: float = None) -> bool:
    """True if `reason` was already emitted within COOLDOWN_S. Any IO/parse
    failure returns False (re-emit — a safety signal must not go silent)."""
    if root is None:
        return False
    now = time.time() if now is None else now
    try:
        state = json.loads(_throttle_path(root).read_text(encoding="utf-8"))
        last = state.get(hashlib.sha256(reason.encode("utf-8")).hexdigest())
        return isinstance(last, (int, float)) and (now - last) < COOLDOWN_S
    except Exception:
        return False


def record_emit(root, reason: str, now: float = None) -> None:
    """Best-effort — a write failure must not block the reminder that was
    just emitted, so this is called after printing and swallows its own errors."""
    if root is None:
        return
    now = time.time() if now is None else now
    key = hashlib.sha256(reason.encode("utf-8")).hexdigest()
    # read where the state IS, write where it must GO — the two differ only in
    # the window between an anchor being seeded and this file being copied, and
    # reading the old one there is what carries the cooldown across the move.
    try:
        state = json.loads(_throttle_path(root).read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            state = {}
    except Exception:
        state = {}
    state[key] = now
    try:
        atomic_write_json(_throttle_path_write(root), state)
    except Exception:
        pass  # best-effort state; never let this fail the hook


def _category_drop(fp: str, root, rules: dict) -> str:
    """A file written straight into the TOP LEVEL of an enforced category dir.

    The only placement signal available without a placement schema, and it is the
    shape the motivating incident had: a one-off session prompt dropped into
    `1_Area/` because nothing objected. Deeper paths are excluded on purpose --
    `0_Project/in_progress/albc/notes/x.md` sits inside a structure somebody
    already chose, while a file at a category's own top level is the drawer that
    offers no resistance. `README.md` is exempt: a category index lives there.

    Measured on one vault before shipping (3,292 tracked files): 6 files sit at an
    enforced dir's top level and 4 are the category README -- so the rule fires on
    exactly the 2 known-bad files and nothing else. A guard that calls current
    practice a violation gets switched off, so that rate IS the gate.
    """
    if root is None or not isinstance(rules, dict):
        return ""
    norm = str(fp).replace("\\", "/")
    try:
        rel = str(Path(norm).resolve().relative_to(Path(root).resolve())).replace("\\", "/")
    except Exception:
        return ""  # outside the project (or unresolvable) -- not ours to judge
    if rel.rsplit("/", 1)[-1] == "README.md":
        return ""
    for d in rules.get("structure", {}).get("directories", []):
        if not d.get("enforced"):
            continue
        path = str(d.get("path", "")).strip("/")
        # `.` (or an empty path) names the project root. It needs its own branch:
        # the prefix test below looks for `path + "/"`, and `relative_to()` never
        # emits a leading `./`, so a root entry silently matched nothing and the
        # rule read as enforced while doing nothing at all.
        if path in ("", "."):
            if "/" in rel:
                continue  # deeper than the root's own top level
        elif not rel.startswith(path + "/") or "/" in rel[len(path) + 1:]:
            continue  # wrong category, or deeper than its own top level
        return "enforced 폴더 최상단에 파일이 생성됨 — %s (role: %s)" % (
            rel, str(d.get("role", ""))[:110])
    return ""


def load_rules(root) -> dict:
    """rules.json as a dict, or {} on any failure (advisory axis, never blocks)."""
    if root is None:
        return {}
    try:
        data = json.loads(omp_rules_json(root).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def detect(tool_name: str, tool_input: dict, root=None, rules: dict = None) -> str:
    """Return a reminder reason string, or '' if nothing relevant happened.

    `root`/`rules` are optional so existing two-arg callers keep working; without
    them the placement signal stays silent rather than guessing.
    """
    if tool_name in WRITE_TOOLS:
        fp = str(tool_input.get("file_path", ""))
        if is_inside_store(fp):
            return ".omp/ SSOT 파일이 수정됨."
        # Placement is a creation-time question, so only Write (which lands a whole
        # file) is asked it -- an Edit/MultiEdit changes a file already placed.
        if tool_name == "Write":
            return _category_drop(fp, root, rules)
        return ""
    if tool_name == "Bash":
        cmd = str(tool_input.get("command", ""))
        segments = _CMD_SPLIT_RE.split(cmd)
        for sub in _extract_command_substitutions(cmd):
            segments.extend(_CMD_SPLIT_RE.split(sub))
        if any(_is_risky_segment(seg) for seg in segments):
            return "파일 이동/삭제 명령이 실행됨."
        return ""
    return ""


def main() -> int:
    try:
        if _skipped("verify"):
            return 0
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {}) or {}
        # root before detect: the placement signal needs it to make a path relative.
        # find_omp_root is cheap (an upward walk) and detect stays silent without it.
        root = find_omp_root(data.get("cwd") or Path.cwd())
        reason = detect(tool_name, tool_input, root, load_rules(root))
        if not reason:
            return 0  # nothing relevant — stay silent
        if should_throttle(root, reason):
            return 0  # same reason emitted within COOLDOWN_S — stay silent
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": build_reminder(reason),
            }
        }
        print(json.dumps(out))
        record_emit(root, reason)
    except Exception as e:  # noqa: BLE001 — fail-open is intentional
        # 에러 맥락을 stderr 로 1줄 남기되(디버그용), stdout 계약·exit code 는
        # 건드리지 않는다 → fail-open 유지(세션 안 막음). T23.
        sys.stderr.write("[omp_verify_emit] swallowed: %r\n" % (e,))
        return 0  # fail-open — never block the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
