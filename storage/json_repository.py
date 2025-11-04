import json
from pathlib import Path # помага за работа с файлови пътища
import json

from  storage.repository import Repository


class JSONRepository(Repository):
    def __init__(self,filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents= True,exist_ok=True) # Създава директорията и всички липсващи родителски директории, ако не съществуват
        if not self.filepath.exists():
            self.save([])

    def load(self):
        with open(self.filepath,"r",encoding = "utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    def save(self,data):
        with open(self.filepath,"w",encoding = "utf-8") as f:
           json.dump(data,f,indent= 4)












