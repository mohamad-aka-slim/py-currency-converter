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
- `currency-converter` CLI with `--date`, `--precision`, `--base`, `--list`
  (installed as `currency_converter` too, and runnable via
  `python -m currency_converter`).
- ECB reference rates via frankfurter.dev; standard library only.
- Test suite (37 tests), type markers (`py.typed`), CI on Python 3.9–3.13.

### Fixed

- Parsing `"42,50"` / `"100,50"` as `4250` / `10050` — European decimal
  commas are now read correctly and genuinely ambiguous amounts (`1,0000`)
  are rejected with an explanation.
- `--precision -1` crashed the CLI with a raw traceback; precision is now
  validated (0–10) with a clean argparse error.
- `Decimal`/`Fraction` amounts raised `TypeError`; `inf`/`nan` were
  accepted. Both now convert or raise a clear `ValueError`.
- Invalid `--base`/`--date` hit the network and surfaced as an opaque
  HTTP 404/422; they are now validated client-side before any request.
- Non-JSON responses (captive portals) and malformed payloads produced
  raw `JSONDecodeError`s; the client now raises `NetworkError` with the
  response excerpt.
- Transient connection failures are retried (3 attempts, no retry on
  HTTP errors); uppercase `TO`/`IN` separators, negative amounts,
  dot-grouped amounts and lowercase codes all parse.

The adversarial pass grew the suite from 37 to 93 tests.
