# Socket Download Server

## Libs

### Standard libs

- `argparse` - parse command line arguments
- `enum` - usage of enum type
- `json` - data serialization
- `os` - for file operations
- `socket` - for creating a socket server
- `sys` - rendering progress bar
- `threading` - for handling multiple clients
- `time` - time operations
- `typing` - usage of generic type

### External libs

- `python-dotenv` - load configs from .env file
- `regex` - regular expression
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

- Run the server with gui

```bash
py server.py --gui
```

- Run the client

```bash
py client.py
# or
python3 client.py
```

- Run the client with gui

```bash
py client.py --gui
```

## Contributors

- Ngo Nguyen The Khoa, [yuran1811](https://github.com/yuran1811)
- Hinh Diem Xuan, [HDXuan15](https://github.com/HDXuan15)

## Docs

- [Refs](./md/refs.md)
- [Todo](./md/todo.md)
- [UML](../diagrams.mdj)
