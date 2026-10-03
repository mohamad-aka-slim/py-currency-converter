"""Adversarial tests for parsing: amounts, expressions, numeric types.

These encode the separator rules from ``parse_amount`` -- they exist
because "42,50" once silently parsed as 4250 (a 100x money error).
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from currency_converter.converter import parse_amount, parse_expression


class TestParseAmount:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("100", 100.0),
            ("0.5", 0.5),
            # US style: comma groups, dot is decimal.
            ("1,000", 1000.0),
            ("1,234.56", 1234.56),
            ("1,000,000", 1_000_000.0),
            ("12,345", 12345.0),
            # European style: dot groups, comma is decimal.
            ("42,50", 42.5),
            ("100,50", 100.5),
            ("1.234,56", 1234.56),
            ("1.000.000", 1_000_000.0),
            # The tricky ones: a lone dot is decimal, a lone comma with
            # three digits groups, unless the integer part is zero.
            ("1.000", 1.0),
            ("0,500", 0.5),
            ("0,5000", 0.5),
            ("123,45", 123.45),
            # Space grouping and negatives.
            ("1 000 000", 1_000_000.0),
            ("-1,000", -1000.0),
            ("-42,50", -42.5),
        ],
    )
    def test_valid(self, text, expected):
        assert parse_amount(text) == expected

    @pytest.mark.parametrize(
        "text",
        [
            "",  # empty
            "abc",  # not a number
            "--5",  # double sign
            "100.5.5",  # two dots
            "1.2.3,4",  # mixed mess
            "1,0000",  # ambiguous: 4 digits after a comma
            "1,00000",  # ambiguous: 5 digits after a comma
        ],
    )
    def test_invalid(self, text):
        with pytest.raises(ValueError):
            parse_amount(text)


class TestParseExpression:
    def test_separators_case_insensitive(self):
        assert parse_expression("100 USD TO EUR") == (100.0, "USD", "EUR")
        assert parse_expression("100 USD In EUR") == (100.0, "USD", "EUR")

    def test_negative_amount(self):
        assert parse_expression("-100 usd to eur") == (-100.0, "USD", "EUR")
        assert parse_expression("$-5 to eur") == (-5.0, "USD", "EUR")

    def test_european_amount(self):
        assert parse_expression("1.234,56 usd to eur") == (1234.56, "USD", "EUR")
        assert parse_expression("42,50 usd to eur") == (42.5, "USD", "EUR")

    def test_codes_come_back_uppercase(self):
        amount, frm, to = parse_expression("10 eur to gbp")
        assert frm == "EUR" and to == "GBP"

    def test_fullwidth_digits_are_rejected(self):
        # Would previously crash float() with a confusing UnicodeDecodeError.
        with pytest.raises(ValueError, match="could not read"):
            parse_expression("１００ usd to eur")

    def test_dangling_separator_keeps_target_none(self):
        assert parse_expression("100 USD to") == (100.0, "USD", None)

    def test_trailing_words_rejected(self):
        with pytest.raises(ValueError):
            parse_expression("100 USD to EUR GBP")

    def test_amount_only(self):
        assert parse_expression("42.50") == (42.5, None, None)


class TestNumericTypes:
    """convert() must not explode on numbers that are not float."""

    def test_decimal(self, conv):
        assert conv.convert(Decimal("100"), "USD", "EUR") == 92.46

    def test_fraction(self, conv):
        assert conv.convert(Fraction(100), "USD", "EUR") == 92.46

    def test_bool_is_an_int_and_fine(self, conv):
        assert conv.convert(True, "USD", "EUR") == 0.92

    @pytest.mark.parametrize("bad", [float("inf"), float("-inf"), float("nan")])
    def test_non_finite_rejected(self, conv, bad):
        with pytest.raises(ValueError, match="finite"):
            conv.convert(bad, "USD", "EUR")
