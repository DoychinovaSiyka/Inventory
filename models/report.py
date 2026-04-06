from datetime import datetime
import uuid


class Report:
    def __init__(self, report_type="", generated_on=None,
                 parameters=None, data=None, report_id=None):

        # Уникален идентификатор на отчета (генерира се само ако липсва)
        self.report_id = report_id or str(uuid.uuid4())

        # Тип на отчета (stock, movements, sales и т.н.)
        self.report_type = report_type

        # Дата на генериране
        self.generated_on = generated_on or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Параметри на отчета (филтри)
        self.parameters = parameters if parameters else {}

        # Данни на отчета (списък от записи)
        self.data = data if data else []

    def to_dict(self):
        """Преобразува отчета в dict за запис в JSON."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "generated_on": self.generated_on,
            "parameters": self.parameters,
            "data": self.data
        }

    @staticmethod
    def from_dict(d):
        """Създава Report обект от dict (зареждане от JSON)."""
        return Report(
            report_id=d.get("report_id"),
            report_type=d.get("report_type"),
            generated_on=d.get("generated_on"),
            parameters=d.get("parameters", {}),
            data=d.get("data", [])
        )
