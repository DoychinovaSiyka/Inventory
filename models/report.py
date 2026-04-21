import uuid

class Report:
    def __init__(self, report_type, generated_on, parameters=None, data=None, report_id=None):
        self.report_id = str(report_id) if report_id else str(uuid.uuid4())
        self.report_type = report_type
        self.generated_on = generated_on
        self.parameters = parameters if parameters is not None else {} # празни колекции, ако не са подадени
        self.data = data if data is not None else []

    def to_dict(self):
        """Превръща обекта в речник за запис в JSON."""
        return {"report_id": self.report_id, "report_type": self.report_type,
                "generated_on": self.generated_on, "parameters": self.parameters, "data": self.data}

    @staticmethod
    def from_dict(d):
        """Зарежда обекта от JSON речник."""
        if not d:
            return None
        return Report(report_id=d.get("report_id"), report_type=d.get("report_type", ""),
                      generated_on=d.get("generated_on", ""), parameters=d.get("parameters"), data=d.get("data"))

    def __str__(self):
        return f"Отчет {self.report_id} | Тип: {self.report_type} | Записан на: {self.generated_on}"
