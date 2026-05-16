import uuid
from datetime import datetime


class Report:
    def __init__(self, report_type, data=None):
        """ Модел за отчет. Съществува само в паметта, за да пренесе данните от контролера към view."""

        self.report_id = str(uuid.uuid4())
        self.generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.report_type = report_type
        self.data = data if data is not None else []

    def __str__(self):
        short_id = self.report_id[:8]
        return f"Отчет #{short_id} | Тип: {self.report_type} | Генериран на: {self.generated_on}"