import datetime
import json
import os
from pathlib import Path

class BudgetManager:
    def __init__(self, daily_budget, notify_thresholds, cutoff_time, io=None):
        self.daily_budget = daily_budget
        self.notify_thresholds = notify_thresholds
        self.cutoff_time = cutoff_time
        self.io = io
        self.cumulative_spend = 0.0
        self.approved = False
        self.last_reset_date = datetime.date.today()
        self.state_file = Path.home() / ".atlas_code" / "budget_state.json"
        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.cumulative_spend = state.get("cumulative_spend", 0.0)
                self.approved = state.get("approved", False)
                last_reset_date_str = state.get("last_reset_date")
                if last_reset_date_str:
                    self.last_reset_date = datetime.datetime.strptime(last_reset_date_str, "%Y-%m-%d").date()

                # Reset if new day
                if self.last_reset_date < datetime.date.today():
                    self.cumulative_spend = 0.0
                    self.approved = False
                    self.last_reset_date = datetime.date.today()

            except Exception as e:
                if self.io:
                    self.io.tool_warning(f"Failed to load budget state: {e}")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _save_state(self):
        state = {
            "cumulative_spend": self.cumulative_spend,
            "approved": self.approved,
            "last_reset_date": self.last_reset_date.strftime("%Y-%m-%d"),
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Failed to save budget state: {e}")

    def add_spend(self, cost):
        self.cumulative_spend += cost
        self._save_state()

    def get_status(self):
        remaining_budget = self.daily_budget - self.cumulative_spend
        return {
            "cumulative_spend": self.cumulative_spend,
            "remaining_budget": remaining_budget,
            "daily_budget": self.daily_budget,
            "approved": self.approved,
            "last_reset_date": self.last_reset_date.strftime("%Y-%m-%d"),
        }

    def set_approved(self, status):
        self.approved = status
        self._save_state()

    def check_thresholds(self):
        notifications = []
        for threshold in self.notify_thresholds:
            if self.cumulative_spend >= self.daily_budget * threshold and \
               (self.cumulative_spend - self.last_added_cost < self.daily_budget * threshold if hasattr(self, 'last_added_cost') else True):
                notifications.append(f"Budget threshold {threshold*100:.0f}% reached!")
        return notifications

    def should_notify(self, estimated_cost):
        for threshold in self.notify_thresholds:
            if (self.cumulative_spend < self.daily_budget * threshold and
                self.cumulative_spend + estimated_cost >= self.daily_budget * threshold):
                return True
        return False

    def should_cutoff(self, estimated_cost):
        return self.cumulative_spend + estimated_cost > self.daily_budget and not self.approved
