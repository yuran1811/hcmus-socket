from rich.layout import Layout
from rich.console import Console
from rich.live import Live

from .rich_table import RichTable
from .rich_progress import RichProgress
from utils.files import convert_file_size


class RichClient:
    def __init__(
        self, *, files: list[tuple[str, int]] = [], table_title: str = "Rich Table"
    ):
        self.layout = Layout()
        self.console = Console(width=120)
        self.live = Live(self.layout, console=self.console, refresh_per_second=6)

        self.layout.split_row(
            Layout(name="download-process", ratio=1), Layout(name="resources", ratio=1)
        )

        self.rich_progress = RichProgress(
            {},
            layout=self.layout["download-process"],
            console=self.console,
            live=self.live,
        )

        self.rich_table = RichTable(
            title=table_title,
            columns={
                "Filename": {
                    "justify": "left",
                    "style": "cyan",
                    "no_wrap": True,
                },
                "Bytes": {"justify": "right", "style": "magenta"},
                "Size": {"justify": "right", "style": "green"},
            },
            rows=[],
            layout=self.layout["resources"],
            console=self.console,
            live=self.live,
        )

        self.live.start(refresh=self.live._renderable is not None)
        self.rich_table.update_layout()
        self.rich_progress.update_layout()

        self.render_file_list(files)

    def convert_to_row(self, files: list[tuple[str, int]]):
        return [[file, str(size), convert_file_size(size)] for file, size in files]

    def render_file_list(self, files: list[tuple[str, int]]):
        __files = self.convert_to_row(files)
        self.rich_table.overwrite_rows(__files)
        self.rich_table.update_layout()
