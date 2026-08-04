class ConsomationTracker:
    def __init__(self, data):
        self.data = data
        self.rule = 0
        self.highly_consomation = self.applying_rules()

    def applying_rules(self):
        return [item for item in self.data if item.get("consumptionM3")]
    