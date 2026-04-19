import sys, os
import json
from pathlib import Path
from storage.repository import Repository

# Добавяме родителската директория, за да работят импортите нормално
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class JSONRepository(Repository):
    """
    Repository слой за работа с JSON файлове.
    Идеята е да зарежда и записва данни безопасно,
    без да прави предположения за структурата.
    """

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Ако файлът липсва, създаваме празен според типа
        if not self.filepath.exists():
            if self.filepath.name == "inventory.json":
                self.save({})
            else:
                self.save([])

    def load(self):
        """Чете JSON файла и връща съдържанието му.
        Ако е празен или повреден, връща подходяща празна структура.
        """
        if not self.filepath.exists():
            return {} if self.filepath.name == "inventory.json" else []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Ако файлът е празен (None), връщаме празна структура
                if data is None:
                    return {} if self.filepath.name == "inventory.json" else []

                return data

        except (json.JSONDecodeError, OSError):
            # Ако JSON-ът е счупен, връщаме празна структура
            return {} if self.filepath.name == "inventory.json" else []

    def save(self, data):
        """Записва данните обратно в JSON файла."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_all(self):
        """Удобен shorthand за load()."""
        return self.load()
