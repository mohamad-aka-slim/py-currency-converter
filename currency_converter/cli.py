"""Command-line interface.

Examples::

    currency-converter 100 USD EUR
    currency-converter "100 USD to EUR"
    currency-converter '$100 to €'          # quote it, or the shell eats the $
    currency-converter 100 USD EUR --date 2024-06-28 --precision 4
    currency-converter --list
"""

import argparse
import sys

from . import __version__
from .converter import CurrencyConverter, parse_amount, parse_expression
from .exceptions import CurrencyConverterError


def _precision(text):
    """argparse type for --precision: an integer between 0 and 10."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from None
    if not 0 <= value <= 10:
        raise argparse.ArgumentTypeError(f"must be between 0 and 10, got {value}")
    return value


def build_parser():
    parser = argparse.ArgumentParser(
        prog="currency-converter",
        description="Convert between currencies using ECB reference rates (via frankfurter.dev).",
    )
    parser.add_argument(
        "expression",
        nargs="*",
        metavar="EXPR",
        help="what to convert: 100 USD EUR, or a phrase like '100 USD to EUR'",
    )
    parser.add_argument(
        "-b",
        "--base",
        default="EUR",
        metavar="CODE",
        help="base currency to fetch rates for (default: EUR)",
    )
    parser.add_argument(
        "-d",
        "--date",
        default="latest",
        metavar="YYYY-MM-DD",
        help="use rates from this date instead of the latest",
    )
    parser.add_argument(
        "-p",
        "--precision",
        type=_precision,
        default=2,
        metavar="N",
        help="decimal places to show, 0-10 (default: 2)",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="list supported currencies and exit",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        conv = CurrencyConverter(base=args.base, date=args.date)

        if args.list:
            for code, name in sorted(conv.currencies.items()):
                print(f"{code}  {name}")
            return 0

        amount, frm, to = _parse_request(args.expression)
        # Resolve early so the output always shows clean uppercase codes.
        frm = conv._resolve(frm or conv.base)
        to = conv._resolve(to or conv.base)
        result = conv.convert(amount, frm, to, ndigits=args.precision)
        rate = conv.rate(frm, to)
    except (CurrencyConverterError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"{amount:,.{args.precision}f} {frm} = {result:,.{args.precision}f} {to}")
    print(f"  1 {frm} = {rate:.6f} {to}  ·  ECB reference rates, {conv.date}")
    return 0


def _parse_request(tokens):
    """Turn the positional CLI arguments into (amount, from, to)."""
    if not tokens:
        raise ValueError("nothing to convert -- try: currency-converter 100 USD EUR")
    if len(tokens) == 1:
        return parse_expression(tokens[0])
    if len(tokens) == 3:
        # parse_amount, not float(), so "1.000,50" and "1,000" read correctly.
        try:
            amount = parse_amount(tokens[0])
        except ValueError:
            raise ValueError(f"{tokens[0]!r} is not a number") from None
        return amount, tokens[1], tokens[2]
    raise ValueError("give one phrase ('100 USD to EUR') or three items (100 USD EUR)")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
