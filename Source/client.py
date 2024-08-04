from time import sleep
from threading import Thread, Event
from socket import (
    socket,
    AF_INET,
    SOCK_STREAM,
    error as SocketError,
    gethostname,
    gethostbyname,
)

from classes import ClientDownloadManager, RichClient
from shared.envs import (
    VERSION,
    ADDR,
    MAX_BUF_SIZE,
    ENCODING_FORMAT,
    SEPARATOR,
    CLIENT_REQUEST_INPUT,
)
from shared.constants import STATUS_SIGNAL, DAT_SIGNAL, get_prior_color
from shared.command import show_help, get_command
from utils.base import get_timestamp, stable_render
from utils.logger import LogType, console_log
from utils.files import render_file_list, extract_download_input, convert_file_size
from utils.args import *
from utils.gui import *


class BaseClient:
    def __init__(self, *, use_rich: bool = False, use_part1: bool = False):
        self.use_rich = use_rich
        self.use_part1 = use_part1

        self.is_served = False
        self.is_shutdown = False
        self.interval = 2
        self.conn_timeout = 10
        self.exception_catch = None

        self.rich_renderer = (
            RichClient(table_title="Available Files") if use_rich else None
        )

        self.download_manager = ClientDownloadManager(
            files=[], rich_client=self.rich_renderer
        )

        self.resources: dict[str, int] = {}
        self.status: dict[str, tuple[int, bool]] = {}
        self.queue: dict[str, int] = {}

        self.exit_signal = Event()
        self.watch_signal = Event()

        self.watch_thread = Thread(target=self.watch_download_list, daemon=False)
        self.download_thread = Thread(target=self.downloads, daemon=False)

        self.client_addr = [gethostbyname(gethostname()), ""]
        self.client = socket(AF_INET, SOCK_STREAM)

    def exception_handler(
        self,
        func,
        *,
        exception_msg="An error occurs",
        raise_outer=False,
        dialog=(True, "Server refused to connected, type any to quit"),
    ):

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionAbortedError:
                self.exception_catch = ConnectionAbortedError
                console_log(LogType.ERR, "Connection is aborted!")
            except ConnectionResetError:
                self.exception_catch = ConnectionResetError
                console_log(LogType.ERR, "Connection is reset!")
            except ConnectionRefusedError:
                self.exception_catch = ConnectionRefusedError
                console_log(LogType.ERR, "Connection refused!")
            except KeyboardInterrupt:
                self.exception_catch = KeyboardInterrupt
                console_log(LogType.INFO, "Client is shutting down...")
            except SocketError:
                self.exception_catch = SocketError
                console_log(LogType.ERR, "Socket error!")
            except Exception as e:
                console_log(LogType.ERR, f"{exception_msg}: {e}")
            finally:
                if dialog[0] and type(self.exception_catch) in [
                    type(ConnectionRefusedError),
                    type(ConnectionResetError),
                ]:
                    tkdialog = tk.CTkInputDialog(
                        text=dialog[1],
                        title="Quit",
                    )
                    tkdialog.get_input()

                self.on_closing() if hasattr(self, "on_closing") else None

                raise self.exception_catch if raise_outer else None

        return wrapper

    def send_status_signal(self, signal: str):
        return self.client.send(STATUS_SIGNAL[signal].encode(ENCODING_FORMAT))

    def send_dat_signal(self, signal: str):
        return self.client.send(DAT_SIGNAL[signal].encode(ENCODING_FORMAT))

    def logging(self, content):
        with open("client.log", "a") as f:
            f.write(f"{get_timestamp()} - {content}\n")

    def must_stop(self):
        return self.is_shutdown or self.exit_signal.is_set()

    def must_exit(self):
        return self.must_stop() or self.watch_signal.is_set()

    def count_down(self):
        for _ in range(self.conn_timeout, 0, -1):
            if self.is_served:
                return
            stable_render(f"{_} seconds...\n", 2)
            sleep(1)
        stable_render("Server is busy now, please wait...\n\n", 3)

    def add_to_download(
        self,
        *,
        filename: str,
        chunk_sz: int,
        tot: int,
        is_overwritten: bool = False,
    ):
        self.download_manager.add_download(
            filename=filename,
            chunk_sz=chunk_sz,
            tot=tot,
            is_overwritten=is_overwritten,
        )

        if self.use_rich:
            self.download_manager.rich_progress.add_task(filename, chunk_sz, tot)

    def update_status(self):
        if self.must_exit():
            return

        with open(CLIENT_REQUEST_INPUT, "r") as f:
            for line in f:
                filename, chunk_sz = extract_download_input(line)

                if filename in self.resources.keys() and filename not in self.status:
                    self.status[filename] = (chunk_sz, False)
                    self.queue[filename] = chunk_sz

                if filename in self.queue and self.status[filename][1]:
                    del self.queue[filename]

    def watch_download_list(self):
        if self.use_part1:
            self.update_status()

            if len(self.queue) == 0 or all(
                [prior[1] for prior in self.status.values()]
            ):
                self.close_connection()

            return

        while not self.must_exit():
            self.update_status()
            sleep(self.interval)

    def downloads(self, sleep_time: float = -1):
        try:
            while not self.must_stop():
                if len(self.queue) == 0 or all(
                    [prior[1] for prior in self.status.values()]
                ):
                    self.queue.clear()

                    if self.use_part1:
                        self.watch_download_list()
                        continue

                    sleep(sleep_time) if sleep_time > 0 else None
                    continue

                to_remove = []
                __queue = self.queue.copy()

                for filename, chunk_sz in __queue.items():
                    if self.status[filename][1]:
                        continue

                    try:
                        self.client.send("file".encode(ENCODING_FORMAT))
                        accept = self.client.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)
                    except SocketError:
                        self.exception_catch = SocketError
                        console_log(LogType.ERR, "Connection is lost!")
                        self.close_connection(True)
                        exit()
                    except Exception as e:
                        self.exception_catch = e
                        continue

                    if accept in [
                        STATUS_SIGNAL["terminate"],
                        STATUS_SIGNAL["interrupt"],
                    ]:
                        raise Exception("Server is terminated!")

                    if accept != STATUS_SIGNAL["accept"]:
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

                    if data == b"done":
                        continue

                    if filename not in self.download_manager.download_list:
                        self.add_to_download(
                            filename=filename,
                            chunk_sz=chunk_sz,
                            tot=self.resources[filename],
                            is_overwritten=True,
                        )

                    self.download_manager.download((filename, data))

                    __is_done = self.download_manager.download_list[filename].is_done()
                    self.status[filename] = (
                        chunk_sz,
                        __is_done,
                    )
                    if __is_done:
                        to_remove.append(filename)

                    if self.use_part1:
                        break

                for filename in to_remove:
                    del self.queue[filename]
                __queue.clear()

                sleep(sleep_time) if sleep_time > 0 else None
        except SocketError:
            self.exception_catch = SocketError
            console_log(LogType.ERR, "Connection is lost!")

            self.close_connection(True)
        except Exception as e:
            self.exception_catch = e
            console_log(LogType.ERR, f"An error occurs when downloading: {e}")

    def update_resources(self, msg: str):
        for line in msg.strip().split("\n"):
            line = line.strip()
            if line == "" or not line:
                continue

            _, filename, size = line.split(SEPARATOR)[:3]
            self.resources[filename] = int(size)

    def fetch_list(self):
        self.client.send("list".encode(ENCODING_FORMAT))
        msg = self.client.recv(MAX_BUF_SIZE).decode(ENCODING_FORMAT)

        if msg in [
            STATUS_SIGNAL["terminate"],
            STATUS_SIGNAL["interrupt"],
        ]:
            return

        if msg[:4] == DAT_SIGNAL["list"]:
            self.resources.clear()
            self.update_resources(msg)

    def handle_fetch(self):
        self.fetch_list()

        if self.use_rich:
            self.rich_renderer.render_file_list(
                [item for item in self.resources.items()]
            )
        else:
            render_file_list([item for item in self.resources.items()])

    def close_connection(self, terminate: bool = False):
        self.exit_signal.set()
        self.watch_signal.set()

        try:
            self.watch_thread.join() if self.watch_thread.is_alive() else None
            self.download_thread.join() if self.download_thread.is_alive() else None

            if self.client:
                if not terminate and not self.is_shutdown:
                    self.client.send("quit".encode(ENCODING_FORMAT))

                self.client.close()
        except Exception:
            pass
        finally:
            self.is_shutdown = True
            console_log(
                LogType.INFO,
                f"Client stopped! - {get_timestamp()} (Press 'Enter' to exit)",
            )

        exit()


class Client(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        try:
            console_log(LogType.INFO, "Connecting to the server...")
            self.client.connect(ADDR)
            self.client_addr[1] = self.client.getsockname()
            console_log(LogType.INFO, "Connected to the server!\n")
            console_log(LogType.INFO, "Waiting for being served...")

            Thread(target=self.count_down, daemon=True).start()

            self.handle_fetch()
            self.update_status()

            self.is_served = True

            self.watch_thread.start()
            self.download_thread.start()

            while not self.must_stop() and not self.exception_catch:
                inp = input("Enter command: ").strip()

                if self.must_exit():
                    break

                cmd = get_command(inp.lower())

                if cmd == "quit":
                    self.exit_signal.set()
                    break
                elif cmd == "list":
                    self.handle_fetch()
                elif cmd == "file":
                    console_log(
                        LogType.INFO,
                        "Download process is automatically triggered! No need to manually trigger it!",
                    )
                    pass
                elif cmd == "help":
                    show_help()
                else:
                    console_log(LogType.ERR, "Invalid command!")
        except KeyboardInterrupt:
            self.exception_catch = KeyboardInterrupt
            console_log(LogType.INFO, f"Client is shutting down...")
        except ConnectionAbortedError:
            self.exception_catch = ConnectionAbortedError
            console_log(LogType.ERR, "Connection is aborted!")
        except ConnectionRefusedError:
            self.exception_catch = ConnectionRefusedError
            console_log(LogType.ERR, "Connection refused!")
        except Exception as e:
            self.exception_catch = e
            console_log(LogType.ERR, f"An error occurs when running: {e}")
        finally:
            if self.use_rich and self.rich_renderer:
                self.rich_renderer.rich_progress.stop()
                self.rich_renderer.live.stop()

            self.close_connection(
                isinstance(self.exception_catch, KeyboardInterrupt)
                or (
                    type(self.exception_catch)
                    in [type(ConnectionRefusedError), type(ConnectionAbortedError)]
                )
            )


class GUIClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.is_ready = False

        self.threads: dict[str, Thread] = {}
        self.create_threads()

        self.init_root()

        self.component: dict[str, tk.CTk | dict[tuple[socket, str], tk.CTk]] = {}

    def init_root(self):
        tk.set_appearance_mode("System")
        tk.set_default_color_theme("dark-blue")
        tk.deactivate_automatic_dpi_awareness()

        self.root = tk.CTk()
        self.root.title("Socket Client")

        self.root.geometry("780x420+30+390")
        self.root.minsize(780, 420)
        self.root.maxsize(1024, 540)

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.close_connection(
            type(self.exception_catch)
            in [type(ConnectionRefusedError), type(ConnectionAbortedError)]
        )
        self.root.quit()
        exit()

    def create_threads(self):
        self.threads["watch-download"] = Thread(
            target=self.watch_download_list, daemon=False
        )
        self.threads["render-input-list"] = Thread(
            target=self.render_input_list, daemon=False
        )
        self.threads["render-download-process"] = Thread(
            target=self.render_download_process, daemon=False
        )

        self.threads["download-files"] = Thread(
            target=self.downloads, args=(10 ** (-4),), daemon=False
        )
        self.threads["run"] = Thread(
            target=self.exception_handler(self.run, exception_msg="Error when running"),
            daemon=True,
        )

    def render_win_title(self):
        self.root.title(
            f"Socket Client - ({self.client_addr[1][0]} | {self.client_addr[0]})::{self.client_addr[1][1]}"
        )

    def render_lt_sidebar(self):
        panel = SidePanel(self.root, col_idx=0)
        panel.set_label("Resource List")

        self.component["lt-sidebar"] = panel
        self.component["resource-list"] = panel.text_box

    def render_rt_sidebar(self):
        panel = SidePanel(self.root, col_idx=2, side=True)
        panel.set_label("Input List")

        panel.text_box.configure(state="normal", cursor="arrow")

        self.component["rt-sidebar"] = panel
        self.component["input-list"] = panel.text_box

    def render_main_frame(self):
        main_frame = create_frame(self.root)
        main_frame.grid(row=0, column=1, padx=0, pady=10, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.component["main"] = main_frame

        self.component["process"] = Section(main_frame, row_idx=0)
        self.component["process"].add_label("Download process")

        self.component["download-process"] = {}

    def render_resource_list(self):
        if "lt-sidebar" not in self.component:
            return

        if self.exit_signal.is_set():
            return

        self.component["resource-list"].configure(state="normal")
        self.component["resource-list"].delete("1.0", "end")

        content = (
            "\n".join(
                [
                    f"{filename} - {convert_file_size(size)}"
                    for filename, size in self.resources.items()
                ]
            )
            if len(self.resources)
            else "No resources found!"
        )
        self.component["resource-list"].insert("1.0", content)

        self.component["resource-list"].configure(state="disabled")

    def render_download_process(self):
        if "process" not in self.component:
            return

        if self.exit_signal.is_set():
            return

        copied_list = self.download_manager.download_list.copy()
        to_remove = []

        for filename in self.component["download-process"]:
            if filename not in [f[0] for f in copied_list.items()]:
                self.component["download-process"][filename][0].destroy()
                to_remove.append(filename)

        for item in to_remove:
            del self.component["download-process"][item]

        self.render_fetch_btn()

        for filename, download in copied_list.items():
            if filename not in self.component["download-process"]:
                self.component["process"].add_progress_bar_frame(
                    label=f"{filename}",
                    row=len(self.component["download-process"]) + 1,
                    col=0,
                    progress_color=get_prior_color(download.chunk_sz // MAX_BUF_SIZE),
                )

                self.component["download-process"][filename] = self.component[
                    "process"
                ].progress_bars[-1]

            *_, percent = download.raw_progress()
            self.component["download-process"][filename][1].set(percent)

            if download.is_done():
                self.component["download-process"][filename][0].destroy()
                del self.component["download-process"][filename]

        self.root.after(250, self.render_download_process)

    def render_input_list(self):
        if "rt-sidebar" not in self.component:
            return

        def get_content(_):
            with open(CLIENT_REQUEST_INPUT, "r") as f:
                content = f.read().strip()

                self.component["input-list"].delete("1.0", "end")
                self.component["input-list"].insert("1.0", content)

        def update_content(_):
            with open(CLIENT_REQUEST_INPUT, "w") as f:
                f.write(self.component["input-list"].get("1.0", "end"))

        get_content(None)
        self.component["input-list"].bind("<FocusIn>", get_content)
        self.component["input-list"].bind("<Leave>", update_content)

    def render_fetch_btn(self):
        if "lt-sidebar" not in self.component:
            return

        if "fetch-btn" not in self.component:

            def action():
                if len(self.queue):
                    return

                self.component["fetch-btn"].configure(state="disabled")
                self.handle_fetch()
                self.render_resource_list()
                self.component["fetch-btn"].configure(state="normal")

            btn = create_btn(
                self.component["lt-sidebar"],
                "Waiting for connection...",
                action,
                fg_color="#0ea5e9",
                hover_color="#0369a1",
                text_color="#082f49",
                text_color_disabled="white",
                state="disabled",
            )
            btn.grid(row=2, column=0, padx=10, pady=10, sticky="sew")

            self.component["fetch-btn"] = btn

        if not self.is_ready:
            self.root.after(750, self.render_fetch_btn)
            return

        self.component["fetch-btn"].configure(
            state="disabled" if len(self.queue) else "normal",
            text="Waiting for downloading..." if len(self.queue) else "Fetch List",
        )

    def render_stop_btn(self):
        if "rt-sidebar" not in self.component:
            return

        if "stop-btn" not in self.component:
            btn = create_btn(
                self.component["rt-sidebar"],
                "Waiting for connection...",
                self.on_closing,
                fg_color="#ef4444",
                hover_color="#991b1b",
                text_color="white",
                text_color_disabled="white",
                state="disabled",
            )
            btn.grid(row=2, column=0, padx=10, pady=10, sticky="sew")

            self.component["stop-btn"] = btn

        if not self.is_ready:
            self.root.after(250, self.render_stop_btn)
            return

        self.component["stop-btn"].configure(state="normal", text="Stop Client")

    def render(self):
        def func():
            self.render_lt_sidebar()
            self.render_rt_sidebar()
            self.render_main_frame()

            self.render_fetch_btn()
            self.render_stop_btn()

            for thread in ["run"]:
                self.threads[thread].start()

            self.root.mainloop()

        self.exception_handler(func, dialog=(False, ""))()

        self.threads["run"].join() if self.threads["run"].is_alive() else None

    def run(self):
        console_log(LogType.INFO, "Connecting to the server...")
        self.client.connect(ADDR)
        self.client_addr[1] = self.client.getsockname()
        self.render_win_title()
        console_log(LogType.INFO, "Connected to the server!")

        self.is_ready = True

        self.handle_fetch()
        self.update_status()

        self.render_resource_list()

        for thread in [
            "watch-download",
            "download-files",
            "render-input-list",
            "render-download-process",
        ]:
            self.threads[thread].start()

        while not self.exit_signal.is_set():
            sleep(2)


if __name__ == "__main__":
    args = parse_args(
        prog="Socket Client",
        desc="A simple socket client for downloading files",
        wrappers=[with_gui_arg, with_rich_arg, with_part1_arg, with_version_arg],
    )

    use_gui = args.gui
    use_rich = args.rich
    use_part1 = args.part1
    use_version = args.version

    if use_version:
        print(f"Socket Client v{VERSION}")
        exit()

    print("--part1 detected, using part1 version") if use_part1 else None
    print("--gui detected, using GUI version") if use_gui else None

    if use_gui:
        print()
        GUIClient(use_part1=use_part1).render()
    else:
        print("--rich detected, using rich version") if use_rich else None
        print()
        Client(use_rich=use_rich, use_part1=use_part1).run()
