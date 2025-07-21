import datetime
import json
import os
from pathlib import Path

class BudgetManager:
    def __init__(self, daily_budget, notify_thresholds, cutoff_time, io=None):
        self.daily_budget = daily_budget
        self.notify_thresholds = sorted(notify_thresholds) if notify_thresholds is not None else []
        self.cutoff_time = cutoff_time
        self.io = io
        
        # Initialize attributes before loading state
        self.current_spend = 0.0
        self.approved_for_over_budget = False
        self.last_spend_reset_date = datetime.date.today()
        self.notified_thresholds = set()

        self.state_file = Path.home() / ".atlas_code" / "budget_state.json"
        self._load_state()
        self.check_and_reset_daily_spend() # Ensure reset on init based on loaded state

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.current_spend = state.get("current_spend", 0.0)
                self.approved_for_over_budget = state.get("approved_for_over_budget", False)
                last_reset_date_str = state.get("last_spend_reset_date")
                if last_reset_date_str:
                    self.last_spend_reset_date = datetime.datetime.strptime(last_reset_date_str, "%Y-%m-%d").date()
                
                notified_thresholds_list = state.get("notified_thresholds", [])
                self.notified_thresholds = set(notified_thresholds_list)

            except Exception as e:
                if self.io:
                    self.io.tool_warning(f"Failed to load budget state: {e}")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _save_state(self):
        state = {
            "current_spend": self.current_spend,
            "approved_for_over_budget": self.approved_for_over_budget,
            "last_spend_reset_date": self.last_spend_reset_date.strftime("%Y-%m-%d"),
            "notified_thresholds": list(self.notified_thresholds),
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Failed to save budget state: {e}")

    def record_spend(self, cost):
        self.current_spend += cost
        self._save_state()

    def get_status_report(self):
        if self.daily_budget is None:
            return (
                "Daily Budget: No budget set\n"
                f"Current Spend: ${self.current_spend:.2f}\n"
                "Remaining Budget: N/A\n"
                "Budget Status: No budget set"
            )

        remaining_budget = self.daily_budget - self.current_spend
        status = "Within budget"
        if self.current_spend > self.daily_budget:
            status = "OVER BUDGET"
            if self.approved_for_over_budget:
                status += " (Approved)"

        report = (
            f"Daily Budget: ${self.daily_budget:.2f}\n"
            f"Current Spend: ${self.current_spend:.2f}\n"
            f"Remaining Budget: ${remaining_budget:.2f}\n"
            f"Budget Status: {status}"
        )
        return report

    def approve_over_budget(self):
        self.approved_for_over_budget = True
        self._save_state()

    def should_notify(self, estimated_cost):
        if self.daily_budget is None:
            return False

        notified_any_new_threshold = False
        for threshold in self.notify_thresholds:
            threshold_value = self.daily_budget * threshold
            if self.current_spend < threshold_value and \
               self.current_spend + estimated_cost >= threshold_value and \
               threshold not in self.notified_thresholds:
                self.notified_thresholds.add(threshold)
                notified_any_new_threshold = True
        
        if notified_any_new_threshold:
            self._save_state()

        return notified_any_new_threshold

    def should_cutoff(self, estimated_cost, current_time=None):
        if self.daily_budget is None:
            return False

        if self.approved_for_over_budget:
            return False # Approved to go over budget

        if self.current_spend + estimated_cost <= self.daily_budget:
            return False # Still within budget

        # If we reach here, it means current_spend + estimated_cost > daily_budget
        # and not approved_for_over_budget

        if self.cutoff_time:
            if current_time is None:
                current_time = datetime.datetime.utcnow()
            
            try:
                cutoff_hour, cutoff_minute = map(int, self.cutoff_time.split(':'))
                cutoff_datetime = current_time.replace(hour=cutoff_hour, minute=cutoff_minute, second=0, microsecond=0)
            except ValueError:
                # Handle invalid cutoff_time format
                if self.io:
                    self.io.tool_warning(f"Invalid cutoff_time format: {self.cutoff_time}. Assuming no cutoff time.")
                return True # Treat as no cutoff time, enforce immediately

            if current_time.time() >= cutoff_datetime.time():
                return True # After cutoff time, enforce cutoff
            else:
                return False # Before cutoff time, allow to go over budget until cutoff
        else:
            return True # No cutoff time set, enforce cutoff immediately if over budget

    def check_and_reset_daily_spend(self):
        today = datetime.date.today()
        if self.last_spend_reset_date < today:
            self.current_spend = 0.0
            self.approved_for_over_budget = False
            self.last_spend_reset_date = today
            self.notified_thresholds = set()
            self._save_state()
