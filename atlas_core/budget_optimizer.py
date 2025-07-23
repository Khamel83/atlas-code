import os
import json
from datetime import datetime, timedelta

class BudgetOptimizer:
    def __init__(self, usage_log_path="data/ralex_usage_log.jsonl", daily_limit=None):
        self.usage_log_path = usage_log_path
        self.daily_limit = daily_limit
        os.makedirs(os.path.dirname(self.usage_log_path), exist_ok=True)

    def record_usage(self, model, tokens_sent, tokens_received, cost):
        """Records usage data to the usage log file."""
        with open(self.usage_log_path, "a") as f:
            record = {
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "tokens_sent": tokens_sent,
                "tokens_received": tokens_received,
                "cost": cost
            }
            f.write(json.dumps(record) + "\n")

    def get_total_spent(self):
        """Reads the usage log and sums the total cost."""
        total_cost = 0.0
        if not os.path.exists(self.usage_log_path):
            return total_cost

        with open(self.usage_log_path, "r") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    total_cost += record.get("cost", 0.0)
                except json.JSONDecodeError:
                    continue
        return total_cost

    def get_spent_today(self):
        """Calculates the total cost spent today."""
        total_cost_today = 0.0
        if not os.path.exists(self.usage_log_path):
            return total_cost_today

        today = datetime.now().date()
        with open(self.usage_log_path, "r") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    record_date = datetime.fromisoformat(record["timestamp"]).date()
                    if record_date == today:
                        total_cost_today += record.get("cost", 0.0)
                except (json.JSONDecodeError, ValueError):
                    continue
        return total_cost_today

    def check_budget_status(self):
        """Compares current spending against the daily limit and returns a status."""
        if self.daily_limit is None:
            return {"status": "no_limit", "spent_today": self.get_spent_today(), "daily_limit": None}

        spent_today = self.get_spent_today()
        percentage_used = (spent_today / self.daily_limit) * 100

        status = "safe"
        if percentage_used >= 100:
            status = "exceeded"
        elif percentage_used >= 80:
            status = "warning"
        
        return {
            "status": status,
            "spent_today": spent_today,
            "daily_limit": self.daily_limit,
            "percentage_used": percentage_used
        }
