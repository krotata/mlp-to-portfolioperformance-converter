import re

# Regular expressions to find categories of transactions
deposit_re = re.compile(r"LASTSCHRIFTEINR\.\s*")
sell_re = re.compile(r"EFFEKTENGUTSCHRIFT\s*WERTPAPIERABRECHNUNG\s*VERKAUF")
sell_old_re = re.compile(r"EFFEKTENGUTSCHRIFT\s*DEPOT.*\s*WERTPAPIERABRECHNUNG")
tax_ret_re = re.compile(
    r"EFFEKTENGUTSCHRIFT\s*WERTPAPIERABRECHNUNG\s*KAUF\s*STEUERAUSGLEICH"
)
dividend_re = re.compile(r"\s*WP-\s*ERTR\S+GNISGUTSCHRIFT")
buy_re = re.compile(r"WERTPAPIERABRECHNUNG\s*KAUF\s*")
collect_re = re.compile(r"EINZUGSERMAECHTIGUNG\s*")
credit_re = re.compile(r"GUTSCHRIFT|.+SAMMELBUCHUNG|.+ERSTATTUNG")
church_tax_re = re.compile(r"KIRCHENSTEUER\s*")
soli_tax_re = re.compile(r"SOLIDARIT\S+TSZUSCHLAG\s*")
capital_gain_tax_re = re.compile(r"KAPITALERTRAGSTEUER\s*")
transfer_re = re.compile(r"UEBERWEISUNG\s*")
fee_re = re.compile(r"ENTGELT\s*")


class MemoProcessor:
    def __init__(self, memo, line_no="0", is_credit=False):
        self.memo = memo
        line_breaks_removed = re.sub("\n\s*", "", memo)
        self.note = re.sub("\s+", " ", line_breaks_removed)
        self.line_no = str(line_no)
        self.is_credit = is_credit

    def process(self):
        # Determine output values that depend on the transaction type
        out_dict = {}
        transaction_is_valid = True
        if deposit_re.match(self.memo) is not None:
            if self.memo.find("SPARPLAN") != -1:
                out_dict["Notiz"] = "Sparplan"
            out_dict["Typ"] = "Einlage"

        elif "STEUERAUSGLEICH" in self.note or "Steuererstattung" in self.note:
            out_dict["Notiz"] = self.note
            if "STORNO" in self.note:
                out_dict["Typ"] = "Steuern"
            else:
                out_dict["Typ"] = "Steuerrückerstattung"

        elif "VORABPAUSCHALE" in self.memo:
            out_dict["Typ"] = "Steuern"
            out_dict["Stück"] = self.find_pieces()
            out_dict["Steuern"] = self.find_taxes()
            out_dict["Wertpapiername"] = self.find_stock_name()
            out_dict["WKN"] = self.find_wkn()

        elif (
            "WERTPAPIERABRECHNUNG" in self.memo
            and ("VERKAUF" in self.note or "DEPOT " in self.note)
            and self.is_credit
        ):
            pieces = self.find_pieces()
            if pieces == "":
                self.print_warning("Could not find number of pieces in line ")
                transaction_is_valid = False
            wkn = self.find_wkn()
            if wkn == "":
                self.print_warning("Could not find WKN in line ")
            # We can still use the transaction
            isin = self.find_isin()
            if isin == "":
                self.print_warning("Could not find ISIN in line ")
            # We can still use the transaction
            name = self.find_stock_name()
            if name == "":
                self.print_warning("Could not find the stock name in line ")
                transaction_is_valid = False
            taxes = self.find_taxes()
            if transaction_is_valid:
                out_dict["Typ"] = "Kauf" if "STORNO" in self.memo else "Verkauf"
                out_dict["Stück"] = pieces
                out_dict["WKN"] = wkn
                out_dict["ISIN"] = isin
                out_dict["Wertpapiername"] = name
                out_dict["Steuern"] = str(taxes).replace(".", ",")

        elif "WERTPAPIERABRECHNUNG" in self.memo and (
            "KAUF" in self.note or "DEPOT" in self.note
        ):
            pieces = self.find_pieces()
            if pieces == "":
                self.print_warning("Could not find number of pieces in line ")
                transaction_is_valid = False
            wkn = self.find_wkn()
            if wkn == "":
                self.print_warning("Could not find WKN in line ")
            # We can still use the transaction
            isin = self.find_isin()
            if isin == "":
                self.print_warning("Could not find ISIN in line ")
            # We can still use the transaction
            name = self.find_stock_name()
            if name == "":
                self.print_warning("Could not find the stock name in line ")
                transaction_is_valid = False
            if transaction_is_valid:
                out_dict["Typ"] = "Kauf"
                out_dict["Stück"] = pieces
                out_dict["WKN"] = wkn
                out_dict["ISIN"] = isin
                out_dict["Wertpapiername"] = name

        elif dividend_re.search(self.memo) is not None:
            out_dict["Typ"] = "Dividende"
            out_dict["Notiz"] = self.note
            out_dict["Stück"] = self.find_pieces()
            out_dict["WKN"] = self.find_wkn()
            out_dict["ISIN"] = self.find_isin()
            out_dict["Wertpapiername"] = self.find_stock_name()
            out_dict["Steuern"] = self.find_taxes()

        elif self.memo.find("DEPOTENTGELT") != -1:
            out_dict["Typ"] = "Gebühren"
            out_dict["Notiz"] = self.note

        elif (collect_re.match(self.memo) is not None) or fee_re.match(
            self.memo
        ) is not None:
            out_dict["Typ"] = "Entnahme"
            out_dict["Notiz"] = "Unbekannte Abbuchung"

        elif credit_re.match(self.note) is not None:
            if "VERTRIEBSFOLGEPROVISION" in self.note:
                out_dict["Typ"] = "Gebührenerstattung"
                out_dict["Notiz"] = "Erstattung Vertriebsfolgeprovision"
            elif "Retoure" in self.note:
                out_dict["Typ"] = "Entnahme"
                out_dict["Notiz"] = self.note
            else:
                out_dict["Typ"] = "Einlage"
                out_dict["Notiz"] = self.note

        elif "Steuerbelastung" in self.note:
            out_dict["Typ"] = "Steuern"
            out_dict["Notiz"] = self.note

        elif church_tax_re.match(self.memo) is not None:
            out_dict["Typ"] = "Steuern"
            out_dict["Notiz"] = "Kirchensteuer"

        elif soli_tax_re.match(self.memo) is not None:
            out_dict["Typ"] = "Steuern"
            out_dict["Notiz"] = "Solidaritätszuschlag"

        elif capital_gain_tax_re.match(self.memo) is not None:
            out_dict["Typ"] = "Steuern"
            out_dict["Notiz"] = "Kapitalertragsteuer"

        elif transfer_re.match(self.memo):
            out_dict["Typ"] = "Entnahme"
        else:
            self.print_warning("Unknown transaction type in line ")

        return out_dict

    def find_pieces(self):
        """Find the number of traded stock pieces in a transaction text

        Returns the number of pieces as a string if the number was found and an
        empty string otherwise
        """
        regex = r"MENGE\s+(\d+,?\d*)"
        matches = re.search(regex, self.memo)
        if matches:
            return matches.group(1)
        else:
            return ""

    def print_warning(self, text):
        """Print an orange colored warning text to stdout"""
        print("\033[33mWarning: " + text + self.line_no + "\033[0m")

    def find_wkn(self):
        """Find the WKN in a transaction text

        Returns the WKN if it was found and an empty string otherwise
        """
        regex = r"WKN\s+(\w{6})\s*/"
        matches = re.search(regex, self.memo)
        if matches:
            return matches.group(1)
        else:
            return ""

    def find_isin(self):
        """Find the ISIN in a transaction text

        Returns the ISIN if it was found and an empty string otherwise
        """
        regex = r"WKN.*/ ([0-9a-zA-Z]*)"
        matches = re.search(regex, self.note)
        if matches:
            return matches.group(1)
        else:
            return ""

    def find_stock_name(self):
        """Find and translate the stock name in a transaction text

        Returns the stock name if it was found and an empty string otherwise. The
        stock name is translated to a more readable string if the abbreviated
        version is known. If it is unknown, the abbreviated string is returned.
        """
        # Dictionary mapping abbreviated stock names to full stock names
        stock_dict = {
            "ACATIS-GANE VAL.EV.F.UI A": "Acatis Gané Value Event Fonds",
            "ISHS CORE DAX UCITS ETF": "iShares Core DAX UCITS ETF",
            "ISHSIII-CORE MSCI WLD DLA": "iShares Core MSCI World UCITS ETF",
            "CARMIGN.PATRIMOI. AEO ACC": "Carmignac Patrimoine A",
            "THREADN.INV.-EU.S.C. RAEO": "Threadneedle European Smaller Companies",
            "ETHNA-DEFENSIV INH. T": "Ethna-Defensiv T EUR ACC",
        }

        regex = r"WKN\s*\w{6}\s*/\s*\w{12}\s*(.+?)\s*DEPOT"
        matches = re.search(regex, self.note)
        if matches:
            name = matches.group(1)
        else:
            # Old transaction text. We have to look before the WKN
            # The structure of the transaction has changed over time: the stock name
            # used to be in the line before the WKN but is now in the line after the
            # WKN. If the name contains "HANDELSTAG" we assume that we have an old
            # transcation text.
            regex = r"DEPOT-NR \d* (.*)\sWKN.*/.*\s"
            matches = re.search(regex, self.note)
            if matches:
                name = matches.group(1)
            else:
                return ""

        # Try to translate the abbreviated name
        if name in stock_dict:
            return stock_dict[name]
        else:
            return name

    def find_taxes(self):
        """Find tax amount in a transaction text

        Looks for tax substractions and returns the total amount of taxes if there
        are any, and 0 otherwise.
        """
        kap = self._extract_tax("KAPST")
        soli = self._extract_tax("SOLZ")
        kist = self._extract_tax("KIST")
        taxes = kap + soli + kist
        return str(round(taxes, 2)).replace(".", ",")

    def _extract_tax(self, tax_type):
        tax = 0
        tax_regex = rf"{tax_type}\s+([\d.,]+)"

        matches = re.search(tax_regex, self.memo)
        if matches:
            tax_str = matches.group(1).replace(".", "")
            tax = float(tax_str.replace(",", "."))

        return tax
