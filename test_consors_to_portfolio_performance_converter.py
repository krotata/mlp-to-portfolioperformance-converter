import unittest
from unittest.mock import patch, mock_open
import consors_to_portfolio_performance_converter as cppc
import sys


class TestCppc(unittest.TestCase):
    def test_opening_hook_csv(self):
        with patch("builtins.open", mock_open()) as mock_file:
            cppc.opening_hook_csv("test.csv", "r")
            mock_file.assert_called_once_with(
                "test.csv", "r", newline="", encoding="utf-8-sig"
            )

    def test_search_header(self):
        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                cppc.search_header(["test"] * 21)
            mock_print.assert_called_once_with(
                "\033[31mError: Header not found in the first 20 lines\033[0m"
            )

        preamble_and_header = [
            "Konto;Inhaber;Exportdatum",
            "923887173;Matthias Klauer;28.08.2026, 16:07:45",
            "",
            "Allgemeine Informationen",
            "Konto;Inhaber;Exportdatum",
            "923887173;Matthias Klauer;28.08.2026, 16:07:45",
            "Kontostand",
            "Saldo;Währung für Saldo;Datum;max. Verfügungsrahmen;Währung für "
            "max. Verfügungsrahmen",
            "11.200,47;EUR;28.08.2026;26.695,77;EUR",
            "Kontoumsätze",
            "Buchung ;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;"
            "Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;"
            "Währung",
        ]
        header, line_no = cppc.search_header(preamble_and_header)
        self.assertEqual(
            header,
            [
                "Buchung",
                "Valuta",
                "Sender / Empfänger",
                "IBAN",
                "BIC",
                "Buchungstext",
                "Verwendungszweck",
                "Kategorie",
                "Stichwörter",
                "Umsatz geteilt",
                "Betrag",
                "Währung",
            ],
        )
        self.assertEqual(line_no, len(preamble_and_header))

    def test_process_transactions_maps_categories_and_types(self):
        rows = [
            {
                "Buchung": "07.08.2026",
                "Verwendungszweck": "GEMEINSAME GELDANLAGE",
                "Kategorie": "Zubuchung",
                "Betrag": "100,00",
                "Währung": "EUR",
            },
            {
                "Buchung": "30.06.2026",
                "Verwendungszweck": "Steuer",
                "Kategorie": "Steuern",
                "Betrag": "-4,16",
                "Währung": "EUR",
            },
            {
                "Buchung": "19.06.2026",
                "Verwendungszweck": "Umbuchung",
                "Kategorie": "Umbuchung zwischen Konten ",
                "Betrag": "4.000,00",
                "Währung": "EUR",
            },
            {
                "Buchung": "17.10.2025",
                "Verwendungszweck": "U7875017 / Matthias Klauer",
                "Kategorie": "Unkategorisierte Ausgaben",
                "Betrag": "-9.000,00",
                "Währung": "EUR",
            },
        ]

        class FakeWriter:
            def __init__(self):
                self.rows = []

            def writerow(self, row):
                self.rows.append(row)

        writer = FakeWriter()
        row_cnt = cppc.process_transactions(rows, writer, header_offset=11)

        self.assertEqual(row_cnt, 4)
        self.assertEqual(
            [row["Typ"] for row in writer.rows],
            ["Einlage", "Steuern", "Umbuchung (Einlage)", "Entnahme"],
        )
        self.assertEqual(writer.rows[0]["Datum"], "07.08.2026")
        self.assertEqual(writer.rows[0]["Wert"], "100,00")
        self.assertEqual(writer.rows[0]["Buchungswährung"], "EUR")
        self.assertEqual(writer.rows[0]["Notiz"], "GEMEINSAME GELDANLAGE")

    @patch("os.path.exists", return_value=False)
    @patch("builtins.print")
    def test_main_file_not_exists(self, mock_print, mock_exists):
        with patch.object(sys, "argv", ["cppc.py", "input.csv"]):
            with self.assertRaises(SystemExit):
                cppc.main()
            mock_print.assert_called_once_with(
                '\033[31mError: Input file "input.csv" does not exist\033[0m'
            )


if __name__ == "__main__":
    unittest.main()
