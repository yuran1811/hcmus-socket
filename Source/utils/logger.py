from enum import Enum


class LogType(Enum):
    INFO = 0
    ERR = 1
    OK = 2


def console_log(log_type: LogType, message: str):
    if log_type in LogType:
        print(f"[{log_type.name}] - {message}")
    else:
        print(f"[i] - {message}")


def local_log(log_type: LogType, *, message: str, path: str):
    with open(path, "a") as f:
        if log_type in LogType:
            f.write(f"[{log_type.name}] - {message}\n")
        else:
            f.write(f"[i] - {message}\n")
