import sys
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from taskx.cli import cli
from taskx.utils.repo import RepoInfo

runner = CliRunner()

@pytest.fixture
def mock_repo(tmp_path):
    repo_root = tmp_path / "myrepo"
    repo_root.mkdir()
    (repo_root / ".taskx-pin").write_text("install=git\nrepo=https://example.com/repo.git\nref=v0.1.0\n")
    return repo_root

def test_upgrade_version(mock_repo):
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=mock_repo):

        mock_detect.return_value = RepoInfo(root=mock_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--version", "v0.2.0"])

        print(result.stdout)
        assert result.exit_code == 0
        assert "Updating" in result.stdout
        assert "v0.2.0" in (mock_repo / ".taskx-pin").read_text()

        # Verify pip call
        # The first call is pip install
        # The second call is verification
        args, _ = mock_check_call.call_args_list[0]
        cmd = args[0]
        assert cmd[:5] == [sys.executable, "-m", "pip", "install", "--upgrade"]
        assert "git+https://example.com/repo.git@v0.2.0" in cmd

def test_upgrade_latest(mock_repo):
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_output") as mock_check_output, \
         patch("subprocess.check_call"), \
         patch("pathlib.Path.cwd", return_value=mock_repo):

        mock_detect.return_value = RepoInfo(root=mock_repo, project_type="python", marker=".git")
        mock_check_output.return_value = "hash1\trefs/tags/v0.1.0\nhash2\trefs/tags/v0.3.0\n"

        result = runner.invoke(cli, ["upgrade", "--latest"])

        print(result.stdout)
        assert result.exit_code == 0
        assert "Latest version: v0.3.0" in result.stdout
        assert "v0.3.0" in (mock_repo / ".taskx-pin").read_text()

def test_upgrade_no_pin(tmp_path):
     with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
          patch("pathlib.Path.cwd", return_value=tmp_path):

        mock_detect.return_value = RepoInfo(root=tmp_path, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade"])

        assert result.exit_code == 1
        assert "No .taskx-pin found" in result.stdout

@pytest.fixture
def mock_pypi_repo(tmp_path):
    repo_root = tmp_path / "myrepo"
    repo_root.mkdir()
    (repo_root / ".taskx-pin").write_text("install=pypi\nref=v0.1.0\n")
    return repo_root


def test_upgrade_pypi_flag(mock_repo):
    """Test that --pypi flag switches install method to PyPI."""
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=mock_repo):

        mock_detect.return_value = RepoInfo(root=mock_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--pypi"])

        print(result.stdout)
        assert result.exit_code == 0
        pin_text = (mock_repo / ".taskx-pin").read_text()
        assert "install=pypi" in pin_text

        # Verify pip was called with taskx-kernel package
        args, _ = mock_check_call.call_args_list[0]
        cmd = args[0]
        assert cmd[:5] == [sys.executable, "-m", "pip", "install", "--upgrade"]
        assert any("taskx-kernel" in item for item in cmd)


def test_upgrade_pypi_with_version(mock_repo):
    """Test that --pypi --version installs a specific version from PyPI."""
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=mock_repo):

        mock_detect.return_value = RepoInfo(root=mock_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--pypi", "--version", "v0.3.0"])

        print(result.stdout)
        assert result.exit_code == 0
        pin_text = (mock_repo / ".taskx-pin").read_text()
        assert "install=pypi" in pin_text
        assert "v0.3.0" in pin_text

        # Verify pip was called with versioned package spec (strips leading 'v')
        args, _ = mock_check_call.call_args_list[0]
        cmd = args[0]
        assert "taskx-kernel==0.3.0" in cmd


def test_upgrade_pypi_latest(mock_pypi_repo):
    """Test that --latest with a PyPI pin file sets ref to 'latest'."""
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=mock_pypi_repo):

        mock_detect.return_value = RepoInfo(root=mock_pypi_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--latest"])

        print(result.stdout)
        assert result.exit_code == 0
        pin_text = (mock_pypi_repo / ".taskx-pin").read_text()
        assert "install=pypi" in pin_text

        # When ref is "latest", no version spec is appended
        args, _ = mock_check_call.call_args_list[0]
        cmd = args[0]
        assert "taskx-kernel" in cmd
        assert "==" not in " ".join(cmd)


def test_upgrade_pypi_pin_updated(mock_repo):
    """Test that the pin file is correctly updated with install=pypi."""
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call"), \
         patch("pathlib.Path.cwd", return_value=mock_repo):

        mock_detect.return_value = RepoInfo(root=mock_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--pypi", "--version", "0.5.0"])

        assert result.exit_code == 0
        pin_text = (mock_repo / ".taskx-pin").read_text()
        assert "install=pypi" in pin_text
        assert "0.5.0" in pin_text
