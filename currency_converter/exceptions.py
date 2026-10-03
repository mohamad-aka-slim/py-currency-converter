"""Exceptions raised by py-currency-converter.

They all derive from :class:`CurrencyConverterError`, so callers can catch
the whole family with a single ``except`` clause::

    try:
        conv.convert(100, "USDD", "EUR")
    except CurrencyConverterError as exc:
        print(exc)
"""


class CurrencyConverterError(Exception):
    """Base class for every error this package raises."""


class UnknownCurrencyError(CurrencyConverterError, ValueError):
    """A currency code was not recognised (e.g. ``"USDD"``).

    Also inherits from :class:`ValueError` so it plays nicely with generic
    input validation.
    """


class NetworkError(CurrencyConverterError, RuntimeError):
    """Rates could not be fetched from the remote API."""
