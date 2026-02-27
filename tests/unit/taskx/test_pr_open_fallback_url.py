"""Fallback URL parsing tests for PR open flow."""

from dopetask.pr.open import _parse_owner_repo


def test_parse_owner_repo_https() -> None:
    assert _parse_owner_repo("https://github.com/acme/dopeTask.git") == "acme/dopeTask"


def test_parse_owner_repo_ssh() -> None:
    assert _parse_owner_repo("git@github.com:acme/dopeTask.git") == "acme/dopeTask"


def test_parse_owner_repo_invalid() -> None:
    assert _parse_owner_repo("https://example.com/acme/dopeTask.git") is None
