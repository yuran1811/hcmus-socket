from time import sleep

from rich.table import Table
from rich.layout import Layout
from rich.console import Console
from rich.live import Live


class RichTable:
    def __init__(
        self,
        *,
        layout: Layout = None,
        console: Console = None,
        live: Live = None,
        title: str = "Rich Table",
        columns: dict[str, dict] = {},
        rows: list[list[str]] = [],
    ):
        self.layout = Layout() if not layout else layout
        self.console = Console(width=80) if not console else console
        self.live = (
            Live(self.layout, refresh_per_second=10, console=self.console)
            if not live
            else live
        )

        self.table_cols = columns
        self.table_rows = rows

        self.table: Table = None
        self.create_table()

    def create_table(self, title: str = "Rich Table"):
        self.table = Table(title=title)
        self.config_table(columns=self.table_cols, rows=self.table_rows)

    def config_table(
        self, *, columns: dict[str, dict] = {}, rows: list[list[str]] = []
    ):
        for column in columns:
            self.table.add_column(column, **columns[column])
        for row in rows:
            self.add_new_row(row)

    def overwrite_rows(self, rows: list[list[str]] = []):
        self.table_rows = rows
        self.create_table()

    def add_new_row(self, row: list[str] = []):
        self.table.add_row(*row)

    def console_render(self):
        self.console.print(self.table if self.table.columns else "No data to display.")

    def layout_render(self):
        self.layout.update(self.table if self.table.columns else "No data to display.")
