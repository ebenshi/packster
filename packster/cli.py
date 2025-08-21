"""Command-line interface for Packster."""

import logging
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from .detect import detect_os, is_ubuntu_or_debian, get_environment_info
from .normalize import normalize_all_packages, get_package_statistics
from .map import load_registry, map_packages, get_mapping_statistics
from .emit import (
    write_brewfile,
    write_language_files,
    write_bootstrap_script,
    write_reports,
)
# Cloud functionality removed - focusing on core migration features
from .llm import ClaudeMigrator
from .types import Report, Decision
from .config import DEFAULT_REGISTRY_PATH, CONSOLE_STYLES

# Create Typer app
app = typer.Typer(
    name="packster",
    help="Cross-OS package migration helper (Ubuntu/WSL → macOS)",
    add_completion=False,
)

# Add commands property for testing
@property
def commands(self):
    """Get available commands for testing."""
    return ["generate", "llm_migrate", "info", "version"]

app.commands = commands.__get__(app)

# Create console for rich output
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)]
    )


def print_banner() -> None:
    """Print the Packster banner."""
    banner = Text("Packster", style="bold cyan")
    subtitle = Text("Cross-OS package migration helper", style="dim")
    
    panel = Panel(
        f"{banner}\n{subtitle}",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)


def print_system_info() -> None:
    """Print system information."""
    env_info = get_environment_info()
    
    table = Table(title="System Information", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    system = env_info["system"]
    table.add_row("OS", system["os"])
    table.add_row("Architecture", system["architecture"])
    table.add_row("WSL", system["wsl"])
    table.add_row("Python Version", system["python_version"])
    
    console.print(table)


def print_package_stats(packages) -> None:
    """Print package collection statistics.
    
    Args:
        packages: List of normalized packages
    """
    stats = get_package_statistics(packages)
    
    table = Table(title="Package Collection Summary", show_header=True, header_style="bold magenta")
    table.add_column("Package Manager", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    for pm, count in stats["by_package_manager"].items():
        table.add_row(pm.upper(), str(count))
    
    table.add_row("Total", str(stats["total"]), style="bold")
    
    console.print(table)


def print_mapping_stats(results) -> None:
    """Print mapping statistics.
    
    Args:
        results: List of mapping results
    """
    stats = get_mapping_statistics(results)
    
    table = Table(title="Mapping Results", show_header=True, header_style="bold magenta")
    table.add_column("Decision", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Percentage", style="yellow", justify="right")
    
    total = stats["total"]
    if total > 0:
        table.add_row("Auto", str(stats["auto"]), f"{(stats['auto']/total)*100:.1f}%")
        table.add_row("Verify", str(stats["verify"]), f"{(stats['verify']/total)*100:.1f}%")
        table.add_row("Manual", str(stats["manual"]), f"{(stats['manual']/total)*100:.1f}%")
        table.add_row("Skipped", str(stats["skipped"]), f"{(stats['skipped']/total)*100:.1f}%")
        table.add_row("Total", str(total), "100.0%", style="bold")
    
    console.print(table)


# Expose helper used by tests for patching
def collect_all_packages():
    return normalize_all_packages()


@app.command()
def generate(
    target: str = typer.Option("macos", "--target", "-t", help="Target platform"),
    out: Path = typer.Option(Path("./packster-out"), "--out", "-o", "--output-dir", help="Output directory"),
    registry: Optional[Path] = typer.Option(None, "--registry", "-r", help="Custom registry file"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip Homebrew validation"),
    format_type: str = typer.Option("json", "--format", "-f", help="Report format (json/yaml)"),
    llm_migrate: bool = typer.Option(False, "--llm-migrate", "-l", help="Automatically run LLM migration after generation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Claude API key (required if --llm-migrate is used)"),
    llm_batch_size: int = typer.Option(50, "--llm-batch-size", help="Number of packages to process per batch in LLM migration"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
         # Cloud upload options removed - focusing on core migration features
) -> None:
    """Generate migration files for the target platform."""
    setup_logging(verbose)
    
    # Print banner
    print_banner()
    
    # Check target platform
    if target.lower() != "macos":
        console.print(f"[yellow]Warning: Target '{target}' is not yet fully supported. Using macOS defaults.[/yellow]")
    
    # Check source OS
    source_os = detect_os()
    if not is_ubuntu_or_debian():
        console.print(f"[yellow]Warning: Source OS '{source_os}' is not Ubuntu/Debian. Some features may not work correctly.[/yellow]")
    
    # Print system info
    print_system_info()
    
    # Create output directory
    try:
        out.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Output directory: {out.absolute()}[/green]")
    except Exception as e:
        console.print(f"[red]Error: Cannot create output directory: {e}[/red]")
        sys.exit(1)
    
    # Load registry
    registry_path = registry or DEFAULT_REGISTRY_PATH
    if not registry_path.exists():
        console.print(f"[red]Error: Registry file not found: {registry_path}[/red]")
        sys.exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load registry
        task = progress.add_task("Loading registry...", total=None)
        try:
            registry_data = load_registry(registry_path)
            progress.update(task, description=f"Loaded registry with {len(registry_data.mappings)} mappings")
        except Exception as e:
            console.print(f"[red]Error loading registry: {e}[/red]")
            sys.exit(1)
        
        # Collect packages
        task = progress.add_task("Collecting packages...", total=None)
        try:
            packages = normalize_all_packages()
            progress.update(task, description=f"Collected {len(packages)} packages")
        except Exception as e:
            console.print(f"[red]Error collecting packages: {e}[/red]")
            sys.exit(1)
        
        # Map packages
        task = progress.add_task("Mapping packages...", total=None)
        try:
            mapping_results = map_packages(packages, registry_data, verify=not no_verify)
            progress.update(task, description=f"Mapped {len(mapping_results)} packages")
        except Exception as e:
            console.print(f"[red]Error mapping packages: {e}[/red]")
            sys.exit(1)
        
        # Generate output files
        task = progress.add_task("Generating output files...", total=None)
        try:
            # Write Brewfile
            brewfile_path = out / "Brewfile"
            write_brewfile(mapping_results, brewfile_path)
            
            # Write language files
            language_files = write_language_files(packages, out)
            
            # Write bootstrap script
            has_python = any(p.source_pm.value == "pip" for p in packages)
            has_npm = any(p.source_pm.value == "npm" for p in packages)
            has_cargo = any(p.source_pm.value == "cargo" for p in packages)
            has_gem = any(p.source_pm.value == "gem" for p in packages)
            
            bootstrap_path = out / "bootstrap.sh"
            write_bootstrap_script(
                bootstrap_path,
                has_python_packages=has_python,
                has_npm_packages=has_npm,
                has_cargo_packages=has_cargo,
                has_gem_packages=has_gem
            )
            
            # Create report
            report = Report(
                mapped_auto=[r for r in mapping_results if r.decision == Decision.AUTO],
                mapped_verify=[r for r in mapping_results if r.decision == Decision.VERIFY],
                manual=[r for r in mapping_results if r.decision == Decision.MANUAL],
                skipped=[r for r in mapping_results if r.decision == Decision.SKIP],
            )
            
            # Write reports
            write_reports(report, out, format_type)
            
            progress.update(task, description="Generated all output files")
        except Exception as e:
            console.print(f"[red]Error generating output files: {e}[/red]")
            sys.exit(1)
        
        # Cloud upload functionality removed - focusing on core migration features
    
    # Print statistics
    console.print("\n[bold cyan]Package Collection Summary:[/bold cyan]")
    print_package_stats(packages)
    
    console.print("\n[bold cyan]Mapping Results:[/bold cyan]")
    print_mapping_stats(mapping_results)
    
    # Print output summary
    console.print(f"\n[bold green]Migration completed![/bold green]")
    console.print(f"Output directory: {out.absolute()}")
    console.print("\n[bold]Generated files:[/bold]")
    
    files_table = Table(show_header=False)
    files_table.add_column("File", style="cyan")
    files_table.add_column("Description", style="green")
    
    files_table.add_row("Brewfile", "Homebrew packages and casks")
    files_table.add_row("bootstrap.sh", "Automated installation script")
    files_table.add_row("report.json", "Detailed migration report (JSON)")
    files_table.add_row("report.html", "Detailed migration report (HTML)")
    
    if language_files:
        files_table.add_row("lang/requirements.txt", "Python packages")
        files_table.add_row("lang/global-node.txt", "Node.js global packages")
        files_table.add_row("lang/cargo.txt", "Rust packages")
        files_table.add_row("lang/gems.txt", "Ruby gems")
    
    console.print(files_table)
    
    # Handle LLM migration if requested
    if llm_migrate:
        if not api_key:
            console.print(f"\n[red]❌ API key required for LLM migration[/red]")
            console.print(f"[yellow]💡 Use --api-key or run 'packster llm-migrate' separately[/yellow]")
        else:
            console.print(f"\n[bold cyan]🤖 Starting LLM-powered migration...[/bold cyan]")
            
            try:
                # Initialize Claude migrator
                migrator = ClaudeMigrator(api_key)
                
                # Convert MappingResult objects to dictionaries for LLM migration
                packages_for_llm = []
                for result in mapping_results:
                    package_dict = {
                        "source": {
                            "source_pm": result.source.source_pm.value,
                            "source_name": result.source.source_name,
                            "source_version": result.source.version
                        },
                        "candidate": {
                            "target_pm": result.candidate.target_pm if result.candidate else None,
                            "target_name": result.candidate.target_name if result.candidate else None,
                            "target_version": None  # Candidate doesn't have version field
                        },
                        "decision": result.decision.value,
                        "notes": result.notes
                    }
                    packages_for_llm.append(package_dict)
                
                # Perform LLM migration
                with console.status(f"[bold green]🤖 Analyzing {len(packages_for_llm)} packages with Claude AI...", spinner="dots"):
                    llm_results = migrator.migrate_packages(packages_for_llm, out, "llm-migration", llm_batch_size)
                
                if llm_results["success"]:
                    llm_summary = llm_results["summary"]
                    console.print(f"\n[bold green]✅ LLM Migration completed![/bold green]")
                    console.print(f"[green]📊 LLM Summary:[/green]")
                    console.print(f"  • Installable: {llm_summary['installable_count']}")
                    console.print(f"  • Unavailable: {llm_summary['unavailable_count']}")
                    console.print(f"  • Success rate: {llm_summary['success_rate']:.1f}%")
                    
                    # Show LLM-generated files
                    if llm_results["saved_files"]:
                        console.print(f"\n[green]🤖 LLM-generated files:[/green]")
                        for file_type, file_path in llm_results["saved_files"].items():
                            console.print(f"  • {file_type}: {file_path}")
                    
                    # Show the LLM installation script
                    if "installation_script" in llm_results["saved_files"]:
                        script_path = llm_results["saved_files"]["installation_script"]
                        console.print(f"\n[bold]🚀 AI-generated installation script:[/bold]")
                        console.print(f"[code]{script_path}[/code]")
                        console.print(f"[dim]Copy this script to your Mac and run: chmod +x {script_path.name} && ./{script_path.name}[/dim]")
                else:
                    console.print(f"\n[red]❌ LLM migration failed: {llm_results['error']}[/red]")
                    
            except Exception as e:
                console.print(f"\n[red]❌ LLM migration error: {e}[/red]")
    
    # Print next steps
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"1. Review the generated files")
    console.print(f"2. Run: cd {out} && ./bootstrap.sh")
    console.print(f"3. Check report.html for detailed information")
    
    if llm_migrate and api_key:
        console.print(f"4. Use the AI-generated installation script for macOS migration")
    else:
        console.print(f"\n[dim]💡 Tip: Use 'packster generate --llm-migrate --api-key YOUR_KEY' for AI-powered migration[/dim]")


@app.command()
def llm_migrate(
    api_key: str = typer.Option(..., "--api-key", "-k", help="Claude API key"),
    report_path: Path = typer.Option("./packster-out/report.json", "--report", "-r", help="Path to report.json file"),
    output: Path = typer.Option("./packster-out", "--output", "-o", help="Output directory for migration files"),
    model: str = typer.Option("claude-3-5-sonnet-20241022", "--model", "-m", help="Claude model to use"),
    batch_size: int = typer.Option(50, "--batch-size", "-b", help="Number of packages to process per batch"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Generate macOS installation commands using Claude AI."""
    setup_logging(verbose)
    print_banner()
    
    console.print("[bold cyan]🤖 LLM-Powered Package Migration[/bold cyan]")
    console.print("[dim]Using Claude AI to intelligently map packages to macOS[/dim]\n")
    
    # Check if report file exists
    if not report_path.exists():
        console.print(f"[red]❌ Report file not found: {report_path}[/red]")
        console.print("[yellow]💡 Run 'packster generate' first to create a report[/yellow]")
        raise typer.Exit(1)
    
    # Load the report
    try:
        import json
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Extract packages from the report
        packages = report_data.get("mapping_results", [])
        if not packages:
            console.print("[red]❌ No packages found in report[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]📦 Found {len(packages)} packages to analyze[/green]\n")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to load report: {e}[/red]")
        raise typer.Exit(1)
    
    # Initialize Claude migrator
    try:
        migrator = ClaudeMigrator(api_key, model)
        console.print(f"[green]✅ Connected to Claude AI (model: {model})[/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize Claude migrator: {e}[/red]")
        raise typer.Exit(1)
    
    # Perform migration
    with console.status(f"[bold green]🤖 Analyzing {len(packages)} packages with Claude AI (batch size: {batch_size})...", spinner="dots"):
        results = migrator.migrate_packages(packages, output, "llm-migration", batch_size)
    
    if not results["success"]:
        console.print(f"[red]❌ Migration failed: {results['error']}[/red]")
        raise typer.Exit(1)
    
    # Display results
    summary = results["summary"]
    console.print(f"\n[bold green]✅ Migration completed successfully![/bold green]")
    console.print(f"[green]📊 Summary:[/green]")
    console.print(f"  • Total packages: {summary['total_packages']}")
    console.print(f"  • Installable: {summary['installable_count']}")
    console.print(f"  • Unavailable: {summary['unavailable_count']}")
    console.print(f"  • Success rate: {summary['success_rate']:.1f}%")
    
    # Show installation methods
    if summary.get("installation_methods"):
        console.print(f"\n[green]📦 Installation methods:[/green]")
        for method, count in summary["installation_methods"].items():
            console.print(f"  • {method}: {count} packages")
    
    # Show saved files
    if results["saved_files"]:
        console.print(f"\n[green]📁 Generated files:[/green]")
        for file_type, file_path in results["saved_files"].items():
            console.print(f"  • {file_type}: {file_path}")
    
    # Show the installation script
    if "installation_script" in results["saved_files"]:
        script_path = results["saved_files"]["installation_script"]
        console.print(f"\n[bold]🚀 Ready-to-run installation script:[/bold]")
        console.print(f"[code]{script_path}[/code]")
        console.print(f"[dim]Copy this script to your Mac and run: chmod +x {script_path.name} && ./{script_path.name}[/dim]")
    
    # Show unavailable packages report
    if "unavailable_report" in results["saved_files"]:
        report_path = results["saved_files"]["unavailable_report"]
        console.print(f"\n[bold]📋 Unavailable packages report:[/bold]")
        console.print(f"[code]{report_path}[/code]")
        console.print(f"[dim]Review this file for packages that couldn't be migrated[/dim]")
    
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"1. Copy the installation script to your Mac")
    console.print(f"2. Make it executable: chmod +x {script_path.name if 'installation_script' in results['saved_files'] else 'script.sh'}")
    console.print(f"3. Run it: ./{script_path.name if 'installation_script' in results['saved_files'] else 'script.sh'}")
    console.print(f"4. Review the unavailable packages report for manual steps")


@app.command()
def info() -> None:
    """Show system information and available package managers."""
    print_banner()
    print_system_info()
    
    # Check package manager availability
    from .detect import check_package_manager_availability
    
    availability = check_package_manager_availability()
    
    table = Table(title="Package Manager Availability", show_header=True, header_style="bold magenta")
    table.add_column("Package Manager", style="cyan")
    table.add_column("Available", style="green")
    
    for pm, available in availability.items():
        status = "✓" if available else "✗"
        style = "green" if available else "red"
        table.add_row(pm.upper(), f"[{style}]{status}[/{style}]")
    
    console.print(table)


@app.command()
def version() -> None:
    """Show Packster version."""
    from . import __version__
    console.print(f"Packster version {__version__}")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
