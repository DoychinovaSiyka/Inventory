import uuid
from datetime import datetime

class Report:
    def __init__(self, report_type, parameters=None, data=None, generated_on=None, report_id=None):
        """ Модел за отчет. Съхранява метаданни и резултати от справки. """

        # СИНХРОНИЗАЦИЯ: 8 символа за консистентност с целия проект
        if not report_id:
            self.report_id = str(uuid.uuid4())[:8]
        else:
            self.report_id = str(report_id)

        self.generated_on = generated_on or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.report_type = report_type
        self.parameters = parameters if parameters is not None else {}
        self.data = data if data is not None else {}

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
        if not d:
            return None
        return Report(
            report_id=d.get("report_id"),
            report_type=d.get("report_type", ""),
            generated_on=d.get("generated_on", ""),
            parameters=d.get("parameters"),
            data=d.get("data")
        )

    def __str__(self):
        # По-красив изглед при принтиране в CMD
        return f"Отчет #{self.report_id} | Тип: {self.report_type} | Генериран на: {self.generated_on}"