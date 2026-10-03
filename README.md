# py-currency-converter

**Friendly currency conversion for Python and the terminal.**

Powered by [ECB daily reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
via the free [Frankfurter API](https://frankfurter.dev) — no API key, no
account, no third-party dependencies (standard library only).

```python
>>> from currency_converter import CurrencyConverter
>>> conv = CurrencyConverter()
>>> conv.convert(100, "USD", "EUR")
92.46
>>> conv("100 USD to EUR")          # yes, that works too
92.46
```

## Highlights

- **Nice syntax** — pass numbers, phrases (`"100 USD to EUR"`), or symbols
  (`"$100"`, `"€"`), in any case, with `to` / `in` / `->` / `→` separators.
- **Zero dependencies** — installs in a blink, nothing to break.
- **CLI included** — `currency-converter 100 USD EUR` right after `pip install`
  (the `currency_converter` spelling is installed too).
- **Friendly errors** — typos get a *"did you mean 'USD'?"* suggestion.
- **Historical rates** — any date since 1999, e.g. `CurrencyConverter(date="2024-06-28")`.
- **Tested** (37 tests) and typed (`py.typed` included).

## Installation

From PyPI (once published):

```bash
pip install py-currency-converter
```

Or straight from GitHub:

```bash
pip install git+https://github.com/<username>/py-currency-converter.git
```

## Quick start

```python
from currency_converter import CurrencyConverter

conv = CurrencyConverter()  # fetches the latest ECB rates

conv.convert(100, "USD", "EUR")  # 92.46
conv.convert(100, "usd", "Eur")  # case never matters
conv.rate("USD", "EUR")  # 0.9246... (per 1 USD)
conv.currencies["JPY"]  # 'Japanese yen'
"USD" in conv  # True
```

### The syntax tour

```python
conv(100, "USD", "EUR")  # the object is callable

conv.convert("100 USD to EUR")  # full phrase
conv.convert("$100 to eur")  # symbols as source...
conv.convert("100 usd to €")  # ...or as target
conv.convert("1,000 usd -> jpy")  # arrows work too: -> => → >
conv.convert("₺100")  # source only; target = base (EUR)

conv.convert(100, "USD", "EUR", ndigits=4)  # 92.4642
conv.convert(100, "USD", "EUR", ndigits=None)  # unrounded float
```

### Historical snapshots

```python
conv = CurrencyConverter(date="2024-06-28")  # rates as of that day
```

### Friendly errors

```python
>>> conv.convert(100, "USDD", "EUR")
currency_converter.exceptions.UnknownCurrencyError:
    unknown currency 'USDD' (did you mean 'USD'?)
```

All exceptions derive from `CurrencyConverterError`, so one `except` catches
everything the package can raise.

## Command line

```text
$ currency-converter 100 USD EUR
100.00 USD = 92.46 EUR
  1 USD = 0.924642 EUR  ·  ECB reference rates, 2026-10-02

$ currency-converter '$100 to €' --precision 4
100.0000 USD = 92.4642 EUR

$ currency-converter 100 GBP JPY --date 2024-06-28
100.00 GBP = 19,932.79 JPY

$ currency-converter --list
AUD  Australian dollar
BGN  Bulgarian lev
...
```

Quote expressions containing `$` — otherwise your shell expands them.

The command installs under **both spellings** — `currency-converter` and
`currency_converter` — plus `python -m currency_converter`, so it always
matches the one your fingers remember. See [A note on the name](#a-note-on-the-name).

## A note on the name

Python cannot import hyphens (`import currency-converter` is a syntax error),
so — like `youtube-dl` (`import youtube_dl`) or `python-dotenv`
(`import dotenv`) — the name is spelled differently depending on where you
use it:

| Where                | Name                   |
| -------------------- | ---------------------- |
| `pip install`        | `py-currency-converter` |
| `import` in Python   | `currency_converter`   |
| shell command        | `currency-converter` **or** `currency_converter` |
| `python -m`          | `currency_converter`   |

For `pip` itself the separator never matters: `py_currency_converter`,
`py-currency-converter` and `Py-Currency-Converter` are all the same package
to the installer.

## Where the data comes from

Rates are the euro foreign exchange reference rates published by the
European Central Bank every working day (~16:00 CET), served by
[frankfurter.dev](https://frankfurter.dev) as JSON. That means ~30 major
currencies, one update per business day, no real-time or crypto quotes.

## Development

```bash
git clone https://github.com/<username>/py-currency-converter
cd py-currency-converter
pip install -e .[dev]

pytest               # run the test suite
ruff check .         # lint
python -m build      # build sdist + wheel into dist/
```

CI runs the tests on Python 3.9–3.13 on every push.

## License

[MIT](LICENSE) — do whatever you want, attribution appreciated.
