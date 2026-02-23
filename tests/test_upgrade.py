import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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

@pytest.fixture
def mock_pypi_repo(tmp_path):
    repo_root = tmp_path / "myrepo"
    repo_root.mkdir()
    (repo_root / ".taskx-pin").write_text("install=pypi\nref=v0.1.0\n")
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
         patch("subprocess.check_call") as mock_check_call, \
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

def test_upgrade_pypi_flag_switches_method(mock_repo):
    """upgrade --pypi should switch install method to pypi and use taskx-kernel package."""
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=mock_repo):

        mock_detect.return_value = RepoInfo(root=mock_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--pypi"])

        print(result.stdout)
        assert result.exit_code == 0

        # Pin file must reflect pypi install method
        pin_text = (mock_repo / ".taskx-pin").read_text()
        assert "install=pypi" in pin_text

        # pip should install taskx-kernel (no version suffix for unversioned upgrade)
        args, _ = mock_check_call.call_args_list[0]
        cmd = args[0]
        assert cmd[:5] == [sys.executable, "-m", "pip", "install", "--upgrade"]
        assert "taskx-kernel" in cmd[-1]

def test_upgrade_pypi_with_version(mock_repo):
    """upgrade --pypi --version v0.2.0 should install taskx-kernel==0.2.0."""
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=mock_repo):

        mock_detect.return_value = RepoInfo(root=mock_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--pypi", "--version", "v0.2.0"])

        print(result.stdout)
        assert result.exit_code == 0

        # Pin file must reflect pypi and correct ref
        pin_text = (mock_repo / ".taskx-pin").read_text()
        assert "install=pypi" in pin_text
        assert "v0.2.0" in pin_text

        # pip should install taskx-kernel==0.2.0 (v prefix stripped)
        args, _ = mock_check_call.call_args_list[0]
        cmd = args[0]
        assert "taskx-kernel==0.2.0" in cmd

def test_upgrade_pypi_latest(mock_pypi_repo):
    """upgrade --latest with pypi install method should set ref to 'latest'."""
    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=mock_pypi_repo):

        mock_detect.return_value = RepoInfo(root=mock_pypi_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--latest"])

        print(result.stdout)
        assert result.exit_code == 0

        # Pin file must reflect pypi and 'latest' ref
        pin_text = (mock_pypi_repo / ".taskx-pin").read_text()
        assert "install=pypi" in pin_text
        assert "latest" in pin_text

        # pip should install plain taskx-kernel (no version pinning for 'latest')
        args, _ = mock_check_call.call_args_list[0]
        cmd = args[0]
        assert "taskx-kernel" in cmd[-1]
        assert "==" not in cmd[-1]

def test_upgrade_version_without_pypi_defaults_to_git(tmp_path):
    """upgrade --version without --pypi should always use git install method."""
    # Start with a wheel-based pin to verify the default-to-git behavior
    wheel_repo = tmp_path / "myrepo"
    wheel_repo.mkdir()
    (wheel_repo / ".taskx-pin").write_text(
        "install=wheel\npath=dist/taskx.whl\nrepo=https://example.com/repo.git\n"
    )

    with patch("taskx.utils.repo.detect_repo_root") as mock_detect, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("pathlib.Path.cwd", return_value=wheel_repo):

        mock_detect.return_value = RepoInfo(root=wheel_repo, project_type="python", marker=".git")

        result = runner.invoke(cli, ["upgrade", "--version", "v0.3.0"])

        print(result.stdout)
        assert result.exit_code == 0

        # install method should have been switched to git
        pin_text = (wheel_repo / ".taskx-pin").read_text()
        assert "install=git" in pin_text
        assert "v0.3.0" in pin_text
