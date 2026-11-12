"""Committed JSON Schema files match the models (drift guard) and keep key properties."""

import json
from pathlib import Path

import pytest

from maigadi_schemas.export import DEFAULT_OUT_DIR, json_schemas, main


def test_committed_schema_files_are_up_to_date() -> None:
    generated = json_schemas()
    on_disk = {p.name.removesuffix(".schema.json") for p in DEFAULT_OUT_DIR.glob("*.schema.json")}
    assert on_disk == set(generated), "run: uv run maigadi-schemas"
    for name, schema in generated.items():
        committed = json.loads((DEFAULT_OUT_DIR / f"{name}.schema.json").read_text("utf-8"))
        assert committed == schema, f"{name} is stale; run: uv run maigadi-schemas"


@pytest.mark.parametrize("name", sorted(json_schemas()))
def test_top_level_objects_forbid_unknown_fields(name: str) -> None:
    schema = json_schemas()[name]
    objects = [schema] if "properties" in schema else schema["$defs"].values()
    for obj in objects:
        if obj.get("type") == "object" and "properties" in obj:
            assert obj.get("additionalProperties") is False, name


def test_local_only_marker_is_visible_to_non_python_consumers() -> None:
    event = json_schemas()["event"]
    assert event["properties"]["media"]["x-maigadi-local-only"] is True


def test_cli_check_mode_detects_drift(tmp_path: Path) -> None:
    assert main(["--out", str(tmp_path), "--check"]) == 1
    assert main(["--out", str(tmp_path)]) == 0
    assert main(["--out", str(tmp_path), "--check"]) == 0
