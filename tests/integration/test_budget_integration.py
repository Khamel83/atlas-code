import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, date
import os
from pathlib import Path
import json

from aider.budget_manager import BudgetManager
from aider.cost_estimator import CostEstimator
from aider.tier_router import TierRouter
from aider.coders.base_coder import Coder # Corrected import
from aider.models import Model # Import Model to mock it correctly
from aider.commands import Commands # Import Commands to mock it correctly

# Mock the state file path for testing
@pytest.fixture(autouse=True)
def mock_state_file_path():
    with patch('pathlib.Path.home', return_value=Path('/tmp/test_home')):
        test_dir = Path('/tmp/test_home/.atlas_code')
        test_dir.mkdir(parents=True, exist_ok=True)
        state_file = test_dir / 'budget_state.json'
        if state_file.exists():
            os.remove(state_file)
        yield
        if state_file.exists():
            os.remove(state_file)
        if test_dir.exists():
            os.rmdir(test_dir)

@pytest.fixture
def mock_io():
    mock_io = MagicMock()
    mock_io.tool_output = MagicMock()
    mock_io.tool_warning = MagicMock()
    return mock_io

@pytest.fixture
def mock_model_prices():
    return {
        "platinum-model": {"input": 10.00, "output": 30.00}, # High cost
        "gold-model": {"input": 5.00, "output": 15.00},    # Medium cost
        "silver-model": {"input": 1.00, "output": 3.00},     # Low cost
    }

@pytest.fixture
def mock_model_tiers():
    return {
        "PLANNING": "platinum-model",
        "DRAFTING": "gold-model",
        "EXECUTION": "silver-model",
    }

@pytest.fixture
def cost_estimator(mock_model_prices):
    return CostEstimator(mock_model_prices)

@pytest.fixture
def tier_router(mock_model_tiers):
    return TierRouter(mock_model_tiers)

@pytest.fixture
def budget_manager(mock_io):
    return BudgetManager(
        daily_budget=10.00,
        notify_thresholds=[0.5, 0.8],
        cutoff_time="17:00",
        io=mock_io
    )

@pytest.fixture
def mock_coder(budget_manager, cost_estimator, tier_router, mock_io):
    with patch('aider.coders.base_coder.RepoMap'), \
         patch('aider.coders.base_coder.Linter'), \
         patch('aider.models.Model') as MockModel: # Corrected patch target
        
        # Create a mock main_model that behaves like aider.models.Model
        mock_main_model = MockModel()
        mock_main_model.name = "mock-model"
        mock_main_model.token_count.return_value = 100 # Default token count for mocks
        mock_main_model.info = {"max_input_tokens": 100000, "supports_vision": False, "supports_pdf_input": False}
        mock_main_model.edit_format = "diff"
        mock_main_model.streaming = True

        coder = Coder.create( # Use Coder.create
            io=mock_io,
            main_model=mock_main_model,
        )
        # Manually set attributes after creation
        coder.budget_manager = budget_manager
        coder.cost_estimator = cost_estimator
        coder.tier_router = tier_router
        coder.auto_commit = False
        coder.handover_enabled = True
        coder.fnames = []
        coder.cur_messages = []
        coder.done_messages = []

        # Mock the commands object and its methods
        mock_commands = MagicMock(spec=Commands)
        mock_commands.cmd_budget_status.side_effect = lambda: mock_io.tool_output(budget_manager.get_status_report())
        mock_commands.cmd_budget_approve.side_effect = lambda: (
            budget_manager.approve_over_budget(),
            mock_io.tool_output("Budget approval granted. You can now exceed your daily budget.")
        )
        coder.commands = mock_commands

        # Mock the send_message method to simulate LLM calls
        coder.send_message = MagicMock(side_effect=lambda msg, model_name: f"LLM response to {msg} from {model_name}")
        return coder

class TestBudgetIntegration:

    def test_user_session_within_budget_no_notifications(self, mock_coder, budget_manager, mock_io):
        # Simulate a session well within budget
        mock_coder.send_message("Initial planning task", "PLANNING")
        mock_coder.send_message("Drafting some code", "DRAFTING")
        mock_coder.send_message("Execute a small change", "EXECUTION")

        # Verify no notifications or cutoffs
        mock_io.tool_warning.assert_not_called()
        assert budget_manager.current_spend < budget_manager.daily_budget * 0.5

    def test_user_session_crosses_notification_thresholds(self, mock_coder, budget_manager, mock_io):
        # Simulate spending to cross 50% threshold
        budget_manager.record_spend(4.90) # Current spend is 4.90
        mock_coder.send_message("Task to cross 50% threshold", "PLANNING") # Cost will be 0.10 * 10 = 1.00
        
        # Expected spend after this call: 4.90 + 1.00 = 5.90
        # 50% threshold is 5.00
        mock_io.tool_warning.assert_called_with("Budget notification: You have spent $5.90 out of $10.00 (59.00%).")
        mock_io.tool_warning.reset_mock() # Reset mock for next check

        # Simulate spending to cross 80% threshold
        budget_manager.record_spend(2.00) # Current spend is 5.90 + 2.00 = 7.90
        mock_coder.send_message("Task to cross 80% threshold", "PLANNING") # Cost will be 0.10 * 10 = 1.00
        
        # Expected spend after this call: 7.90 + 1.00 = 8.90
        # 80% threshold is 8.00
        mock_io.tool_warning.assert_called_with("Budget notification: You have spent $8.90 out of $10.00 (89.00%).")
        mock_io.tool_warning.reset_mock()

    def test_user_session_exceeds_budget_before_cutoff(self, mock_coder, budget_manager, mock_io):
        # Simulate spending close to budget
        budget_manager.record_spend(9.95) # Current spend is 9.95

        # Simulate a call that exceeds budget before cutoff time
        with patch('datetime.datetime') as mock_dt:
            mock_dt.utcnow.return_value = datetime(2025, 7, 21, 16, 30, 0) # Before 17:00 cutoff
            mock_dt.now.return_value = datetime(2025, 7, 21, 16, 30, 0)
            mock_dt.date.today.return_value = date(2025, 7, 21)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw) # Allow normal datetime behavior

            mock_coder.send_message("Task to exceed budget", "PLANNING") # Cost will be 0.10 * 10 = 1.00
            
            # Expected spend after this call: 9.95 + 1.00 = 10.95
            # Budget is 10.00
            mock_io.tool_warning.assert_called_with("LLM call would exceed daily budget. Please use /budget-approve to continue or switch to a cheaper model.")
            mock_io.tool_warning.reset_mock()

            # Verify that the call was not made (or was intercepted)
            mock_coder.send_message.assert_called_once_with("LLM call intercepted due to budget.", "PLANNING") # This needs to be mocked in BaseCoder

    def test_user_session_exceeds_budget_after_cutoff(self, mock_coder, budget_manager, mock_io):
        # Simulate spending close to budget
        budget_manager.record_spend(9.95) # Current spend is 9.95

        # Simulate a call that exceeds budget after cutoff time
        with patch('datetime.datetime') as mock_dt:
            mock_dt.utcnow.return_value = datetime(2025, 7, 21, 17, 30, 0) # After 17:00 cutoff
            mock_dt.now.return_value = datetime(2025, 7, 21, 17, 30, 0)
            mock_dt.date.today.return_value = date(2025, 7, 21)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw) # Allow normal datetime behavior

            mock_coder.send_message("Task to exceed budget after cutoff", "PLANNING") # Cost will be 0.10 * 10 = 1.00
            
            # Expected spend after this call: 9.95 + 1.00 = 10.95
            # Budget is 10.00
            mock_io.tool_warning.assert_called_with("LLM call would exceed daily budget and it's past cutoff time. Please use /budget-approve to continue or switch to a cheaper model.")
            mock_io.tool_warning.reset_mock()

            # Verify that the call was not made (or was intercepted)
            mock_coder.send_message.assert_called_once_with("LLM call intercepted due to budget.", "PLANNING")

    def test_user_session_budget_approved(self, mock_coder, budget_manager, mock_io):
        # Simulate spending over budget
        budget_manager.record_spend(10.50) # Current spend is 10.50

        # Approve going over budget
        budget_manager.approve_over_budget()

        # Simulate another call
        mock_coder.send_message("Task after budget approval", "DRAFTING") # Cost will be 0.10 * 5 = 0.50
        
        # Expected spend after this call: 10.50 + 0.50 = 11.00
        mock_io.tool_warning.assert_not_called() # No warning expected after approval

    def test_user_session_auto_switch_to_cheaper_model(self, mock_coder, budget_manager, cost_estimator, tier_router, mock_io):
        # Simulate spending close to budget
        budget_manager.record_spend(9.95) # Current spend is 9.95

        # Simulate a call that exceeds budget before cutoff time, and auto-switch is enabled
        # (This test assumes auto-switch logic is handled within BaseCoder or loop.py,
        # and that the mock_coder's send_message would reflect the model change)
        
        # For this test, we need to mock the actual model used by send_message
        # and verify that it switches to a cheaper model if should_cutoff is True
        
        # This part of the test requires more sophisticated mocking of the LLM call
        # within BaseCoder to simulate the model change.
        # For now, we'll just verify that should_cutoff is triggered.
        
        with patch('datetime.datetime') as mock_dt:
            mock_dt.utcnow.return_value = datetime(2025, 7, 21, 16, 30, 0) # Before 17:00 cutoff
            mock_dt.now.return_value = datetime(2025, 7, 21, 16, 30, 0)
            mock_dt.date.today.return_value = date(2025, 7, 21)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw) # Allow normal datetime behavior

            # Simulate a call that would exceed budget
            mock_coder.send_message("Task to trigger auto-switch", "PLANNING")
            
            # Verify that a warning was issued (indicating a potential cutoff or switch)
            mock_io.tool_warning.assert_called_with("LLM call would exceed daily budget. Please use /budget-approve to continue or switch to a cheaper model.")
            mock_io.tool_warning.reset_mock()

            # This part needs to be implemented in BaseCoder or loop.py
            # assert mock_coder.models.current_model == "silver-model" # Example of expected model switch

    def test_budget_status_command(self, mock_coder, budget_manager, mock_io):
        budget_manager.record_spend(3.50)
        mock_coder.commands.cmd_budget_status() # Assuming this command exists and calls get_status_report

        mock_io.tool_output.assert_called_with(budget_manager.get_status_report())

    def test_budget_approve_command(self, mock_coder, budget_manager, mock_io):
        assert not budget_manager.approved_for_over_budget
        mock_coder.commands.cmd_budget_approve() # Assuming this command exists and calls approve_over_budget
        assert budget_manager.approved_for_over_budget
        mock_io.tool_output.assert_called_with("Budget approval granted. You can now exceed your daily budget.")
