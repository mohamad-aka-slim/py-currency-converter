"""Shared fixtures: a converter wired to a canned API response."""

import pytest

from currency_converter import converter

RATES_RESPONSE = {
    "amount": 1.0,
    "base": "EUR",
    "date": "2026-10-02",
    "rates": {
        "USD": 1.0815,
        "GBP": 0.8401,
        "JPY": 162.35,
        "CHF": 0.9352,
        "TRY": 37.6,
    },
}

CURRENCIES_RESPONSE = {
    "EUR": "Euro",
    "USD": "United States dollar",
    "GBP": "British pound",
    "JPY": "Japanese yen",
    "CHF": "Swiss franc",
    "TRY": "Turkish lira",
}


@pytest.fixture
def conv(monkeypatch):
    """A CurrencyConverter that never touches the network."""
    monkeypatch.setattr(converter, "fetch_rates", lambda base, date: RATES_RESPONSE)
    monkeypatch.setattr(converter, "fetch_currencies", lambda: CURRENCIES_RESPONSE)
    return converter.CurrencyConverter()
