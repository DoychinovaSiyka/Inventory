import sys, os
import json
from pathlib import Path
from storage.repository import Repository

# Добавям родителската директория, за да работят импортите нормално
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class JSONRepository(Repository):
    """ Repository слой за работа с JSON файлове. Да зарежда и записва данни безопасно."""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        # Автоматично създаваме папките, ако липсват
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        # Кеш за избягване на излишни записи
        self._last_saved_data = None

    def load(self):
        """Чете JSON файла и връща съдържанието му.
           Ако файлът липсва - създава правилната празна структура.
           Ако е празен - връща правилната структура."""

        # Определяме правилната празна структура според името на файла
        if self.filepath.name == "inventory.json":
            empty = {}      # инвентарът е речник
        else:
            empty = []      # всички други JSON-и са списъци

        # Ако файлът липсва -> създаваме го
        if not self.filepath.exists():
            self.save(empty)
            return empty

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Празен файл -> връщаме правилната структура
                if not content:
                    return empty

                data = json.loads(content)
                self._last_saved_data = data
                return data

        except Exception:
            # При грешка -> връщаме правилната структура
            return empty

    def save(self, data):
        """Записва данните обратно в JSON файла."""

        if self.filepath.name == "report_history.json" and isinstance(data, list):
            try:
                data = sorted(data, key=lambda r: r.get("generated_on", ""))
            except Exception:
                pass  # ако нещо стане, просто записваме без сортиране

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self._last_saved_data = data
        except Exception as e:
            print(f"Грешка при запис във файл {self.filepath.name}: {e}")

    def get_all(self):
        """ Връща всички данни от файла. """
        return self.load()
