"""Tests for the CurrencyConverter API."""

import pytest

from currency_converter import (
    CurrencyConverterError,
    UnknownCurrencyError,
    parse_expression,
)


class TestBasicConversion:
    def test_from_base(self, conv):
        assert conv.convert(100, "EUR", "USD") == 108.15

    def test_to_base(self, conv):
        assert conv.convert(100, "USD", "EUR") == 92.46

    def test_cross_rate(self, conv):
        # USD -> JPY goes through the base currency.
        assert conv.convert(100, "USD", "JPY") == 15011.56

    def test_same_currency_is_identity(self, conv):
        assert conv.convert(123.45, "GBP", "GBP") == 123.45

    def test_call_alias(self, conv):
        assert conv(100, "EUR", "USD") == conv.convert(100, "EUR", "USD")

    def test_case_insensitive(self, conv):
        assert conv.convert(100, "usd", "Eur") == 92.46

    def test_currency_symbols(self, conv):
        assert conv.convert(100, "$", "€") == 92.46

    def test_defaults_to_base(self, conv):
        # Both sides default to the base currency, so this is EUR -> EUR.
        assert conv.convert(100) == 100.0
        assert conv.convert(100, "USD") == 92.46  # target defaults to EUR

    def test_ndigits_none_keeps_full_precision(self, conv):
        result = conv.convert(100, "USD", "EUR", ndigits=None)
        assert result == pytest.approx(92.46416921183587)

    def test_rate(self, conv):
        assert conv.rate("EUR", "USD") == 1.0815
        assert conv.rate("USD", "EUR") == pytest.approx(1 / 1.0815)


class TestStringForm:
    def test_plain_phrase(self, conv):
        assert conv.convert("100 USD to EUR") == 92.46

    def test_arrow_separator(self, conv):
        assert conv.convert("100 usd -> eur") == 92.46

    def test_symbol_before_amount(self, conv):
        assert conv.convert("$100 to eur") == 92.46

    def test_symbol_as_target(self, conv):
        assert conv.convert("100 usd to €") == 92.46

    def test_thousands_separator(self, conv):
        assert conv.convert("1,000 usd to eur") == conv.convert(1000, "USD", "EUR")

    def test_missing_target_defaults_to_base(self, conv):
        assert conv.convert("₺100") == 2.66  # 100 TRY is about 2.66 EUR

    def test_unparseable_string(self, conv):
        with pytest.raises(ValueError, match="could not read"):
            conv.convert("hello world")


class TestParseExpression:
    def test_full_phrase(self):
        assert parse_expression("100 USD to EUR") == (100.0, "USD", "EUR")

    def test_uses_defaults_for_missing_parts(self):
        assert parse_expression("100", "USD", "EUR") == (100.0, "USD", "EUR")

    def test_amount_only(self):
        assert parse_expression("42.50") == (42.5, None, None)


class TestFriendlyErrors:
    def test_unknown_currency_suggests_close_match(self, conv):
        with pytest.raises(UnknownCurrencyError, match=r"'USDD'.*did you mean 'USD'\?"):
            conv.convert(100, "USDD", "EUR")

    def test_unknown_currency_without_suggestion(self, conv):
        with pytest.raises(UnknownCurrencyError, match="unknown currency 'QQQZ'"):
            conv.convert(100, "QQQZ", "EUR")

    def test_errors_share_a_base_class(self, conv):
        with pytest.raises(CurrencyConverterError):
            conv.convert(100, "NOPE", "EUR")


class TestIntrospection:
    def test_properties(self, conv):
        assert conv.base == "EUR"
        assert conv.date == "2026-10-02"
        assert conv.currencies["USD"] == "United States dollar"

    def test_rates_includes_base_at_one(self, conv):
        assert conv.rates["EUR"] == 1.0

    def test_rates_returns_a_copy(self, conv):
        rates = conv.rates
        rates["USD"] = 0
        assert conv.rates["USD"] == 1.0815

    def test_contains(self, conv):
        assert "USD" in conv
        assert "usd" in conv
        assert "$" in conv
        assert "XYZ" not in conv

    def test_repr(self, conv):
        assert repr(conv) == ("CurrencyConverter(base='EUR', date='2026-10-02', currencies=6)")
