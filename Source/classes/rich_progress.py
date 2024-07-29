from rich.align import Align
from rich.spinner import Spinner
from rich.layout import Layout
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.progress import (
    Task,
    TaskID,
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


class ReverseProgress(Progress):
    def get_renderables(self):
        yield self.make_tasks_table(self.tasks[::-1])


class RichProgress:
    def __init__(
        self,
        initial_tasks: dict[str, tuple[int, int]] = {},
        *,
        layout: Layout = None,
        console: Console = None,
        live: Live = None,
    ):
        self.is_stop = False
        self.tasks: list[TaskID] = []
        self.task_map: dict[int, tuple[str, int, int]] = {}

        self.layout = Layout() if not layout else layout
        self.console = Console(width=80) if not console else console
        self.live = (
            Live(self.layout, refresh_per_second=10, console=self.console)
            if not live
            else live
        )

        self.progress = ReverseProgress(
            TextColumn("[bold blue]{task.fields[task_name]}"),
            BarColumn(bar_width=35),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            "•",
            TextColumn("[bold blue]{task.completed}/{task.total}"),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
        )

        self.config_layout()
        self.map_tasks(initial_tasks)

    def stop(self):
        self.is_stop = True

    def config_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )

    def map_tasks(self, tasks: dict[str, tuple[int, int]] = {}):
        for task_name, info in tasks.items():
            self.add_task(task_name, info[0], info[1])

    def map_task_id(self, task_id: TaskID, task_map: tuple[str, int, int]):
        self.task_map[task_id] = task_map

    def add_task(self, task_name: str, chunk: int, total: int):
        t = self.progress.add_task("", task_name=task_name, total=total)

        self.map_task_id(t, (task_name, chunk, total))
        self.tasks.append(t)

    def get_download_status(self):
        return self.progress.finished

    def get_panel_height(self):
        task_count = len(self.progress.tasks)
        return task_count + 2

    def update_header(self):
        self.layout["header"].update(
            Align.center(
                (
                    Spinner(
                        "dots",
                        text=("[bold blue]Downloading files..."),
                    )
                    if not self.get_download_status()
                    else "[bold green]Download complete!"
                ),
                vertical="middle",
            )
        )

    def update_panel(self):
        self.layout["main"].update(
            Panel.fit(
                self.progress,
                title="[bold yellow]Task Progress",
                height=self.get_panel_height(),
            )
        )

    def update_footer(self):
        self.layout["footer"].update(
            Align.center(
                (
                    Spinner("dots", text="[bold green]Watching files...")
                    if not self.is_stop
                    else "[bold blue]Stopped watching."
                ),
                vertical="middle",
            )
        )

    def update_task_prog(self, task_id: TaskID):
        task: Task = self.progress.tasks[task_id]
        increment = self.task_map[task_id][1]

        if not task.finished:
            remaining = task.total - task.completed
            increment = min(increment, remaining)
            self.progress.update(task_id, advance=increment)

    def display_progress_with_title(self):
        self.update_header()
        self.update_panel()
        self.update_footer()

        while True:
            for task_id in self.tasks:
                self.update_task_prog(task_id)

            self.update_header()
            self.update_panel()
            self.update_footer()

            if self.is_stop:
                break

            yield "continue"

        yield "stop"
