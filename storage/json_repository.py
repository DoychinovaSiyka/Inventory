
import json
from pathlib import Path
from storage.repository import Repository


class JSONRepository(Repository):
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        if not self.filepath.exists():
            self.save([])

    def load(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def save(self, data):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # --- ДОБАВЕНО: нужно за LocationController, MovementMenu и документацията ---
    def get_all(self):
        return self.load()

# При JSON не ми се налага да извличам и добавям ръчно ред по ред.
# С json.load(file) получавам директно списък от речници,
# който веднага мога да превърна в обекти чрез from_dict.
# Това е по‑кратко и по‑удобно от CSV или plain text.json.dump се използва, когато
# искам директно да запиша Python обект във файл в JSON формат.
# Ако искам само да получа JSON като низ, използвам json.dumps







