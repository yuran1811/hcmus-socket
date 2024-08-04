from argparse import ArgumentParser


def with_gui_arg(parser: ArgumentParser):
    parser.add_argument("--gui", help="Run with GUI", action="store_true")


def with_rich_arg(parser: ArgumentParser):
    parser.add_argument("-r", "--rich", help="Run with rich", action="store_true")


def with_part1_arg(parser: ArgumentParser):
    parser.add_argument("-p1", "--part1", help="Run part 1", action="store_true")


def with_version_arg(parser: ArgumentParser):
    parser.add_argument("-v", "--version", help="Version", action="store_true")


def parse_args(*, prog: str, desc: str, wrappers: list):
    parser = ArgumentParser(
        prog=prog,
        description=desc,
    )

    for wrapper in wrappers:
        wrapper(parser)

    return parser.parse_args()
