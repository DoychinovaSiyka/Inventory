import json
from pathlib import Path
from storage.repository import Repository




class JSONRepository(Repository):
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._cache = None


    def load(self):
        if not self.filepath.exists():
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
                return self._cache
        except:
            return None



    def save(self, data):
        if data == self._cache:
            return
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self._cache = data
        except Exception as e:
            print(f"Грешка при запис: {e}")