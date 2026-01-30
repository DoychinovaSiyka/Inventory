from models.report import Report
from storage.json_repository import JSONRepository
from datetime import datetime


class ReportController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.reports = self._load()

    # -----------------------------
    # Вътрешни методи
    # -----------------------------
    def _load(self):
        data = self.repo.load()
        return [Report.from_dict(item) for item in data]

    def _save(self):
        self.repo.save([r.to_dict() for r in self.reports])

    # -----------------------------
    # Основни операции
    # -----------------------------
    def create_report(self, report_type, parameters, summary, author):
        """
        Създава нова справка.
        report_type: тип на справката (products, movements, low_stock, invoices и др.)
        parameters: критерии за филтриране
        summary: текстово описание на резултата
        author: потребителят, който е генерирал справката
        """

        report = Report(
            report_type=report_type,
            parameters=parameters,
            summary=summary,
            author=author
        )

        self.reports.append(report)
        self._save()
        return report

    # -----------------------------
    # Търсене и филтриране
    # -----------------------------
    def get_all(self):
        return self.reports

    def get_by_id(self, report_id):
        for r in self.reports:
            if r.report_id == report_id:
                return r
        return None

    def search_by_type(self, report_type):
        return [r for r in self.reports if r.report_type.lower() == report_type.lower()]

    def search_by_author(self, author):
        return [r for r in self.reports if r.author.lower() == author.lower()]

    def search_by_date(self, date_str):
        """
        date_str: 'YYYY-MM-DD'
        """
        return [r for r in self.reports if r.created_at.startswith(date_str)]

    def filter_by_parameter(self, key, value):
        """
        Филтрира справки по параметър.
        Пример: key="category", value="Drinks"
        """
        return [
            r for r in self.reports
            if key in r.parameters and str(r.parameters[key]).lower() == str(value).lower()
        ]

    # -----------------------------
    # Изтриване (ако е нужно)
    # -----------------------------
    def remove(self, report_id):
        for r in self.reports:
            if r.report_id == report_id:
                self.reports.remove(r)
                self._save()
                return True
        return False
