import pytest
from aider.budget_manager import BudgetManager
from aider.tier_router import TierRouter
from aider.cost_estimator import CostEstimator
from datetime import datetime
import os
from pathlib import Path

@pytest.fixture(autouse=True)
def cleanup_state_file():
    # Ensure a clean state for each test
    state_file = Path.home() / ".atlas_code" / "budget_state.json"
    if state_file.exists():
        os.remove(state_file)
    yield
    if state_file.exists():
        os.remove(state_file)

@pytest.fixture
def budget_manager():
    # Provide a dummy io object to suppress warnings during tests
    class MockIO:
        def tool_warning(self, message):
            pass
    return BudgetManager(daily_budget=10.00, notify_thresholds=[0.8], cutoff_time="17:00", io=MockIO())

@pytest.fixture
def tier_router():
    return TierRouter({
        "PLANNING": "gpt-4o",
        "DRAFTING": "claude-3-opus-20240229",
        "EXECUTION": "google/gemini-2.0-flash-lite-001",
    })

@pytest.fixture
def cost_estimator():
    return CostEstimator({
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "google/gemini-2.0-flash-lite-001": {"input": 0.05, "output": 0.05},
    })

def test_auto_downgrade_tier_on_budget_limit(budget_manager, tier_router, cost_estimator):
    # Spend enough to be over budget
    budget_manager.record_spend(10.01)

    # The current model for DRAFTING is expensive
    original_model = tier_router.get_model_for_task("DRAFTING")
    assert original_model == "claude-3-opus-20240229"

    # Mock the time to be after the cutoff time
    mock_time = datetime.utcnow().replace(hour=18, minute=0)

    # If we are over budget, we should get the cheaper execution model
    if budget_manager.should_cutoff(0, current_time=mock_time):
        model_to_use = tier_router.get_model_for_task("EXECUTION")
    else:
        model_to_use = original_model

    assert model_to_use == "google/gemini-2.0-flash-lite-001"

def test_model_tier_remains_when_under_budget(budget_manager, tier_router):
    budget_manager.record_spend(5.0)
    original_model = tier_router.get_model_for_task("DRAFTING")
    assert original_model == "claude-3-opus-20240229"

    mock_time = datetime.utcnow().replace(hour=18, minute=0)

    if budget_manager.should_cutoff(0, current_time=mock_time):
        model_to_use = tier_router.get_model_for_task("EXECUTION")
    else:
        model_to_use = original_model

    assert model_to_use == "claude-3-opus-20240229"

def test_notification_triggered_at_threshold(budget_manager):
    budget_manager.record_spend(7.9)
    assert budget_manager.should_notify(0.1) == True

def test_no_downgrade_when_over_budget_and_approved(budget_manager, tier_router):
    budget_manager.record_spend(10.01)
    budget_manager.approve_over_budget()

    original_model = tier_router.get_model_for_task("DRAFTING")
    assert original_model == "claude-3-opus-20240229"

    mock_time = datetime.utcnow().replace(hour=18, minute=0)

    if budget_manager.should_cutoff(0, current_time=mock_time):
        model_to_use = tier_router.get_model_for_task("EXECUTION")
    else:
        model_to_use = original_model

    assert model_to_use == "claude-3-opus-20240229"
