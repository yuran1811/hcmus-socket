from sys import stdout

from shared.constants import PRIOR_MAPPING


def print_divider():
    print("+" * 25)


def get_prior_weight(prior: str) -> int:
    return PRIOR_MAPPING.get(prior, 1)


def stable_render(content: str):
    stdout.write(f"\r{content}")
    stdout.flush()
