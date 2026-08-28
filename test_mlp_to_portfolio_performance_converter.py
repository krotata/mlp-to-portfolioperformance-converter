import unittest
from unittest.mock import patch, mock_open
import mlp_to_portfolio_performance_converter as mppc
import sys


class TestMppc(unittest.TestCase):
    def test_opening_hook_csv(self):
        with patch("builtins.open", mock_open()) as mock_file:
            mppc.opening_hook_csv("test.csv", "r")
            mock_file.assert_called_once_with(
                "test.csv", "r", newline="", encoding="iso-8859-1"
            )

    def test_print_message(self):
        with patch("builtins.print") as mock_print:
            mppc.print_message("test", 31)
            mock_print.assert_called_once_with("\033[31mtest\033[0m")

    def test_convert_to_german_number(self):
        self.assertEqual(mppc.convert_to_german_number("1,000.00"), "1.000,00")
        self.assertEqual(mppc.convert_to_german_number("1000.00"), "1.000,00")
        self.assertEqual(mppc.convert_to_german_number("600,00"), "600,00")
        self.assertEqual(mppc.convert_to_german_number("-600.00"), "-600,00")
        self.assertEqual(mppc.convert_to_german_number("-99.87"), "-99,87")

    def test_is_string_of_positive_number(self):
        self.assertTrue(mppc.is_positive("1.000,00"))
        self.assertTrue(mppc.is_positive("1.000"))
        self.assertTrue(mppc.is_positive("1.000,-"))
        self.assertFalse(mppc.is_positive("-99,99"))
        self.assertFalse(mppc.is_positive("  -99,99"))

    def test_search_header(self):
        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                mppc.search_header(["test"] * 21)
            mock_print.assert_called_once_with(
                "\033[31mError: Header not found in the first 20 lines\033[0m"
            )

        header, line_no = mppc.search_header(["Buchungstag;Umsatz"])
        self.assertEqual(header, ["Buchungstag", "Umsatz"])
        self.assertEqual(line_no, 1)

        header, line_no = mppc.search_header(["test"] * 2 + ["Buchungstag;Umsatz"])
        self.assertEqual(header, ["Buchungstag", "Umsatz"])
        self.assertEqual(line_no, 3)

    @patch("os.path.exists", return_value=False)
    @patch("builtins.print")
    def test_main_file_not_exists(self, mock_print, mock_exists):
        with patch.object(sys, "argv", ["mlpc.py", "input.csv"]):
            with self.assertRaises(SystemExit):
                mppc.main()
            mock_print.assert_called_once_with(
                '\033[31mError: Input file "input.csv" does not exist\033[0m'
            )


if __name__ == "__main__":
    unittest.main()
