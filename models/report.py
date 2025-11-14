import uuid
from datetime import datetime

class Report:
    def __init__(self,report_id,report_type = "",parameters = None,summary="",author = "",created_at = None):
        self.report_id = report_id if report_id else str(uuid.uuid4())
        self.report_type = report_type
        self.parameters = parameters if parameters else {}
        self.summary = summary
        self.author = anuthor
        self.created_at = created_at if created_at else datetime.now().strftime('%Y-%m-%d %H:%m:%S')


    def to_dict(self):
        return {
            "report_id":self.report_id,
            "report_type":self.report_type,
            "parameters": self.parameters,
            "summary": self.summary,
            "author": self.author,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data):
        return Report(
            report_id = data.get("report_id"),
            report_type = data.get("report_type"),
            parameters= data.get("parameters",{}),
            summary = data.get("summary"),
            author = data.get("author"),
            created_at = data.get("created_at")

        )


