from sys import stdout
from datetime import datetime


def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S, %d.%m.%y")


def print_divider() -> str:
    print("+" * 25)


def stable_render(content: str, lines: int = 1):
    stdout.write(f"\r{content}")
    stdout.flush()

    stdout.write("\033[F" * (lines - 1))
