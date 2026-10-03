"""Thin HTTP client for the Frankfurter API (https://frankfurter.dev).

Frankfurter serves the daily reference rates published by the European
Central Bank. It is free, needs no API key and returns plain JSON, which
lets this package stay dependency-free -- everything below uses the
standard library only.
"""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .exceptions import NetworkError

BASE_URL = "https://api.frankfurter.dev/v1"
TIMEOUT = 15  # seconds

# The API rejects requests without a User-Agent, so identify ourselves.
HEADERS = {"User-Agent": "py-currency-converter/0.1"}


def _get_json(path):
    url = f"{BASE_URL}{path}"
    request = Request(url, headers=HEADERS)
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise NetworkError(f"API returned HTTP {exc.code} for {url}: {exc.reason}") from exc
    except (URLError, OSError) as exc:
        raise NetworkError(f"could not reach {url}: {exc}") from exc


def fetch_rates(base="EUR", date="latest"):
    """Return the rates payload for one unit of *base*.

    The dict looks like ``{"base": ..., "date": ..., "rates": {code: rate}}``
    where every rate means "1 *base* is worth this much *code*".
    """
    return _get_json(f"/{date}?base={base.upper()}")


def fetch_currencies():
    """Return the supported currency codes and their display names."""
    return _get_json("/currencies")
