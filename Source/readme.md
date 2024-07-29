# Socket Download Server

## Libs

### Standard libs

- `argparse` - parse command line arguments
- `enum` - usage of enum type
- `json` - data serialization
- `os` - for file operations
- `re` - usage of regex
- `socket` - for creating a socket server
- `sys` - rendering progress bar
- `threading` - for handling multiple clients
- `time` - time operations
- `typing` - usage of generic type

### External libs

- `customtkinter` - making gui
- `python-dotenv` - load configs from .env file
- `rich` - rendering more beautiful console progress bar
- `watchdog` - watching file changes

## Usage

- Download necessary libs

```bash
pip install -r requirements.txt
```

- Run the server

```bash
py server.py
# or
python3 server.py
```

- Run the server with `gui`

```bash
py server.py --gui
```

- Run the server with `part1`

```bash
py server.py --part1
```

- Run the server with `gui` and `part1`

```bash
py server.py --gui --part1
```

### Run the client

- Run the client

```bash
py client.py
# or
python3 client.py
```

- Run the client with `gui`

```bash
py client.py --gui
```

- Run the client with rich progress bar

```bash
py client.py --rich
```

- Run the client with `part1`

```bash
py client.py --part1
```

- Run the client with `gui`, `part1` and `rich`

```bash
py client.py --gui --part1 --rich
```

## Contributors

- Ngo Nguyen The Khoa, [yuran1811](https://github.com/yuran1811)
- Hinh Diem Xuan, [HDXuan15](https://github.com/HDXuan15)

## Docs

- [Refs](./md/refs.md)
- [Todo](./md/todo.md)
- [UML](../diagrams.mdj)
