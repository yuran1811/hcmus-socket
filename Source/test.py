from unittest import TestCase, TestSuite, TestLoader, TextTestRunner

from shared.envs import MAX_BUF_SIZE
from shared.constants import PRIOR_MAPPING
from shared.command import get_command
from utils.files import convert_file_size, extract_download_input


class UtilsTest(TestCase):
    def test_convert_file_size(self):
        self.assertEqual(convert_file_size(-1811), "not valid size")
        self.assertEqual(convert_file_size(1), "1B")
        self.assertEqual(convert_file_size(1023), "1023B")

        self.assertEqual(convert_file_size(1024), "1.00KB")
        self.assertEqual(convert_file_size(1024**2 - 1), "1024.00KB")

        self.assertEqual(convert_file_size(1024**2), "1.00MB")
        self.assertEqual(convert_file_size(1024**2 + 1), "1.00MB")
        self.assertEqual(convert_file_size(1024**3 - 1), "1024.00MB")

        self.assertEqual(convert_file_size(1024**3), "1.00GB")
        self.assertEqual(convert_file_size(1024**3 + 1), "1.00GB")

        self.assertEqual(convert_file_size(1024**4), "1024.00GB")

    def test_extract_download_input(self):
        self.assertEqual(extract_download_input(""), ("", MAX_BUF_SIZE))
        self.assertEqual(
            extract_download_input("file0.txt"), ("file0.txt", MAX_BUF_SIZE)
        )
        self.assertEqual(
            extract_download_input("file1.txt 0 0 0"), ("file1.txt", MAX_BUF_SIZE)
        )
        self.assertEqual(
            extract_download_input("file2.txt  \t  "), ("file2.txt", MAX_BUF_SIZE)
        )

        self.assertEqual(
            extract_download_input("file3.txt CRIT"),
            ("file3.txt", MAX_BUF_SIZE * PRIOR_MAPPING["CRIT"]),
        )
        self.assertEqual(
            extract_download_input("file4.txt\tCRIT"),
            ("file4.txt", MAX_BUF_SIZE * PRIOR_MAPPING["CRIT"]),
        )
        self.assertEqual(
            extract_download_input("file5.txt  \t  CRIT"),
            ("file5.txt", MAX_BUF_SIZE * PRIOR_MAPPING["CRIT"]),
        )
        self.assertEqual(
            extract_download_input("file6.txt\t   CRIT"),
            ("file6.txt", MAX_BUF_SIZE * PRIOR_MAPPING["CRIT"]),
        )
        self.assertEqual(
            extract_download_input("file7.txt     \tCRIT"),
            ("file7.txt", MAX_BUF_SIZE * PRIOR_MAPPING["CRIT"]),
        )
        self.assertEqual(
            extract_download_input("file8.txt  \t  \t CRIT"),
            ("file8.txt", MAX_BUF_SIZE * PRIOR_MAPPING["CRIT"]),
        )


class SharedTest(TestCase):
    def test_get_command(self):
        self.assertEqual(get_command("help"), "help")
        self.assertEqual(get_command("h"), "help")

        self.assertEqual(get_command("exit"), None)
        self.assertEqual(get_command("ctrl+c"), None)
        self.assertEqual(get_command("quit"), "quit")
        self.assertEqual(get_command("q"), "quit")

        self.assertEqual(get_command("list"), "list")
        self.assertEqual(get_command("ls"), "list")

        self.assertEqual(get_command("unknown"), None)


def suite():
    suite = TestSuite()

    for test_case in [UtilsTest, SharedTest]:
        suite.addTests(TestLoader().loadTestsFromTestCase(test_case))

    return suite


if __name__ == "__main__":
    TextTestRunner().run(suite())
