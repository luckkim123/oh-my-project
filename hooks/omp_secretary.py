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

sys.path.insert(0, str(Path(__file__).parent))
from omp_paths import has_store  # noqa: E402
from omp_paths import rules_json as omp_rules_json  # noqa: E402
from omp_paths import secretary_dir  # noqa: E402

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
#: How long an axis must have been running before an untouched chronicler
#: surface counts as dormant rather than merely new. Every other stale check
#: fires on a record that EXISTS; this one fires on the absence of any.
STALE_DORMANT_DAYS = 14
#: The three surfaces only chronicler writes. When one is empty, every count
#: derived from it reads as a healthy zero.
CHRONICLER_SURFACES = ("raid.md", "todo.txt", "decisions/")
RAID_ENTRY_RE = re.compile(r"\[(?:open|closed)\]")
SOURCE_KINDS = ("todo", "journal", "status", "schedule")
OPEN_CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[ \](\s|$)")
FENCE_RE = re.compile(r"^\s*```")  # fence toggle so a checkbox example inside a code block isn't counted (D11 ceiling lifted).


def find_omp_root(start):
    try:
        cur = Path(start).resolve()
        home = Path.home().resolve()
        for cand in (cur, *cur.parents):
            if has_store(cand):
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
    """The anchor-gated secretary/ path. Stage 2 makes read and write the same
    computation (omp_paths._resolve), so every caller below — readers and the
    two writers (append_ledger, session_stub) — uses this one resolver."""
    return secretary_dir(root)


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


def _raid_entries(sec):
    """Entries raid.md holds, open or closed. Zero means nobody ever filed one —
    which `_open_blockers` reports identically to a raid that was filed and
    cleared, and the traffic light reads both as 'no blockers'."""
    p = Path(sec) / "raid.md"
    if not p.is_file():
        return 0
    return sum(1 for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()
               if RAID_ENTRY_RE.search(ln))


def surface_entries(sec, used=None):
    """Entry counts for the chronicler-owned judgment surfaces this project uses.

    `used` restricts the set (see `load_secretary_surfaces`); None means all
    three, which is what a project that has never declared otherwise gets."""
    sec = Path(sec)
    todo = sec / "todo.txt"
    dec = sec / "decisions"
    counts = {
        "raid.md": _raid_entries(sec),
        "todo.txt": sum(1 for ln in todo.read_text(encoding="utf-8", errors="replace").splitlines()
                        if parse_todo_line(ln)) if todo.is_file() else 0,
        "decisions/": sum(1 for _ in dec.glob("*.md")) if dec.is_dir() else 0,
    }
    if used is None:
        return counts
    return {k: v for k, v in counts.items() if k in used}


def load_secretary_surfaces(root):
    """`rules.json` secretary.surfaces[] — which chronicler surfaces this project
    actually uses. Absent means all three (a project that never declared is not a
    project that opted out). An explicit `[]` declares the chronicler axis unused,
    which silences the dormancy checks: a finding that can never be cleared stops
    being information and becomes noise, and the read-map half of the axis
    (`sources[]`) is independently useful without it. Fail-open to all three."""
    try:
        rules = json.loads(omp_rules_json(root).read_text(encoding="utf-8"))
        declared = rules.get("secretary", {}).get("surfaces")
        if not isinstance(declared, list):
            return set(CHRONICLER_SURFACES)
        return {s for s in declared if s in CHRONICLER_SURFACES}
    except Exception:
        return set(CHRONICLER_SURFACES)


def _axis_age_days(oldest_ts, now_ts):
    """Days since this axis started recording, from the ledger's oldest entry.
    None when the ledger is empty — a project with no session history yet is
    NEW, not dormant, and must never be flagged."""
    if oldest_ts is None:
        return None
    return int((now_ts - oldest_ts) // 86400)


def load_secretary_sources(root):
    """rules.json secretary.sources[] — the codify-gated read-map (D14).
    Fail-open: missing/corrupt rules.json or malformed entries -> skipped/[]."""
    try:
        rules = json.loads(omp_rules_json(root).read_text(encoding="utf-8"))
        out = []
        for s in rules.get("secretary", {}).get("sources", []):
            if isinstance(s, dict) and s.get("path") and s.get("kind") in SOURCE_KINDS:
                out.append(s)
        return out
    except Exception:
        return []


def _count_open_in_file(p):
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    if p.suffix == ".txt":
        tasks = [t for t in map(parse_todo_line, lines) if t]
        return sum(1 for t in tasks if not t["done"])
    count = 0
    in_fence = False
    for ln in lines:
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            continue
        if not in_fence and OPEN_CHECKBOX_RE.match(ln):
            count += 1
    return count


def count_source_open(root, source):
    """Open-item count for one registered source. Only kinds todo|schedule count
    (journal|status are read-map pointers -> 0). A file: *.txt parses as todo.txt
    lines, anything else counts open markdown checkboxes. A directory: non-recursive
    sum of the same per-file count across sorted(*.md) (design Part II §14.1 — e.g.
    a daily-notes dir). Fail-open -> 0."""
    if source.get("kind") not in ("todo", "schedule"):
        return 0
    try:
        p = Path(root) / source["path"]
        if p.is_file():
            return _count_open_in_file(p)
        if p.is_dir():
            return sum(_count_open_in_file(f) for f in sorted(p.glob("*.md")) if f.is_file())
        return 0
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
    raid_entries = 0
    oldest_ts = None
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
        raid_entries += _raid_entries(sec)
        for e in _iter_ledger(sec):
            try:
                ts = datetime.fromisoformat(e["ts"]).timestamp()
            except Exception:
                ts = None
            if ts is not None:
                if e.get("event") == "task_done" and ts >= week_ago:
                    done_7d += 1
                if oldest_ts is None or ts < oldest_ts:
                    oldest_ts = ts
            if e.get("stage"):
                last_stage = e["stage"]
    tracks_raid = "raid.md" in load_secretary_surfaces(root)
    if blockers > 0:
        light, reason = "red", "%d open blocker(s)" % blockers
    elif open_tasks > 10:
        light, reason = "yellow", "%d open tasks (ceiling 10)" % open_tasks
    elif tracks_raid:
        light, reason = "green", "%d open tasks, no blockers" % open_tasks
    else:
        # This project declared it does not keep raid.md, so it has no basis for
        # the "no blockers" half of the green reason. Report only what is counted.
        light, reason = "green", "%d open tasks" % open_tasks
    # RED is reachable only through the blocker count, so a raid nobody has ever
    # filed makes RED unreachable AND makes the reason line assert "no blockers"
    # about a surface that holds no evidence either way. Say which zero it is.
    axis_age = _axis_age_days(oldest_ts, datetime.now().timestamp())
    raid_dormant = (raid_entries == 0 and axis_age is not None
                    and axis_age > STALE_DORMANT_DAYS and tracks_raid)
    if raid_dormant:
        reason += "; raid.md never filed in %dd — 0 blockers is absence, not evidence" % axis_age
    return {"light": light, "reason": reason, "open_tasks": open_tasks,
            "open_blockers": blockers, "done_7d": done_7d, "last_stage": last_stage,
            "raid_dormant": raid_dormant, "sources": registered}


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
    # The four checks above all need a record to exist before they can fire, so a
    # surface nobody ever wrote to is the one state the review agenda cannot see.
    # The ledger keeps growing regardless (the hook writes it), which is what
    # makes a dormant axis look like a healthy one.
    oldest_ts = None
    for e in _iter_ledger(sec):
        try:
            ts = datetime.fromisoformat(e["ts"]).timestamp()
        except Exception:
            continue
        if oldest_ts is None or ts < oldest_ts:
            oldest_ts = ts
    age = _axis_age_days(oldest_ts, now.timestamp())
    if age is not None and age > STALE_DORMANT_DAYS:
        for name, n in surface_entries(sec, load_secretary_surfaces(root)).items():
            if n == 0:
                finds.append({"kind": "axis_dormant", "path": name,
                              "detail": "no entry in %dd of recorded session history — "
                                        "every other stale check needs a record to exist" % age})
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
