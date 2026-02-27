import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dopetask.cli import cli
from dopetask.guard.identity import RepoIdentityGuardError, assert_repo_identity


def _write_project_json(repo_dir: Path, project_id: object) -> None:
    dopetask_dir = repo_dir / ".dopetask"
    dopetask_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "project_id": project_id,
        "project_slug": "dopeTask",
        "repo_remote_hint": "dopeTask",
        "packet_required_header": False,
    }
    (dopetask_dir / "project.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_dopetaskroot(repo_dir: Path) -> None:
    (repo_dir / ".dopetaskroot").write_text("dopetask\n", encoding="utf-8")


def test_assert_repo_identity_pass(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_dopetaskroot(repo_dir)
    _write_project_json(repo_dir, "dopetask.core")

    identity = assert_repo_identity(repo_dir, expected_project_id=None)
    assert identity.project_id == "dopetask.core"


def test_assert_repo_identity_missing_project_json(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_dopetaskroot(repo_dir)

    with pytest.raises(RepoIdentityGuardError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_missing_dopetaskroot(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_project_json(repo_dir, "dopetask.core")

    with pytest.raises(RepoIdentityGuardError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_missing_project_id(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_dopetaskroot(repo_dir)
    dopetask_dir = repo_dir / ".dopetask"
    dopetask_dir.mkdir(parents=True, exist_ok=True)
    (dopetask_dir / "project.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RuntimeError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_invalid_json(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_dopetaskroot(repo_dir)
    dopetask_dir = repo_dir / ".dopetask"
    dopetask_dir.mkdir(parents=True, exist_ok=True)
    (dopetask_dir / "project.json").write_text("{not-json}", encoding="utf-8")

    with pytest.raises(RuntimeError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_non_string_project_id(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_dopetaskroot(repo_dir)
    _write_project_json(repo_dir, ["not", "a", "string"])

    with pytest.raises(RuntimeError):
        assert_repo_identity(repo_dir)


def test_assert_repo_identity_mismatch(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_dopetaskroot(repo_dir)
    _write_project_json(repo_dir, "something.else")

    with pytest.raises(RepoIdentityGuardError) as exc:
        assert_repo_identity(repo_dir, expected_project_id="dopetask.core")
    message = str(exc.value)
    assert "expected_project_id" in message
    assert "observed_project_id" in message
    assert str(repo_dir) in message


def test_docs_refresh_guard_refuses(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _write_dopetaskroot(repo_dir)
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
            "dopetask.core",
        ],
    )

    assert result.exit_code == 2
    assert "REFUSAL: repo identity mismatch" in result.stdout
