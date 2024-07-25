import sys
from unittest import TestCase, TestSuite, TestLoader, TextTestRunner

sys.path.append("..")

from shared.envs import MAX_BUF_SIZE
from shared.constants import PRIOR_MAPPING
from shared.command import get_command
from utils.base import get_prior_weight
from utils.files import convert_file_size, extract_download_input


class UtilsTest(TestCase):
    def test_get_prior_weight(self):
        self.assertEqual(get_prior_weight("CRIT"), 2**6)
        self.assertEqual(get_prior_weight("HIGH"), 2**4)
        self.assertEqual(get_prior_weight("MIDD"), 2**2)
        self.assertEqual(get_prior_weight("NORM"), 1)

        self.assertEqual(get_prior_weight("UNKNOWN"), 1)

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
            extract_download_input("\t   file1.txt 0 0 0  \t\t"),
            ("file1.txt", MAX_BUF_SIZE),
        )
        self.assertEqual(
            extract_download_input(" \t\t file2.txt  \t  "), ("file2.txt", MAX_BUF_SIZE)
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

        self.assertEqual(get_command("quit"), "quit")
        self.assertEqual(get_command("q"), "quit")
        self.assertEqual(get_command("exit"), None)
        self.assertEqual(get_command("ctrl+c"), None)

        self.assertEqual(get_command("list"), "list")
        self.assertEqual(get_command("l"), "list")
        self.assertEqual(get_command("ls"), None)

        self.assertEqual(get_command("get"), "get")
        self.assertEqual(get_command("g"), "get")
        self.assertEqual(get_command("dl"), None)

        self.assertEqual(get_command("unknown"), None)


def suite():
    suite = TestSuite()

    for test_case in [UtilsTest, SharedTest]:
        suite.addTests(TestLoader().loadTestsFromTestCase(test_case))

    return suite


if __name__ == "__main__":
    TextTestRunner().run(suite())
