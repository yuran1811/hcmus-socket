from threading import Thread, Event
from socket import (
    socket,
    AF_INET,
    SOCK_STREAM,
    SHUT_RDWR,
)

from classes.download_manager import ServerDownloadManager
from shared.envs import (
    ADDR,
    BACKLOG,
    MAX_BUF_SIZE,
    ENCODING_FORMAT,
    SEPARATOR,
    SERVER_RESOURCES_PATH,
)
from shared.constants import STATUS_SIGNAL, DAT_SIGNAL
from shared.command import get_command
from utils.logger import LogType, local_log, console_log
from utils.files import get_resource_list_data, get_asset_size
from utils.resources_watching import start_watching


class Server:
    def __init__(self):
        self.resources_path = SERVER_RESOURCES_PATH

        self.addresses: dict[socket, str] = {}

        self.exit_signal = Event()
        self.watching_thread: Thread = None

        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(ADDR)

    def send_status_signal(self, conn: socket, signal: str):
        conn.send(STATUS_SIGNAL[signal].encode(ENCODING_FORMAT))

    def send_dat_signal(self, conn: socket, signal: str):
        conn.send(DAT_SIGNAL[signal].encode(ENCODING_FORMAT))

    def client_log(self, type: str, addr: str, msg: str):
        console_log(type, f"[CLIENT] - {addr}: {msg}")

    def close_connection(self, conn: socket, addr: str):
        try:
            if not conn or not addr:
                return

            conn.send(STATUS_SIGNAL["terminate"].encode())
            conn.shutdown(SHUT_RDWR)
            conn.close()

            del self.addresses[conn]

            self.client_log(LogType.INFO, addr, "Connection closed!")
        except Exception as e:
            self.client_log(
                LogType.ERR, addr, f"An error occurs when closing connection::{e}"
            )

    def handle_client(self, conn: socket, addr: str):
        try:
            if not conn or not addr:
                return

            self.client_log(LogType.INFO, addr, "Connection established!")

            self.download_manager = ServerDownloadManager([])

            while not self.exit_signal.is_set():
                msg = conn.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
                cmd = get_command(msg)

                if cmd == "quit":
                    self.close_connection(conn, addr)
                    break
                elif cmd == "list":
                    list_data: dict = get_resource_list_data()
                    available_files = "\n".join(
                        [
                            f"{DAT_SIGNAL['list']}{SEPARATOR}{filename}{SEPARATOR}{fileinfo[0]}{SEPARATOR}"
                            for filename, fileinfo in list_data.items()
                        ]
                    )

                    conn.sendall(available_files.encode(ENCODING_FORMAT))

                    self.send_status_signal(conn, "success")
                    # conn.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
                elif cmd == "get":
                    self.send_status_signal(conn, "accept")

                    while not self.exit_signal.is_set():
                        msg = conn.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
                        if not msg or msg in [
                            STATUS_SIGNAL["success"],
                            STATUS_SIGNAL["terminate"],
                            STATUS_SIGNAL["interrupt"],
                        ]:
                            break

                        _, filename, prior = msg.split(SEPARATOR)[:3]

                        if filename not in self.download_manager.download_list:
                            self.download_manager.add_download(
                                filename=filename,
                                chunk_sz=int(prior),
                                tot=get_asset_size(filename),
                            )

                        try:
                            bytes_to_send = self.download_manager.download(filename)
                            conn.sendall(bytes_to_send)
                        except StopIteration:
                            self.send_dat_signal(conn, "done")
                            break

                    self.send_status_signal(conn, "success")
                else:
                    self.send_status_signal(conn, "invalid")
        except Exception as e:
            self.client_log(
                LogType.ERR, addr, f"An error occurs when handling request::{e}"
            )
        finally:
            del self.download_manager

    def start_server(self):
        try:
            self.server.listen(BACKLOG)
            console_log(LogType.INFO, f"Server has started at {ADDR}")

            while not self.exit_signal.is_set():
                if not self.server:
                    continue

                conn, addr = self.server.accept()
                self.addresses[conn] = addr

                Thread(target=self.handle_client, args=(conn, addr)).start()
        except Exception as e:
            local_log(
                LogType.ERR,
                f"[start_server] - An error occurs when handling client: {e}",
            )

    def shutdown_server(self):
        self.exit_signal.set()

        self.watching_thread.join()

        if len(self.addresses.items()):
            for conn, addr in self.addresses.items():
                console_log(LogType.INFO, f"Ensure closing connection from {addr}!")
                self.server.send(STATUS_SIGNAL["terminate"].encode())
                conn.close()

            self.server.shutdown(SHUT_RDWR)

        self.server.close()
        console_log(LogType.INFO, "Server stopped!")

    def run(self):
        try:
            self.watching_thread = Thread(
                target=start_watching,
                args=(self.resources_path, self.exit_signal),
                daemon=False,
            )
            self.watching_thread.start()

            Thread(target=self.start_server, daemon=True).start()

            while not self.exit_signal.is_set():
                pass
        except KeyboardInterrupt:
            console_log(LogType.INFO, "Server is shutting down...")
        except Exception as e:
            console_log(LogType.ERR, f"An error occurs when running server: {e}")
        finally:
            self.shutdown_server()


if __name__ == "__main__":
    Server().run()