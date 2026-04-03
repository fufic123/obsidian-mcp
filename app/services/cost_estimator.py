"""Estimates cost of LLM API calls from token counts and model pricing."""

from app.domain.models.model_pricing import KNOWN_MODEL_PRICING


class CostEstimator:
    def estimate(self, model: str, input_tokens: int, output_tokens: int) -> float | None:
        """Return cost in USD, or None if the model is not in the pricing table."""
        pricing = KNOWN_MODEL_PRICING.get(model)
        if pricing is None:
            return None
        return (
            input_tokens * pricing.input_per_million / 1_000_000
            + output_tokens * pricing.output_per_million / 1_000_000
        )
