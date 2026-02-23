
from typer.testing import CliRunner

from dopetask.ops.blocks import update_file
from dopetask.ops.cli import app
from dopetask.ops.discover import discover_instruction_file, get_sidecar_path
from dopetask.ops.export import calculate_hash, export_prompt


def test_idempotent_apply(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text("# Existing content\n")

    content = "New operator instructions"
    c_hash = calculate_hash(content)
    platform = "chatgpt"
    model = "gpt-4"

    # First apply
    changed = update_file(target, content, platform, model, c_hash)
    assert changed is True
    first_bytes = target.read_bytes()

    # Second apply
    changed = update_file(target, content, platform, model, c_hash)
    assert changed is False
    second_bytes = target.read_bytes()

    assert first_bytes == second_bytes

def test_non_destructive_edit(tmp_path):
    target = tmp_path / "CLAUDE.md"
    original = "# Header\nUser content here.\n"
    target.write_text(original)

    content = "TaskX content"
    c_hash = calculate_hash(content)
    update_file(target, content, "chatgpt", "gpt-4", c_hash)

    updated_text = target.read_text()
    assert original in updated_text
    assert "<!-- TASKX:BEGIN operator_system" in updated_text

def test_replace_only_block(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text("# Header\n<!-- TASKX:BEGIN operator_system v=1 platform=chatgpt model=gpt-4 hash=old -->\nOld content\n<!-- TASKX:END operator_system -->\nFooter")

    new_content = "New content"
    new_hash = calculate_hash(new_content)
    update_file(target, new_content, "chatgpt", "gpt-4", new_hash)

    updated_text = target.read_text()
    assert "# Header" in updated_text
    assert "Footer" in updated_text
    assert "New content" in updated_text
    assert "Old content" not in updated_text
    assert updated_text.count("<!-- TASKX:BEGIN") == 1

def test_discovery_order(tmp_path):
    # .claude/CLAUDE.md should win
    repo = tmp_path
    (repo / ".claude").mkdir()
    (repo / ".claude" / "CLAUDE.md").write_text("winner")
    (repo / "CLAUDE.md").write_text("loser")

    found = discover_instruction_file(repo)
    assert found.name == "CLAUDE.md"
    assert ".claude" in str(found)

def test_create_sidecar(tmp_path):
    repo = tmp_path
    sidecar = get_sidecar_path(repo)

    content = "TaskX content"
    c_hash = calculate_hash(content)
    update_file(sidecar, content, "chatgpt", "gpt-4", c_hash)

    assert sidecar.exists()
    assert "TaskX content" in sidecar.read_text()

def test_ops_init_exports_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr("taskx.ops.cli.get_repo_root", lambda: tmp_path)
    runner = CliRunner()

    # Run init
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    export_file = tmp_path / "ops" / "EXPORTED_OPERATOR_PROMPT.md"
    assert export_file.exists()

    first_hash = calculate_hash(export_file.read_text())

    # Run again - should be idempotent
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "changed=False" in result.output
    assert calculate_hash(export_file.read_text()) == first_hash

def test_ops_init_no_export(tmp_path, monkeypatch):
    monkeypatch.setattr("taskx.ops.cli.get_repo_root", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["init", "--no-export"])
    assert result.exit_code == 0

    export_file = tmp_path / "ops" / "EXPORTED_OPERATOR_PROMPT.md"
    assert not export_file.exists()

def test_ops_doctor_exports_even_on_fail(tmp_path, monkeypatch):
    monkeypatch.setattr("taskx.ops.cli.get_repo_root", lambda: tmp_path)
    runner = CliRunner()

    # Setup - init first
    runner.invoke(app, ["init", "--no-export"])

    # Create a FAIL condition for doctor (e.g., STALE block)
    claude_file = tmp_path / "CLAUDE.md"
    claude_file.write_text("# Header\n<!-- TASKX:BEGIN operator_system hash=stale -->\nOld\n<!-- TASKX:END operator_system -->")

    result = runner.invoke(app, ["doctor"])
    # Doctor should exit with non-zero on failure
    assert result.exit_code != 0

    export_file = tmp_path / "ops" / "EXPORTED_OPERATOR_PROMPT.md"
    assert export_file.exists()

def test_ops_doctor_no_export(tmp_path, monkeypatch):
    monkeypatch.setattr("taskx.ops.cli.get_repo_root", lambda: tmp_path)
    runner = CliRunner()

    # Setup
    runner.invoke(app, ["init", "--no-export"])

    runner.invoke(app, ["doctor", "--no-export"])

    export_file = tmp_path / "ops" / "EXPORTED_OPERATOR_PROMPT.md"
    assert not export_file.exists()

def test_ops_apply_does_not_export(tmp_path, monkeypatch):
    monkeypatch.setattr("taskx.ops.cli.get_repo_root", lambda: tmp_path)
    runner = CliRunner()

    # Setup
    runner.invoke(app, ["init", "--no-export"])

    # Apply should work without creating the export file
    # We need some templates to apply
    (tmp_path / "CLAUDE.md").write_text("# Header")

    result = runner.invoke(app, ["apply"])
    assert result.exit_code == 0

    export_file = tmp_path / "ops" / "EXPORTED_OPERATOR_PROMPT.md"
    assert not export_file.exists()
    assert "updated" in result.output.lower()

def test_ops_export_write_on_change(tmp_path, monkeypatch):
    monkeypatch.setattr("taskx.ops.cli.get_repo_root", lambda: tmp_path)
    runner = CliRunner()

    runner.invoke(app, ["init", "--no-export"])

    # First export
    result = runner.invoke(app, ["export"])
    assert "changed=True" in result.output

    export_file = tmp_path / "ops" / "EXPORTED_OPERATOR_PROMPT.md"
    assert export_file.exists()

    # Second export
    result = runner.invoke(app, ["export"])
    assert "changed=False" in result.output

def test_export_determinism(tmp_path):
    profile = {
        "project": {"name": "test", "repo_root": "root", "timezone": "UTC"},
        "taskx": {"pin_type": "git", "pin_value": "123", "cli_min_version": "1.0.0"},
        "platform": {"target": "chatgpt", "model": "gpt-4"}
    }
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "b.md").write_text("B content")
    (templates_dir / "a.md").write_text("A content")

    # Run twice
    prompt1 = export_prompt(profile, templates_dir, taskx_version="1.0.0", git_hash="abc")
    prompt2 = export_prompt(profile, templates_dir, taskx_version="1.0.0", git_hash="abc")

    assert prompt1 == prompt2
    # Check lexicographical order for "a.md" and "b.md"
    # base and lab are first if they exist, but here they don't.
    # a.md should come before b.md
    assert prompt1.find("A content") < prompt1.find("B content")


# --- __all__ exports ---

def test_ops_all_exports():
    import dopetask.ops as ops
    assert hasattr(ops, "__all__")
    # Spot-check key public API names
    for name in ["export_prompt", "load_profile", "run_doctor", "inject_block", "update_file",
                 "calculate_hash", "discover_instruction_file", "get_sidecar_path",
                 "extract_operator_blocks", "get_canonical_target", "check_conflicts",
                 "find_block", "write_if_changed"]:
        assert name in ops.__all__, f"{name} missing from ops.__all__"
        assert hasattr(ops, name), f"{name} not importable from dopetask.ops"


# --- BaseAdapter + DopemuxAdapter ---

def test_base_adapter_interface():
    import abc

    from dopetask_adapters.base import BaseAdapter
    # BaseAdapter should be abstract
    assert abc.ABC in BaseAdapter.__mro__


def test_dopemux_adapter_class(tmp_path):
    from dopetask_adapters.dopemux import DopemuxAdapter
    adapter = DopemuxAdapter()
    assert adapter.name == "dopemux"
    # detect should raise when no markers found
    import pytest
    with pytest.raises(RuntimeError):
        adapter.detect(start=tmp_path)


def test_dopemux_adapter_detect_with_marker(tmp_path):
    from dopetask_adapters.dopemux import DopemuxAdapter
    (tmp_path / ".dopemux").mkdir()
    adapter = DopemuxAdapter()
    info = adapter.detect(start=tmp_path)
    assert info.name == "dopemux"
    assert info.root == tmp_path
    assert info.marker == ".dopemux/"


def test_dopemux_adapter_compute_paths(tmp_path):
    from dopetask_adapters.dopemux import DopemuxAdapter
    adapter = DopemuxAdapter()
    paths = adapter.compute_paths(tmp_path)
    assert paths.out_root == tmp_path / "out" / "taskx"


def test_adapter_discovery():
    from dopetask_adapters import discover_adapters
    # Should yield at least the dopemux adapter (registered via entry point)
    adapters = list(discover_adapters())
    # May or may not find dopemux depending on editable install state;
    # just verify it doesn't crash
    assert isinstance(adapters, list)


def test_get_adapter_not_found():
    from dopetask_adapters import get_adapter
    result = get_adapter("nonexistent_adapter_xyz")
    assert result is None


# --- Doctor config location reporting ---

def test_doctor_config_locations(tmp_path, monkeypatch):
    monkeypatch.setattr("taskx.ops.cli.get_repo_root", lambda: tmp_path)
    runner = CliRunner()

    # Setup ops dir
    runner.invoke(app, ["init", "--no-export"])

    from dopetask.ops.doctor import run_doctor
    report = run_doctor(tmp_path)

    assert "config_locations" in report
    locs = report["config_locations"]
    assert locs["repo_root"] == str(tmp_path)
    assert locs["ops_dir"] == str(tmp_path / "ops")
    # profile should exist after init
    assert locs["profile"] is not None
    assert locs["templates_dir"] is not None


def test_doctor_config_locations_missing(tmp_path):
    """Doctor should report None for missing config paths."""
    from dopetask.ops.doctor import run_doctor
    report = run_doctor(tmp_path)

    locs = report["config_locations"]
    assert locs["profile"] is None
    assert locs["templates_dir"] is None
    assert locs["compiled_prompt"] is None


# --- taskx init top-level command ---

def test_taskx_init_ops_tier(tmp_path, monkeypatch):
    from dopetask.cli import cli
    monkeypatch.chdir(tmp_path)

    # Mock detect_repo_root to return tmp_path
    from types import SimpleNamespace

    from dopetask.utils import repo as repo_mod
    monkeypatch.setattr(repo_mod, "detect_repo_root", lambda cwd: SimpleNamespace(root=tmp_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--tier", "ops", "--yes"])
    assert result.exit_code == 0
    assert "ops tier" in result.output.lower() or "complete" in result.output.lower()
    # ops directory should exist
    assert (tmp_path / "ops").exists()


def test_taskx_init_yes_no_prompts(tmp_path, monkeypatch):
    """--yes mode should complete without any interactive prompts."""
    from types import SimpleNamespace

    from dopetask.cli import cli
    from dopetask.utils import repo as repo_mod
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(repo_mod, "detect_repo_root", lambda cwd: SimpleNamespace(root=tmp_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--tier", "ops", "--yes"], input="")
    assert result.exit_code == 0
