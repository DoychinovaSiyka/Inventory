from datetime import datetime



# Модел на справка

class Report:
    def __init__(self,report_type,params = None,result = None,created =None):
        self.report_type = report_type
        self.params = params or {}
        if self.result is not None:
            self.result  = result
        else:
            self.result = []
        self.created = created or datetime.now().isoformat()