import os
import json
from datetime import datetime

class BudgetOptimizer:
    def __init__(self, usage_log_path="data/usage_log.jsonl"):
        self.usage_log_path = usage_log_path
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
