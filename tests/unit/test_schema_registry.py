"""Verify SchemaRegistry discovers and loads required schemas."""
import pytest

from dopetask.utils.schema_registry import SchemaRegistry

REQUIRED = {"allowlist_diff", "promotion_token", "run_envelope", "run_summary"}


def test_required_schemas_available():
    registry = SchemaRegistry()
    assert set(registry.available) >= REQUIRED


def test_schema_loads_as_dict():
    registry = SchemaRegistry()
    for name in REQUIRED:
        schema = registry.get_json(name)
        assert isinstance(schema, dict)


def test_missing_schema_raises_keyerror():
    registry = SchemaRegistry()
    with pytest.raises(KeyError):
        registry.get_json("this_schema_does_not_exist_anywhere")
