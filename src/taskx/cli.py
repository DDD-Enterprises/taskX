"""TaskX Ultra-Min CLI - Task Packet Lifecycle Commands Only."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Import pipeline modules (from migrated taskx code)
try:
    from taskx.pipeline.task_compiler.compiler import compile_task_packets
except ImportError:
    compile_task_packets = None

try:
    from taskx.pipeline.task_runner.runner import run_task as run_task_impl
except ImportError:
    run_task_impl = None

try:
    from taskx.pipeline.evidence.collector import collect_evidence as collect_evidence_impl
except ImportError:
    collect_evidence_impl = None

try:
    from taskx.pipeline.compliance.gate import gate_allowlist as gate_allowlist_impl
except ImportError:
    gate_allowlist_impl = None

try:
    from taskx.pipeline.promotion.gate import promote_run as promote_run_impl
except ImportError:
    promote_run_impl = None

try:
    from taskx.pipeline.spec_feedback.feedback import generate_spec_feedback
except ImportError:
    generate_spec_feedback = None

try:
    from taskx.pipeline.loop.orchestrator import run_loop
    LOOP_AVAILABLE = True
except ImportError:
    run_loop = None
    LOOP_AVAILABLE = False


cli = typer.Typer(
    name="taskx",
    help="TaskX - Minimal Task Packet Lifecycle CLI",
    no_args_is_help=True,
)
console = Console()


def _check_repo_guard(bypass: bool) -> Path:
    """
    Check TaskX repo guard unless bypassed.

    Args:
        bypass: If True, skip guard check and warn user

    Returns:
        Path to detected repo root (or cwd if bypassed)

    Raises:
        RuntimeError: If guard check fails and not bypassed
    """
    from taskx.utils.repo import require_taskx_repo_root

    if bypass:
        console.print(
            "[bold yellow]⚠️  WARNING: Repo guard bypassed![/bold yellow]\n"
            "[yellow]Running stateful command without TaskX repo detection.[/yellow]"
        )
        return Path.cwd()

    # Will raise RuntimeError with helpful message if not in TaskX repo
    return require_taskx_repo_root(Path.cwd())


def _require_module(module_func, module_name: str):
    """Check if a required module is available."""
    if module_func is None:
        console.print(f"[bold red]Error:[/bold red] {module_name} module not available in this TaskX build")
        raise typer.Exit(1)


@cli.command()
def compile_tasks(
    mode: str = typer.Option(
        "mvp",
        help="Compilation mode: mvp, hardening, or full",
    ),
    max_packets: Optional[int] = typer.Option(
        None,
        help="Maximum number of task packets to generate",
    ),
    out: Path = typer.Option(
        Path("./out/tasks"),
        help="Output directory for compiled task packets",
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        help="Repository root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Compile task packets from spec documents."""
    _require_module(compile_task_packets, "task_compiler")
    
    console.print("[cyan]Compiling task packets...[/cyan]")
    
    try:
        compile_task_packets(
            mode=mode,
            max_packets=max_packets,
            output_dir=out,
            repo_root=repo_root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Task compilation complete[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@cli.command()
def run_task(
    task_id: str = typer.Option(
        ...,
        help="Task packet ID to execute",
    ),
    task_queue: Path = typer.Option(
        Path("./out/tasks/task_queue.json"),
        help="Path to task queue file",
    ),
    out: Path = typer.Option(
        Path("./out/runs"),
        help="Output directory for run artifacts",
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        help="Repository root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Execute a task packet and capture output."""
    _require_module(run_task_impl, "task_runner")
    
    console.print(f"[cyan]Running task: {task_id}[/cyan]")
    
    try:
        run_task_impl(
            task_id=task_id,
            task_queue_path=task_queue,
            output_dir=out,
            repo_root=repo_root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Task execution complete[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@cli.command()
def collect_evidence(
    run: Path = typer.Option(
        ...,
        help="Path to run directory",
    ),
    max_claims: int = typer.Option(
        100,
        help="Maximum number of claims to extract",
    ),
    max_evidence_chars: int = typer.Option(
        50000,
        help="Maximum characters of evidence to collect",
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        help="Repository root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Collect verification evidence from a task run."""
    _require_module(collect_evidence_impl, "evidence")
    
    console.print("[cyan]Collecting evidence...[/cyan]")
    
    try:
        collect_evidence_impl(
            run_dir=run,
            max_claims=max_claims,
            max_evidence_chars=max_evidence_chars,
            repo_root=repo_root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Evidence collection complete[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@cli.command()
def gate_allowlist(
    run: Path = typer.Option(
        ...,
        help="Path to run directory",
    ),
    diff_mode: str = typer.Option(
        "auto",
        help="Diff detection mode: git, fs, or auto",
    ),
    require_verification_evidence: bool = typer.Option(
        True,
        help="Require verification evidence to pass gate",
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        help="Repository root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
    no_repo_guard: bool = typer.Option(
        False,
        "--no-repo-guard",
        help="Skip TaskX repo detection (use with caution)",
    ),
):
    """Run allowlist compliance gate on a task run."""
    _require_module(gate_allowlist_impl, "compliance")

    # Guard check
    _check_repo_guard(no_repo_guard)

    console.print("[cyan]Running allowlist gate...[/cyan]")
    
    try:
        result = gate_allowlist_impl(
            run_dir=run,
            diff_mode=diff_mode,
            require_verification_evidence=require_verification_evidence,
            repo_root=repo_root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        
        if result["passed"]:
            console.print("[green]✓ Allowlist gate passed[/green]")
            raise typer.Exit(0)
        else:
            console.print("[red]✗ Allowlist gate failed[/red]")
            raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@cli.command()
def promote_run(
    run: Path = typer.Option(
        ...,
        help="Path to run directory",
    ),
    require_run_summary: bool = typer.Option(
        False,
        help="Require RUN_SUMMARY.json to exist",
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        help="Repository root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
    no_repo_guard: bool = typer.Option(
        False,
        "--no-repo-guard",
        help="Skip TaskX repo detection (use with caution)",
    ),
):
    """Promote a task run by issuing completion token."""
    _require_module(promote_run_impl, "promotion")

    # Guard check
    _check_repo_guard(no_repo_guard)

    console.print("[cyan]Promoting run...[/cyan]")
    
    try:
        result = promote_run_impl(
            run_dir=run,
            require_run_summary=require_run_summary,
            repo_root=repo_root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        
        if result["promoted"]:
            console.print("[green]✓ Run promoted successfully[/green]")
            raise typer.Exit(0)
        else:
            console.print("[red]✗ Run promotion failed[/red]")
            raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@cli.command()
def spec_feedback(
    runs: list[Path] = typer.Option(
        ...,
        help="Paths to run directories",
    ),
    task_queue: Path = typer.Option(
        Path("./out/tasks/task_queue.json"),
        help="Path to task queue file",
    ),
    out: Path = typer.Option(
        Path("./out/feedback"),
        help="Output directory for feedback",
    ),
    require_promotion: bool = typer.Option(
        True,
        help="Only include promoted runs in feedback",
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        help="Repository root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Generate spec feedback from completed runs."""
    _require_module(generate_spec_feedback, "spec_feedback")
    
    console.print("[cyan]Generating spec feedback...[/cyan]")
    
    try:
        generate_spec_feedback(
            run_dirs=runs,
            task_queue_path=task_queue,
            output_dir=out,
            require_promotion=require_promotion,
            repo_root=repo_root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Spec feedback generated[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@cli.command()
def loop(
    loop_id: Optional[str] = typer.Option(
        None,
        help="Loop identifier (auto-generated if not provided)",
    ),
    out: Path = typer.Option(
        Path("./out/loops"),
        help="Output directory for loop artifacts",
    ),
    mode: str = typer.Option(
        "mvp",
        help="Loop mode: mvp, hardening, or full",
    ),
    run_task: Optional[str] = typer.Option(
        None,
        help="Specific task ID to run in loop",
    ),
    collect_evidence: bool = typer.Option(
        True,
        help="Collect evidence after task execution",
    ),
    feedback: bool = typer.Option(
        True,
        help="Generate feedback after runs",
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        help="Repository root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Run complete task packet lifecycle loop."""
    if not LOOP_AVAILABLE:
        console.print("[bold red]Error:[/bold red] loop module not installed in this TaskX build")
        raise typer.Exit(1)
    
    _require_module(run_loop, "loop")
    
    console.print("[cyan]Starting task packet loop...[/cyan]")
    
    try:
        run_loop(
            loop_id=loop_id,
            output_dir=out,
            mode=mode,
            task_id=run_task,
            collect_evidence_flag=collect_evidence,
            feedback_flag=feedback,
            repo_root=repo_root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Loop execution complete[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


# ============================================================================
# Dopemux Adapter Commands
# ============================================================================

dopemux_app = typer.Typer(
    name="dopemux",
    help="Dopemux-integrated TaskX commands with automatic path detection",
    no_args_is_help=True,
)
cli.add_typer(dopemux_app, name="dopemux")

# Import dopemux adapter
try:
    from taskx_adapters.dopemux import (
        compute_dopemux_paths,
        detect_dopemux_root,
        select_run_folder,
    )
    DOPEMUX_AVAILABLE = True
except ImportError:
    DOPEMUX_AVAILABLE = False


def _require_dopemux():
    """Check if dopemux adapter is available."""
    if not DOPEMUX_AVAILABLE:
        console.print("[bold red]Error:[/bold red] dopemux adapter not available")
        console.print("Install with: pip install -e .[dopemux]")
        raise typer.Exit(1)


@dopemux_app.command(name="compile")
def dopemux_compile(
    mode: str = typer.Option(
        "mvp",
        help="Compilation mode: mvp, hardening, or full",
    ),
    max_packets: Optional[int] = typer.Option(
        None,
        help="Maximum number of packets to compile",
    ),
    dopemux_root: Optional[Path] = typer.Option(
        None,
        help="Override Dopemux root detection",
    ),
    out_root: Optional[Path] = typer.Option(
        None,
        help="Override output root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Compile task packets with Dopemux path conventions."""
    _require_dopemux()
    _require_module(compile_task_packets, "task_compiler")
    
    # Detect Dopemux root and compute paths
    detection = detect_dopemux_root(override=dopemux_root)
    paths = compute_dopemux_paths(detection.root, out_root_override=out_root)
    
    console.print(f"[cyan]Dopemux root:[/cyan] {detection.root} ({detection.marker_used})")
    console.print(f"[cyan]Task queue output:[/cyan] {paths.task_queue_out}")
    
    # Ensure output directory exists
    paths.task_queue_out.mkdir(parents=True, exist_ok=True)
    
    try:
        compile_task_packets(
            output_dir=paths.task_queue_out,
            mode=mode,
            max_packets=max_packets,
            repo_root=detection.root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print(f"[green]✓ Task packets compiled to {paths.task_queue_out}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@dopemux_app.command(name="run")
def dopemux_run(
    task_id: str = typer.Option(
        ...,
        help="Task packet ID to execute",
    ),
    run_id: Optional[str] = typer.Option(
        None,
        help="Run identifier (auto-generated if not provided)",
    ),
    dopemux_root: Optional[Path] = typer.Option(
        None,
        help="Override Dopemux root detection",
    ),
    out_root: Optional[Path] = typer.Option(
        None,
        help="Override output root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Execute a task packet with Dopemux path conventions."""
    _require_dopemux()
    _require_module(run_task_impl, "task_runner")
    
    # Detect Dopemux root and compute paths
    detection = detect_dopemux_root(override=dopemux_root)
    paths = compute_dopemux_paths(detection.root, out_root_override=out_root)
    
    # Generate run_id if not provided
    if run_id is None:
        from datetime import datetime
        timestamp = "1970-01-01T00-00-00Z" if timestamp_mode == "deterministic" else datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        run_id = f"RUN_{timestamp}_{task_id}"
    
    run_out = paths.runs_out / run_id
    
    console.print(f"[cyan]Dopemux root:[/cyan] {detection.root} ({detection.marker_used})")
    console.print(f"[cyan]Task queue:[/cyan] {paths.task_queue_default}")
    console.print(f"[cyan]Run output:[/cyan] {run_out}")
    
    # Ensure directories exist
    run_out.mkdir(parents=True, exist_ok=True)
    
    try:
        run_task_impl(
            task_id=task_id,
            task_queue=paths.task_queue_default,
            output_dir=run_out,
            repo_root=detection.root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print(f"[green]✓ Task executed: {run_out}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@dopemux_app.command(name="collect")
def dopemux_collect(
    run: Optional[Path] = typer.Option(
        None,
        help="Specific run folder (auto-selects most recent if not provided)",
    ),
    max_claims: int = typer.Option(
        100,
        help="Maximum claims to collect",
    ),
    max_evidence_chars: int = typer.Option(
        50000,
        help="Maximum evidence characters",
    ),
    dopemux_root: Optional[Path] = typer.Option(
        None,
        help="Override Dopemux root detection",
    ),
    out_root: Optional[Path] = typer.Option(
        None,
        help="Override output root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Collect evidence with Dopemux path conventions."""
    _require_dopemux()
    _require_module(collect_evidence_impl, "evidence")
    
    # Detect Dopemux root and compute paths
    detection = detect_dopemux_root(override=dopemux_root)
    paths = compute_dopemux_paths(detection.root, out_root_override=out_root)
    
    # Select run folder
    selected_run = select_run_folder(paths.runs_out, run)
    
    console.print(f"[cyan]Dopemux root:[/cyan] {detection.root} ({detection.marker_used})")
    console.print(f"[cyan]Collecting from:[/cyan] {selected_run}")
    
    try:
        collect_evidence_impl(
            run_dir=selected_run,
            max_claims=max_claims,
            max_evidence_chars=max_evidence_chars,
            repo_root=detection.root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Evidence collected[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@dopemux_app.command(name="gate")
def dopemux_gate(
    run: Optional[Path] = typer.Option(
        None,
        help="Specific run folder (auto-selects most recent if not provided)",
    ),
    diff_mode: str = typer.Option(
        "auto",
        help="Diff mode: git, fs, or auto",
    ),
    require_verification_evidence: bool = typer.Option(
        True,
        help="Require verification evidence",
    ),
    dopemux_root: Optional[Path] = typer.Option(
        None,
        help="Override Dopemux root detection",
    ),
    out_root: Optional[Path] = typer.Option(
        None,
        help="Override output root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Run allowlist gate with Dopemux path conventions."""
    _require_dopemux()
    _require_module(gate_allowlist_impl, "compliance")
    
    # Detect Dopemux root and compute paths
    detection = detect_dopemux_root(override=dopemux_root)
    paths = compute_dopemux_paths(detection.root, out_root_override=out_root)
    
    # Select run folder
    selected_run = select_run_folder(paths.runs_out, run)
    
    console.print(f"[cyan]Dopemux root:[/cyan] {detection.root} ({detection.marker_used})")
    console.print(f"[cyan]Gating run:[/cyan] {selected_run}")
    
    try:
        result = gate_allowlist_impl(
            run_dir=selected_run,
            diff_mode=diff_mode,
            require_verification_evidence=require_verification_evidence,
            repo_root=detection.root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        
        if result.get("passed", False):
            console.print("[green]✓ Gate passed[/green]")
            raise typer.Exit(0)
        else:
            console.print("[red]✗ Gate failed[/red]")
            raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@dopemux_app.command(name="promote")
def dopemux_promote(
    run: Optional[Path] = typer.Option(
        None,
        help="Specific run folder (auto-selects most recent if not provided)",
    ),
    require_run_summary: bool = typer.Option(
        True,
        help="Require run summary for promotion",
    ),
    dopemux_root: Optional[Path] = typer.Option(
        None,
        help="Override Dopemux root detection",
    ),
    out_root: Optional[Path] = typer.Option(
        None,
        help="Override output root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Promote a run with Dopemux path conventions."""
    _require_dopemux()
    _require_module(promote_run_impl, "promotion")
    
    # Detect Dopemux root and compute paths
    detection = detect_dopemux_root(override=dopemux_root)
    paths = compute_dopemux_paths(detection.root, out_root_override=out_root)
    
    # Select run folder
    selected_run = select_run_folder(paths.runs_out, run)
    
    console.print(f"[cyan]Dopemux root:[/cyan] {detection.root} ({detection.marker_used})")
    console.print(f"[cyan]Promoting run:[/cyan] {selected_run}")
    
    try:
        result = promote_run_impl(
            run_dir=selected_run,
            require_run_summary=require_run_summary,
            repo_root=detection.root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        
        if result.get("promoted", False):
            console.print("[green]✓ Run promoted[/green]")
            raise typer.Exit(0)
        else:
            console.print("[red]✗ Promotion denied[/red]")
            raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@dopemux_app.command(name="feedback")
def dopemux_feedback(
    require_promotion: bool = typer.Option(
        True,
        help="Only process promoted runs",
    ),
    dopemux_root: Optional[Path] = typer.Option(
        None,
        help="Override Dopemux root detection",
    ),
    out_root: Optional[Path] = typer.Option(
        None,
        help="Override output root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Generate spec feedback with Dopemux path conventions."""
    _require_dopemux()
    _require_module(generate_spec_feedback, "spec_feedback")
    
    # Detect Dopemux root and compute paths
    detection = detect_dopemux_root(override=dopemux_root)
    paths = compute_dopemux_paths(detection.root, out_root_override=out_root)
    
    console.print(f"[cyan]Dopemux root:[/cyan] {detection.root} ({detection.marker_used})")
    console.print(f"[cyan]Runs directory:[/cyan] {paths.runs_out}")
    console.print(f"[cyan]Task queue:[/cyan] {paths.task_queue_default}")
    console.print(f"[cyan]Feedback output:[/cyan] {paths.spec_feedback_out}")
    
    # Ensure output directory exists
    paths.spec_feedback_out.mkdir(parents=True, exist_ok=True)
    
    try:
        generate_spec_feedback(
            runs_dir=paths.runs_out,
            task_queue=paths.task_queue_default,
            output_dir=paths.spec_feedback_out,
            require_promotion=require_promotion,
            repo_root=detection.root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Spec feedback generated[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@dopemux_app.command(name="loop")
def dopemux_loop(
    loop_id: Optional[str] = typer.Option(
        None,
        help="Loop identifier (auto-generated if not provided)",
    ),
    mode: str = typer.Option(
        "mvp",
        help="Loop mode: mvp, hardening, or full",
    ),
    run_task: Optional[str] = typer.Option(
        None,
        help="Specific task ID to run in loop",
    ),
    collect_evidence: bool = typer.Option(
        True,
        help="Collect evidence after task execution",
    ),
    feedback: bool = typer.Option(
        True,
        help="Generate feedback after runs",
    ),
    dopemux_root: Optional[Path] = typer.Option(
        None,
        help="Override Dopemux root detection",
    ),
    out_root: Optional[Path] = typer.Option(
        None,
        help="Override output root directory",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        help="Project root directory",
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        help="Timestamp mode: deterministic or wallclock",
    ),
):
    """Run complete lifecycle loop with Dopemux path conventions."""
    _require_dopemux()
    
    if not LOOP_AVAILABLE:
        console.print("[bold red]Error:[/bold red] loop module not installed in this TaskX build")
        raise typer.Exit(1)
    
    _require_module(run_loop, "loop")
    
    # Detect Dopemux root and compute paths
    detection = detect_dopemux_root(override=dopemux_root)
    paths = compute_dopemux_paths(detection.root, out_root_override=out_root)
    
    console.print(f"[cyan]Dopemux root:[/cyan] {detection.root} ({detection.marker_used})")
    console.print(f"[cyan]Loop output:[/cyan] {paths.loop_out}")
    
    # Ensure output directory exists
    paths.loop_out.mkdir(parents=True, exist_ok=True)
    
    try:
        run_loop(
            loop_id=loop_id,
            output_dir=paths.loop_out,
            mode=mode,
            task_id=run_task,
            collect_evidence_flag=collect_evidence,
            feedback_flag=feedback,
            repo_root=detection.root,
            project_root=project_root,
            timestamp_mode=timestamp_mode,
        )
        console.print("[green]✓ Loop execution complete[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@cli.command(name="doctor")
def doctor_cmd(
    out: Path = typer.Option(
        Path("./out/taskx_doctor"),
        "--out",
        "-o",
        help="Output directory for doctor reports"
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        "--timestamp-mode",
        help="Timestamp mode: deterministic or wallclock"
    ),
    require_git: bool = typer.Option(
        False,
        "--require-git",
        help="Fail if git is not available"
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        help="Override repository root path"
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        help="Override project root path"
    ),
) -> None:
    """Run installation integrity checks and generate DOCTOR_REPORT.
    
    Validates that TaskX is correctly installed with all required schemas
    bundled and accessible. Useful for diagnosing packaging issues.
    
    Exit codes:
      0 - All checks passed
      2 - One or more checks failed
      1 - Tooling error
    """
    from taskx.doctor import run_doctor
    
    try:
        report = run_doctor(
            out_dir=out,
            timestamp_mode=timestamp_mode,
            require_git=require_git,
            repo_root=repo_root,
            project_root=project_root
        )
        
        # Print summary
        typer.echo(f"\nTaskX Doctor Report")
        typer.echo(f"Status: {report.status.upper()}")
        typer.echo(f"\nChecks:")
        typer.echo(f"  Passed: {report.checks['passed']}")
        typer.echo(f"  Failed: {report.checks['failed']}")
        typer.echo(f"  Warnings: {report.checks['warnings']}")
        typer.echo(f"\nReports written to:")
        typer.echo(f"  {out / 'DOCTOR_REPORT.json'}")
        typer.echo(f"  {out / 'DOCTOR_REPORT.md'}")
        
        # Exit with appropriate code
        if report.status == "failed":
            typer.echo("\n❌ Some checks failed. See report for details.")
            raise typer.Exit(code=2)
        else:
            typer.echo("\n✅ All checks passed.")
            raise typer.Exit(code=0)
    
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"❌ Doctor run failed: {e}", err=True)
        raise typer.Exit(code=1)


@cli.command(name="ci-gate")
def ci_gate_cmd(
    out: Path = typer.Option(
        Path("./out/taskx_ci_gate"),
        "--out",
        "-o",
        help="Output directory for CI gate reports"
    ),
    timestamp_mode: str = typer.Option(
        "deterministic",
        "--timestamp-mode",
        help="Timestamp mode: deterministic or wallclock"
    ),
    require_git: bool = typer.Option(
        False,
        "--require-git",
        help="Fail if git is not available"
    ),
    run: Optional[Path] = typer.Option(
        None,
        "--run",
        help="Specific run directory to validate promotion against"
    ),
    runs_root: Optional[Path] = typer.Option(
        None,
        "--runs-root",
        help="Runs directory to search for latest run"
    ),
    promotion_filename: str = typer.Option(
        "PROMOTION.json",
        "--promotion-filename",
        help="Name of promotion file to validate"
    ),
    require_promotion: bool = typer.Option(
        True,
        "--require-promotion",
        help="Whether to require promotion validation"
    ),
    require_promotion_passed: bool = typer.Option(
        True,
        "--require-promotion-passed",
        help="Whether to require promotion status == 'passed'"
    ),
    no_repo_guard: bool = typer.Option(
        False,
        "--no-repo-guard",
        help="Skip TaskX repo detection (use with caution)",
    ),
) -> None:
    """Run CI gate checks (doctor + promotion validation).

    Combines TaskX installation health checks with run promotion validation
    for use in CI/CD pipelines. Ensures both the environment is sane and
    that runs have valid promotion tokens.

    Exit codes:
      0 - All checks passed
      2 - One or more checks failed (policy violation)
      1 - Tooling error
    """
    from taskx.ci_gate import run_ci_gate

    # Guard check
    _check_repo_guard(no_repo_guard)

    try:
        report = run_ci_gate(
            out_dir=out,
            timestamp_mode=timestamp_mode,
            require_git=require_git,
            run_dir=run,
            runs_root=runs_root,
            promotion_filename=promotion_filename,
            require_promotion=require_promotion,
            require_promotion_passed=require_promotion_passed
        )
        
        # Print summary
        typer.echo(f"\nTaskX CI Gate Report")
        typer.echo(f"Status: {report.status.upper()}")
        typer.echo(f"\nDoctor: {report.doctor['status']}")
        
        if report.promotion["required"]:
            promo_status = "✅ Validated" if report.promotion["validated"] else "❌ Failed"
            typer.echo(f"Promotion: {promo_status}")
            if report.promotion["run_dir"]:
                typer.echo(f"  Run: {report.promotion['run_dir']}")
        else:
            typer.echo("Promotion: Not required")
        
        typer.echo(f"\nChecks:")
        typer.echo(f"  Passed: {report.checks['passed']}")
        typer.echo(f"  Failed: {report.checks['failed']}")
        typer.echo(f"  Warnings: {report.checks['warnings']}")
        
        typer.echo(f"\nReports written to:")
        typer.echo(f"  {out / 'CI_GATE_REPORT.json'}")
        typer.echo(f"  {out / 'CI_GATE_REPORT.md'}")
        
        # Exit with appropriate code
        if report.status == "failed":
            typer.echo("\n❌ CI gate failed.")
            raise typer.Exit(code=2)
        else:
            typer.echo("\n✅ CI gate passed.")
            raise typer.Exit(code=0)
    
    except Exception as e:
        typer.echo(f"❌ CI gate run failed: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    cli()
