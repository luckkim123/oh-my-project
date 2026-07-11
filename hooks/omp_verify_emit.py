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
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omp_atomic import atomic_write_json  # noqa: E402
from omp_secretary import find_omp_root  # noqa: E402

COOLDOWN_S = 300

# Bash command substrings that imply a move/delete (organize safety relevant).
RISKY_CMD_MARKERS = ("mv ", "rm ", "trash ", "gio trash", "rmdir ", "Remove-Item")
WRITE_TOOLS = ("Edit", "Write", "MultiEdit")


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
    return Path(root) / ".omp" / "state" / "verify-throttle.json"


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
    path = _throttle_path(root)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            state = {}
    except Exception:
        state = {}
    state[key] = now
    try:
        atomic_write_json(path, state)
    except Exception:
        pass  # best-effort state; never let this fail the hook


def detect(tool_name: str, tool_input: dict) -> str:
    """Return a reminder reason string, or '' if nothing relevant happened."""
    if tool_name in WRITE_TOOLS:
        fp = str(tool_input.get("file_path", ""))
        # normalize separators so Windows backslashes also match
        if "/.omp/" in fp.replace("\\", "/") or fp.replace("\\", "/").endswith("/.omp"):
            return ".omp/ SSOT 파일이 수정됨."
        return ""
    if tool_name == "Bash":
        cmd = str(tool_input.get("command", ""))
        if any(marker in cmd for marker in RISKY_CMD_MARKERS):
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
        reason = detect(tool_name, tool_input)
        if not reason:
            return 0  # nothing relevant — stay silent
        root = find_omp_root(data.get("cwd") or Path.cwd())
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
