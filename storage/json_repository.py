import sys, os
import json
from pathlib import Path
from storage.repository import Repository

# Родителската директория за стабилни импорти
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class JSONRepository(Repository):
    """
    Чист, безопасен Repository слой.
    - НЕ прави предположения за структурата на данните.
    - Връща {} ако файлът съдържа {}.
    - Връща [] ако файлът съдържа [].
    - Ако файлът е празен или повреден → връща празна структура според съдържанието.
    """

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Ако файлът не съществува → създаваме празен файл
        if not self.filepath.exists():
            # Ако името подсказва речник → {}
            if self.filepath.name == "inventory.json":
                self.save({})
            else:
                self.save([])

    def load(self):
        """Зарежда JSON съдържанието безопасно."""
        if not self.filepath.exists():
            return {} if self.filepath.name == "inventory.json" else []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Ако е None → връщаме празна структура
                if data is None:
                    return {} if self.filepath.name == "inventory.json" else []

                # Ако е валиден JSON → връщаме го
                return data

        except (json.JSONDecodeError, OSError):
            # Ако файлът е повреден → връщаме празна структура
            return {} if self.filepath.name == "inventory.json" else []

    def save(self, data):
        """Записва JSON съдържание безопасно."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_all(self):
        return self.load()
