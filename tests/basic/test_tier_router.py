import pytest
from aider.tier_router import TierRouter

class TestTierRouter:
    @pytest.fixture
    def tier_router(self):
        # Mock model tiers for testing
        mock_model_tiers = {
            "PLANNING": "gpt-4o",
            "DRAFTING": "deepseek/deepseek-chat-v3-0324",
            "EXECUTION": "google/gemini-2.0-flash-lite-001",
        }
        return TierRouter(mock_model_tiers)

    def test_get_model_for_task_planning(self, tier_router):
        model = tier_router.get_model_for_task("PLANNING")
        assert model == "gpt-4o"

    def test_get_model_for_task_drafting(self, tier_router):
        model = tier_router.get_model_for_task("DRAFTING")
        assert model == "deepseek/deepseek-chat-v3-0324"

    def test_get_model_for_task_execution(self, tier_router):
        model = tier_router.get_model_for_task("EXECUTION")
        assert model == "google/gemini-2.0-flash-lite-001"

    def test_get_model_for_task_invalid(self, tier_router):
        with pytest.raises(ValueError, match="Model tier 'INVALID_TASK' is not configured."):
            tier_router.get_model_for_task("INVALID_TASK")

    def test_get_model_for_task_case_insensitivity(self, tier_router):
        model = tier_router.get_model_for_task("planning")
        assert model == "gpt-4o"

    def test_get_model_for_task_with_none_tiers(self):
        tier_router = TierRouter(None)
        with pytest.raises(ValueError, match="Model tiers are not configured."):
            tier_router.get_model_for_task("PLANNING")

    def test_get_model_for_task_with_missing_tier(self):
        mock_model_tiers = {
            "PLANNING": "gpt-4o",
            "DRAFTING": "deepseek/deepseek-chat-v3-0324",
            # EXECUTION is missing
        }
        tier_router = TierRouter(mock_model_tiers)
        with pytest.raises(ValueError, match="Model tier 'EXECUTION' is not configured."):
            tier_router.get_model_for_task("EXECUTION")