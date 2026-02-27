"""Tests for neon UI module functions and behavior."""

from __future__ import annotations

import pytest

from dopetask.ui import (
    THEMES,
    NeonSpinner,
    get_theme_name,
    get_theme_palette,
    neon_enabled,
    render_banner,
    should_show_banner,
    strict_enabled,
    strict_violation,
    worship,
)


def test_neon_enabled_default(monkeypatch) -> None:
    """DOPETASK_NEON defaults to '1' (enabled)."""
    monkeypatch.delenv("DOPETASK_NEON", raising=False)
    assert neon_enabled() is True


def test_neon_enabled_explicit_on(monkeypatch) -> None:
    """DOPETASK_NEON='1' enables neon."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    assert neon_enabled() is True


def test_neon_enabled_explicit_off(monkeypatch) -> None:
    """DOPETASK_NEON='0' disables neon."""
    monkeypatch.setenv("DOPETASK_NEON", "0")
    assert neon_enabled() is False


def test_strict_enabled_default(monkeypatch) -> None:
    """DOPETASK_STRICT defaults to '0' (disabled)."""
    monkeypatch.delenv("DOPETASK_STRICT", raising=False)
    assert strict_enabled() is False


def test_strict_enabled_explicit_on(monkeypatch) -> None:
    """DOPETASK_STRICT='1' enables strict mode."""
    monkeypatch.setenv("DOPETASK_STRICT", "1")
    assert strict_enabled() is True


def test_strict_enabled_explicit_off(monkeypatch) -> None:
    """DOPETASK_STRICT='0' disables strict mode."""
    monkeypatch.setenv("DOPETASK_STRICT", "0")
    assert strict_enabled() is False


def test_get_theme_name_default(monkeypatch) -> None:
    """DOPETASK_THEME defaults to 'mintwave'."""
    monkeypatch.delenv("DOPETASK_THEME", raising=False)
    assert get_theme_name() == "mintwave"


def test_get_theme_name_custom(monkeypatch) -> None:
    """DOPETASK_THEME can be set to custom theme."""
    monkeypatch.setenv("DOPETASK_THEME", "cyberpunk")
    assert get_theme_name() == "cyberpunk"


def test_get_theme_palette_uses_default(monkeypatch) -> None:
    """get_theme_palette with no argument uses env var."""
    monkeypatch.setenv("DOPETASK_THEME", "ultraviolet")
    palette = get_theme_palette()
    assert palette == THEMES["ultraviolet"]


def test_get_theme_palette_explicit_override() -> None:
    """get_theme_palette with explicit theme overrides env."""
    palette = get_theme_palette(theme="magma")
    assert palette == THEMES["magma"]


def test_get_theme_palette_fallback_on_unknown() -> None:
    """get_theme_palette returns mintwave for unknown themes."""
    palette = get_theme_palette(theme="nonexistent")
    assert palette == THEMES["mintwave"]


def test_should_show_banner_disabled_when_neon_off(monkeypatch) -> None:
    """Banner disabled when DOPETASK_NEON=0."""
    monkeypatch.setenv("DOPETASK_NEON", "0")
    assert should_show_banner(["dopetask"]) is False
    assert should_show_banner(["dopetask", "--help"]) is False


def test_should_show_banner_on_no_args(monkeypatch) -> None:
    """Banner shown when dopetask invoked with no args."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    assert should_show_banner(["dopetask"]) is True


def test_should_show_banner_on_help_flag(monkeypatch) -> None:
    """Banner shown for --help flag."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    assert should_show_banner(["dopetask", "--help"]) is True
    assert should_show_banner(["dopetask", "route", "--help"]) is True


def test_should_show_banner_on_version_flag(monkeypatch) -> None:
    """Banner shown for --version flag."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    assert should_show_banner(["dopetask", "--version"]) is True


def test_should_show_banner_on_version_command(monkeypatch) -> None:
    """Banner shown for version command."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    assert should_show_banner(["dopetask", "version"]) is True


def test_should_show_banner_off_for_normal_commands(monkeypatch) -> None:
    """Banner not shown for normal commands."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    assert should_show_banner(["dopetask", "doctor"]) is False
    assert should_show_banner(["dopetask", "compile-tasks"]) is False


def test_render_banner_outputs_when_enabled(capsys, monkeypatch) -> None:
    """render_banner prints output when DOPETASK_NEON=1."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    render_banner(theme="mintwave")
    captured = capsys.readouterr()

    # Check for ASCII art banner content
    assert "████████╗" in captured.out
    assert "DETERMINISTIC TASK EXECUTION KERNEL" in captured.out
    assert "NO FALLBACKS. NO RETRIES. NO GHOST BEHAVIOR." in captured.out
    assert "ONE INVOCATION. ONE PATH. ONE OUTCOME." in captured.out
    assert "Theme: mintwave" in captured.out
    assert "DOPETASK_NEON=0" in captured.out


def test_render_banner_silent_when_disabled(capsys, monkeypatch) -> None:
    """render_banner produces no output when DOPETASK_NEON=0."""
    monkeypatch.setenv("DOPETASK_NEON", "0")
    render_banner(theme="mintwave")
    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


def test_render_banner_uses_theme_override(capsys, monkeypatch) -> None:
    """render_banner respects explicit theme parameter."""
    monkeypatch.setenv("DOPETASK_NEON", "1")
    monkeypatch.setenv("DOPETASK_THEME", "mintwave")

    render_banner(theme="cyberpunk")
    captured = capsys.readouterr()

    assert "Theme: cyberpunk" in captured.out


def test_render_banner_all_themes_work(capsys, monkeypatch) -> None:
    """All theme names render without error."""
    monkeypatch.setenv("DOPETASK_NEON", "1")

    for theme_name in THEMES:
        render_banner(theme=theme_name)
        captured = capsys.readouterr()
        assert f"Theme: {theme_name}" in captured.out


# NeonSpinner Tests


def test_neon_spinner_runs_function_when_enabled(monkeypatch) -> None:
    """NeonSpinner executes function and returns result when neon enabled."""
    monkeypatch.setenv("DOPETASK_NEON", "1")

    def test_fn() -> int:
        return 42

    spinner = NeonSpinner(message="Testing...")
    result = spinner.run(test_fn)
    assert result == 42


def test_neon_spinner_runs_function_when_disabled(monkeypatch) -> None:
    """NeonSpinner executes function when neon disabled (no spinner shown)."""
    monkeypatch.setenv("DOPETASK_NEON", "0")

    def test_fn() -> str:
        return "result"

    spinner = NeonSpinner(message="Testing...")
    result = spinner.run(test_fn)
    assert result == "result"


def test_neon_spinner_propagates_exceptions(monkeypatch) -> None:
    """NeonSpinner propagates exceptions from wrapped function."""
    monkeypatch.setenv("DOPETASK_NEON", "1")

    def failing_fn() -> None:
        raise ValueError("test error")

    spinner = NeonSpinner(message="This will fail...")
    with pytest.raises(ValueError, match="test error"):
        spinner.run(failing_fn)


# strict_violation Tests


def test_strict_violation_prints_when_enabled(capsys, monkeypatch) -> None:
    """strict_violation prints warning when DOPETASK_STRICT=1."""
    monkeypatch.setenv("DOPETASK_STRICT", "1")

    strict_violation("Test violation message")
    captured = capsys.readouterr()

    assert "STRICT MODE VIOLATION" in captured.out
    assert "Test violation message" in captured.out


def test_strict_violation_silent_when_disabled(capsys, monkeypatch) -> None:
    """strict_violation is silent when DOPETASK_STRICT=0."""
    monkeypatch.setenv("DOPETASK_STRICT", "0")

    strict_violation("This should not appear")
    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


# worship Tests


def test_worship_outputs_when_neon_enabled(capsys, monkeypatch) -> None:
    """worship command outputs formatted text when DOPETASK_NEON=1."""
    monkeypatch.setenv("DOPETASK_NEON", "1")

    worship()
    captured = capsys.readouterr()

    assert "KERNEL WORSHIP ACCEPTED" in captured.out
    assert "Show me the packet." in captured.out
    assert "Leave artifacts. No excuses." in captured.out
    assert "One path. Stay honest." in captured.out
    assert "Refusal is integrity." in captured.out


def test_worship_outputs_plain_when_neon_disabled(capsys, monkeypatch) -> None:
    """worship command outputs plain text when DOPETASK_NEON=0."""
    monkeypatch.setenv("DOPETASK_NEON", "0")

    worship()
    captured = capsys.readouterr()

    # Should print to stdout in plain mode
    assert "KERNEL WORSHIP ACCEPTED" in captured.out
    assert "Show me the packet." in captured.out
    assert "Leave artifacts. No excuses." in captured.out
    assert "One path. Stay honest." in captured.out
    assert "Refusal is integrity." in captured.out


# Programmatic theme validation tests


def test_render_neon_rc_block_rejects_invalid_theme() -> None:
    """Test that render_neon_rc_block validates theme to prevent shell injection."""
    from dopetask.ui import render_neon_rc_block

    # Test shell injection attempt via command substitution
    with pytest.raises(ValueError) as exc_info:
        render_neon_rc_block(theme="evil$(whoami)")
    assert "Unknown theme: 'evil$(whoami)'" in str(exc_info.value)
    assert "Valid themes:" in str(exc_info.value)

    # Test shell injection attempt via semicolon
    with pytest.raises(ValueError) as exc_info:
        render_neon_rc_block(theme="malicious; rm -rf /")
    assert "Unknown theme:" in str(exc_info.value)

    # Verify valid theme works
    block = render_neon_rc_block(theme="mintwave")
    assert 'export DOPETASK_THEME="mintwave"' in block


def test_persist_neon_rc_file_rejects_invalid_theme(tmp_path) -> None:
    """Test that persist_neon_rc_file validates theme to prevent shell injection."""
    from dopetask.ui import persist_neon_rc_file

    rc = tmp_path / "rc"

    # Test shell injection attempt via command substitution
    with pytest.raises(ValueError) as exc_info:
        persist_neon_rc_file(
            path=rc,
            theme="evil$(whoami)",
            remove=False,
            dry_run=True,
        )
    assert "Unknown theme: 'evil$(whoami)'" in str(exc_info.value)
    assert "Valid themes:" in str(exc_info.value)
    assert not rc.exists()  # File should not be created

    # Test shell injection attempt via semicolon
    with pytest.raises(ValueError) as exc_info:
        persist_neon_rc_file(
            path=rc,
            theme="malicious; rm -rf /",
            remove=False,
            dry_run=True,
        )
    assert "Unknown theme:" in str(exc_info.value)
    assert not rc.exists()

    # Verify valid theme works
    result = persist_neon_rc_file(
        path=rc,
        theme="mintwave",
        remove=False,
        dry_run=True,
    )
    assert result.changed
