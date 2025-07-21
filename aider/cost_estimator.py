class CostEstimator:
    def __init__(self, model_prices):
        self.model_prices = model_prices

    def estimate_cost(self, model_name, input_tokens, output_tokens):
        prices = self.model_prices.get(model_name)
        if not prices:
            # Default to a generic price if not found
            return (input_tokens + output_tokens) * 0.000001 # $1 per 1M tokens

        input_cost = (input_tokens / 1_000_000) * prices.get("input_cost_per_million_tokens", 0)
        output_cost = (output_tokens / 1_000_000) * prices.get("output_cost_per_million_tokens", 0)

        return input_cost + output_cost
