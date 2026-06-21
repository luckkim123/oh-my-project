"""Deterministic Dockerfile/compose anti-pattern checks for the omp-audit docker axis.

Pure stdlib (re). No file mutation. Returns violation dicts. The `auditor` agent
invokes these as the canonical check algorithm (mirrors hooks/omp_content_audit.py).

Severity is 'warn' by default: GUI/GPU/sim/ROS containers legitimately break
non-root/distroless/privileged rules, so the docker axis WARNS and never FAILs an
overall audit. A project may override severity per rule-id via rules.json.
Linter rule-ids (DL3007 hadolint, compose-version Compose Spec) are carried as DATA.
"""
from __future__ import annotations
import re
from typing import Optional

_CONT = re.compile(r"\\\s*$")
_INSTR = re.compile(r"^\s*([A-Za-z]+)\s+(.*)$")
# secret-looking env/arg keys (leak via docker history)
_SECRET_KEY = re.compile(r"(SECRET|PASSWORD|PASSWD|API[_-]?KEY|TOKEN|PRIVATE[_-]?KEY)", re.I)


def parse_dockerfile_instructions(text: str) -> list[tuple[str, str]]:
    """Return [(INSTRUCTION, args)] handling backslash line-continuations, comments, blanks."""
    out: list[tuple[str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        # join continuations
        buf = raw
        while _CONT.search(buf.rstrip()) and i + 1 < len(lines):
            buf = _CONT.sub("", buf.rstrip()) + " " + lines[i + 1]
            i += 1
        m = _INSTR.match(buf.strip())
        if m:
            out.append((m.group(1).upper(), m.group(2).strip()))
        i += 1
    return out


def check_dockerfile(text: str, rules: Optional[dict] = None) -> list[dict]:
    """Return anti-pattern violations. Default severity 'warn'. rules may override severity by rule_id."""
    rules = rules or {}
    overrides = rules.get("docker_severity_overrides", {})

    def sev(rule_id: str) -> str:
        return overrides.get(rule_id, "warn")

    violations: list[dict] = []
    instrs = parse_dockerfile_instructions(text)
    for idx, (instr, args) in enumerate(instrs):
        if instr == "FROM":
            # DL3007: base pinned, not :latest and not untagged (digest is fine)
            ref = args.split()[0] if args else ""
            if "@sha256:" not in ref:
                # Isolate the final path component (image name + optional tag).
                # A colon BEFORE the last "/" is a registry port, not a tag separator.
                # e.g. "registry.example.com:5000/myimage" → final_component="myimage" (no tag)
                #      "registry.example.com:5000/myimage:1.2.3" → final_component="myimage:1.2.3"
                final_component = ref.rsplit("/", 1)[-1]  # "" if ref is empty
                tag = final_component.split(":")[-1] if ":" in final_component else ""
                if tag == "latest" or ":" not in final_component:
                    violations.append({"rule_id": "DL3007", "severity": sev("DL3007"),
                                       "line": idx,  # line = instruction index, not source line number
                                       "message": f"base image not pinned ({ref or 'untagged'}); avoid :latest"})
        if instr in ("ENV", "ARG"):
            if _SECRET_KEY.search(args):
                violations.append({"rule_id": "secret-in-env", "severity": sev("secret-in-env"),
                                   "line": idx, "message": f"secret material in {instr} leaks via docker history; use BuildKit --mount=type=secret"})
    return violations


_COMPOSE_VERSION = re.compile(r"^\s*version\s*:", re.M)


def check_compose(text: str) -> list[dict]:
    """Return compose anti-pattern violations (warn-default)."""
    violations: list[dict] = []
    if _COMPOSE_VERSION.search(text):
        violations.append({"rule_id": "compose-version", "severity": "warn",
                           "line": 0, "message": "top-level 'version:' key is obsolete (Compose Spec ignores it); remove it"})
    return violations
