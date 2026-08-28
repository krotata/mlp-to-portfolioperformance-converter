import re

from common import print_message

# Categories the Consors "Kategorie" column already assigns a clear Portfolio
# Performance type to.
CATEGORY_TO_TYPE = {
    "Zubuchung": "Einlage",
    "Steuern": "Steuern",
    "Zins- & Kapitalerträge": "Zinsen",
}

# Transfers between the account owner's own accounts get a dedicated
# Portfolio Performance type, chosen by the sign of the amount.
TRANSFER_CATEGORY = "Umbuchung zwischen Konten"

# Consors' own catch-all categories for otherwise unclassified transactions.
# These fall back to Einlage/Entnahme without a warning, unlike a truly
# unrecognized category.
UNCATEGORIZED_CATEGORIES = {"Unkategorisierte Einnahmen", "Unkategorisierte Ausgaben"}


class ConsorsCategoryProcessor:
    def __init__(self, memo, kategorie, line_no="0", is_credit=False):
        self.memo = memo
        line_breaks_removed = re.sub(r"\n\s*", "", memo)
        self.note = re.sub(r"\s+", " ", line_breaks_removed)
        self.kategorie = kategorie.strip()
        self.line_no = str(line_no)
        self.is_credit = is_credit

    def process(self):
        """Determine the Portfolio Performance Typ and Notiz for this row"""
        out_dict = {"Notiz": self.note}

        typ = CATEGORY_TO_TYPE.get(self.kategorie)
        if typ is not None:
            out_dict["Typ"] = typ
        elif self.kategorie == TRANSFER_CATEGORY:
            out_dict["Typ"] = (
                "Umbuchung (Einlage)" if self.is_credit else "Umbuchung (Entnahme)"
            )
        else:
            if self.kategorie not in UNCATEGORIZED_CATEGORIES:
                self.print_warning(f'Unknown category "{self.kategorie}" in line ')
            out_dict["Typ"] = "Einlage" if self.is_credit else "Entnahme"

        return out_dict

    def print_warning(self, text):
        """Print an orange colored warning text to stdout"""
        print_message("Warning: " + text + self.line_no, 33)
