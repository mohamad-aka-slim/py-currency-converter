"""Tests for the command-line interface (no network involved)."""

import pytest

from currency_converter.cli import main


class TestOutput:
    def test_three_items(self, conv, capsys):
        assert main(["100", "usd", "eur"]) == 0
        out = capsys.readouterr().out
        assert "100.00 USD = 92.46 EUR" in out
        assert "ECB reference rates" in out

    def test_single_phrase(self, conv, capsys):
        assert main(["100 usd to eur"]) == 0
        assert "100.00 USD = 92.46 EUR" in capsys.readouterr().out

    def test_precision(self, conv, capsys):
        assert main(["10", "eur", "usd", "--precision", "4"]) == 0
        assert "10.0000 EUR = 10.8150 USD" in capsys.readouterr().out

    def test_list_currencies(self, conv, capsys):
        assert main(["--list"]) == 0
        out = capsys.readouterr().out
        assert "USD  United States dollar" in out
        assert "EUR  Euro" in out


class TestErrors:
    def test_unknown_currency_exits_with_error(self, conv, capsys):
        assert main(["100", "usdd", "eur"]) == 1
        captured = capsys.readouterr()
        assert "did you mean 'USD'?" in captured.err

    def test_no_expression(self, conv, capsys):
        assert main([]) == 1
        assert "nothing to convert" in capsys.readouterr().err

    def test_wrong_number_of_items(self, conv, capsys):
        assert main(["100", "usd"]) == 1
        assert "one phrase" in capsys.readouterr().err

    def test_amount_is_not_a_number(self, conv, capsys):
        assert main(["abc", "usd", "eur"]) == 1
        assert "is not a number" in capsys.readouterr().err


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
