import datetime

class TierRouter:
    def __init__(self, model_tiers, daily_budget, notify_thresholds, cutoff_time):
        self.model_tiers = model_tiers
        self.daily_budget = daily_budget
        self.notify_thresholds = sorted(notify_thresholds)
        self.cutoff_time = datetime.datetime.strptime(cutoff_time, "%H:%M").time()

    def get_current_tier(self, current_spend):
        # Check time of day for potential tier downgrade
        now = datetime.datetime.now().time()
        if now >= self.cutoff_time:
            return self.model_tiers.get("execution", "default_execution_model")

        # Check budget thresholds for tier downgrade
        for threshold in self.notify_thresholds:
            if current_spend >= self.daily_budget * threshold:
                # If current spend exceeds a threshold, suggest a lower tier
                if threshold == self.notify_thresholds[-1]: # Last threshold, likely budget exhausted
                    return self.model_tiers.get("execution", "default_execution_model")
                elif threshold == self.notify_thresholds[0]: # First threshold, suggest drafting
                    return self.model_tiers.get("drafting", "default_drafting_model")

        # Default to planning tier if no conditions met for downgrade
        return self.model_tiers.get("planning", "default_planning_model")
