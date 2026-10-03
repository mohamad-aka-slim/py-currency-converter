"""A quick tour of the library. Run it with:

    python examples/basic_usage.py

(needs internet access -- it talks to the live API)
"""

from currency_converter import CurrencyConverter

conv = CurrencyConverter()

# The basics.
print(conv.convert(100, "USD", "EUR"))
print(conv.rate("USD", "EUR"))

# The object is callable, for the impatient.
print(conv(100, "USD", "EUR"))

# Phrases, symbols, arrows -- all understood.
print(conv.convert("100 USD to EUR"))
print(conv.convert("$100 to €"))
print(conv.convert("1,000 usd -> jpy"))

# History.
old = CurrencyConverter(date="2024-06-28")
print(f"back in June 2024, 100 USD was {old.convert(100, 'USD', 'EUR')} EUR")

# Introspection.
print("USD" in conv)
print(conv.currencies["TRY"])
print(repr(conv))
