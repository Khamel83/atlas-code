import pytest
from datetime import datetime, timedelta
from aider.budget_manager import BudgetManager
import os
from pathlib import Path

class TestBudgetManager:
    @pytest.fixture(autouse=True)
    def cleanup_state_file(self):
        # Ensure a clean state for each test
        state_file = Path.home() / ".atlas_code" / "budget_state.json"
        if state_file.exists():
            os.remove(state_file)
        yield
        if state_file.exists():
            os.remove(state_file)

    @pytest.fixture
    def budget_manager(self):
        # Default budget: $10.00, thresholds: 50%, 80%, cutoff: 17:00 UTC
        return BudgetManager(daily_budget=10.00, notify_thresholds=[0.5, 0.8], cutoff_time="17:00")

    def test_initial_state(self, budget_manager):
        assert budget_manager.daily_budget == 10.00
        assert budget_manager.notify_thresholds == [0.5, 0.8]
        assert budget_manager.cutoff_time == "17:00"
        assert budget_manager.current_spend == 0.0
        assert not budget_manager.approved_for_over_budget
        assert budget_manager.notified_thresholds == set()

    def test_record_spend(self, budget_manager):
        budget_manager.record_spend(2.50)
        assert budget_manager.current_spend == 2.50
        budget_manager.record_spend(1.00)
        assert budget_manager.current_spend == 3.50

    def test_should_notify_below_threshold(self, budget_manager):
        budget_manager.record_spend(4.00)  # 40% of 10.00
        assert not budget_manager.should_notify(0.0) # No new spend, already notified for 0.0
        assert budget_manager.notified_thresholds == set()

    def test_should_notify_at_first_threshold(self, budget_manager):
        budget_manager.record_spend(4.90)
        assert budget_manager.should_notify(0.10) # Total 5.00, hits 50% threshold
        assert budget_manager.notified_thresholds == {0.5}

    def test_should_notify_at_second_threshold(self, budget_manager):
        budget_manager.record_spend(4.90) # Spend up to 4.90
        assert budget_manager.should_notify(0.10) # Crosses 0.5 threshold (total 5.00)
        assert budget_manager.notified_thresholds == {0.5}

        budget_manager.record_spend(2.90) # Spend up to 7.80
        assert budget_manager.should_notify(0.20) # Crosses 0.8 threshold (total 8.00)
        assert budget_manager.notified_thresholds == {0.5, 0.8}

    def test_should_notify_past_all_thresholds(self, budget_manager):
        budget_manager.record_spend(4.90) # Spend up to 4.90
        budget_manager.should_notify(0.10) # Crosses 0.5 threshold (total 5.00)
        budget_manager.record_spend(2.90) # Spend up to 7.80
        budget_manager.should_notify(0.20) # Crosses 0.8 threshold (total 8.00)

        budget_manager.record_spend(1.00) # Spend up to 9.00
        assert not budget_manager.should_notify(0.50) # Total 9.50, past all thresholds, no new notification
        assert budget_manager.notified_thresholds == {0.5, 0.8}

    def test_should_cutoff_below_budget(self, budget_manager):
        budget_manager.record_spend(9.00)
        assert not budget_manager.should_cutoff(0.50) # Total 9.50, still within budget

    def test_should_cutoff_at_budget(self, budget_manager):
        budget_manager.record_spend(9.90)
        assert not budget_manager.should_cutoff(0.10) # Total 10.00, exactly at budget, not cutoff

    def test_should_cutoff_over_budget_not_approved(self, budget_manager):
        budget_manager.record_spend(10.00)
        now = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0) # Before 17:00 cutoff
        assert not budget_manager.should_cutoff(0.01, current_time=now) # Total 10.01, over budget, but before cutoff

    def test_should_cutoff_over_budget_approved(self, budget_manager):
        budget_manager.record_spend(10.00)
        budget_manager.approve_over_budget()
        assert not budget_manager.should_cutoff(0.01) # Total 10.01, over budget, but approved

    def test_approve_over_budget(self, budget_manager):
        budget_manager.approve_over_budget()
        assert budget_manager.approved_for_over_budget

    def test_reset_daily_spend_next_day(self, budget_manager):
        budget_manager.record_spend(5.00)
        budget_manager.last_spend_reset_date = (datetime.utcnow() - timedelta(days=1)).date()
        budget_manager.check_and_reset_daily_spend()
        assert budget_manager.current_spend == 0.0
        assert not budget_manager.approved_for_over_budget
        assert budget_manager.notified_thresholds == set()

    def test_reset_daily_spend_same_day(self, budget_manager):
        budget_manager.record_spend(5.00)
        budget_manager.check_and_reset_daily_spend()
        assert budget_manager.current_spend == 5.00  # Should not reset

    def test_get_status_report(self, budget_manager):
        budget_manager.record_spend(6.00)
        report = budget_manager.get_status_report()
        assert "Daily Budget: $10.00" in report
        assert "Current Spend: $6.00" in report
        assert "Remaining Budget: $4.00" in report
        assert "Budget Status: Within budget" in report

    def test_get_status_report_over_budget(self, budget_manager):
        budget_manager.record_spend(10.50)
        report = budget_manager.get_status_report()
        assert "Budget Status: OVER BUDGET" in report

    def test_get_status_report_approved_over_budget(self, budget_manager):
        budget_manager.record_spend(10.50)
        budget_manager.approve_over_budget()
        report = budget_manager.get_status_report()
        assert "Budget Status: OVER BUDGET (Approved)" in report

    def test_get_status_report_no_budget(self):
        budget_manager = BudgetManager(daily_budget=None, notify_thresholds=[], cutoff_time=None)
        report = budget_manager.get_status_report()
        assert "Daily Budget: No budget set" in report
        assert "Current Spend: $0.00" in report
        assert "Remaining Budget: N/A" in report
        assert "Budget Status: No budget set" in report

    def test_cutoff_time_logic_before_cutoff(self, budget_manager):
        # Set current time to before cutoff (e.g., 16:00 UTC if cutoff is 17:00 UTC)
        now = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
        budget_manager.record_spend(9.90)
        
        # Should not cutoff if over budget but before cutoff time
        assert not budget_manager.should_cutoff(0.20, current_time=now) # Total 10.10

    def test_cutoff_time_logic_after_cutoff(self, budget_manager):
        # Set current time to after cutoff (e.g., 18:00 UTC if cutoff is 17:00 UTC)
        now = datetime.utcnow().replace(hour=18, minute=0, second=0, microsecond=0)
        budget_manager.record_spend(9.90)
        
        # Should cutoff if over budget and after cutoff time
        assert budget_manager.should_cutoff(0.20, current_time=now) # Total 10.10

    def test_cutoff_time_logic_after_cutoff_approved(self, budget_manager):
        # Set current time to after cutoff (e.g., 18:00 UTC if cutoff is 17:00 UTC)
        now = datetime.utcnow().replace(hour=18, minute=0, second=0, microsecond=0)
        budget_manager.record_spend(9.90)
        budget_manager.approve_over_budget()
        
        # Should not cutoff if over budget and after cutoff time, and approved
        assert not budget_manager.should_cutoff(0.20, current_time=now) # Total 10.10

    def test_cutoff_time_logic_no_cutoff_time_set(self):
        budget_manager = BudgetManager(daily_budget=10.00, notify_thresholds=[0.5, 0.8], cutoff_time=None)
        budget_manager.record_spend(9.90)
        
        # Should cutoff if over budget, regardless of time if no cutoff time is set
        assert budget_manager.should_cutoff(0.20) # Total 10.10

    def test_cutoff_time_logic_no_budget_set(self):
        budget_manager = BudgetManager(daily_budget=None, notify_thresholds=[0.5, 0.8], cutoff_time="17:00")
        budget_manager.record_spend(100.00)
        
        # Should never cutoff if no budget is set
        assert not budget_manager.should_cutoff(1.00)