import os
from decimal import Decimal
from typing import Annotated, Dict, Literal, Union

from pydantic import BaseModel, Field, parse_raw_as


class ModelRate(BaseModel):
    prompt_price: Annotated[Decimal, Field(default_factory=Decimal)]
    completion_price: Annotated[Decimal, Field(default_factory=Decimal)]


class TokenModelRate(ModelRate):
    unit: Literal["token"]

    def calculate(
        self, request_content: str, response_content: str, usage: dict | None
    ):
        price = Decimal(0)
        if usage is None:
            return price

        prompt_tokens = Decimal(usage["prompt_tokens"])
        completion_tokens = Decimal(usage["completion_tokens"])

        return (
            self.prompt_price * prompt_tokens
            + self.completion_price * completion_tokens
        )


class CharWithoutSpaceModelRate(ModelRate):
    unit: Literal["char_without_whitespace"]

    @staticmethod
    def get_chars_without_whitespaces(a: str):
        return sum([1 if i != " " else 0 for i in a])

    def calculate(
        self, request_content: str, response_content: str, usage: dict | None
    ):
        request_len = self.get_chars_without_whitespaces(request_content)
        response_len = self.get_chars_without_whitespaces(response_content)
        return (
            self.prompt_price * request_len
            + self.completion_price * response_len
        )


Rates = Dict[
    str,
    Annotated[
        Union[TokenModelRate, CharWithoutSpaceModelRate],
        Field(discriminator="unit"),
    ],
]


class RatesCalculator:
    def __init__(self, rates_str: str | None = None):
        if rates_str is None:
            rates_str = os.environ.get("MODEL_RATES", "{}")
        assert rates_str is not None
        self.rates = parse_raw_as(Rates, rates_str)

    def get_rate(self, deployment: str, model: str):
        deployment_rate = self.rates.get(deployment)

        if deployment_rate is not None:
            return deployment_rate
        else:
            return self.rates.get(model)

    def calculate_price(
        self,
        deployment: str,
        model: str,
        request_content: str,
        response_content: str,
        usage: dict | None,
    ) -> Decimal:
        rate = self.get_rate(deployment, model)

        if not rate:
            return Decimal(0)

        return rate.calculate(request_content, response_content, usage)
