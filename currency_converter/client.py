"""Thin HTTP client for the Frankfurter API (https://frankfurter.dev).

Frankfurter serves the daily reference rates published by the European
Central Bank. It is free, needs no API key and returns plain JSON, which
lets this package stay dependency-free -- everything below uses the
standard library only.
"""

import json
import re
import time
from datetime import date as _date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .exceptions import NetworkError

BASE_URL = "https://api.frankfurter.dev/v1"
TIMEOUT = 15  # seconds
ATTEMPTS = 3  # handshakes do time out now and then; a retry or two helps
RETRY_DELAY = 0.5  # seconds, multiplied by the attempt number

# The API rejects requests without a User-Agent, so identify ourselves.
HEADERS = {"User-Agent": "py-currency-converter/0.1"}

_BASE_RE = re.compile(r"[A-Za-z]{3}")
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def fetch_rates(base="EUR", date="latest"):
    """Return the rates payload for one unit of *base*.

    The dict looks like ``{"base": ..., "date": ..., "rates": {code: rate}}``
    where every rate means "1 *base* is worth this much *code*".
    """
    base = str(base).strip().upper()
    date = str(date).strip()
    if not _BASE_RE.fullmatch(base):
        raise ValueError(f"base currency must be a 3-letter code, got {base!r}")
    if date != "latest" and not _DATE_RE.fullmatch(date):
        raise ValueError(f"date must be 'latest' or YYYY-MM-DD, got {date!r}")
    if date != "latest":
        try:
            _date.fromisoformat(date)
        except ValueError:
            raise ValueError(f"date must be 'latest' or YYYY-MM-DD, got {date!r}") from None

    payload = _get_json(f"/{date}", f"?base={base}")
    try:
        return {
            "base": payload["base"],
            "date": payload["date"],
            "rates": {code: float(rate) for code, rate in payload["rates"].items()},
        }
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise NetworkError(f"unexpected response from the rates API: {payload!r:.120}") from exc


def fetch_currencies():
    """Return the supported currency codes and their display names."""
    payload = _get_json("/currencies")
    if (
        not isinstance(payload, dict)
        or not payload
        or not all(
            isinstance(code, str) and isinstance(name, str) for code, name in payload.items()
        )
    ):
        raise NetworkError(f"unexpected response from the currencies API: {payload!r:.120}")
    return payload


def _get_json(path, query=""):
    url = f"{BASE_URL}{path}{query}"
    last_error = None
    for attempt in range(1, ATTEMPTS + 1):
        request = Request(url, headers=HEADERS)
        try:
            with urlopen(request, timeout=TIMEOUT) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            # HTTP errors are the server answering; retrying won't help.
            message = _read_error_message(exc)
            detail = f": {message}" if message else ""
            raise NetworkError(f"API returned HTTP {exc.code} for {url}{detail}") from exc
        except (URLError, OSError) as exc:
            last_error = exc
            if attempt < ATTEMPTS:
                time.sleep(RETRY_DELAY * attempt)
        else:
            break  # got a body, stop retrying
    else:
        raise NetworkError(f"could not reach {url} after {ATTEMPTS} attempts: {last_error}")

    try:
        return json.loads(body)
    except ValueError as exc:
        # A proxy or captive portal answering with HTML, most likely.
        raise NetworkError(f"{url} did not return JSON: {body[:120]!r}") from exc


def _read_error_message(exc):
    """The API explains failures in a small JSON body; surface it if present."""
    try:
        payload = json.loads(exc.read().decode("utf-8"))
        return str(payload.get("message", ""))
    except Exception:
        return ""
