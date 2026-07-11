"""Secretary-axis pure functions (spec §4.4). stdlib only, fail-open callers.

Contracts live in references/secretary-protocol.md — grammar and parser side by side.
Writer ownership (D7): hooks own mechanical appends (ledger, journal stubs);
the chronicler agent owns narrative content. Lines are disjoint; never truncate.
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,255}$")
TAG_RE = re.compile(r"\[(BLOCKER|LESSON|DECISION):([A-Za-z0-9_-]+)\]")
MANAGED_RE = re.compile(r"<!--\s*omp-managed:\s*sha256:([a-f0-9]{64})\s*-->")
_SECRET_PATTERNS = (
    ("bearer", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9-]{8,}")),
    ("openai", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
    ("github", re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("aws", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{4,}")),
)
TODO_DONE_RE = re.compile(r"^x\s+(\d{4}-\d{2}-\d{2})(?:\s+(\d{4}-\d{2}-\d{2}))?\s+(.*)$")
TODO_OPEN_RE = re.compile(r"^(?:\((?P<pri>[A-Z])\)\s+)?(?:(?P<created>\d{4}-\d{2}-\d{2})\s+)?(?P<text>.+)$")
STALE_TASK_DAYS, STALE_BLOCKER_DAYS = 30, 14
SOURCE_KINDS = ("todo", "journal", "status", "schedule")
OPEN_CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[ \](\s|$)")


def find_omp_root(start):
    try:
        cur = Path(start).resolve()
        home = Path.home().resolve()
        for cand in (cur, *cur.parents):
            if (cand / ".omp").is_dir():
                return cand
            if cand == home:
                break
        return None
    except Exception:
        return None


def sanitize_session_id(sid):
    return sid if isinstance(sid, str) and SESSION_ID_RE.match(sid) else None


def redact_secrets(text):
    for kind, pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED:%s]" % kind, text)
    return text


def parse_todo_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    done_m = TODO_DONE_RE.match(line)
    if done_m:
        completed, created, rest = done_m.group(1), done_m.group(2), done_m.group(3)
        base = {"done": True, "priority": None, "completed": completed, "created": created}
    else:
        m = TODO_OPEN_RE.match(line)
        base = {"done": False, "priority": m.group("pri"), "completed": None,
                "created": m.group("created")}
        rest = m.group("text")
    words = rest.split()
    kv = dict(w.split(":", 1) for w in words if ":" in w and " " not in w and not w.startswith(("http:", "https:")))
    return {**base,
            "text": rest,
            "projects": [w[1:] for w in words if w.startswith("+")],
            "contexts": [w[1:] for w in words if w.startswith("@")],
            "kv": kv}


def _sec(root):
    return Path(root) / ".omp" / "secretary"


def append_ledger(root, event):
    """O_APPEND single complete JSON line (+newline). NOT via omp_atomic —
    atomic_write_json is whole-file replace, reserved for todo/done rewrites."""
    sec = _sec(root)
    sec.mkdir(parents=True, exist_ok=True)
    event = dict(event)
    event.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    line = redact_secrets(json.dumps(event, ensure_ascii=False)) + "\n"
    fd = os.open(str(sec / "ledger.jsonl"), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def _iter_ledger(sec):
    p = Path(sec) / "ledger.jsonl"
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip():
            continue
        try:
            yield json.loads(raw)
        except Exception:
            sys.stderr.write("[omp_secretary] skip corrupt ledger line\n")


def _open_blockers(sec):
    p = Path(sec) / "raid.md"
    if not p.is_file():
        return 0
    return sum(1 for ln in p.read_text(encoding="utf-8").splitlines() if "[open]" in ln)


def load_secretary_sources(root):
    """rules.json secretary.sources[] — the codify-gated read-map (D14).
    Fail-open: missing/corrupt rules.json or malformed entries -> skipped/[]."""
    try:
        rules = json.loads((Path(root) / ".omp" / "rules.json").read_text(encoding="utf-8"))
        out = []
        for s in rules.get("secretary", {}).get("sources", []):
            if isinstance(s, dict) and s.get("path") and s.get("kind") in SOURCE_KINDS:
                out.append(s)
        return out
    except Exception:
        return []


def count_source_open(root, source):
    """Open-item count for one registered source. Only kinds todo|schedule count
    (journal|status are read-map pointers -> 0). *.txt parses as todo.txt lines;
    anything else counts open markdown checkboxes. Fail-open -> 0."""
    if source.get("kind") not in ("todo", "schedule"):
        return 0
    try:
        p = Path(root) / source["path"]
        if not p.is_file():
            return 0
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if p.suffix == ".txt":
            tasks = [t for t in map(parse_todo_line, lines) if t]
            return sum(1 for t in tasks if not t["done"])
        return sum(1 for ln in lines if OPEN_CHECKBOX_RE.match(ln))
    except Exception:
        return 0


def derive_status(root, sources=None):
    """D8: the ONLY place progress indicators are computed. Counts, never prose.

    sources: optional list of secretary-shaped dirs (Part I) or secretary.sources[]
    dicts (Release 2, plan §13-R1) to aggregate. Default is [.omp/secretary/] plus
    whatever load_secretary_sources(root) finds in rules.json — with no secretary
    block this is byte-identical to Part I behavior (plus an empty "sources": []).
    """
    if sources is None:
        sources = [_sec(root)] + load_secretary_sources(root)
    open_tasks = 0
    blockers = 0
    done_7d = 0
    last_stage = None
    registered = []
    week_ago = datetime.now().timestamp() - 7 * 86400
    for sec in sources:
        if isinstance(sec, dict):  # a secretary.sources[] entry (Release 2)
            n = count_source_open(root, sec)
            open_tasks += n
            registered.append({"path": sec.get("path"), "kind": sec.get("kind"),
                               "open": n if sec.get("kind") in ("todo", "schedule") else None})
            continue
        sec = Path(sec)
        todo = sec / "todo.txt"
        if todo.is_file():
            tasks = [t for t in map(parse_todo_line, todo.read_text(encoding="utf-8").splitlines()) if t]
            open_tasks += sum(1 for t in tasks if not t["done"])
        blockers += _open_blockers(sec)
        for e in _iter_ledger(sec):
            if e.get("event") == "task_done":
                try:
                    if datetime.fromisoformat(e["ts"]).timestamp() >= week_ago:
                        done_7d += 1
                except Exception:
                    pass
            if e.get("stage"):
                last_stage = e["stage"]
    if blockers > 0:
        light, reason = "red", "%d open blocker(s)" % blockers
    elif open_tasks > 10:
        light, reason = "yellow", "%d open tasks (ceiling 10)" % open_tasks
    else:
        light, reason = "green", "%d open tasks, no blockers" % open_tasks
    return {"light": light, "reason": reason, "open_tasks": open_tasks,
            "open_blockers": blockers, "done_7d": done_7d, "last_stage": last_stage,
            "sources": registered}


def brief_hash_check(path):
    path = Path(path)
    if not path.is_file():
        return "missing"
    text = path.read_text(encoding="utf-8")
    m = MANAGED_RE.search(text)
    if not m:
        return "dirty"
    body = MANAGED_RE.sub("", text, count=1).lstrip("\n")
    return "clean" if hashlib.sha256(body.encode("utf-8")).hexdigest() == m.group(1) else "dirty"


def session_stub(root, session_id, changed, last_stage=None):
    sid = sanitize_session_id(session_id)
    if sid is None:
        return  # silent no-op — never write with an unsanitized id
    sec = _sec(root)
    (sec / "journal").mkdir(parents=True, exist_ok=True)
    day = datetime.now().strftime("%Y-%m-%d")
    stub = "- %s session `%s` ended%s%s\n" % (
        datetime.now().strftime("%H:%M"), sid,
        " at stage %s" % last_stage if last_stage else "",
        " · touched: %s" % ", ".join(changed[:8]) if changed else "")
    fd = os.open(str(sec / "journal" / (day + ".md")),
                 os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, redact_secrets(stub).encode("utf-8"))
    finally:
        os.close(fd)
    append_ledger(root, {"event": "session_end", "session": sid, "stage": last_stage})


def scan_stale(root, now):
    finds = []
    sec = _sec(root)
    todo = sec / "todo.txt"
    if todo.is_file():
        for t in filter(None, map(parse_todo_line, todo.read_text(encoding="utf-8").splitlines())):
            if not t["done"] and t["created"]:
                try:
                    age = (now - datetime.strptime(t["created"], "%Y-%m-%d")).days
                    if age > STALE_TASK_DAYS:
                        finds.append({"kind": "stale_task", "path": "todo.txt",
                                      "detail": "%s (%dd)" % (t["text"][:60], age)})
                except ValueError:
                    pass
    raid = sec / "raid.md"
    if raid.is_file():
        for ln in raid.read_text(encoding="utf-8").splitlines():
            m = re.search(r"\[open\].*\(opened:(\d{4}-\d{2}-\d{2})\)", ln)
            if m:
                age = (now - datetime.strptime(m.group(1), "%Y-%m-%d")).days
                if age > STALE_BLOCKER_DAYS:
                    finds.append({"kind": "stale_blocker", "path": "raid.md",
                                  "detail": "%s (%dd)" % (ln.strip()[:60], age)})
    brief = sec / "BRIEF.md"
    if brief.is_file() and brief_hash_check(brief) == "dirty":
        finds.append({"kind": "brief_drift", "path": "BRIEF.md",
                      "detail": "human-edited since last regeneration (managed-hash mismatch)"})
    if sec.is_dir():
        for p in sec.rglob("*"):
            if re.search(r" \d+\.[A-Za-z0-9]+$", p.name):  # "NAME 2.ext" sync conflict copy
                finds.append({"kind": "conflict_copy", "path": str(p.relative_to(sec)),
                              "detail": "possible iCloud/sync duplicate"})
    return finds


def scan_journal_tags(root):
    out = []
    jdir = _sec(root) / "journal"
    if not jdir.is_dir():
        return out
    for f in sorted(jdir.glob("*.md")):
        for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in TAG_RE.finditer(ln):
                out.append({"tag": m.group(1), "ref": m.group(2),
                            "file": f.name, "line": i})
    return out
