import datetime

class TierRouter:
    def __init__(self, model_tiers):
        self.model_tiers = model_tiers

    def get_model_for_task(self, task_type):
        if not self.model_tiers:
            raise ValueError("Model tiers are not configured.")

        task_type_upper = task_type.upper()
        model = self.model_tiers.get(task_type_upper)

        if model is None:
            raise ValueError(f"Model tier '{task_type_upper}' is not configured.")

        return model