import unittest
from unittest.mock import patch

from consors_category_processor import ConsorsCategoryProcessor


class TestConsorsCategoryProcessor(unittest.TestCase):
    def test_process_zubuchung(self):
        processor = ConsorsCategoryProcessor(
            "GEMEINSAME GELDANLAGE", "Zubuchung", is_credit=True
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Einlage")
        self.assertEqual(result["Notiz"], "GEMEINSAME GELDANLAGE")

    def test_process_steuer(self):
        processor = ConsorsCategoryProcessor("Steuer", "Steuern", is_credit=False)
        result = processor.process()
        self.assertEqual(result["Typ"], "Steuern")

    def test_process_zinsen(self):
        processor = ConsorsCategoryProcessor(
            "Abschluss", "Zins- & Kapitalerträge", is_credit=True
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Zinsen")

    def test_process_umbuchung_credit(self):
        processor = ConsorsCategoryProcessor(
            "Umbuchung", "Umbuchung zwischen Konten ", is_credit=True
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Umbuchung (Einlage)")

    def test_process_umbuchung_debit(self):
        processor = ConsorsCategoryProcessor(
            "Umbuchung", "Umbuchung zwischen Konten ", is_credit=False
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Umbuchung (Entnahme)")

    def test_process_unkategorisierte_einnahmen(self):
        with patch("builtins.print") as mock_print:
            processor = ConsorsCategoryProcessor(
                "EURO-Überweisung", "Unkategorisierte Einnahmen", is_credit=True
            )
            result = processor.process()
            mock_print.assert_not_called()
        self.assertEqual(result["Typ"], "Einlage")

    def test_process_unkategorisierte_ausgaben(self):
        with patch("builtins.print") as mock_print:
            processor = ConsorsCategoryProcessor(
                "U7875017 / Matthias Klauer",
                "Unkategorisierte Ausgaben",
                is_credit=False,
            )
            result = processor.process()
            mock_print.assert_not_called()
        self.assertEqual(result["Typ"], "Entnahme")

    def test_process_unknown_category_warns_and_falls_back(self):
        with patch("builtins.print") as mock_print:
            processor = ConsorsCategoryProcessor(
                "Something new", "Some New Category", 5, is_credit=True
            )
            result = processor.process()
            mock_print.assert_called_once()
        self.assertEqual(result["Typ"], "Einlage")

        with patch("builtins.print") as mock_print:
            processor = ConsorsCategoryProcessor(
                "Something new", "Some New Category", 5, is_credit=False
            )
            result = processor.process()
            mock_print.assert_called_once()
        self.assertEqual(result["Typ"], "Entnahme")

    def test_note_cleans_line_breaks_and_whitespace(self):
        processor = ConsorsCategoryProcessor(
            "Foo \n            Bar",
            "Zubuchung",
            is_credit=True,
        )
        result = processor.process()
        self.assertEqual(result["Notiz"], "Foo Bar")


if __name__ == "__main__":
    unittest.main()
