#!/usr/bin/env python3
"""Main entry point for the autonomous browser agent."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from src.task_parser import TaskLoader
from src.agent import AutonomousAgent
from src.scheduler import TaskScheduler
from src.config import config

app = typer.Typer(help="Autonomous Browser Agent for Web Research")
console = Console()


@app.command()
def run(
    task_id: str = typer.Argument(..., help="Task ID (filename without .md extension)"),
    tasks_dir: str = typer.Option("./tasks", help="Directory containing task files"),
):
    """Execute a single task."""
    console.print(f"\n[bold blue]Loading task:[/bold blue] {task_id}")

    try:
        # Load task
        loader = TaskLoader(Path(tasks_dir))
        task = loader.load_task(task_id)

        console.print(f"[green]✓[/green] Task loaded: {task.metadata.title}")
        console.print(f"  Output: {task.metadata.output_type}")
        if task.metadata.attachments:
            console.print(f"  Attachments: {', '.join(task.metadata.attachments)}")

        # Execute task
        console.print("\n[bold yellow]Executing task...[/bold yellow]\n")

        agent = AutonomousAgent()
        result = asyncio.run(agent.execute_task(task))

        # Display results
        console.print("\n[bold]Results:[/bold]")
        console.print(f"  Success: {'✓' if result.success else '✗'}")
        console.print(f"  Results Count: {result.results_count}")
        console.print(f"  Storage: {', '.join(result.storage_locations)}")

        console.print(f"\n[bold]Summary:[/bold]")
        console.print(result.summary)

        if result.errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in result.errors:
                console.print(f"  • {error}")

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Task file not found: {task_id}.md")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def list_tasks(
    tasks_dir: str = typer.Option("./tasks", help="Directory containing task files"),
    show_recurring: bool = typer.Option(False, "--recurring", "-r", help="Show only recurring tasks"),
):
    """List all available tasks."""
    loader = TaskLoader(Path(tasks_dir))

    if show_recurring:
        tasks = loader.get_recurring_tasks()
        console.print("\n[bold]Recurring Tasks:[/bold]")
    else:
        tasks = loader.load_all_tasks()
        console.print("\n[bold]All Tasks:[/bold]")

    if not tasks:
        console.print("  No tasks found.")
        return

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Output")
    table.add_column("Schedule", justify="center")

    for task in tasks:
        schedule = task.metadata.recurring or task.metadata.cron or "-"
        table.add_row(
            task.id,
            task.metadata.title,
            task.metadata.output_type,
            schedule,
        )

    console.print(table)
    console.print(f"\nTotal: {len(tasks)} tasks\n")


@app.command()
def schedule(
    tasks_dir: str = typer.Option("./tasks", help="Directory containing task files"),
):
    """Start the task scheduler for recurring tasks."""
    console.print("\n[bold blue]Starting Task Scheduler[/bold blue]\n")

    scheduler = TaskScheduler(tasks_dir)
    scheduler.load_and_schedule_all()
    scheduler.list_jobs()

    console.print("\n[bold green]Scheduler is running. Press Ctrl+C to stop.[/bold green]\n")

    try:
        asyncio.run(scheduler.run_forever())
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler stopped.[/yellow]")


@app.command()
def init():
    """Initialize a new project with example files."""
    console.print("\n[bold blue]Initializing Autonomous Browser Agent[/bold blue]\n")

    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        console.print("[yellow]Creating .env file from template...[/yellow]")
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            console.print("[green]✓[/green] Created .env file")
            console.print("[bold yellow]⚠ Please edit .env and add your API keys![/bold yellow]")
        else:
            console.print("[red]✗[/red] .env.example not found")

    # Create directories
    Path("./tasks/attachments").mkdir(parents=True, exist_ok=True)
    Path("./data").mkdir(parents=True, exist_ok=True)
    console.print("[green]✓[/green] Created directories")

    # Install playwright
    console.print("\n[yellow]Installing Playwright browsers...[/yellow]")
    console.print("Run: python -m playwright install chromium")

    console.print("\n[bold green]✓ Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Edit .env and add your API keys")
    console.print("  2. Install Playwright: python -m playwright install chromium")
    console.print("  3. Create task files in ./tasks/")
    console.print("  4. Run a task: python main.py run <task_id>")


@app.command()
def config_info():
    """Show current configuration."""
    console.print("\n[bold]Current Configuration:[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="dim")
    table.add_column("Value")
    table.add_column("Status", justify="center")

    def check_status(value):
        return "[green]✓[/green]" if value else "[red]✗[/red]"

    table.add_row("AI Model", config.ai_model, "✓")
    table.add_row("OpenAI API Key", "***" if config.openai_api_key else "Not set",
                  check_status(config.openai_api_key))
    table.add_row("Google API Key", "***" if config.google_api_key else "Not set",
                  check_status(config.google_api_key))
    table.add_row("Brave API Key", "***" if config.brave_api_key else "Not set",
                  check_status(config.brave_api_key))
    table.add_row("Google Sheets", "Configured" if config.google_service_account_json or
                  config.google_service_account_path else "Not configured",
                  check_status(config.google_service_account_json or config.google_service_account_path))
    table.add_row("SQLite DB", str(config.sqlite_db_path), "✓")
    table.add_row("FAISS Index", str(config.faiss_index_path), "✓")

    console.print(table)
    console.print()


@app.command()
def query_results(
    task_id: str = typer.Option(None, help="Filter by task ID"),
    table_name: str = typer.Option(None, help="Filter by table name"),
    limit: int = typer.Option(10, help="Number of results to show"),
):
    """Query results from SQLite database."""
    from src.storage.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(config.sqlite_db_path)
    results = storage.get_results(task_id=task_id, table_name=table_name, limit=limit)

    if not results:
        console.print("\n[yellow]No results found.[/yellow]\n")
        return

    console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")

    for i, result in enumerate(results, 1):
        console.print(f"[bold cyan]{i}.[/bold cyan] Task: {result.get('_task_id', 'N/A')}")
        console.print(f"    Created: {result.get('_created_at', 'N/A')}")

        # Show result data
        for key, value in result.items():
            if not key.startswith('_'):
                console.print(f"    {key}: {value}")

        console.print()


if __name__ == "__main__":
    app()
