import json
import os
from decimal import Decimal

rates = json.loads(os.environ.get("MODEL_RATES", "{}"))

for model, rate in rates.items():
    if "prompt_price" in rate:
        rate["prompt_price"] = Decimal(rate["prompt_price"])
    if "completion_price" in rate:
        rate["completion_price"] = Decimal(rate["completion_price"])


def number_of_chars_without_whitespaces(a: str):
    return sum([1 if i != " " else 0 for i in a])


def calculate_price(
    model: str, request_content: str, response_content: str, usage: any
) -> Decimal:
    model_rate = rates.get(model)
    if not model_rate:
        return Decimal(0)

    price = Decimal(0)
    if model_rate["unit"] == "token":
        if usage is None:
            return price

        if "prompt_price" in model_rate:
            price += model_rate["prompt_price"] * Decimal(usage["prompt_tokens"])
        if "completion_price" in model_rate:
            price += model_rate["completion_price"] * Decimal(
                usage["completion_tokens"]
            )
    elif model_rate["unit"] == "char_without_whitespace":
        if "prompt_price" in model_rate:
            price += model_rate["prompt_price"] * number_of_chars_without_whitespaces(
                request_content
            )
        if "completion_price" in model_rate:
            price += model_rate[
                "completion_price"
            ] * number_of_chars_without_whitespaces(response_content)

    return price
