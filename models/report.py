import uuid
from datetime import datetime

class Report:
    def __init__(self, report_id=None, report_type="", generated_on=None,
                 parameters=None, data=None):
        self.report_id = report_id or str(uuid.uuid4())
        self.report_type = report_type
        self.generated_on = generated_on or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.parameters = parameters if parameters else {}
        self.data = data if data else []

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "generated_on": self.generated_on,
            "parameters": self.parameters,
            "data": self.data
        }

    @staticmethod
    def from_dict(d):
        return Report(
            report_id=d.get("report_id"),
            report_type=d.get("report_type"),
            generated_on=d.get("generated_on"),
            parameters=d.get("parameters", {}),
            data=d.get("data", [])
        )
