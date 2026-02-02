from models.location import Location
from storage.json_repository import JSONRepository


class LocationController:
    def __init__(self, location_repo: JSONRepository):
        self.location_repo = location_repo

    # --- Създаване на локация ---
    def create_location(self, name):
        if not name or name.strip() == "":
            print("Името на локацията не може да бъде празно.")
            return None

        new_location = Location(name=name)
        self.location_repo.add(new_location)
        print(f"Локацията '{name}' е добавена успешно.")
        return new_location

    # --- Връщане на всички локации ---
    def get_all_locations(self):
        return self.location_repo.get_all()

    # --- Намиране по ID ---
    def get_location_by_id(self, location_id):
        return self.location_repo.get_by_id(location_id)

    # --- Актуализиране ---
    def update_location(self, location_id, new_name):
        location = self.location_repo.get_by_id(location_id)
        if not location:
            print("Локацията не е намерена.")
            return None

        if not new_name or new_name.strip() == "":
            print("Новото име не може да бъде празно.")
            return None

        location.name = new_name
        self.location_repo.update(location)
        print("Локацията е обновена успешно.")
        return location

    # --- Изтриване ---
    def delete_location(self, location_id):
        location = self.location_repo.get_by_id(location_id)
        if not location:
            print("Локацията не е намерена.")
            return False

        self.location_repo.delete(location_id)
        print("Локацията е изтрита успешно.")
        return True

# LocationController е важен,защото иначе няма кой да управлява:
# създаване на локации
# списък с локации
# връзка между склад и локация
# евентуално търсене по локация
