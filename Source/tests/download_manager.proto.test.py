from sys import stdout


from utils.files import (
    get_download_path,
    get_downloaded_list,
    get_resource_list_data,
    get_resource_path,
    get_to_download_list,
    update_resources_data,
)


class FileDownloader:
    def __init__(
        self,
        *,
        chunk_sz: int,
        tot: int,
        filename: str,
        filepath: str,
        render_content: str = "",
    ):
        self.chunk_sz = chunk_sz
        self.filename = filename
        self.path = filepath

        self.cur = 0
        self.tot = tot
        self.render_content = render_content or filename

        # Create a generator to read the file by chunks
        self.file_gen = self.read_by_chunks_generator()

        # Create an empty file or overwrite the existing one
        with open(self.path, "wb"):
            pass

    def is_done(self) -> bool:
        return self.cur >= self.tot

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

    def read_by_chunks_generator(self):
        with open(get_resource_path(self.filename), "rb") as file:
            while True:
                data = file.read(self.chunk_sz)
                if not data:
                    break
                yield data

    def download(self):
        with open(self.path, "ab") as f:
            try:
                if self.is_done():
                    return

                chunk = next(self.file_gen)
                if not chunk:
                    return

                f.write(chunk)
                self.cur += len(chunk)
            except StopIteration:
                pass


class DownloadManager:
    def __init__(self, files: list[tuple[str, int, int]]):
        self.queue: list[FileDownloader] = []
        self.download_list: dict[str, FileDownloader] = {}
        self.resource_list: dict[str, tuple[int, int]] = {}

        self.exists: set[str] = set(get_downloaded_list())
        self.duplicates: set[str] = set()

        for filename, chunk_sz, tot in files:
            self.resource_list[filename] = (chunk_sz, tot)

            self.add_download(
                filename=filename,
                filepath=get_download_path(filename),
                chunk_sz=chunk_sz,
                tot=tot,
            )

    def is_all_done(self) -> bool:
        return all(f.is_done() for f in self.queue)

    def add_download(
        self,
        *,
        filename: str,
        filepath: str,
        chunk_sz: int,
        tot: int,
        is_overwritten: bool = False,
    ):
        if not is_overwritten and filename in self.exists:
            self.duplicates.add(filename)
            return

        self.download_list[filename] = FileDownloader(
            filename=filename,
            filepath=filepath,
            chunk_sz=chunk_sz,
            tot=tot,
        )
        self.queue.append(self.download_list[filename])

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
                    filepath=get_download_path(filename),
                    chunk_sz=self.resource_list[filename][0],
                    tot=self.resource_list[filename][1],
                    is_overwritten=True,
                )
                to_remove.append(filename)

        print()

        for filename in to_remove:
            self.duplicates.discard(filename)

    def downloads(self):
        while not self.is_all_done():
            for file_downloader in self.queue:
                if not file_downloader.is_done():
                    file_downloader.download()

            stdout.write("Downloading files...\n")
            for file_downloader in self.queue:
                file_downloader.render_progress_bar()
            stdout.flush()
            stdout.write("\033[F" * (len(self.queue) + 1))

        if len(self.queue):
            stdout.write("All files has been downloaded!\n")
            for file_downloader in self.queue:
                file_downloader.render_progress_bar()
            stdout.flush()

        self.exists.update(self.queue)
        self.queue.clear()

    def start(self):
        self.show_duplicates()
        if (
            not self.duplicates
            or len(self.duplicates) == 0
            or input("Do you want to redownload the files? (y/n): ").strip() == "y"
        ):
            self.redownload()

        self.downloads()


def main():
    try:
        update_resources_data()
        res_list = get_resource_list_data()
        files = get_to_download_list(res_list)

        download_manager = DownloadManager(files)
        download_manager.start()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
