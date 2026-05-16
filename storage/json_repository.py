import json
import os
from pathlib import Path
from storage.repository import Repository




class JSONRepository(Repository):
    """ JSON Repository:
    - inventory.json - речник
    - всички други - списък
    - стабилен кеш
    - никога не връща грешен тип"""


    def __init__(self, filepath, is_dict=False):
        self.filepath = Path(filepath)
        self.is_dict = is_dict
        self.default_data = {} if is_dict else []

        # Създаваме папката, ако липсва
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        self._cache = self._safe_load()



    def _safe_load(self):
        if not self.filepath.exists():
            return self.default_data.copy()

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()

                if not content:
                    return self.default_data.copy()

                data = json.loads(content)

                # Ако структурата е грешна - връщаме default
                if self.is_dict and not isinstance(data, dict):
                    return self.default_data.copy()

                if not self.is_dict and not isinstance(data, list):
                    return self.default_data.copy()

                return data

        except Exception:
            return self.default_data.copy()


    def load(self):
        """Връща последното валидно състояние."""
        self._cache = self._safe_load()
        return self._cache



    def save(self, data):
        """Записва само ако има промяна и имаме правилен тип."""

        if self.is_dict and not isinstance(data, dict):
            return
        if not self.is_dict and not isinstance(data, list):
            return


        if data == self._cache:
            return

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self._cache = data

        except Exception as e:
            print(f"Грешка при запис в {self.filepath.name}: {e}")



    def get_all(self):
        """Връща текущото състояние."""
        return self.load()
