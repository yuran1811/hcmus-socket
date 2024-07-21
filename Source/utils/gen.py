def generate_binfile(path: str, size: int):
    with open(path, "wb") as file:
        file.write(b"\0" * size)
