from sys import stdout
from datetime import datetime

from shared.constants import PRIOR_MAPPING


def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S, %d.%m.%y")


def print_divider() -> str:
    print("+" * 25)


def get_prior_weight(prior: str) -> int:
    return PRIOR_MAPPING.get(prior, 1)


def stable_render(content: str):
    stdout.write(f"\r{content}")
    stdout.flush()
