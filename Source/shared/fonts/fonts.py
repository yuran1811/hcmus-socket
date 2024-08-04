import pathlib

import customtkinter as tk


FONTS_PATH = pathlib.Path(__file__).parent
FONT_SCALE = 0.75
FONT_SIZE = {
    "xs": 12,
    "sm": 14,
    "base": 16,
    "lg": 18,
    "xl": 20,
    "2xl": 24,
    "3xl": 30,
    "4xl": 36,
}


class FontFace:
    def __init__(self, family="JetBrains Mono"):
        self.families = [family]

    def load_fonts(
        self,
        fonts: list[tuple[str, str]] = [("JetBrains Mono", "JetBrainsMono[wght].ttf")],
    ):
        for family, path in fonts:
            self.families.append(family)
            tk.FontManager.load_font(str(FONTS_PATH.joinpath(path)))

    def get_font(
        self,
        *,
        family="JetBrains Mono",
        font_size="",
        bold=False,
        italic=False,
        underline=False
    ):
        return tk.CTkFont(
            family=family,
            size=int(FONT_SIZE.get(font_size, FONT_SIZE["base"]) * FONT_SCALE),
            weight="bold" if bold else "normal",
            slant="italic" if italic else "roman",
            underline=underline,
        )


APP_FONT = FontFace(family="JetBrains Mono")
