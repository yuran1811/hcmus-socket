import time, os, threading
from watchdog.observers import Observer

from classes.monitor_filesys import MonitorFileSystemHandler
from shared.envs import SERVER_RESOURCES_PATH
from .files import update_resources_data
from .logger import console_log, LogType


def update_resource_list(path: str, event_type: str):
    console_log(LogType.INFO, f"[{event_type}]: {path}")
    console_log(LogType.INFO, "Updating resources data")
    update_resources_data()
    console_log(LogType.OK, "Resources data updated successfully!")


def start_watching(path=SERVER_RESOURCES_PATH, exit_signal: threading.Event = None):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

        console_log(LogType.ERR, f"Path {path} does not exist")
        console_log(LogType.INFO, f"Created {path}!")

    update_resources_data()
    console_log(LogType.INFO, f'Watching changes from "{path}"')

    event_handler = MonitorFileSystemHandler(updater=update_resource_list)

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        if exit_signal is not None:
            while not exit_signal.is_set():
                time.sleep(2.5)
        else:
            while True:
                time.sleep(2.5)
    finally:
        console_log(LogType.INFO, "Observer stopped!")
        observer.stop()
        observer.join()
