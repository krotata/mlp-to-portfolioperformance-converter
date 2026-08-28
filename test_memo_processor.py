import unittest

from memo_processor import MemoProcessor


class TestMemoProcessor(unittest.TestCase):
    def test_process_depotentgelt(self):
        processor = MemoProcessor(
            "0008 DEPOTENTGELT 26259318 Q1/2021 DEPOT 8507908370 UST-ID            DE143449956 NETTO 12,24EUR 19%     "
            "UST. 2,33EUR"
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Gebühren")
        self.assertEqual(
            result["Notiz"],
            "0008 DEPOTENTGELT 26259318 Q1/2021 DEPOT 8507908370 UST-ID DE143449956 NETTO 12,24EUR 19% "
            "UST. 2,33EUR",
        )

    def test_process_wertpapierverkauf(self):
        processor = MemoProcessor(
            "WERTPAPIERABRECHNUNG VERKAUF WKN   A1J3M4 / LU0728929174 ASSCVI-WLD   SM.COMP. AAEO DEPOTNR.: 8507908370 "
            "HANDELSTAG 06.04.2021              MENGE 15,2580 KUR                  S 27,12610000                      "
            "AUFTRAGSNR. 7612487000",
            is_credit=True,
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Verkauf")
        self.assertEqual(result["Stück"], "15,2580")
        self.assertEqual(result["WKN"], "A1J3M4")
        self.assertEqual(result["ISIN"], "LU0728929174")
        self.assertEqual(result["Wertpapiername"], "ASSCVI-WLD SM.COMP. AAEO")

    def test_process_storno_wertpapierverkauf(self):
        processor = MemoProcessor(
            "STORNOSTORNO WERTPAPIERABRECHNUNG VERKAUF WKN   A1J3M4 / LU0728929174 ASSCVI-WLD   SM.COMP. AAEO DEPOTNR.: 8507908370 "
            "HANDELSTAG 06.04.2021              MENGE 15,2580 KUR                  S 27,12610000                      "
            "AUFTRAGSNR. 7612487000",
            is_credit=False,
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Kauf")
        self.assertEqual(result["Stück"], "15,2580")
        self.assertEqual(result["WKN"], "A1J3M4")
        self.assertEqual(result["ISIN"], "LU0728929174")
        self.assertEqual(result["Wertpapiername"], "ASSCVI-WLD SM.COMP. AAEO")

    def test_process_wertpapierverkauf_old(self):
        processor = MemoProcessor(
            """
            DEPOT    8505581964 
            WERTPAPIERABRECHNUNG 
            DEPOT-NR       8505581964 
            RENTENSTRAT. MULTIMAN. OP 
            WKN A0M5RE / LU0326856928 
            HANDELSTAG       08.10.2014
            MENGE                0,8830
            KURS            52,28000000
            ZAST/KAPST            0,17 
            SOLZ            0,01 
            AUFTR.-NR.  000001796491800
            """,
            is_credit=True,
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Verkauf")
        self.assertEqual(result["Stück"], "0,8830")
        self.assertEqual(result["WKN"], "A0M5RE")
        self.assertEqual(result["ISIN"], "LU0326856928")
        self.assertEqual(result["Wertpapiername"], "RENTENSTRAT. MULTIMAN. OP")

    def test_process_dividend(self):
        processor = MemoProcessor(
            "WP- ERTRÄGNISGUTSCHRIFT             INVESTMENTFONDS WKN A0M430 /       LU0323578657                      "
            " FLOSSB.V.STORCH-MUL.OPP.R          DEPOTNR.: 8507908370 MENGE         1,7540 ABRECHN.NR. 84724240680"
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Dividende")

    def test_process_steuerrueckzahlung(self):
        processor = MemoProcessor("""
                                  GUTSCHRIFT: 
                                  STEUERAUSGLEICH 
                                  KAP.STEUER 3,86 EURO
                                  """)
        result = processor.process()
        self.assertEqual(result["Typ"], "Steuerrückerstattung")
        self.assertEqual(
            result["Notiz"], "GUTSCHRIFT: STEUERAUSGLEICH KAP.STEUER 3,86 EURO"
        )

    def test_storno_steuerrueckzahlung(self):
        processor = MemoProcessor("""
            STORNOSTORNO WERTPAPIERABRECHNUNG
            VERKAUF STEUERAUSGLEICH
            WKN A14XAR / FR0010858498
            LAZARD CONV.GLOBAL RCEODEPOTNR.: 8505581964
            HANDELSTAG 02.02.2024
            MENGE 1,6960
            KURS 470,63000000
            AUFTRAGSNR. 7051699250
        """)
        result = processor.process()
        self.assertEqual(result.get("Typ"), "Steuern")

    def test_process_steuererstattung(self):
        processor = MemoProcessor("Steuererstattung Kirchenst.Steuerausgleich")
        result = processor.process()
        self.assertEqual(result["Typ"], "Steuerrückerstattung")
        self.assertEqual(
            result["Notiz"], "Steuererstattung Kirchenst.Steuerausgleich"
        )

    def test_process_steuerbelastung(self):
        processor = MemoProcessor(
            "Steuerbelastung Kap.Steuer         Rückzahlung Bestandsprovisionen"
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Steuern")
        self.assertEqual(
            result["Notiz"],
            "Steuerbelastung Kap.Steuer Rückzahlung Bestandsprovisionen",
        )

    def test_process_vorabpauschale(self):
        processor = MemoProcessor(
            "VORABPAUSCHALEINVESTMENTFONDSWKN   A1H6XK / LU0552385295MORGAN        "
            "STAN.I-GL.OPP.ADLDEPOTNR.:         8507908370MENGE 8,8780KAPST        1,97SOLZ 0,"
            "11KIST                  0,16ABRECHN.NR. 51264614230"
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Steuern")
        self.assertEqual(result["Steuern"], "2,24")
        self.assertEqual(result["Wertpapiername"], "MORGAN STAN.I-GL.OPP.ADL")
        self.assertEqual(result.get("WKN"), "A1H6XK")

    def test_process_effektengutschrift(self):
        processor = MemoProcessor("""
            EFFEKTENGUTSCHRIFT
            WP-ERTRï¿½GNISGUTSCHRIFT
            INVESTMENTFONDS
            WKN A0LHCM / LU0278152516
            ACATIS F.V.M.VERMOEG.1 A
            DEPOTNR.:      8505581964
            MENGE             73,2960
            KAPST           42,88
            SOLZ             2,35
            KIST             1,70
            ABRECHN.NR.     57849107710
            """)
        result = processor.process()
        self.assertEqual(result.get("Typ"), "Dividende")
        self.assertEqual(result.get("Stück"), "73,2960")
        self.assertEqual(result.get("Steuern"), "46,93")

    def test_process_effektengutschrift_one_line(self):
        processor = MemoProcessor(
            "WP- ERTRÄGNISGUTSCHRIFT INVESTMENTFONDSWKN A0LHCM /"
            "LU0278152516ACATIS F.V.M.VERMOEG.1 ADEPOTNR.: 8505581964"
            "MENGE 73,2960KAPST 42,88SOLZ 2,35KIST 1,70ABRECHN.NR. 57849107710"
        )
        result = processor.process()
        self.assertEqual(result.get("Typ"), "Dividende")
        self.assertEqual(result.get("Stück"), "73,2960")
        self.assertEqual(result.get("Steuern"), "46,93")

    def test_process_wertpapierkauf(self):
        processor = MemoProcessor(
            """
            EFFEKTEN
            WERTPAPIERABRECHNUNG
            KAUF
            WKN A12GPB / IE00BQ3D6V05
            COMGEST GROWTH ASIA DLAC
            DEPOTNR.:      8505581964
            HANDELSTAG 05.03.2024
            MENGE              0,9070
            KURS       59,87000000
            DEVISENKURS       1,0870000
            AUFTRAGSNR.      7498553600
            """,
            is_credit=True,
        )
        result = processor.process()
        self.assertEqual(result["Typ"], "Kauf")

    def test_process_erstattung_vertriebsfolgeprovision(self):
        processor = MemoProcessor("""
                GUTSCHRIFT
                0060 ERSTATTUNG VERTRIEBSFO
                LGEPROVISION/BESTANDSPROVIS
                ION 58384158 Q1/2024 DEPOT
                8507908370 EREF: VFP 2024 Q
                UARTAL I
                """)
        result = processor.process()
        self.assertEqual(result["Typ"], "Gebührenerstattung")
        self.assertEqual(result["Notiz"], "Erstattung Vertriebsfolgeprovision")

    def test_process_wertpapierabrechnung_kauf_old(self):
        processor = MemoProcessor(
            "DEPOT    8505581964                WERTPAPIERABRECHNUNG               DEPOT-NR     "
            "  8505581964          FRANKF.AKTIENFO.F.STIFT.T          WKN A0M8HD / DE000A0M8HD2 "
            "         HANDELSTAG       15.09.2014        MENGE                0,5050        "
            "KURS            98,94000000        AUFTR.-NR.  000001814863300"
        )
        result = processor.process()
        self.assertEqual(result.get("Typ"), "Kauf")
        self.assertEqual(result.get("Stück"), "0,5050")
        self.assertEqual(result.get("WKN"), "A0M8HD")
        self.assertEqual(result.get("ISIN"), "DE000A0M8HD2")
        self.assertEqual(result.get("Wertpapiername"), "FRANKF.AKTIENFO.F.STIFT.T")

    def test_process_dividende_old(self):
        processor = MemoProcessor(
            "DEPOT     8505581964               WP-ERTRÄGNISGUTSCHRIFT             DEPOT-NR     "
            "  8505581964          FRANKF.AKTIENFO.F.STIFT.T          WKN A0M8HD / DE000A0M8HD2 "
            "         ABRECHNUNGSTAG   02.10.2014        MENGE                0,5050        "
            "AUFTR.-NR.  000077508075250"
        )
        result = processor.process()
        self.assertEqual(result.get("Typ"), "Dividende")
        self.assertEqual(result.get("Stück"), "0,5050")
        self.assertEqual(result.get("WKN"), "A0M8HD")
        self.assertEqual(result.get("ISIN"), "DE000A0M8HD2")
        self.assertEqual(result.get("Wertpapiername"), "FRANKF.AKTIENFO.F.STIFT.T")

    def test_process_retoure_shall_not_be_processed(self):
        processor = MemoProcessor(
            "Retoure SEPA Lastschrift vom 02.10.2017, Rueckgabegrund: AC06 Konto gesperrt SVWZ: "
            "RETURN/REFUND, 3702517 VERMOEGENSDEPOT SAMMELBUCHUNG SPARPLAN WKN A0M430, 974968, "
            "A0M8HD A0RB8A, 847811, 984811 u.a. EREF: SPARSP 2802474 ENTG: 3,00 EUR SEPA "
            "Basislastschrift Rücklas     EREF+SPARSP 2802474        MREF+WPBF0000017817 [MLP "
            "Vermögensdepot Konto] Retoure SEPA Lastschrift vom 02.10.2017, Rueckgabegrun -4,"
            "500.00 -  Depotkosten:Orderstreichung -3.00 - ",
            is_credit=False,
        )
        result = processor.process()
        self.assertEqual(result.get("Typ"), "Entnahme")

    def test_find_pieces(self):
        processor = MemoProcessor("MENGE 10")
        result = processor.find_pieces()
        self.assertEqual(result, "10")

    def test_find_wkn(self):
        processor = MemoProcessor("WKN 123456 /")
        result = processor.find_wkn()
        self.assertEqual(result, "123456")

    def test_find_isin(self):
        processor = MemoProcessor("WKN 123456 / LU1234567890")
        result = processor.find_isin()
        self.assertEqual(result, "LU1234567890")

    def test_find_isin_steuerausgleich(self):
        processor = MemoProcessor(
            "WERTPAPIERABRECHNUNG VERKAUF       STEUERAUSGLEICH WKN 974515 /       LU0087412390 DWS CON.DJE           "
            "ALP.REN.GL LC DEPOTNR.:            8505581964 HANDELSTAG 04.10.2018   MENGE 3,3940 KURS 121,57000000     "
            "AUFTRAGSNR. 2026035700"
        )
        result = processor.find_isin()
        self.assertEqual(result, "LU0087412390")

    def test_find_stock_name_with_spaces(self):
        processor = MemoProcessor(
            "WKN 123456 / DE1234567890 ACATIS-GANE VAL.EV.F.UI A    DEPOT"
        )
        result = processor.find_stock_name()
        self.assertEqual("Acatis Gané Value Event Fonds", result)

    def test_find_stock_name_with_line_breaks(self):
        processor = MemoProcessor("""
            WKN 123456 / US1234567890
            S&P 500 ETF
            DEPOT
            """)
        result = processor.find_stock_name()
        self.assertEqual("S&P 500 ETF", result)

    def test_find_stock_name_old(self):
        processor = MemoProcessor(
            "DEPOT    8505581964                WERTPAPIERABRECHNUNG               DEPOT-NR     "
            "  8505581964          FRANKF.AKTIENFO.F.STIFT.T          WKN A0M8HD / DE000A0M8HD2 "
            "         HANDELSTAG       15.09.2014        MENGE                0,5050        "
            "KURS            98,94000000        AUFTR.-NR.  000001814863300"
        )
        result = processor.find_stock_name()
        self.assertEqual("FRANKF.AKTIENFO.F.STIFT.T", result)

    def test_find_taxes(self):
        processor = MemoProcessor("""
            KAPST 10,00-
            SOLZ 5,00-
            KIST 2,00-
            """)
        result = processor.find_taxes()
        self.assertEqual(result, "17,0")

    def test_find_taxes_with_thousand_separator(self):
        processor = MemoProcessor("""
            KAPST 10.000,00-
            SOLZ 5.000,00-
            KIST 2.000,00-
            """)
        result = processor.find_taxes()
        self.assertEqual(result, "17000,0")


if __name__ == "__main__":
    unittest.main()
