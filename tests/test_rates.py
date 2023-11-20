import json
from decimal import Decimal

import pytest

from aidial_analytics_realtime.rates import RatesCalculator

MODEL_RATES = json.dumps(
    {
        "gpt-4": {
            "unit": "token",
            "prompt_price": "0.00003",
            "completion_price": "0.00006",
        },
        "gpt-35-turbo": {
            "unit": "token",
            "prompt_price": "0.0000015",
            "completion_price": "0.000002",
        },
        "chat-bison": {
            "unit": "char_without_whitespace",
            "prompt_price": "0.00005",
            "completion_price": "0.00005",
        },
        "chat-bison@001": {
            "unit": "char_without_whitespace",
            "prompt_price": "0.0000005",
            "completion_price": "0.0000005",
        },
    }
)


token_rates_testdata = [
    ("gpt-4", "gpt-4", "0.00012"),
    ("gpt-4", "gpt-35-turbo", "0.00012"),
    ("gpt-4", "non-existent", "0.00012"),
    ("gpt-4", "gpt-4", "0.00012"),
    ("gpt-35-turbo", "gpt-4", "0.0000050"),
    ("non-existent", "gpt-4", "0.00012"),
    ("gpt-35-turbo", "gpt-4", "0.0000050"),
    ("gpt-35-turbo", "gpt-35-turbo", "0.0000050"),
    ("non-existent", "non-existent", "0"),
]


@pytest.mark.parametrize("deployment, model, price", token_rates_testdata)
def test_token_rates(deployment: str, model: str, price: str):
    rates = RatesCalculator(MODEL_RATES)
    calculated_price = rates.calculate_price(
        deployment,
        model,
        "hello",
        "hello",
        {"prompt_tokens": 2, "completion_tokens": 1},
    )
    assert calculated_price == Decimal(price)


char_rates_testdata = [
    ("chat-bison@001", "chat-bison@001", "0.0000035"),
    ("chat-bison@001", "chat-bison", "0.0000035"),
    ("chat-bison@001", "non-existent", "0.0000035"),
    ("chat-bison@001", "chat-bison@001", "0.0000035"),
    ("chat-bison", "chat-bison@001", "0.00035"),
    ("non-existent", "chat-bison@001", "0.0000035"),
    ("chat-bison", "chat-bison@001", "0.00035"),
    ("chat-bison", "chat-bison", "0.00035"),
    ("non-existent", "non-existent", "0"),
]


@pytest.mark.parametrize("deployment, model, price", char_rates_testdata)
def test_char_rates(deployment: str, model: str, price: str):
    rates = RatesCalculator(MODEL_RATES)
    calculated_price = rates.calculate_price(
        deployment, model, "hi", "hello", None
    )
    assert calculated_price == Decimal(price)
