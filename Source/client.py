from socket import socket, AF_INET, SOCK_STREAM
from threading import Event, Thread
from time import sleep
from argparse import ArgumentParser

from classes.download_manager import ClientDownloadManager
from shared.envs import (
    ADDR,
    MAX_BUF_SIZE,
    ENCODING_FORMAT,
    SEPARATOR,
    CLIENT_REQUEST_INPUT,
)
from shared.constants import STATUS_SIGNAL, DAT_SIGNAL
from shared.command import show_help, get_command
from utils.args import with_gui_arg
from utils.logger import LogType, console_log
from utils.files import render_file_list, extract_download_input


class Client:
    def __init__(self):
        self.interval = 2

        self.download_manager = ClientDownloadManager([])

        self.status: dict[str, tuple[int, bool]] = {}
        self.resources: dict[str, int] = {}

        self.exit_signal = Event()
        self.watch_signal = Event()

        self.client = socket(AF_INET, SOCK_STREAM)

    def send_status_signal(self, signal: str):
        self.client.send(STATUS_SIGNAL[signal].encode(ENCODING_FORMAT))

    def send_dat_signal(self, signal: str):
        self.client.send(DAT_SIGNAL[signal].encode(ENCODING_FORMAT))

    def add_to_download(self, file: tuple[str, int, int]):
        filename, chunk_sz, tot = file
        self.download_manager.add_download(filename, chunk_sz, tot)

    def update_status(self):
        with open(CLIENT_REQUEST_INPUT, "a") as f:
            pass
        with open(CLIENT_REQUEST_INPUT, "r") as f:
            for line in f:
                filename, chunk_sz = extract_download_input(line)
                if filename in self.resources.keys() and filename not in self.status:
                    self.status[filename] = (chunk_sz, False)

    def watch_download_list(self):
        while not self.exit_signal.is_set() and not self.watch_signal.is_set():
            self.update_status()

            download_thread = Thread(target=self.downloads)
            download_thread.start()
            download_thread.join()

            sleep(self.interval)

    def downloads(self):
        try:
            self.client.send("get".encode(ENCODING_FORMAT))

            accepted = self.client.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
            if accepted != STATUS_SIGNAL["accept"]:
                return

            queue = [
                (filename, prior[0])
                for filename, prior in [
                    item for item in self.status.items() if item[1][1] is False
                ]
            ]
            if len(queue):
                print()

            while not self.exit_signal.is_set():
                if len(queue) == 0 or all([prior[1] for prior in self.status.values()]):
                    break

                for filename, chunk_sz in queue:
                    if self.status[filename][1]:
                        continue

                    self.client.send(
                        f"{DAT_SIGNAL['data']}{SEPARATOR}{filename}{SEPARATOR}{chunk_sz}{SEPARATOR}".encode(
                            ENCODING_FORMAT
                        )
                    )

                    data = self.client.recv(chunk_sz)
                    if not data:
                        break

                    if filename not in self.download_manager.download_list:
                        self.download_manager.add_download(
                            filename=filename,
                            chunk_sz=chunk_sz,
                            tot=self.resources[filename],
                            is_overwritten=True,
                        )

                    self.download_manager.download((filename, data))
                    self.status[filename] = (
                        chunk_sz,
                        self.download_manager.download_list[filename].is_done(),
                    )

            self.send_status_signal("success")
            self.client.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
        except Exception as e:
            console_log(LogType.ERR, f"An error occurs when downloading: {e}")

    def fetch_list(self):
        self.client.send("list".encode(ENCODING_FORMAT))

        while len(msg := self.client.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)) > 0:
            if msg in [
                STATUS_SIGNAL["success"],
                STATUS_SIGNAL["terminate"],
                STATUS_SIGNAL["interrupt"],
            ]:
                break

            for line in msg.split("\n"):
                if line == "" or not line:
                    continue

                _, filename, size = line.split(SEPARATOR)[:3]
                self.resources[filename] = int(size)

    def handle_fetch(self):
        self.fetch_list()
        render_file_list([item for item in self.resources.items()])

    def run(self):
        try:
            self.client.connect(ADDR)
            console_log(LogType.INFO, "Connected to the server!")

            self.handle_fetch()
            self.update_status()

            Thread(target=self.watch_download_list, daemon=True).start()

            while not self.exit_signal.is_set():
                cmd_req = input("Enter command: ").strip()
                command = get_command(cmd_req.lower())

                if command == "quit":
                    self.exit_signal.set()
                    break
                elif command == "list":
                    self.handle_fetch()
                elif command == "get":
                    self.downloads()
                elif command == "help":
                    show_help()
                else:
                    console_log(LogType.ERR, "Invalid command!")

        except KeyboardInterrupt:
            console_log(LogType.INFO, f"Client is shutting down...")
        except Exception as e:
            console_log(LogType.ERR, f"An error occurs when running: {e}")
        finally:
            self.exit_signal.set()
            self.watch_signal.set()

            if self.client:
                self.client.send("quit".encode())
                self.client.close()

            console_log(LogType.INFO, f"Client stopped!")


class GUIClient(Client):
    def __init__(self):
        super().__init__()

    def run(self):
        pass


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Socket Client",
        description="A simple socket client for file downloading",
    )
    with_gui_arg(parser)
    args = parser.parse_args()

    use_gui = args.gui
    if use_gui:
        print("--gui detected, using GUI version")
        GUIClient().run()
    else:
        print("--gui not detected, using console version")
        Client().run()
