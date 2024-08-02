from time import sleep
from threading import Thread, Event
from socket import (
    socket,
    AF_INET,
    SOCK_STREAM,
    SHUT_RDWR,
    error as SocketError,
    gethostname,
    gethostbyname,
)

import customtkinter as tk

from classes import ServerDownloadManager
from shared.envs import (
    ADDR,
    BACKLOG,
    MAX_BUF_SIZE,
    ENCODING_FORMAT,
    SEPARATOR,
    SERVER_RESOURCES_PATH,
)
from shared.fonts import APP_FONT
from shared.constants import STATUS_SIGNAL, DAT_SIGNAL
from shared.command import get_command
from utils.base import get_timestamp
from utils.logger import LogType, raw_log, local_log, console_log
from utils.files import get_resource_list_data, get_asset_size, convert_file_size
from utils.resources_watching import start_watching, update_resource_list
from utils.args import *
from utils.gui import *


class BaseServer:
    def __init__(self, *, watching_updater=update_resource_list, client_updater: None):
        self.server_addr = [gethostbyname(gethostname()), ADDR]
        self.resources_path = SERVER_RESOURCES_PATH
        self.is_shutdown = False
        self.updater = {"watching": watching_updater, "client": client_updater}

        self.download_manager: dict[socket, ServerDownloadManager] = {}
        self.addresses: dict[socket, str] = {}
        self.resources: dict[str, tuple[int, str]] = {}

        self.exit_signal = Event()
        self.watching_thread: Thread = None

        try:
            self.server = socket(AF_INET, SOCK_STREAM)
            self.server.bind(ADDR)
        except SocketError:
            console_log(LogType.ERR, "Failed to create server socket!")
            self.shutdown_server()
            exit()

    def send_status_signal(self, conn: socket, signal: str):
        return conn.send(STATUS_SIGNAL[signal].encode(ENCODING_FORMAT))

    def send_dat_signal(self, conn: socket, signal: str):
        return conn.send(DAT_SIGNAL[signal].encode(ENCODING_FORMAT))

    def client_log(self, type: str, addr: str, msg: str):
        console_log(type, f"[CLIENT] - {addr}: {msg}")

    def send_resource_list(self, conn: socket):
        self.resources = get_resource_list_data()

        available_files = "\n".join(
            [
                f"{DAT_SIGNAL['list']}{SEPARATOR}{filename}{SEPARATOR}{fileinfo[0]}{SEPARATOR}"
                for filename, fileinfo in self.resources.items()
            ]
        )

        conn.sendall(available_files.encode(ENCODING_FORMAT))

    def send_files(self, conn: socket):
        if self.exit_signal.is_set() or self.is_shutdown:
            return

        self.send_status_signal(conn, "accept")
        msg = conn.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)

        if not msg or msg in [
            "quit",
            STATUS_SIGNAL["terminate"],
            STATUS_SIGNAL["interrupt"],
        ]:
            self.close_connection(conn, self.addresses[conn])
            return

        if not msg.startswith(DAT_SIGNAL["data"]):
            return

        if len(msg_plit := msg.split(SEPARATOR)) < 3:
            return

        _, filename, prior = msg_plit[:3]

        if filename not in self.download_manager[conn].queue:
            self.download_manager[conn].add_download(
                filename=filename,
                chunk_sz=int(prior),
                tot=get_asset_size(filename),
            )

        try:
            bytes_to_send = self.download_manager[conn].download(filename)
            conn.sendall(bytes_to_send)
        except StopIteration:
            self.send_dat_signal(conn, "done")

    def handle_client(self, conn: socket, addr: str):
        try:
            if not conn or not addr:
                return

            self.client_log(LogType.INFO, addr, "Connection established!")

            self.updater["client"]() if self.updater["client"] else None

            self.download_manager[conn] = ServerDownloadManager(files=[])

            while not self.exit_signal.is_set() and not self.is_shutdown:
                msg = conn.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
                cmd = get_command(msg[:4])

                if not msg or msg in [
                    STATUS_SIGNAL["terminate"],
                    STATUS_SIGNAL["interrupt"],
                ]:
                    break

                if cmd == "quit":
                    self.close_connection(conn, addr)
                    break
                elif cmd == "list":
                    self.send_resource_list(conn)
                elif cmd == "file":
                    self.send_files(conn)
                else:
                    self.send_status_signal(conn, "invalid")
        except SocketError:
            self.close_connection(conn, addr)
        except Exception as e:
            self.client_log(
                LogType.ERR, addr, f"An error occurs when handling request::{e}"
            )
        finally:
            self.client_log(LogType.INFO, addr, "Connection closed!")
            try:
                del self.addresses[conn]
                del self.download_manager[conn]
            except KeyError:
                pass

    def close_connection(self, conn: socket, addr: str):
        try:
            if not conn or not addr or conn not in self.addresses:
                return

            if self.send_status_signal(conn, "terminate"):
                conn.shutdown(SHUT_RDWR)

            conn.close()

            del self.addresses[conn]
        except SocketError:
            self.client_log(LogType.ERR, addr, "Connection is lost!")
        except Exception as e:
            self.client_log(
                LogType.ERR, addr, f"An error occurs when closing connection::{e}"
            )
        finally:
            self.client_log(LogType.INFO, addr, "Connection closed!")

    def shutdown_server(self):
        self.exit_signal.set()

        (
            self.watching_thread.join()
            if self.watching_thread and self.watching_thread.is_alive()
            else None
        )

        if len(self.addresses) > 0:
            try:
                for conn, addr in self.addresses.items():
                    console_log(LogType.INFO, f"Ensure closing connection from {addr}!")
                    self.send_status_signal(conn, "terminate")
                    conn.close()
            except SocketError:
                pass

            self.addresses.clear()

        # self.server.shutdown(SHUT_RDWR) if not self.is_shutdown else None
        self.server.close()
        self.is_shutdown = True
        console_log(LogType.INFO, "Server stopped!")

    def pipe_res_watching_thread(self):
        if self.watching_thread:
            return

        self.watching_thread = Thread(
            target=start_watching,
            args=(self.resources_path, self.exit_signal, self.updater["watching"]),
            daemon=False,
        )
        self.watching_thread.start()


class Server(BaseServer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start_server(self):
        try:
            self.server.listen(BACKLOG)
            console_log(LogType.INFO, f"Server has started at {ADDR}")

            while not self.exit_signal.is_set() and not self.is_shutdown:
                if not self.server:
                    continue

                conn, addr = self.server.accept()
                self.addresses[conn] = addr

                Thread(target=self.handle_client, args=(conn, addr)).start()
        except SocketError:
            pass
        except Exception as e:
            local_log(
                LogType.ERR,
                message=f"[start_server] - An error occurs when handling client: {e}",
                path="server.log",
            )

    def run(self):
        try:
            self.pipe_res_watching_thread()

            Thread(target=self.start_server, daemon=True).start()

            while not self.exit_signal.is_set() and not self.is_shutdown:
                sleep(5)
        except KeyboardInterrupt:
            console_log(LogType.INFO, "Server is shutting down...")
        except Exception as e:
            local_log(
                LogType.ERR,
                message=f"An error occurs when running server: {e}",
                path="server.log",
            )
        finally:
            self.shutdown_server()


class GUIServer(Server):
    def __init__(self):
        def updater(**kwargs):
            update_resource_list(**kwargs)
            self.render_resource_list()

        super().__init__(
            watching_updater=updater, client_updater=self.render_client_list
        )

        self.init_root()

        self.threads: dict[str, Thread] = {}
        self.create_threads()

        self.component: dict[str, tk.CTk | dict[tuple[socket, str], tk.CTk]] = {}

    def init_root(self):
        tk.set_appearance_mode("System")
        tk.set_default_color_theme("dark-blue")
        tk.deactivate_automatic_dpi_awareness()

        self.root = tk.CTk()
        self.root.title(
            f"Socket Server - ({self.server_addr[1][0]} | {self.server_addr[0]})::{self.server_addr[1][1]}"
        )

        self.root.geometry("780x420+30+30")
        self.root.minsize(780, 420)
        self.root.maxsize(1024, 540)

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.shutdown_server()
        self.root.quit()
        exit()

    def create_threads(self):
        self.threads["render-resource-list"] = Thread(
            target=self.render_resource_list, daemon=False
        )
        self.threads["render-client-list"] = Thread(
            target=self.render_client_list, daemon=False
        )
        self.threads["render-download-process"] = Thread(
            target=self.render_download_process, daemon=False
        )

        self.threads["run"] = Thread(target=self.run, daemon=True)

    def logging(self, text: str):
        if "log" not in self.component:
            return

        self.component["log"].configure(state="normal")
        self.component["log"].insert("1.0", f"{text}\n")
        self.component["log"].see("1.0")

        __now_size = self.component["log"].get("1.0", "end")
        if len(__now_size.split("\n")) > 20:
            self.component["log"].delete("end - 2 lines", "end")

        self.component["log"].configure(state="disabled")

    def render_lt_sidebar(self):
        panel = SidePanel(self.root, col_idx=0)
        panel.set_label("Resource List")

        self.component["lt-sidebar"] = panel
        self.component["resource-list"] = panel.text_box

    def render_rt_sidebar(self):
        panel = SidePanel(self.root, col_idx=2, side=True)
        panel.set_label("Client List")

        self.component["rt-sidebar"] = panel
        self.component["client-list"] = panel.text_box

    def render_main_frame(self):
        main_frame = create_frame(self.root)
        main_frame.grid(row=0, column=1, padx=0, pady=10, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.component["main"] = main_frame

        self.component["process"] = Section(main_frame, row_idx=0)
        self.component["process"].add_label("Download process")

        self.component["download-process"] = {}

        self.render_log_box()

    def render_resource_list(self):
        if "lt-sidebar" not in self.component:
            return

        if self.exit_signal.is_set():
            return

        self.resources = get_resource_list_data()

        self.component["resource-list"].configure(state="normal")
        self.component["resource-list"].delete("1.0", "end")
        content = "\n".join(
            [
                f"{filename} - {convert_file_size(fileinfo[0])}"
                for filename, fileinfo in self.resources.items()
            ]
        )
        self.component["resource-list"].insert("1.0", content)
        self.component["resource-list"].configure(state="disabled")

        self.logging(
            raw_log(LogType.INFO, f"{get_timestamp()}\n\tResource list updated!")
        )

    def render_client_list(self):
        if "rt-sidebar" not in self.component:
            return

        if self.exit_signal.is_set():
            return

        self.component["client-list"].configure(state="normal")
        self.component["client-list"].delete("1.0", "end")

        content = "\n".join([f"{addr}\n" for addr in self.addresses.values()])
        self.component["client-list"].insert("1.0", content)

        self.component["client-list"].configure(state="disabled")

        self.logging(
            raw_log(LogType.INFO, f"{get_timestamp()}\n\tClient list updated!")
        )

    def cleanup_process(self, manager: dict[socket, ServerDownloadManager]):
        if "download-process" not in self.component:
            return

        to_remove: list[str] = []

        try:
            for key in self.component["download-process"]:
                addr, filename = key.split("|")

                if addr == "null":
                    to_remove.append(key)
                    continue

                for name in [
                    f.download_list
                    for (conn, f) in manager.items()
                    if conn in self.addresses and self.addresses[conn][1] == addr
                ]:
                    if filename not in name:
                        to_remove.append(key)

            for key in set(to_remove):
                if key in self.component["download-process"]:
                    self.component["download-process"][key][0].destroy()
                    del self.component["download-process"][key]
        except Exception as e:
            local_log(
                LogType.ERR,
                message=f"An error occurs when cleanup: {e}",
                path="server.log",
            )

    def render_download_process(self):
        if "process" not in self.component:
            return

        if self.exit_signal.is_set():
            return

        copied_manager = self.download_manager.copy()

        for conn, manager in copied_manager.items():
            queue = manager.download_list.copy()
            for item in queue:
                file = queue[item]
                if not file:
                    continue

                *_, percent = file.raw_progress()
                filename = file.filename
                if not filename:
                    continue

                _label = f"{self.addresses[conn][1] if conn in self.addresses else 'null'}|{filename}"

                if (
                    _label.split("|")[0] != "null"
                    and _label not in self.component["download-process"]
                ):
                    self.component["process"].add_progress_bar_frame(
                        label=_label,
                        row=len(self.component["download-process"]) + 1,
                        col=0,
                    )

                    self.component["download-process"][_label] = (
                        self.component["process"]
                    ).progress_bars[-1]

                if _label.split("|")[0] != "null":
                    self.component["download-process"][_label][1].set(percent)

                if file.is_done() and _label.split("|")[0] != "null":
                    self.component["download-process"][_label][0].destroy()
                    del self.component["download-process"][_label]

        self.cleanup_process(self.download_manager)

        self.root.after(250, self.render_download_process)

    def render_log_box(self):
        if "main" not in self.component:
            return

        frame = Section(self.component["main"], row_idx=1)
        frame.add_label("Log Box")
        frame.add_text_box()

        self.component["log"] = frame.text_box
        self.component["log-box"] = frame

    def render_stop_btn(self):
        if "lt-sidebar" not in self.component:
            return

        btn = create_btn(
            self.component["lt-sidebar"],
            "Stop Server",
            self.on_closing,
            fg_color="#ef4444",
            hover_color="#991b1b",
            text_color="white",
        )
        btn.grid(row=2, column=0, padx=10, pady=10, sticky="sew")

        self.component["stop-btn"] = btn

    def render(self):
        try:
            self.render_lt_sidebar()
            self.render_rt_sidebar()
            self.render_main_frame()

            self.render_stop_btn()

            self.pipe_res_watching_thread()
            for thread in [
                "render-download-process",
                "render-resource-list",
                "render-client-list",
                "run",
            ]:
                self.threads[thread].start()

            self.root.mainloop()
        except KeyboardInterrupt:
            console_log(LogType.INFO, "GUIServer is shutting down...")
        except Exception as e:
            local_log(
                LogType.ERR,
                message=f"An error occurs when running gui server: {e}",
                path="server.log",
            )
        finally:
            self.on_closing()
            self.threads["run"].join() if self.threads["run"].is_alive() else None


if __name__ == "__main__":
    args = parse_args(
        prog="Socket Server",
        desc="A simple socket server for downloading files",
        wrappers=[with_gui_arg, with_part1_arg],
    )

    if args.gui:
        print("--gui detected, using GUI version\n")
        GUIServer().render()
    else:
        print("--gui 'not' detected, using console version\n")
        Server().run()
