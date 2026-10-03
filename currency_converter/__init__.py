"""py-currency-converter -- friendly currency conversion for Python.

Rates are the daily reference rates of the European Central Bank, served
by https://frankfurter.dev (no API key needed). The package uses only
the standard library::

    >>> from currency_converter import CurrencyConverter
    >>> conv = CurrencyConverter()
    >>> conv.convert(100, "USD", "EUR")
    92.46
    >>> conv("100 USD to EUR")     # string form
    92.46
"""

from .converter import SYMBOLS, CurrencyConverter, parse_expression
from .exceptions import CurrencyConverterError, NetworkError, UnknownCurrencyError

__version__ = "0.1.0"

__all__ = [
    "CurrencyConverter",
    "CurrencyConverterError",
    "NetworkError",
    "UnknownCurrencyError",
    "SYMBOLS",
    "parse_expression",
    "__version__",
]
