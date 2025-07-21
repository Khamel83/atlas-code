import pytest
from aider.cost_estimator import CostEstimator

class TestCostEstimator:
    @pytest.fixture
    def cost_estimator(self):
        # Mock model prices for testing
        mock_model_prices = {
            "gpt-4o": {"input": 5.00, "output": 15.00},
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            "deepseek/deepseek-chat-v3-0324": {"input": 0.10, "output": 0.10}, # Example prices
            "google/gemini-2.0-flash-lite-001": {"input": 0.05, "output": 0.05}, # Example prices
        }
        return CostEstimator(mock_model_prices)

    def test_estimate_cost_known_model(self, cost_estimator):
        # Assuming a hypothetical model with known pricing
        # In a real scenario, model prices would be loaded from a config or API
        model_name = "gpt-4o"
        input_tokens = 1000
        output_tokens = 500
        
        # These prices are hypothetical and should match what CostEstimator uses internally
        # For gpt-4o, let's assume $5.00 / 1M input tokens, $15.00 / 1M output tokens
        expected_cost = (1000 / 1_000_000 * 5.00) + (500 / 1_000_000 * 15.00)
        
        cost = cost_estimator.estimate_cost(model_name, input_tokens, output_tokens)
        assert cost == pytest.approx(expected_cost)

    def test_estimate_cost_unknown_model(self, cost_estimator):
        model_name = "unknown-model"
        input_tokens = 1000
        output_tokens = 500
        
        cost = cost_estimator.estimate_cost(model_name, input_tokens, output_tokens)
        assert cost == 0.0  # Unknown models should have 0 cost

    def test_estimate_cost_zero_tokens(self, cost_estimator):
        model_name = "gpt-4o"
        input_tokens = 0
        output_tokens = 0
        
        cost = cost_estimator.estimate_cost(model_name, input_tokens, output_tokens)
        assert cost == 0.0

    def test_estimate_cost_only_input_tokens(self, cost_estimator):
        model_name = "gpt-4o"
        input_tokens = 2000
        output_tokens = 0
        
        expected_cost = (2000 / 1_000_000 * 5.00)
        
        cost = cost_estimator.estimate_cost(model_name, input_tokens, output_tokens)
        assert cost == pytest.approx(expected_cost)

    def test_estimate_cost_only_output_tokens(self, cost_estimator):
        model_name = "gpt-4o"
        input_tokens = 0
        output_tokens = 750
        
        expected_cost = (750 / 1_000_000 * 15.00)
        
        cost = cost_estimator.estimate_cost(model_name, input_tokens, output_tokens)
        assert cost == pytest.approx(expected_cost)

    def test_estimate_cost_different_model(self, cost_estimator):
        model_name = "claude-3-opus-20240229"
        input_tokens = 1000
        output_tokens = 500
        
        # Hypothetical prices for claude-3-opus-20240229
        # Assume $15.00 / 1M input tokens, $75.00 / 1M output tokens
        expected_cost = (1000 / 1_000_000 * 15.00) + (500 / 1_000_000 * 75.00)
        
        cost = cost_estimator.estimate_cost(model_name, input_tokens, output_tokens)
        assert cost == pytest.approx(expected_cost)
