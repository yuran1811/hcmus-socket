import os, re, json

from shared.envs import (
    MAX_BUF_SIZE,
    SERVER_DIR_PATH,
    SERVER_RESOURCES_PATH,
    CLIENT_DIR_PATH,
    CLIENT_DOWNLOADS_PATH,
)
from .base import get_prior_weight, print_divider


def render_file_list(files: list[tuple[str, int]]):
    print()
    print_divider()
    print("Available files:")
    for i, f in enumerate(files):
        print(f"\t{i+1}. {f[0]} - {convert_file_size(f[1])}")
    print_divider()
    print()


def get_asset_size(filename: str):
    return os.path.getsize(get_resource_path(filename))


def get_resource_list():
    os.makedirs(SERVER_RESOURCES_PATH, exist_ok=True)
    return os.listdir(SERVER_RESOURCES_PATH)


def get_resource_path(filename: str):
    os.makedirs(SERVER_RESOURCES_PATH, exist_ok=True)
    return os.path.join(SERVER_RESOURCES_PATH, filename)


def get_downloaded_list():
    os.makedirs(CLIENT_DOWNLOADS_PATH, exist_ok=True)
    return os.listdir(CLIENT_DOWNLOADS_PATH)


def get_download_path(filename: str):
    os.makedirs(CLIENT_DOWNLOADS_PATH, exist_ok=True)
    return os.path.join(CLIENT_DOWNLOADS_PATH, filename)


def update_resources_data():
    path = os.path.join(SERVER_DIR_PATH, "resources.json")

    data: dict[str, tuple[int, str]] = {}
    filenames = get_resource_list()
    for filename in filenames:
        size = get_asset_size(filename)
        data[filename] = size, get_resource_path(filename)

    with open(path, "w") as f:
        f.write(json.dumps(data).replace(" ", ""))


def get_resource_list_data():
    path = os.path.join(SERVER_DIR_PATH, "resources.json")

    if not os.path.exists(path):
        update_resources_data()

    with open(path, "r") as f:
        return json.loads(f.read())


def extract_download_input(line: str):
    reg_list = re.split("[\\s\\t\\n]+", line.strip())

    if len(reg_list) == 1:
        return reg_list[0], MAX_BUF_SIZE * get_prior_weight("NORM")

    if len(reg_list) >= 2:
        filename, prior = reg_list[:2]
        return filename, MAX_BUF_SIZE * get_prior_weight(prior.upper())

    return "", 0


def get_to_download_list(res_list: dict[str, tuple[int, str]]):
    with open(os.path.join(CLIENT_DIR_PATH, "input.txt"), "r") as f:
        downloads: list[tuple[str, int, int]] = []

        for line in f:
            filename, chunk_sz = extract_download_input(line.strip())
            if (filename not in res_list) or (filename == ""):
                continue
            downloads.append((filename, chunk_sz, res_list[filename][0]))

        return downloads


def convert_file_size(size: int, use_int: bool = False):
    if size < 0:
        return f"not valid size"
    elif size < 1024:
        return f"{size}B"
    elif size < 1024**2:
        return f"{size/1024:.2f}KB" if not use_int else f"{size//1024}KB"
    elif size < 1024**3:
        return f"{size/(1024**2):.2f}MB" if not use_int else f"{size//(1024**2)}MB"
    else:
        return f"{size/(1024**3):.2f}GB" if not use_int else f"{size//(1024**3)}GB"
