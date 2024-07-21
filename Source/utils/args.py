from argparse import ArgumentParser


def with_gui_arg(parser: ArgumentParser):
    parser.add_argument("--gui", help="Run server with GUI", action="store_true")
    return parser
