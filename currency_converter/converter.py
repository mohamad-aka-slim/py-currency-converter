"""The public API: one class, a handful of methods, no surprises.

::

    >>> conv = CurrencyConverter()
    >>> conv.convert(100, "USD", "EUR")
    92.46
    >>> conv("100 USD to EUR")      # same thing, string form
    92.46
"""

import re
from difflib import get_close_matches
from math import isfinite

from .client import fetch_currencies, fetch_rates
from .exceptions import UnknownCurrencyError

# A few well-known currency symbols, so "$100" and "€" read naturally.
# Only symbols the ECB actually publishes rates for (see frankfurter.dev).
SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₪": "ILS",
    "₩": "KRW",
    "฿": "THB",
    "₺": "TRY",
}

# Understands "100 USD to EUR", "$42.50 -> gbp", "1.234,56 in JPY", "-3 to USD", ...
# [0-9] (not \d) so fullwidth/Arabic-Indic digits are rejected rather than
# crashing float() later; re.IGNORECASE so "TO"/"IN" work as separators.
_EXPRESSION = re.compile(
    r"""
    ^\s*
    (?:(?P<from_symbol>[$€£¥₹₪₩฿₺])\s*)?        # optional symbol before the amount
    (?P<amount>-?[0-9][0-9.,\s]*)               # the amount; parse_amount() validates
    \s*
    (?:(?P<from>[A-Za-z]{3}))?                  # optional source code
    \s*
    (?:
        (?:->|=>|to|in|→|>)                     # separator
        \s*
        (?:(?P<to_symbol>[$€£¥₹₪₩฿₺])\s*)?   # optional target symbol
        (?P<to>[A-Za-z]{3})?                    # target code (or just a symbol)
    )?
    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)


def parse_amount(text):
    """Turn the amount part of an expression into a float.

    Accepts US style (``1,234.56``), European style (``1.234,56`` or
    ``42,50``) and space grouping (``1 000 000``). The rules, so nothing
    is ever silently misread by a factor of a thousand:

    * with mixed separators, the *last* one is the decimal point
    * a single dot is always a decimal point (``1.000`` is one)
    * a single comma followed by exactly three digits is a thousands
      separator (``1,000`` is a thousand); with fewer digits it is a
      decimal point (``42,50``), with more it is an error (``1,0000``)
    * repeated separators are grouping: ``1,000,000`` and ``1.000.000``
      are both a million
    """
    s = re.sub(r"\s+", "", str(text))
    if not re.fullmatch(r"-?[0-9]+(?:[.,][0-9]+)*", s):
        raise ValueError(f"could not read the amount {s!r}")

    negative = s.startswith("-")
    body = s.removeprefix("-")
    if "." not in body and "," not in body:
        return -float(body) if negative else float(body)

    pos = max(body.rfind("."), body.rfind(","))
    sep, tail = body[pos], body[pos + 1 :]
    integer = body[:pos]

    def bad():
        return ValueError(f"could not read the amount {s!r}")

    if sep in integer:
        # Repeated same separator: pure grouping ("1,000,000", "1.000.000").
        groups = body.split(sep)
        if not all(len(g) == 3 for g in groups[1:]):
            raise bad()
        number = "".join(groups)
    elif "," in integer or "." in integer:
        # Mixed separators: the last one is the decimal point, the other
        # one must group in threes ("1,234.56", "1.234,56").
        groups = integer.split("," if sep == "." else ".")
        if not all(len(g) == 3 for g in groups[1:]):
            raise bad()
        number = "".join(groups) + "." + tail
    else:
        # Single separator: a dot is always decimal; a comma is decimal
        # too, unless it groups exactly three digits ("1,000" -> one
        # thousand) after a non-zero integer part ("0,500" reads 0.5).
        if sep == "," and len(tail) == 3 and integer != "0":
            number = integer + tail
        else:
            if sep == "," and len(tail) > 3 and integer != "0":
                raise ValueError(f"ambiguous amount {s!r} -- write it without separators")
            number = integer + "." + tail

    value = float(number)
    return -value if negative else value


def parse_expression(text, default_from=None, default_to=None):
    """Parse a string like ``"100 USD to EUR"`` into ``(amount, from, to)``.

    Currency codes are upper-cased and symbols (``$`` ``€`` ``£`` ...) are
    resolved to their ISO code. Anything the string leaves out falls back
    to *default_from* / *default_to*, or stays ``None`` if not given.
    """
    match = _EXPRESSION.match(text)
    if match is None:
        raise ValueError(f"could not read {text!r} -- try something like '100 USD to EUR'")
    parts = match.groupdict()
    amount = parse_amount(parts["amount"])
    frm = parts["from"] or SYMBOLS.get(parts["from_symbol"]) or default_from
    to = parts["to"] or SYMBOLS.get(parts["to_symbol"]) or default_to
    return amount, frm.upper() if frm else None, to.upper() if to else None


class CurrencyConverter:
    """Convert money between currencies using ECB daily reference rates.

    Rates are fetched once, when the converter is created, and kept in
    memory; converting is then pure arithmetic.

    :param base: currency the rates are quoted against (default ``"EUR"``)
    :param date: ``"latest"`` or an ISO date such as ``"2024-06-28"``
        for a historical snapshot

    Usage::

        conv = CurrencyConverter()
        conv.convert(100, "USD", "EUR")     # 92.46
        conv("100 USD to EUR")              # same thing
        conv.rate("USD", "EUR")             # 0.9246...
    """

    def __init__(self, base="EUR", date="latest"):
        data = fetch_rates(base=base, date=date)
        self._base = data["base"]
        self._date = data["date"]
        # Store everything as "1 <base> = rate <code>", including the base
        # itself (rate 1.0), so any pair converts with a single division.
        self._rates = {code: float(rate) for code, rate in data["rates"].items()}
        self._rates[self._base] = 1.0
        self._names = fetch_currencies()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def base(self):
        """The currency rates are quoted against, e.g. ``"EUR"``."""
        return self._base

    @property
    def date(self):
        """The date of this rate snapshot, e.g. ``"2026-10-02"``."""
        return self._date

    @property
    def rates(self):
        """A copy of the rate table: ``1 base = rates[code] code``."""
        return dict(self._rates)

    @property
    def currencies(self):
        """Supported currency codes and their display names."""
        return dict(self._names)

    def __contains__(self, code):
        try:
            self._resolve(code)
        except UnknownCurrencyError:
            return False
        return True

    def __repr__(self):
        return (
            f"CurrencyConverter(base={self._base!r}, date={self._date!r}, "
            f"currencies={len(self._rates)})"
        )

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def rate(self, from_currency, to_currency):
        """How many *to_currency* one unit of *from_currency* is worth."""
        frm = self._resolve(from_currency)
        to = self._resolve(to_currency)
        return self._rates[to] / self._rates[frm]

    def convert(self, amount=1.0, from_currency=None, to_currency=None, *, ndigits=2):
        """Convert *amount* and return a float rounded to *ndigits* places.

        Both currency arguments accept ISO codes in any case (``"usd"``
        works) and common symbols (``"$"``). *amount* may also be a whole
        expression string::

            conv.convert(100, "USD", "EUR")
            conv.convert("$100", "EUR")
            conv.convert("100 usd -> eur")

        Codes left out default to the converter's base currency. Pass
        ``ndigits=None`` for the unrounded result.
        """
        if isinstance(amount, str):
            amount, from_currency, to_currency = parse_expression(
                amount, from_currency, to_currency
            )
        if not isinstance(amount, (int, float)):
            amount = float(amount)  # Decimal, Fraction, numpy scalars, ...
        if not isfinite(amount):
            raise ValueError(f"amount must be a finite number, got {amount!r}")
        frm = self._resolve(from_currency or self._base)
        to = self._resolve(to_currency or self._base)
        result = amount * self._rates[to] / self._rates[frm]
        return round(result, ndigits) if ndigits is not None else result

    # Nice short form: conv(100, "USD", "EUR").
    __call__ = convert

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve(self, code):
        """Normalise a code or symbol to a known three-letter code."""
        code = str(code).strip()
        code = SYMBOLS.get(code, code).upper()
        if code in self._rates:
            return code
        hint = ""
        guess = get_close_matches(code, self._rates, n=1, cutoff=0.6)
        if guess:
            hint = f" (did you mean {guess[0]!r}?)"
        raise UnknownCurrencyError(f"unknown currency {code!r}{hint}")
