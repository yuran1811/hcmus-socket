from watchdog.events import FileSystemEventHandler


class MonitorFileSystemHandler(FileSystemEventHandler):
    def __init__(self, updater) -> None:
        super().__init__()

        self.updater = updater

    def on_modified(self, event):
        self.updater(path=event.src_path, event_type="modified")

    def on_created(self, event):
        self.updater(path=event.src_path, event_type="created")

    def on_deleted(self, event):
        self.updater(path=event.src_path, event_type="deleted")

    def on_moved(self, event):
        self.updater(path=event.src_path, event_type="moved")
