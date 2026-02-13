"""Compatibility coverage for docs refresh marker helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from taskx.docs.refresh_llm import (
    AUTOGEN_END,
    AUTOGEN_START,
    MarkerStructureError,
    apply_autogen_update,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_apply_autogen_update_inserts_when_missing(tmp_path: Path) -> None:
    path = tmp_path / "CLAUDE.md"
    path.write_text("# Title\n", encoding="utf-8")

    updated, state = apply_autogen_update(path.read_text(encoding="utf-8"), "content")
    assert state == "created"
    assert AUTOGEN_START in updated
    assert AUTOGEN_END in updated


def test_apply_autogen_update_refuses_malformed_marker_structure() -> None:
    with pytest.raises(MarkerStructureError, match="Invalid AUTOGEN marker structure"):
        apply_autogen_update(f"{AUTOGEN_START}\n", "content")
