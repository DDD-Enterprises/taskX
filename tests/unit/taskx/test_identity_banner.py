"""Tests for dopeTask identity banner output."""

from __future__ import annotations

from dopetask.guard.banner import BannerContext, print_identity_banner


def test_banner_prints_single_line_when_origin_matches_hint(capsys, monkeypatch) -> None:
    """Matching origin hint should print only the banner line."""
    monkeypatch.setenv("NO_COLOR", "1")

    ctx = BannerContext(
        project_id="dopetask",
        project_slug="dopeTask",
        branch="tp/dopetask/tp-0111-demo",
        run_id="RUN_0111",
        origin_url="git@github.com:example/dopeTask.git",
        repo_remote_hint="dopeTask",
    )

    print_identity_banner(ctx)
    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err.splitlines() == [
        "[dopetask] project=dopetask repo=dopeTask branch=tp/dopetask/tp-0111-demo run=RUN_0111"
    ]


def test_banner_prints_warning_when_origin_missing_hint(capsys, monkeypatch) -> None:
    """Mismatched origin hint should emit a warning line."""
    monkeypatch.setenv("NO_COLOR", "1")

    ctx = BannerContext(
        project_id="dopetask",
        project_slug="dopeTask",
        branch="main",
        run_id="RUN_X",
        origin_url="git@github.com:example/other.git",
        repo_remote_hint="dopeTask",
    )

    print_identity_banner(ctx)
    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err.splitlines() == [
        "[dopetask] project=dopetask repo=dopeTask branch=main run=RUN_X",
        "[dopetask][WARNING] origin URL does not match repo_remote_hint='dopeTask' (origin='git@github.com:example/other.git')",
    ]


def test_banner_prints_warning_when_origin_unavailable(capsys, monkeypatch) -> None:
    """Missing origin URL should emit not-available warning."""
    monkeypatch.setenv("NO_COLOR", "1")

    ctx = BannerContext(
        project_id="dopetask",
        project_slug="dopeTask",
        branch="main",
        run_id=None,
        origin_url=None,
        repo_remote_hint="dopeTask",
    )

    print_identity_banner(ctx)
    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err.splitlines() == [
        "[dopetask] project=dopetask repo=dopeTask branch=main run=none",
        "[dopetask][WARNING] origin URL not available",
    ]
