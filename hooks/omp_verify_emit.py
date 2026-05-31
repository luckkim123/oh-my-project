"""omp PostToolUse hook: inject an integrity reminder after risky operations.

Stdlib only (a test enforces this). Fires on Edit/Write/MultiEdit/Bash. Reminds
(does NOT auto-fix, does NOT freeze) when:
  - a file under .omp/ was edited (rules/manifest may need re-validation), or
  - a move/delete command ran (organize safety: verify residue == 0 before delete)

Critically does NOT use the phrase "fix before continuing" (that wording is known
to freeze the model — see OMC post-tool-verifier freeze pattern). Reminder tone
only; the session decides whether to act. Fail-open: any error returns 0.
"""
import json
import sys

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
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {}) or {}
        reason = detect(tool_name, tool_input)
        if not reason:
            return 0  # nothing relevant — stay silent
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": build_reminder(reason),
            }
        }
        print(json.dumps(out))
    except Exception as e:  # noqa: BLE001 — fail-open is intentional
        # 에러 맥락을 stderr 로 1줄 남기되(디버그용), stdout 계약·exit code 는
        # 건드리지 않는다 → fail-open 유지(세션 안 막음). T23.
        sys.stderr.write("[omp_verify_emit] swallowed: %r\n" % (e,))
        return 0  # fail-open — never block the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
