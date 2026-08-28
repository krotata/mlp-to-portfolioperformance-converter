"""Shared helpers for bank-CSV-to-Portfolio-Performance converters."""

import locale
import re
import sys


def opening_hook_csv(filename, mode):
    """CSV opening hook for the fileinput.input() function."""
    return open(filename, mode, newline="", encoding="iso-8859-1")


def print_message(text, color_code):
    """Print a colored message to stdout"""
    print(f"\033[{color_code}m{text}\033[0m")


def convert_to_german_number(number_string):
    """Convert English number string to German format"""
    pattern = r"^-*[,\d]+\.\d{2}$"
    if re.match(pattern, number_string):
        number = float(number_string.replace(",", ""))
        locale.setlocale(locale.LC_ALL, "de_DE")
        return locale.format_string("%.2f", number, grouping=True)
    return number_string


def is_positive(german_number_string):
    return not german_number_string.strip().startswith("-")


def find_header(csv_file, required_columns, max_lines=20):
    """Search for the header row in a CSV file.

    Scans csv_file line by line for a row (split on ";", each field
    stripped) that contains all of required_columns, and returns
    (fields, line_no). Exits with an error message if no such row is found
    within the first max_lines lines, or in the whole file.
    """
    line_no = 0
    found_header = None

    for line in csv_file:
        line_no += 1
        fields = [
            field.strip() for field in line.strip().replace('"', "").split(";")
        ]
        if all(column in fields for column in required_columns):
            found_header = fields
            break
        if line_no >= max_lines:
            print_message(
                f"Error: Header not found in the first {max_lines} lines", 31
            )
            sys.exit(1)

    if found_header is None:
        print_message("Error: Header not found in the file", 31)
        sys.exit(1)

    return found_header, line_no
