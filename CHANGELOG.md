# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-04

### Added

- `CurrencyConverter` class: `convert()`, `rate()`, `currencies`, `rates`,
  `base`, `date`, callable shortcut, and `in` support.
- Phrase parsing: `"100 USD to EUR"`, symbols (`$ € £ ¥ ₹ ₪ ₩ ฿ ₺`),
  separators `to` / `in` / `->` / `=>` / `→` / `>`, thousands commas.
- Historical rates via `CurrencyConverter(date="YYYY-MM-DD")`.
- Friendly typos: `UnknownCurrencyError` with did-you-mean suggestions.
- `currency-converter` CLI with `--date`, `--precision`, `--base`, `--list`.
- ECB reference rates via frankfurter.dev; standard library only.
- Test suite (37 tests), type markers (`py.typed`), CI on Python 3.9–3.13.
