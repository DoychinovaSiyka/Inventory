import sys, os
import json
from pathlib import Path
from storage.repository import Repository

# Добавяме родителската директория, за да работят импортите нормално
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class JSONRepository(Repository):
    """ Repository слой за работа с JSON файлове. Да зареждат и записват данни безопасно,
    без да прави предположения за структурата."""
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        # Кеш за избягване на излишни записи
        self._last_saved_data = None

    def load(self):
        """Чете JSON файла и връща съдържанието му. Ако е празен или повреден, връща подходяща празна структура."""

        if not self.filepath.exists():
            return {} if self.filepath.name == "inventory.json" else []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data is None:
                    return {} if self.filepath.name == "inventory.json" else []

                self._last_saved_data = data
                return data

        except (json.JSONDecodeError, OSError):
            return {} if self.filepath.name == "inventory.json" else []

    def save(self, data):
        """Записва данните обратно в JSON файла."""

        # Пишем само ако данните са различни.
        if self._last_saved_data is not None and self._last_saved_data == data:
            return

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        self._last_saved_data = data

    def get_all(self):
        return self.load()