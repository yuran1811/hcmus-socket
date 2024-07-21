from utils.base import print_divider

COMMANDS = {
    "help": {
        "alias": ["help", "h"],
        "desc": "Show all commands",
    },
    "quit": {
        "alias": ["quit", "q"],
        "desc": "Quit the program",
    },
    "list": {
        "alias": ["list", "l"],
        "desc": "Get list of available files from server",
    },
    "get": {
        "alias": ["get", "g"],
        "desc": "Download files from server",
    },
}


def get_command(command: str):
    for key in COMMANDS:
        if command in COMMANDS[key]["alias"]:
            return key
    return None


def show_help():
    print_divider()
    print("Available commands:")
    for key in COMMANDS:
        print(f"\t{', '.join(COMMANDS[key]['alias'])}\t: {COMMANDS[key]['desc']}")
    print_divider()
