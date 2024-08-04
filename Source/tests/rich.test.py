from sys import path
from threading import Thread
from time import sleep

path.append("..")


from classes import RichProgress, RichTable, Layout, Console, Live


if __name__ == "__main__":
    layout = Layout()
    console = Console(width=160)
    live = Live(layout, refresh_per_second=6, console=console)

    layout.split_row(
        Layout(name="progress", ratio=1), Layout(name="resources", ratio=1)
    )

    columns = {
        "Released": {
            "justify": "center",
            "style": "cyan",
            "no_wrap": True,
        },
        "Title": {"justify": "left", "style": "magenta"},
        "Box Office": {"justify": "right", "style": "green"},
    }
    rows = [
        ["Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$952,110,690"],
        ["May 25, 2018", "Solo: A Star Wars Story", "$393,151,347"],
        ["Dec 15, 2017", "Star Wars Ep. V111: The Last Jedi", "$1,332,539,889"],
        ["Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,332,439"],
    ]

    rich_table = RichTable(
        columns=columns,
        rows=[],
        layout=layout["resources"],
        console=console,
        live=live,
    )
    rich_table.overwrite_rows(rows)
    rich_table.layout_render()

    rich_progress = RichProgress(
        {"file1": (3, 65), "file2": (2, 41), "file3": (4, 100)},
        layout=layout["progress"],
        console=console,
        live=live,
    )

    def progress_thread_action():
        render = rich_progress.display_progress_with_title()
        try:
            while True:
                next(render)
                sleep(0.1)
        except StopIteration:
            pass

    def table_thread_action():
        try:
            while not rich_progress.is_stop:
                if len(rich_table.table.rows) < 12:
                    rich_table.add_new_row(
                        [
                            "Dec 20, 2019",
                            "Star Wars: The Rise of Skywalker",
                            "$952,110,690",
                        ]
                    )

                if len(rich_table.table.rows) > 4:
                    rich_table.overwrite_rows(
                        [
                            [
                                "Dec 20, 2019",
                                "Star Wars: The Rise of Skywalker",
                                "$952,110,690",
                            ]
                        ]
                    )
                rich_table.layout_render()
                sleep(0.1)
        except StopIteration:
            pass

    threads = [
        Thread(target=progress_thread_action),
        Thread(target=table_thread_action),
    ]

    try:
        live.start(refresh=live._renderable is not None)

        for thread in threads:
            thread.start()

        sleep(4)
        flag = False
        while not flag:
            rich_progress.add_task("file4", 6, 57)
            flag = True
            sleep(3)
            rich_progress.stop()
    except KeyboardInterrupt:
        rich_progress.stop()
        print("Download has been stopped.")
    finally:
        live.stop()
        for thread in threads:
            thread.join()
        print("Download has been completed.")
