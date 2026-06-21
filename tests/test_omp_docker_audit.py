"""Tests for deterministic Dockerfile/compose anti-pattern checks (omp-audit docker axis).

Pure stdlib, no file mutation. Mirrors hooks/omp_content_audit.py shape:
returns violation dicts; the auditor agent invokes these as the canonical algorithm.
Default severity is 'warn' — GUI/GPU/sim containers legitimately break non-root/distroless,
so the docker axis warns, it does not FAIL the build.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
import omp_docker_audit as da


def test_parse_handles_line_continuation():
    """A RUN spanning lines via backslash is one instruction."""
    df = "RUN apt-get update \\\n  && apt-get install -y curl\n"
    instrs = da.parse_dockerfile_instructions(df)
    assert len(instrs) == 1
    assert instrs[0][0] == "RUN"
    assert "curl" in instrs[0][1]


def test_parse_skips_comments_and_blanks():
    df = "# comment\nFROM python:3.12\n\n# another\nCMD [\"python\"]\n"
    instrs = da.parse_dockerfile_instructions(df)
    assert [i[0] for i in instrs] == ["FROM", "CMD"]


def test_dl3007_latest_tag_flagged():
    """DL3007: base image pinned, not :latest. Warn (not fail)."""
    v = da.check_dockerfile("FROM python:latest\n")
    ids = [x["rule_id"] for x in v]
    assert "DL3007" in ids
    assert all(x["severity"] == "warn" for x in v if x["rule_id"] == "DL3007")


def test_no_false_positive_on_pinned_base():
    """FROM with a real tag must NOT trigger DL3007 (parse, don't naive-grep 'latest')."""
    v = da.check_dockerfile("FROM python:3.12-slim\n# latest is just a comment word\n")
    assert "DL3007" not in [x["rule_id"] for x in v]


def test_secret_in_env_flagged():
    """A secret-looking ENV/ARG leaks via docker history."""
    v = da.check_dockerfile("FROM x:1\nENV AWS_SECRET_ACCESS_KEY=abc123\n")
    assert any("secret" in x["message"].lower() for x in v)


def test_compose_obsolete_version_key():
    """Compose top-level version: is obsolete (Compose Spec ignores it)."""
    v = da.check_compose("version: '3.8'\nservices:\n  app:\n    image: x:1\n")
    assert any(x["rule_id"] == "compose-version" for x in v)


def test_clean_dockerfile_no_violations():
    """A pinned, secret-free Dockerfile yields no warnings from these rules."""
    df = "FROM python:3.12-slim@sha256:" + "a" * 64 + "\nRUN pip install x\nCMD [\"python\"]\n"
    v = da.check_dockerfile(df)
    assert v == []
