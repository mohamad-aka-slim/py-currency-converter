"""Adversarial tests for the HTTP client: validation and bad responses.

Everything here runs offline -- urlopen is faked.
"""

import pytest

from currency_converter import client
from currency_converter.exceptions import NetworkError


def _fake_urlopen(monkeypatch, body=b"{}", status_ok=True, calls=None):
    """Replace urlopen with a stub returning *body*; count invocations."""

    def urlopen(request, timeout):
        if calls is not None:
            calls.append(request)
        return _FakeResponse(body)

    monkeypatch.setattr(client, "urlopen", urlopen)


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class TestInputValidation:
    def test_bad_base_is_rejected_without_network(self, monkeypatch):
        calls = []
        _fake_urlopen(monkeypatch, calls=calls)
        with pytest.raises(ValueError, match="3-letter code"):
            client.fetch_rates(base="USDD")
        with pytest.raises(ValueError, match="3-letter code"):
            client.fetch_rates(base="US")
        assert calls == []  # nothing was sent

    def test_bad_date_is_rejected_without_network(self, monkeypatch):
        calls = []
        _fake_urlopen(monkeypatch, calls=calls)
        for bad in ["yesterday", "2024-13-40", "2024-02-30", "24-06-28"]:
            with pytest.raises(ValueError, match="YYYY-MM-DD"):
                client.fetch_rates(date=bad)
        assert calls == []

    def test_valid_inputs_are_accepted(self, monkeypatch):
        rates = b'{"base":"EUR","date":"2026-10-02","rates":{"USD":1.1}}'
        _fake_urlopen(monkeypatch, rates)
        assert client.fetch_rates(base="eur", date="2024-06-28")["rates"] == {"USD": 1.1}


class TestBadResponses:
    def test_html_instead_of_json(self, monkeypatch):
        _fake_urlopen(monkeypatch, b"<html>captive portal</html>")
        with pytest.raises(NetworkError, match="did not return JSON"):
            client.fetch_rates()

    def test_missing_fields(self, monkeypatch):
        _fake_urlopen(monkeypatch, b'{"base":"EUR"}')  # no date, no rates
        with pytest.raises(NetworkError, match="unexpected response"):
            client.fetch_rates()

    def test_non_numeric_rate(self, monkeypatch):
        _fake_urlopen(monkeypatch, b'{"base":"EUR","date":"x","rates":{"USD":"high"}}')
        with pytest.raises(NetworkError, match="unexpected response"):
            client.fetch_rates()

    def test_empty_currencies_payload(self, monkeypatch):
        _fake_urlopen(monkeypatch, b"{}")
        with pytest.raises(NetworkError, match="unexpected response"):
            client.fetch_currencies()

    def test_http_error_is_wrapped_not_raised_raw(self, monkeypatch):
        import urllib.error

        def urlopen(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", None, None)

        monkeypatch.setattr(client, "urlopen", urlopen)
        with pytest.raises(NetworkError, match="HTTP 404"):
            client.fetch_rates()


class TestRetries:
    def test_transient_failure_is_retried(self, monkeypatch):
        import urllib.error

        calls = []

        def flaky_urlopen(request, timeout):
            calls.append(request)
            if len(calls) < 3:  # fail twice, then succeed
                raise urllib.error.URLError("handshake timed out")
            return _FakeResponse(b'{"base":"EUR","date":"x","rates":{}}')

        monkeypatch.setattr(client, "urlopen", flaky_urlopen)
        monkeypatch.setattr(client.time, "sleep", lambda seconds: None)
        assert client.fetch_rates()["base"] == "EUR"
        assert len(calls) == 3

    def test_persistent_failure_raises_after_all_attempts(self, monkeypatch):
        import urllib.error

        calls = []

        def dead_urlopen(request, timeout):
            calls.append(request)
            raise urllib.error.URLError("no route to host")

        monkeypatch.setattr(client, "urlopen", dead_urlopen)
        monkeypatch.setattr(client.time, "sleep", lambda seconds: None)
        with pytest.raises(NetworkError, match="after 3 attempts"):
            client.fetch_rates()
        assert len(calls) == client.ATTEMPTS

    def test_http_error_is_not_retried(self, monkeypatch):
        import urllib.error

        calls = []

        def urlopen(request, timeout):
            calls.append(request)
            raise urllib.error.HTTPError(request.full_url, 500, "boom", None, None)

        monkeypatch.setattr(client, "urlopen", urlopen)
        with pytest.raises(NetworkError, match="HTTP 500"):
            client.fetch_rates()
        assert len(calls) == 1  # server answered; retrying would be pointless
