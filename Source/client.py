from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
from threading import Event, Thread
from time import sleep

from classes import ClientDownloadManager
from shared.envs import (
    ADDR,
    MAX_BUF_SIZE,
    ENCODING_FORMAT,
    SEPARATOR,
    CLIENT_REQUEST_INPUT,
)
from shared.constants import STATUS_SIGNAL, DAT_SIGNAL
from shared.command import show_help, get_command
from utils.logger import LogType, console_log
from utils.files import render_file_list, extract_download_input
from utils.args import *
from utils.gui import *


class Client:
    def __init__(self):
        self.interval = 1

        self.download_manager = ClientDownloadManager([])

        self.status: dict[str, tuple[int, bool]] = {}
        self.resources: dict[str, int] = {}

        self.exit_signal = Event()
        self.watch_signal = Event()
        self.is_shutdown = False

        self.watch_thread = Thread(target=self.watch_download_list, daemon=False)

        self.client = socket(AF_INET, SOCK_STREAM)

    def send_status_signal(self, signal: str):
        self.client.send(STATUS_SIGNAL[signal].encode(ENCODING_FORMAT))

    def send_dat_signal(self, signal: str):
        self.client.send(DAT_SIGNAL[signal].encode(ENCODING_FORMAT))

    def add_to_download(self, file: tuple[str, int, int]):
        filename, chunk_sz, tot = file
        self.download_manager.add_download(filename, chunk_sz, tot)

    def update_status(self):
        if self.is_shutdown or self.exit_signal.is_set() or self.watch_signal.is_set():
            return

        with open(CLIENT_REQUEST_INPUT, "r") as f:
            for line in f:
                filename, chunk_sz = extract_download_input(line)
                if filename in self.resources.keys() and filename not in self.status:
                    self.status[filename] = (chunk_sz, False)

    def watch_download_list(self):
        while (
            not self.is_shutdown
            and not self.exit_signal.is_set()
            and not self.watch_signal.is_set()
        ):
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
                raise Exception("Server is not ready to download!")

            if accepted == STATUS_SIGNAL["terminate"]:
                raise SocketError("Server is terminated!")

            queue = [
                (filename, prior[0])
                for filename, prior in [
                    item for item in self.status.items() if item[1][1] is False
                ]
            ]
            if len(queue):
                print()

            while not self.is_shutdown and not self.exit_signal.is_set():
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

                    if data == STATUS_SIGNAL["terminate"].encode(ENCODING_FORMAT):
                        raise Exception("Server is terminated!")

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
        except SocketError:
            console_log(LogType.ERR, "Connection is lost!")
            self.close_connection(True)
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

    def close_connection(self, terminate: bool = False):
        self.exit_signal.set()
        self.watch_signal.set()

        if self.client:
            if not terminate and not self.is_shutdown:
                self.client.send("quit".encode(ENCODING_FORMAT))

            self.client.close()

        self.is_shutdown = True
        console_log(LogType.INFO, f"Client stopped!")

    def run(self):
        self.__exception = None

        try:
            self.client.connect(ADDR)
            console_log(LogType.INFO, "Connected to the server!")

            self.handle_fetch()
            self.update_status()

            self.watch_thread.start()

            while (
                not self.is_shutdown
                and not self.__exception
                and not self.exit_signal.is_set()
            ):
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
                    # if self.__exception or self.exit_signal.is_set():
                    #     raise Exception("Got exception")
                    console_log(LogType.ERR, "Invalid command!")
        except KeyboardInterrupt:
            console_log(LogType.INFO, f"Client is shutting down...")
            self.__exception = KeyboardInterrupt
        except Exception as e:
            console_log(LogType.ERR, f"An error occurs when running: {e}")
            self.__exception = e
        finally:
            self.close_connection(isinstance(self.__exception, KeyboardInterrupt))


class GUIClient(Client):
    def __init__(self):
        super().__init__()

    def run(self):
        pass


if __name__ == "__main__":
    args = parse_args(
        prog="Socket Client",
        desc="A simple socket client for downloading files",
        wrappers=[with_gui_arg, with_part1_arg],
    )

    if args.gui:
        print("--gui detected, using GUI version")
        GUIClient().run()
    else:
        print("--gui 'not' detected, using console version")
        Client().run()
