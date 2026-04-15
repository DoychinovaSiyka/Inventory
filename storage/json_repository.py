import sys, os
import json
from pathlib import Path
from storage.repository import Repository

# Родителската директория за стабилни импорти
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class JSONRepository(Repository):
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        # Създаване на директорията при нужда
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Ако файлът не съществува – създаваме празен JSON
        if not self.filepath.exists():
            self.save([])

    def load(self):
        # Зареждане на данните от JSON файла
        with open(self.filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def save(self, data):
        # Записване на данните в JSON файла
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_all(self):
        # Връща всички записи от файла
        return self.load()




