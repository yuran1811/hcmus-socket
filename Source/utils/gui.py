import customtkinter as tk
import tkinter


from shared.fonts import APP_FONT


def create_frame(root: tk.CTk, **kwargs):
    return tk.CTkFrame(root, **kwargs)


def create_scrollable_frame(root: tk.CTk, **kwargs):
    return tk.CTkScrollableFrame(root, **kwargs)


def create_scrollbar(root: tk.CTk, command, **kwargs):
    return tk.CTkScrollbar(root, command=command, **kwargs)


def create_label(root: tk.CTk, text: str = "label", **kwargs):
    return tk.CTkLabel(root, font=APP_FONT.get_font(bold=True), text=text, **kwargs)


def create_text(root: tk.CTk, **kwargs):
    return tkinter.Text(root, font=APP_FONT.get_font(), **kwargs)


def create_text_box(root: tk.CTk, **kwargs):
    return tk.CTkTextbox(root, font=APP_FONT.get_font(), **kwargs)


def create_btn(root: tk.CTk, text: str, command, **kwargs):
    return tk.CTkButton(
        root,
        font=APP_FONT.get_font(bold=True),
        text=text,
        command=command,
        width=20,
        **kwargs
    )


def create_checkbox(root: tk.CTk, text: str, **kwargs):
    return tk.CTkCheckBox(root, font=APP_FONT.get_font(), text=text, **kwargs)


def create_progress_bar(root: tk.CTk, **kwargs):
    return tk.CTkProgressBar(root, **kwargs)


class SidePanel(tk.CTkFrame):
    def __init__(self, root, *, col_idx: int, side: bool = False, **kwargs):
        super().__init__(root, **kwargs)

        self.side = side

        self.config_frame(col_idx)
        self.add_text_box()

    def config_frame(self, col_idx: int):
        self.grid(
            row=0,
            column=col_idx,
            pady=10,
            padx=10,
            sticky="ns" + ("e" if self.side else "w"),
        )
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def set_label(self, text: str, **kwargs):
        self.label = create_label(self, text=text, **kwargs)
        self.label.grid(
            row=0, column=0, padx=10, sticky="ns" + ("e" if self.side else "w")
        )

    def add_text_box(self):
        self.text_box = create_text_box(self)
        self.text_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.text_box.configure(state="disabled", cursor="arrow")


class Section(tk.CTkScrollableFrame):
    def __init__(self, root, *, row_idx: int, **kwargs):
        super().__init__(root, **kwargs)

        self.config_frame(row_idx)

        self.progress_bars = []

    def config_frame(self, row_idx: int):
        self.grid(row=row_idx, column=0, padx=10, pady=10, sticky="nsew")
        self.rowconfigure(0, weight=0)
        self.columnconfigure(0, weight=1)

    def add_label(self, text: str, **kwargs):
        self.label = create_label(self, text=text, **kwargs)
        self.label.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    def add_btn(self, text: str, command, *, row: int, col: int, **kwargs):
        self.btn = create_btn(self, text=text, command=command, **kwargs)
        self.btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def add_checkbox(self, text: str, *, row: int, col: int, **kwargs):
        self.checkbox = create_checkbox(self, text=text, **kwargs)
        self.checkbox.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def add_progress_bar(self, *, root, row: int, col: int, **kwargs):
        progress_bar = create_progress_bar(root or self, **kwargs)
        progress_bar.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        return progress_bar

    def add_progress_bar_frame(
        self, *, label: str, row: int, col: int, progress_color: str = "green", **kwargs
    ):
        frame = create_frame(self)
        frame.grid(row=row, column=col, pady=5, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)

        create_label(frame, text=label).grid(
            row=0, column=0, padx=(10, 0), sticky="nse"
        )

        bar = self.add_progress_bar(
            root=frame, row=0, col=1, progress_color=progress_color, **kwargs
        )
        self.progress_bars.append((frame, bar))

    def add_text_box(self, **kwargs):
        self.text_box = create_text_box(self, **kwargs)
        self.text_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.text_box.configure(state="disabled", cursor="arrow")
