import json
import sys
import os
from pathlib import Path
from storage.repository import Repository

# родителската директория, за да работят импортите нормално
sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class JSONRepository(Repository):
    def __init__(self, filepath, is_dict=False):
        self.filepath = Path(filepath)
        # Дефинираме структурата (речник за inventory, списък за останалите)
        self.default_data = {} if is_dict else []
        # Създаваме папката data/, ако не съществува
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._cache = self.load()

    def load(self):
        if not self.filepath.exists():
            return self.default_data

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return self.default_data

                data = json.loads(content)
                self._cache = data  # Обновяваме кеша при всяко успешно четене
                return data
        except Exception:
            return self.default_data

    def save(self, data):
        """ Записва данните само ако има реална промяна. """
        if data == self._cache:
            return

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self._cache = data
        except Exception as e:
            print(f"Грешка при запис в {self.filepath.name}: {e}")

    def get_all(self):
        """ Връща текущото състояние на данните. """
        return self.load()