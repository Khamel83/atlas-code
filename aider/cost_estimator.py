class CostEstimator:
    def __init__(self, model_prices):
        self.model_prices = model_prices

    def estimate_cost(self, model_name, input_tokens, output_tokens):
        prices = self.model_prices.get(model_name)
        if not prices:
            return 0.0  # Unknown models should have 0 cost

        input_cost = (input_tokens / 1_000_000) * prices.get("input", 0)
        output_cost = (output_tokens / 1_000_000) * prices.get("output", 0)

        return input_cost + output_cost