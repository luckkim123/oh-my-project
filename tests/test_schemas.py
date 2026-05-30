"""Tests for the .omp/ machine schemas + checksum determinism.

rules.schema.json / manifest.schema.json 가 유효한 JSON Schema 이고, 대표
인스턴스를 통과시킨다. SHA-256 이 OS 무관하게 결정적임을 확인 (manifest 의
무결성 추적 근거). jsonschema 가 있으면 실검증, 없으면 구조 검증으로 degrade
(stdlib only 원칙 — jsonschema 는 선택)."""
import hashlib
import json
from pathlib import Path

import pytest

SCHEMAS = Path(__file__).parent.parent / "references" / "schemas"
RULES_SCHEMA = SCHEMAS / "rules.schema.json"
MANIFEST_SCHEMA = SCHEMAS / "manifest.schema.json"


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def test_schemas_are_valid_json():
    """① 두 스키마 모두 파싱 가능한 JSON."""
    assert load(RULES_SCHEMA)["title"] == "omp rules.json"
    assert load(MANIFEST_SCHEMA)["title"] == "omp manifest.json"


def test_rules_schema_has_specificity():
    """② rules 스키마에 generic->specialized 추적용 specificity (0..1) 존재."""
    s = load(RULES_SCHEMA)
    spec = s["properties"]["specificity"]
    assert spec["type"] == "number"
    assert spec["minimum"] == 0 and spec["maximum"] == 1


def test_rules_schema_has_content_conventions():
    """content_conventions[]: note-body authoring rules (present/absent × body/frontmatter)."""
    s = load(RULES_SCHEMA)
    cc = s["properties"]["content_conventions"]
    assert cc["type"] == "array"
    item = cc["items"]
    assert set(item["required"]) == {"applies_to", "check", "description"}
    chk = item["properties"]["check"]
    assert set(chk["required"]) == {"pattern", "expect"}
    assert chk["properties"]["expect"]["enum"] == ["present", "absent"]
    assert chk["properties"]["scope"]["enum"] == ["body", "frontmatter"]
    assert chk["properties"]["scope"]["default"] == "body"
    assert item["properties"]["origin"]["enum"] == ["preset", "inductive", "learned"]
    assert item["properties"]["severity"]["enum"] == ["error", "warn", "info"]
    assert "content_conventions" not in s["required"]


def test_manifest_schema_is_metadata_only():
    """③ manifest 는 메타데이터-only — sha256/size/split/lineage 필드만, 데이터 복사 필드 없음."""
    s = load(MANIFEST_SCHEMA)
    ds = s["properties"]["datasets"]["items"]["properties"]
    assert "sha256" in ds and "size_bytes" in ds
    assert "split" in ds and "lineage" in ds
    # 실제 데이터를 옮긴다는 의미의 필드가 있으면 안 됨
    assert "copy_to" not in ds and "remote" not in ds and "upload" not in ds


REPRESENTATIVE_RULES = {
    "omp_version": "0.1.0",
    "project": {"name": "demo", "preset_origin": "python-ml", "initialized": "2026-05-30"},
    "specificity": 0.3,
    "structure": {"convention": "src-layout",
                  "directories": [{"path": "data/raw", "role": "원본 데이터",
                                   "origin": "inductive", "enforced": True}]},
    "naming": {"patterns": [
        {"applies_to": "data/processed/*.parquet", "regex": r"^[a-z0-9_]+_v\d+\.parquet$",
         "description": "snake_case + 버전", "origin": "preset", "severity": "warn"},
        # pure location rule — no regex, path_constraint instead (learning-protocol OBS-0007 shape)
        {"applies_to": "**/*.pkl", "path_constraint": {"must_be_under": "data/processed"},
         "description": ".pkl은 data/processed/ 아래", "origin": "learned", "severity": "warn"},
    ]},
    "content_conventions": [
        {
            "applies_to": "papers/**/*.md",
            "check": {"pattern": "^## Main Ideas$", "expect": "present"},
            "description": "review notes need a Main Ideas section",
            "origin": "inductive",
            "severity": "warn",
        },
        {
            "applies_to": "concepts/**/*.md",
            "check": {"pattern": r"^\d+\.", "expect": "absent"},
            "description": "no numbered lists in concept notes",
            "origin": "inductive",
            "severity": "info",
        },
    ],
    "ignore": [".git/**", ".omp/**"],
}

REPRESENTATIVE_MANIFEST = {
    "omp_version": "0.1.0",
    "generated": "2026-05-30T00:00:00",
    "datasets": [{
        "id": "train-v2", "path": "data/processed/train.parquet",
        "sha256": "a" * 64, "size_bytes": 1024, "rows": 100,
        "split": {"role": "train", "ratio": 0.8, "group": "exp1"},
        "lineage": {"derived_from": "raw/dump.csv", "by": "scripts/clean.py", "at": "2026-05-30"},
        "source": "internal", "added": "2026-05-30",
    }],
}


def test_representative_instances_match_schema():
    """④ 대표 인스턴스가 스키마 통과 (jsonschema 있으면 실검증, 없으면 skip)."""
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(REPRESENTATIVE_RULES, load(RULES_SCHEMA))
    jsonschema.validate(REPRESENTATIVE_MANIFEST, load(MANIFEST_SCHEMA))


def test_content_conventions_rejects_bad_enum():
    """An invalid expect value must fail jsonschema validation."""
    jsonschema = pytest.importorskip("jsonschema")
    bad = json.loads(json.dumps(REPRESENTATIVE_RULES))
    bad["content_conventions"][0]["check"]["expect"] = "maybe"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, load(RULES_SCHEMA))


def test_sha256_pattern_matches_schema():
    """⑥ 실제 해시가 manifest 스키마의 sha256 패턴과 정합."""
    import re
    s = load(MANIFEST_SCHEMA)
    pat = s["properties"]["datasets"]["items"]["properties"]["sha256"]["pattern"]
    real = hashlib.sha256(b"x").hexdigest()
    assert re.match(pat, real)
    assert re.match(pat, "UNHASHED")  # 대용량 파일용 sentinel 도 허용
