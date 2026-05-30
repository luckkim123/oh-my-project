"""Tests for the atomic JSON write helper (T20).

omp 의 .omp/ SSOT 파일(rules.json·manifest.json·versions/ 스냅샷)은 쓰기 중
크래시 시 단일 진실원이 손상되면 하네스 전체가 죽는다. atomic write 가 그 무결성
보험이다. stdlib only, cross-platform (os.replace 는 POSIX·Windows 동일 볼륨
atomic rename 보장, py3.3+)."""
import json
from pathlib import Path

from hooks.omp_atomic import atomic_write_json


def test_atomic_write_replaces_intact(tmp_path):
    """기본: dict 를 JSON 으로 쓰고 그대로 다시 읽힌다."""
    target = tmp_path / "rules.json"
    atomic_write_json(target, {"v": 1})
    assert json.loads(target.read_text(encoding="utf-8"))["v"] == 1


def test_atomic_write_no_partial_leftover(tmp_path):
    """덮어쓰기 후 임시파일 잔재가 없고 target 만 최종값을 갖는다."""
    target = tmp_path / "rules.json"
    atomic_write_json(target, {"v": 1})
    atomic_write_json(target, {"v": 2})
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "rules.json"]
    assert leftovers == [], f"임시파일 잔재: {leftovers}"
    assert json.loads(target.read_text(encoding="utf-8"))["v"] == 2


def test_atomic_write_creates_parent_dirs(tmp_path):
    """work/versions/ 처럼 없는 상위 디렉토리도 만들어 쓴다."""
    target = tmp_path / "work" / "versions" / "rules-v01-2026-05-30.json"
    atomic_write_json(target, {"snap": True})
    assert target.is_file()
    assert json.loads(target.read_text(encoding="utf-8"))["snap"] is True


def test_atomic_write_preserves_unicode(tmp_path):
    """ensure_ascii=False — 한글·비ASCII 가 이스케이프 없이 보존된다(.omp 는 한국어 다수)."""
    target = tmp_path / "rules.json"
    atomic_write_json(target, {"역할": "구조 규칙"})
    raw = target.read_text(encoding="utf-8")
    assert "역할" in raw and "\\u" not in raw


def test_atomic_write_accepts_str_path(tmp_path):
    """Path 와 str 경로 모두 받는다."""
    target = str(tmp_path / "manifest.json")
    atomic_write_json(target, {"ok": 1})
    assert Path(target).is_file()


def test_atomic_write_stdlib_only():
    """T19 경량 제약: 헬퍼가 third-party import 없이 stdlib 만 쓴다."""
    src = (Path(__file__).parent.parent / "hooks" / "omp_atomic.py").read_text()
    assert "import requests" not in src and "import yaml" not in src
    assert "os.replace" in src  # atomic rename 의 핵심 — 회귀 방지
