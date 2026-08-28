# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Two Python scripts that each convert a bank's CSV transaction export into a
CSV format importable by [Portfolio
Performance](https://github.com/buchen/portfolio): one for MLP Financepilot
Banking, one for Consors. They share number/CSV-header helpers via
`common.py` but each has its own transaction-classification module, because
the two banks' export formats and how much structure they expose are
genuinely different (see Architecture below).

## Environment setup

- Python 3.10 (see `Pipfile`), managed via `pipenv` (or a plain `.venv`, which is
  already present in the repo checkout).
- On Linux, converting German number formats requires the `de_DE` locale:
  `sudo locale-gen de_DE`.
- Only dev dependency is `pytest`.

```bash
pipenv install --dev   # install dependencies
pipenv shell           # activate the environment
```

## Common commands

```bash
# Run the converters
python mlp_to_portfolio_performance_converter.py testData/Umsaetze.csv
python consors_to_portfolio_performance_converter.py "testData/Umsatzübersicht_923887173.csv"
python mlp_to_portfolio_performance_converter.py <infile> -o <outfile>

# Run all tests (project uses unittest-style TestCase classes, run via pytest)
pytest

# Run a single test file / test case / test method
pytest test_memo_processor.py
pytest test_memo_processor.py::TestMemoProcessor::test_process_wertpapierverkauf

# Equivalent using unittest directly (this is what .vscode is configured for)
python -m unittest discover -v -s . -p "test_*.py"
```

There is sample input/expected-output data in `testData/` for both
converters (`Umsaetze.csv`/`Umsaetze_converted.csv` for MLP,
`Umsatzübersicht_923887173.csv`/`..._converted.csv` for Consors) useful for
manual end-to-end checks.

## Architecture

- **`common.py`** — bank-agnostic helpers shared by both converters:
  `opening_hook_csv` (iso-8859-1, MLP's encoding — Consors overrides this
  locally with its own `utf-8-sig` hook since its export is UTF-8 with a
  BOM), `print_message`, `convert_to_german_number` (requires the `de_DE`
  locale), `is_positive`, and `find_header(csv_file, required_columns,
  max_lines=20)` — a generic "scan the first N lines for a row containing
  all of these column names" search, since both banks' exports have a
  variable-length preamble before the real header row, but disagree on
  which columns identify it. Each converter's own `search_header()` is a
  thin wrapper pinning the columns for its bank.

### MLP (`mlp_to_portfolio_performance_converter.py` / `memo_processor.py`)

- **`mlp_to_portfolio_performance_converter.py`** — the CLI entry point and I/O
  pipeline. It:
  1. Opens the input file with `iso-8859-1` encoding (MLP's export encoding) via
     a `fileinput` open-hook.
  2. `search_header()` scans the first 20 lines for the real CSV header (MLP
     exports have a variable-length preamble before the header row).
  3. Reads rows with `csv.DictReader` and, for each row, converts the amount to
     German decimal format (`convert_to_german_number`, which requires the
     `de_DE` locale) and delegates interpretation of the free-text memo field
     (`Verwendungszweck`) to `MemoProcessor`.
  4. A small `CATEGORY_TO_TYPE` lookup handles rows where MLP already supplies a
     `Category` column value (interest/withholding tax rows) — these bypass
     `MemoProcessor.process()` and go straight to a fixed `Typ`.
  5. Writes rows out via `csv.DictWriter` using the fixed Portfolio Performance
     column set (`Datum`, `Typ`, `Wert`, `Buchungswährung`, `Steuern`, `Stück`,
     `ISIN`, `WKN`, `Ticker-Symbol`, `Wertpapiername`, `Notiz`).

- **`memo_processor.py`** — `MemoProcessor` is the classification engine. MLP's
  memo text (`Verwendungszweck`) is unstructured and its format has changed
  over the years, so this class matches it against an ordered chain of regexes
  in `process()` (deposits, buys/sells, dividends, taxes, fees, transfers,
  etc.) to derive the Portfolio Performance transaction `Typ` and to extract
  structured fields (piece count, WKN, ISIN, stock name, tax amounts) via
  helper methods (`find_pieces`, `find_wkn`, `find_isin`, `find_stock_name`,
  `find_taxes`).
  - **Order matters**: `process()` is a big `if/elif` chain checked in a
    specific priority order (e.g. STORNO/cancellation and old-format buy/sell
    memos must be distinguished before falling through to generic handlers).
    When adding a new memo pattern, be careful about where in the chain it
    goes.
  - A small `stock_dict` in `find_stock_name()` translates known MLP
    abbreviated fund/ETF names to their full names; unknown abbreviations are
    passed through unchanged.
  - Old vs. new transaction text layouts: `find_stock_name()` and
    `find_isin()`/`find_wkn()` have separate regex branches because the
    position of the stock name relative to the WKN changed in MLP's export
    format over time (see `test_process_wertpapierverkauf_old`).
  - When a field expected for a given transaction type can't be parsed
    (missing pieces, WKN, ISIN, stock name), `print_warning()` logs a warning
    to stdout including the source line number; missing pieces or stock name
    specifically mark the transaction as invalid (`transaction_is_valid =
    False`) and it is skipped from output, while a missing WKN/ISIN only warns
    but still emits the row.

### Consors (`consors_to_portfolio_performance_converter.py` / `consors_category_processor.py`)

Consors' export ("Umsatzübersicht") is structurally different enough from
MLP's that it doesn't reuse `MemoProcessor`:
- It has a multi-section preamble (`Allgemeine Informationen`, `Kontostand`,
  `Kontoumsätze`) rather than just a variable-length run-up to the header.
  Account balance is given once in the `Kontostand` section, not as inline
  `Anfangssaldo`/`Endsaldo` rows to filter out (unlike MLP).
- Its header has a column named `"Buchung "` (trailing space) — this is why
  `common.find_header` strips each field individually.
- Transaction meaning is already structured in a `Kategorie` column, so
  `ConsorsCategoryProcessor` is a simple lookup
  (`CATEGORY_TO_TYPE`: `Zubuchung`→Einlage, `Steuern`→Steuern,
  `Zins- & Kapitalerträge`→Zinsen) plus two special cases instead of a regex
  chain: `Umbuchung zwischen Konten` (inter-account transfers) maps to PP's
  `Umbuchung (Einlage)`/`Umbuchung (Entnahme)` by sign, and anything else
  unrecognized (including Consors' own `Unkategorisierte
  Einnahmen`/`Ausgaben` catch-alls) falls back to plain `Einlage`/`Entnahme`
  by sign — printing a warning only for categories outside that expected
  fallback set, so genuinely new/unhandled categories still get surfaced.
- This account is cash-only in practice (deposits, withdrawals, taxes,
  interest); there's no security-trade (buy/sell/dividend/WKN/ISIN) handling
  here the way MLP's `MemoProcessor` has.

## Testing conventions

- Tests use `unittest.TestCase` (not pytest fixtures/asserts), even though they
  are commonly run via `pytest`.
- `test_memo_processor.py` tests are largely characterization tests against
  real (anonymized) MLP memo strings for each transaction type — when adding
  support for a new memo format, follow this pattern: add a real example memo
  string as a new test case.
- `test_mlp_to_portfolio_performance_converter.py` and
  `test_consors_to_portfolio_performance_converter.py` use
  `unittest.mock.patch` extensively to isolate `open`, `print`, and
  `sys.argv`/`os.path.exists` rather than touching the real filesystem.
