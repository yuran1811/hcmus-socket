import pathlib

import customtkinter as ctk


fonts_path = pathlib.Path(__file__).parent
ctk.FontManager.load_font(str(fonts_path.joinpath("JetBrainsMono[wght].ttf")))

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
    def __init__(
        self,
        family="JetBrans Mono",
        size="base",
        weight="normal",
        slant="roman",
        underline=False,
    ):
        self.family = family
        self.size = size
        self.weight = weight
        self.slant = slant
        self.underline = underline

    def get_font(self, *, font_size: str, bold=False, italic=False, underline=False):
        return ctk.CTkFont(
            family=self.family,
            size=FONT_SIZE.get(font_size, FONT_SIZE["base"]),
            weight="bold" if bold else "normal",
            slant="italic" if italic else "roman",
            underline=underline,
        )


APP_FONT = FontFace(family="JetBrains Mono")
