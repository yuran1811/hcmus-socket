from os import path, getenv
from dotenv import load_dotenv

load_dotenv()

# Socket config
HOST = getenv("HOST") or "127.0.0.1"
PORT = int(getenv("PORT")) or 1811
ADDR = (HOST, PORT)

BACKLOG = int(getenv("BACKLOG")) or 5
MAX_BUF_SIZE = int(getenv("MAX_BUF_SIZE")) or 1024

SEPARATOR = getenv("SEPARATOR") or "<SEPARATOR>"
ENCODING_FORMAT = "utf8"

# Application config
APP_ROOT_PATH = "app"

SERVER_DIR_PATH = path.join(APP_ROOT_PATH, "server")
SERVER_RESOURCES_PATH = getenv("SERVER_RESOURCES_PATH") or path.join(
    SERVER_DIR_PATH, "resources"
)

CLIENT_DIR_PATH = path.join(APP_ROOT_PATH, "client")
CLIENT_DOWNLOADS_PATH = getenv("CLIENT_DOWNLOADS_PATH") or path.join(
    CLIENT_DIR_PATH, "downloads"
)
CLIENT_REQUEST_INPUT = getenv("CLIENT_REQUEST_INPUT") or path.join(
    CLIENT_DIR_PATH, "input.txt"
)
