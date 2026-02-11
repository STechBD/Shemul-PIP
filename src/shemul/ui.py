from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class UI:
    def __init__(self) -> None:
        self.console = Console()

    def error(self, message: str) -> None:
        self.console.print(f"[red]ERROR: {message}[/red]")

    def warn(self, message: str) -> None:
        self.console.print(f"[yellow]WARN: {message}[/yellow]")

    def info(self, message: str) -> None:
        self.console.print(f"[cyan]INFO: {message}[/cyan]")

    def success(self, message: str) -> None:
        self.console.print(f"[green]OK: {message}[/green]")

    def table(self, title: str, columns: list[str], rows: list[list[str]]) -> None:
        table = Table(title=title, show_lines=False)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*row)
        self.console.print(table)

    def panel(self, title: str, body: str) -> None:
        self.console.print(Panel(Text(body), title=title))
