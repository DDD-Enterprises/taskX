import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dopetask.cli import cli
from dopetask.guard.identity import RepoIdentityGuardError, assert_repo_identity


def _write_project_json(repo_dir: Path, project_id: object) -> None:
    taskx_dir = repo_dir / ".taskx"
    taskx_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "project_id": project_id,
        "project_slug": "taskX",
        "repo_remote_hint": "taskX",
        "packet_required_header": False,
    }
    (taskx_dir / "project.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_taskxroot(repo_dir: Path) -> None:
    (repo_dir / ".taskxroot").write_text("taskx\n", encoding="utf-8")


def test_assert_repo_identity_pass(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_taskxroot(repo_dir)
    _write_project_json(repo_dir, "taskx.core")

    identity = assert_repo_identity(repo_dir, expected_project_id=None)
    assert identity.project_id == "taskx.core"


def test_assert_repo_identity_missing_project_json(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_taskxroot(repo_dir)

    with pytest.raises(RepoIdentityGuardError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_missing_taskxroot(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_project_json(repo_dir, "taskx.core")

    with pytest.raises(RepoIdentityGuardError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_missing_project_id(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_taskxroot(repo_dir)
    taskx_dir = repo_dir / ".taskx"
    taskx_dir.mkdir(parents=True, exist_ok=True)
    (taskx_dir / "project.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RuntimeError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_invalid_json(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_taskxroot(repo_dir)
    taskx_dir = repo_dir / ".taskx"
    taskx_dir.mkdir(parents=True, exist_ok=True)
    (taskx_dir / "project.json").write_text("{not-json}", encoding="utf-8")

    with pytest.raises(RuntimeError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_non_string_project_id(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_taskxroot(repo_dir)
    _write_project_json(repo_dir, ["not", "a", "string"])

    with pytest.raises(RuntimeError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_mismatch(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_taskxroot(repo_dir)
    _write_project_json(repo_dir, "something.else")

    with pytest.raises(RepoIdentityGuardError) as exc:
        assert_repo_identity(repo_dir, expected_project_id="taskx.core")
    message = str(exc.value)
    assert "expected_project_id" in message
    assert "observed_project_id" in message
    assert str(repo_dir) in message


def test_docs_refresh_guard_refuses(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_taskxroot(repo_dir)
    _write_project_json(repo_dir, "wrong.id")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "docs",
            "refresh-llm",
            "--repo-root",
            str(repo_dir),
            "--check",
            "--require-project-id",
            "taskx.core",
        ],
    )

    assert result.exit_code == 2
    assert "REFUSAL: repo identity mismatch" in result.stdout
