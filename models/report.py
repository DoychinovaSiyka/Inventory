import uuid


class Report:
    def __init__(self, report_type, generated_on, parameters=None, data=None, report_id=None):
        # Моделът вече не генерира датата сам - той я получава от контролера
        self.report_id = report_id or str(uuid.uuid4())
        self.report_type = report_type
        self.generated_on = generated_on

        # Гарантираме, че са празни колекции, ако не са подадени
        self.parameters = parameters if parameters is not None else {}
        self.data = data if data is not None else []

    def to_dict(self):
        """Превръща обекта в речник за запис в JSON."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "generated_on": self.generated_on,
            "parameters": self.parameters,
            "data": self.data
        }

    @staticmethod
    def from_dict(d):
        """Зарежда обекта от JSON речник."""
        return Report(
            report_id=d.get("report_id"),
            report_type=d.get("report_type", ""),
            generated_on=d.get("generated_on", ""),
            parameters=d.get("parameters"),
            data=d.get("data")
        )