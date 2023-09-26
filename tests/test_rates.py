import json
from decimal import Decimal

from aidial_analytics_realtime.rates import RatesCalculator

MODEL_RATES = json.dumps(
    {
        "gpt-4": {
            "unit": "token",
            "prompt_price": "0.00003",
            "completion_price": "0.00006",
        },
        "chat-bison@001": {
            "unit": "char_without_whitespace",
            "prompt_price": "0.0000005",
            "completion_price": "0.0000005",
        },
    }
)


def test_token_rates():
    rates = RatesCalculator(MODEL_RATES)
    price = rates.calculate_price(
        "gpt-4", "hello", "hello", {"prompt_tokens": 2, "completion_tokens": 1}
    )
    assert price == Decimal("0.00012")


def test_char_rates():
    rates = RatesCalculator(MODEL_RATES)
    price = rates.calculate_price("chat-bison@001", "hi", "hello", None)
    assert price == Decimal("0.0000035")
