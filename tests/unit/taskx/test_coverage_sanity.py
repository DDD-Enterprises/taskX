"""Coverage sanity tests - ensures real package code is executed during test runs.

These tests are minimal but exercise actual code paths to prevent "no data collected" warnings.
"""
from pathlib import Path

import pytest

from dopetask import __version__


class TestdopeTaskImport:
    """Test that dopeTask package can be imported and has expected attributes."""

    def test_dopetask_imports(self):
        """dopeTask package imports successfully."""
        import dopetask

        assert dopetask is not None
        assert hasattr(dopetask, "__version__")
        assert dopetask.__version__ == __version__

    def test_doctor_module_imports(self):
        """Doctor module imports successfully."""
        from dopetask.doctor import DoctorReport, _check_dopetask_import

        assert DoctorReport is not None
        assert _check_dopetask_import is not None


class TestSchemaRegistry:
    """Test schema registry functionality."""

    def test_schema_registry_initialization(self):
        """Schema registry initializes and discovers schemas."""
        from dopetask.utils.schema_registry import SchemaRegistry

        registry = SchemaRegistry()
        assert registry is not None
        assert len(registry.available) > 0
        assert "allowlist_diff" in registry.available

    def test_get_schema_json(self):
        """Can load a schema as JSON."""
        from dopetask.utils.schema_registry import get_schema_json

        schema = get_schema_json("allowlist_diff")
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"


class TestDoctorNonCLI:
    """Test doctor functionality without invoking CLI."""

    def test_check_dopetask_import(self):
        """Internal dopetask import check works."""
        from dopetask.doctor import _check_dopetask_import

        result = _check_dopetask_import()
        assert result.status == "pass"
        assert __version__ in result.message

    def test_check_schema_registry(self):
        """Internal schema registry check works."""
        from dopetask.doctor import _check_schema_registry

        result = _check_schema_registry()
        assert result.status == "pass"
        assert "schemas available" in result.message

    def test_run_doctor_minimal(self, tmp_path: Path):
        """Can run doctor and generate report."""
        from dopetask.doctor import run_doctor

        out_dir = tmp_path / "doctor_output"
        out_dir.mkdir()

        report = run_doctor(
            out_dir=out_dir,
            timestamp_mode="deterministic",
            require_git=False,
        )

        # Verify report structure
        assert report is not None
        assert report.status in ("passed", "failed")
        assert report.timestamp_mode == "deterministic"
        assert report.generated_at == "1970-01-01T00:00:00Z"

        # Verify report files were created
        assert (out_dir / "DOCTOR_REPORT.json").exists()
        assert (out_dir / "DOCTOR_REPORT.md").exists()


class TestRepoUtils:
    """Test repository utility functions."""

    def test_find_dopetask_repo_root_with_marker(self, tmp_path: Path):
        """Can find dopeTask repo root with .dopetaskroot marker."""
        from dopetask.utils.repo import find_dopetask_repo_root

        # Create a mock repo with marker
        marker = tmp_path / ".dopetaskroot"
        marker.touch()

        result = find_dopetask_repo_root(tmp_path)
        assert result == tmp_path

    def test_find_dopetask_repo_root_no_marker(self, tmp_path: Path):
        """Returns None when no dopeTask repo marker found."""
        from dopetask.utils.repo import find_dopetask_repo_root

        result = find_dopetask_repo_root(tmp_path)
        assert result is None

    def test_require_dopetask_repo_root_raises(self, tmp_path: Path):
        """Raises helpful error when repo not found."""
        from dopetask.utils.repo import require_dopetask_repo_root

        with pytest.raises(RuntimeError) as exc_info:
            require_dopetask_repo_root(tmp_path)

        assert "dopeTask repo not detected" in str(exc_info.value)
        assert "touch .dopetaskroot" in str(exc_info.value)
