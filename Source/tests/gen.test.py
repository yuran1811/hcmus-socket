import os

from utils.files import get_resource_path, convert_file_size
from utils.gen import generate_binfile

SIZES = [1024, 1024**2, 5 * 1024**2, 10 * 1024**2]
[
    generate_binfile(
        os.path.join(get_resource_path(f"pat{convert_file_size(x)}.bin")), x
    )
    for x in SIZES
]
