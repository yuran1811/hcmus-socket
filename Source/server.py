from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, gethostbyname, gethostname
from threading import Thread, Event
from argparse import ArgumentParser
from datetime import datetime

import customtkinter as tk

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
from utils.args import with_gui_arg
from utils.logger import LogType, local_log, console_log, raw_log
from utils.files import get_resource_list_data, get_asset_size, convert_file_size
from utils.resources_watching import start_watching
from utils.gui import *


class Server:
    def __init__(self):
        self.resources_path = SERVER_RESOURCES_PATH

        self.download_manager: dict[socket, ServerDownloadManager] = {}
        self.addresses: dict[socket, str] = {}
        self.resources: dict[str, tuple[int, str]] = {}

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

    def send_resource_list(self, conn: socket):
        self.resources = get_resource_list_data()
        available_files = "\n".join(
            [
                f"{DAT_SIGNAL['list']}{SEPARATOR}{filename}{SEPARATOR}{fileinfo[0]}{SEPARATOR}"
                for filename, fileinfo in self.resources.items()
            ]
        )

        conn.sendall(available_files.encode(ENCODING_FORMAT))

        self.send_status_signal(conn, "success")

    def send_files(self, conn: socket):
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
                break

        self.send_status_signal(conn, "success")

    def handle_client(self, conn: socket, addr: str):
        try:
            if not conn or not addr:
                return

            self.client_log(LogType.INFO, addr, "Connection established!")

            self.download_manager[conn] = ServerDownloadManager([])

            while not self.exit_signal.is_set():
                msg = conn.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
                cmd = get_command(msg)

                if cmd == "quit":
                    self.close_connection(conn, addr)
                    break
                elif cmd == "list":
                    self.send_resource_list(conn)
                elif cmd == "get":
                    self.send_files(conn)
                else:
                    self.send_status_signal(conn, "invalid")
        except Exception as e:
            self.client_log(
                LogType.ERR, addr, f"An error occurs when handling request::{e}"
            )
        finally:
            try:
                del self.addresses[conn]
                del self.download_manager[conn]
            except KeyError:
                pass

    def close_connection(self, conn: socket, addr: str):
        try:
            if not conn or not addr:
                return

            self.send_status_signal(conn, "terminate")
            conn.shutdown(SHUT_RDWR)
            conn.close()

            del self.addresses[conn]

            self.client_log(LogType.INFO, addr, "Connection closed!")
        except Exception as e:
            self.client_log(
                LogType.ERR, addr, f"An error occurs when closing connection::{e}"
            )

    def start_server(self):
        try:
            self.server.listen(BACKLOG)
            console_log(LogType.INFO, f"Server has started at {ADDR}")
            console_log(LogType.INFO, f"Alternative: {gethostbyname(gethostname())}\n")

            while not self.exit_signal.is_set():
                if not self.server:
                    continue

                conn, addr = self.server.accept()
                self.addresses[conn] = addr

                Thread(target=self.handle_client, args=(conn, addr)).start()
        except Exception as e:
            local_log(
                LogType.ERR,
                message=f"[start_server] - An error occurs when handling client: {e}",
                path="server.log",
            )

    def shutdown_server(self):
        self.exit_signal.set()

        self.watching_thread.join()

        if len(self.addresses) > 0:
            for conn, addr in self.addresses.items():
                console_log(LogType.INFO, f"Ensure closing connection from {addr}!")
                self.send_status_signal(conn, "terminate")
                conn.close()

            self.server.shutdown(SHUT_RDWR)

        self.server.close()
        console_log(LogType.INFO, "Server stopped!")

    def pipe_res_watching_thread(self):
        if self.watching_thread:
            return

        self.watching_thread = Thread(
            target=start_watching,
            args=(self.resources_path, self.exit_signal),
            daemon=False,
        )
        self.watching_thread.start()

    def run(self):
        try:
            self.pipe_res_watching_thread()

            Thread(target=self.start_server, daemon=True).start()

            while not self.exit_signal.is_set():
                pass
        except KeyboardInterrupt:
            console_log(LogType.INFO, "Server is shutting down...")
        except Exception as e:
            console_log(LogType.ERR, f"An error occurs when running server: {e}")
        finally:
            self.shutdown_server()


class GUIServer(Server):
    def __init__(self):
        super().__init__()

        self.init_root()

        self.component: dict[str, tk.CTk | dict[tuple[socket, str], tk.CTk]] = {}

        self.threads: dict[str, Thread] = {}
        self.create_threads()

    def init_root(self):
        tk.set_appearance_mode("System")
        tk.set_default_color_theme("dark-blue")
        tk.deactivate_automatic_dpi_awareness()

        self.root = tk.CTk()
        self.root.title("Socket Server")

        self.root.geometry("780x420+50+50")
        self.root.minsize(780, 420)
        self.root.maxsize(1024, 540)

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)

    def create_threads(self):
        self.threads["render-resource-list"] = Thread(
            target=self.render_resource_list, daemon=True
        )
        self.threads["render-client-list"] = Thread(
            target=self.render_client_list, daemon=True
        )
        self.threads["render-download-process"] = Thread(
            target=self.render_download_process, daemon=True
        )
        self.threads["run"] = Thread(target=self.run, daemon=True)

    def logging(self, text: str):
        if not "log" in self.component:
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

        self.component["resource-list"] = panel.text_box
        self.component["lt-sidebar"] = panel

    def render_rt_sidebar(self):
        panel = SidePanel(self.root, col_idx=2, side=True)
        panel.set_label("Client List")

        self.component["client-list"] = panel.text_box
        self.component["rt-sidebar"] = panel

    def render_main_frame(self):
        main_frame = create_frame(self.root)
        main_frame.grid(row=0, column=1, padx=0, pady=10, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.component["main"] = main_frame

    def render_resource_list(self):
        if not "lt-sidebar" in self.component:
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
            raw_log(
                LogType.INFO,
                f"{datetime.now()}\n\tResource list updated!",
            )
        )
        self.root.after(2000, self.render_resource_list)

    def render_client_list(self):
        if not "rt-sidebar" in self.component:
            return

        if self.exit_signal.is_set():
            return

        self.component["client-list"].configure(state="normal")

        self.component["client-list"].delete("1.0", "end")

        content = "\n".join([f"{addr}\n" for addr in self.addresses.values()])
        self.component["client-list"].insert("1.0", content)

        self.component["client-list"].configure(state="disabled")

        self.logging(raw_log(LogType.INFO, f"{datetime.now()}\n\tClient list updated!"))

        self.root.after(2000, self.render_client_list)

    def render_download_process(self):
        if not "main" in self.component:
            return

        if self.exit_signal.is_set():
            return

        self.component["process"] = Section(self.component["main"], row_idx=0)
        self.component["process"].add_label("Download process")

        for conn, manager in self.download_manager.items():
            for item in manager.queue:
                cur, tot, percent = manager.queue[item].raw_progress()

                if percent >= 100:
                    # destroy the progress bar
                    pass

        # for i in range(1, 10):
        #     self.component["process"].add_progress_bar(row=i, col=0)
        
        self.root.after(2000, self.render_download_process)

    def render_log_box(self):
        if not "main" in self.component:
            return

        frame = Section(self.component["main"], row_idx=1)
        frame.add_label("Log Box")
        frame.add_text_box()

        self.component["log"] = frame.text_box
        self.component["log-box"] = frame

    def render_start_btn(self):
        if not "lt-sidebar" in self.component:
            return

        def start_action():
            self.threads["run"].start()

            self.component["start-btn"].configure(state="disabled")

        btn = create_btn(self.component["lt-sidebar"], "Start Server", start_action)
        btn.grid(row=2, column=0, padx=10, pady=10, sticky="sew")

        self.component["start-btn"] = btn

    def render(self):
        try:
            self.render_lt_sidebar()
            self.render_rt_sidebar()

            self.render_main_frame()
            self.render_download_process()
            self.render_log_box()

            self.pipe_res_watching_thread()

            self.threads["render-resource-list"].start()
            self.threads["render-client-list"].start()

            self.render_start_btn()
            self.root.mainloop()

        except KeyboardInterrupt:
            console_log(LogType.INFO, "Server is shutting down...")
        except Exception as e:
            console_log(LogType.ERR, f"An error occurs when running server: {e}")
        finally:
            self.shutdown_server()

            self.threads["run"].join() if self.threads["run"].is_alive() else None


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Socket Server",
        description="A simple socket server for file downloading",
    )
    with_gui_arg(parser)
    args = parser.parse_args()

    use_gui = args.gui
    if use_gui:
        print("--gui detected, using GUI version\n")
        GUIServer().render()
    else:
        print("--gui not detected, using console version\n")
        Server().run()
