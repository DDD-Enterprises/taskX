"""Focused tests for Python 3.9 compatibility helpers."""

from __future__ import annotations

from types import ModuleType, SimpleNamespace

import dopetask.utils.toml_compat as toml_compat
import dopetask_adapters


def test_load_tomllib_falls_back_to_tomli(monkeypatch) -> None:
    fallback = ModuleType("tomli")

    def fake_import_module(name: str) -> ModuleType:
        if name == "tomllib":
            raise ModuleNotFoundError(name)
        if name == "tomli":
            return fallback
        raise AssertionError(f"unexpected module import: {name}")

    monkeypatch.setattr(toml_compat.importlib, "import_module", fake_import_module)

    assert toml_compat.load_tomllib() is fallback


def test_adapter_entry_points_supports_selectable_api(monkeypatch) -> None:
    expected = [SimpleNamespace(group="dopetask.adapters")]

    class Selectable(list):
        def select(self, **kwargs):
            assert kwargs == {"group": "dopetask.adapters"}
            return expected

    monkeypatch.setattr(dopetask_adapters.importlib_metadata, "entry_points", lambda: Selectable())

    assert list(dopetask_adapters._adapter_entry_points()) == expected


def test_adapter_entry_points_supports_legacy_mapping(monkeypatch) -> None:
    expected = [SimpleNamespace(group="dopetask.adapters")]

    monkeypatch.setattr(
        dopetask_adapters.importlib_metadata,
        "entry_points",
        lambda: {"dopetask.adapters": expected},
    )

    assert list(dopetask_adapters._adapter_entry_points()) == expected
