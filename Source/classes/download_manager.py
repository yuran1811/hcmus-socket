from sys import stdout
from typing import TypeVar, Generic

from utils.logger import LogType, console_log
from utils.files import (
    get_resource_path,
    get_download_path,
    get_downloaded_list,
)


class FileDownloader:
    def __init__(
        self,
        *,
        filename: str,
        chunk_sz: int,
        tot: int,
        render_content: str = "",
    ):
        self.filename = filename
        self.chunk_sz = chunk_sz

        self.cur = 0
        self.tot = tot
        self.render_content = render_content or filename

    def is_done(self) -> bool:
        return self.cur >= self.tot

    def raw_progress(self):
        return (self.cur, self.tot, self.cur / float(self.tot))

    def render_progress_bar(self, len: int = 20) -> None:
        percent = self.cur / float(self.tot)
        cur_len = int(percent * len)

        if self.render_content:
            stdout.write(self.render_content + ": ")

        stdout.write(
            "{:.2f}".format(percent * 100)
            + "% "
            + "[%s%s]" % ("=" * cur_len, " " * (len - cur_len))
            + " %d/%d bytes received\n" % (self.cur, self.tot)
        )


class ClientFileDownloader(FileDownloader):
    def __init__(
        self,
        *,
        filename: str,
        chunk_sz: int,
        tot: int,
        render_content: str = "",
    ):
        super().__init__(
            filename=filename,
            chunk_sz=chunk_sz,
            tot=tot,
            render_content=render_content,
        )

        self.path = get_download_path(filename)

        # Create an empty file or overwrite the existing one
        with open(self.path, "wb"):
            pass

    def download(self, chunk_data: bytes):
        if self.is_done() or not chunk_data:
            return

        with open(self.path, "ab") as f:
            try:
                f.write(chunk_data)
                self.cur += len(chunk_data)
            except Exception as e:
                console_log(LogType.ERR, f"An error occurs when downloading file: {e}")


class ServerFileDownloader(FileDownloader):
    def __init__(
        self,
        *,
        filename: str,
        chunk_sz: int,
        tot: int,
        render_content: str = "",
    ):
        super().__init__(
            filename=filename,
            chunk_sz=chunk_sz,
            tot=tot,
            render_content=render_content,
        )

        self.path = get_resource_path(filename)

        # Create a generator to read the file by chunks
        self.file_gen = self.read_by_chunks_generator()

    def read_by_chunks_generator(self):
        with open(self.path, "rb") as f:
            while True:
                data = f.read(self.chunk_sz)
                self.cur += len(data)

                if not data:
                    break
                yield data


T = TypeVar("T", ClientFileDownloader, ServerFileDownloader)


class DownloadManager(Generic[T]):
    def __init__(self, files: list[tuple[str, int, int]]):
        self.queue: dict[str, T] = {}
        self.download_list: dict[str, T] = {}
        self.resource_list: dict[str, tuple[int, int]] = {}

        self.exists: set[str] = set()
        self.duplicates: set[str] = set()

        self.add_download_list(files)

    def is_all_done(self) -> bool:
        return all(f.is_done() for f in self.queue.values())

    def add_download(
        self,
        *,
        filename: str,
        chunk_sz: int,
        tot: int,
        is_overwritten: bool = False,
    ):
        if not is_overwritten and filename in self.exists:
            self.duplicates.add(filename)
            return

        if isinstance(self, ClientDownloadManager):
            self.download_list[filename] = ClientFileDownloader(
                filename=filename,
                chunk_sz=chunk_sz,
                tot=tot,
            )
        elif isinstance(self, ServerDownloadManager):
            self.download_list[filename] = ServerFileDownloader(
                filename=filename,
                chunk_sz=chunk_sz,
                tot=tot,
            )

        self.queue[filename] = self.download_list[filename]

    def add_download_list(self, files: list[tuple[str, int, int]]):
        for filename, chunk_sz, tot in files:
            self.add_download(
                filename=filename,
                chunk_sz=chunk_sz,
                tot=tot,
            )

    def finish(self):
        if not self.is_all_done():
            return

        self.exists.update([k for k in self.queue.keys()])
        self.queue.clear()


class ClientDownloadManager(DownloadManager[ClientFileDownloader]):
    def __init__(self, files: list[tuple[str, int, int]]):
        super().__init__(files)

        self.exists.update(get_downloaded_list())

    def show_duplicates(self):
        if not self.duplicates or len(self.duplicates) == 0:
            return

        stdout.write("The following files are already being downloaded:\n")
        for filename in self.duplicates:
            stdout.write(f" - {filename}\n")
        stdout.write("\n")

    def redownload(self):
        to_remove: list[str] = []

        for filename in self.duplicates:
            if input(f"+ Download '{filename}'? (y/n): ").strip() == "y":
                self.add_download(
                    filename=filename,
                    chunk_sz=self.resource_list[filename][0],
                    tot=self.resource_list[filename][1],
                    is_overwritten=True,
                )
                to_remove.append(filename)

        print()

        for filename in to_remove:
            self.duplicates.discard(filename)

    def handle_duplicate(self):
        self.show_duplicates()
        if (
            not self.duplicates
            or len(self.duplicates) == 0
            or input("Do you want to redownload the files? (y/n): ").strip() == "y"
        ):
            self.redownload()

    def render_download_status(self):
        if len(self.queue):
            stdout.write(
                # "All files has been downloaded!\n"
                f"Waiting for new files{" " * 25}\n"
                if self.is_all_done()
                else f"Downloading files...{" " * 25}\n"
            )
            for file_downloader in self.queue.values():
                file_downloader.render_progress_bar()
            stdout.flush()

            if not self.is_all_done():
                stdout.write("\033[F" * (len(self.queue) + 1))

    def download(self, raw_data: tuple[str, bytes]):
        if not raw_data or not len(raw_data):
            return

        filename, data = raw_data
        if filename in self.queue and not self.queue[filename].is_done():
            self.queue[filename].download(data)

        self.render_download_status()
        self.finish()


class ServerDownloadManager(DownloadManager[ServerFileDownloader]):
    def __init__(self, files: list[tuple[str, int, int]]):
        super().__init__(files)

    def download(self, filename: str):
        data = None
        if filename in self.queue and not self.queue[filename].is_done():
            data = next(self.queue[filename].file_gen)

        self.finish()

        return data
