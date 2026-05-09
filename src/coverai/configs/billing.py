from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class BillingSettings(BaseSettings):
    model_config = CONFIG_MODEL

    prediction_cost_credits: int = Field(default=1, alias="PREDICTION_COST_CREDITS")
    credit_price_rub: int = Field(default=1, alias="CREDIT_PRICE_RUB")
    standard_subscription_price_rub: int = Field(
        default=399,
        alias="STANDARD_SUBSCRIPTION_PRICE_RUB",
    )
    pro_subscription_price_rub: int = Field(
        default=999,
        alias="PRO_SUBSCRIPTION_PRICE_RUB",
    )
