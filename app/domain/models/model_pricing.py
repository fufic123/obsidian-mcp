"""Model pricing table for cost estimation."""

from pydantic import BaseModel


class ModelPricing(BaseModel):
    """Cost in USD per 1 million tokens."""

    input_per_million: float
    output_per_million: float


KNOWN_MODEL_PRICING: dict[str, ModelPricing] = {
    "claude-opus-4-6": ModelPricing(input_per_million=15.0, output_per_million=75.0),
    "claude-sonnet-4-6": ModelPricing(input_per_million=3.0, output_per_million=15.0),
    "claude-haiku-4-5": ModelPricing(input_per_million=0.8, output_per_million=4.0),
    "claude-haiku-4-5-20251001": ModelPricing(input_per_million=0.8, output_per_million=4.0),
    "gpt-4o": ModelPricing(input_per_million=2.5, output_per_million=10.0),
    "gpt-4o-mini": ModelPricing(input_per_million=0.15, output_per_million=0.6),
    "o1": ModelPricing(input_per_million=15.0, output_per_million=60.0),
    "o3-mini": ModelPricing(input_per_million=1.1, output_per_million=4.4),
}
