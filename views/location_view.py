from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.location_controller import LocationController
from validators.location_validator import LocationValidator
from models.user import User


class LocationView:
    def __init__(self, location_controller: LocationController):
        self.location_controller = location_controller

    def show_menu(self, user: User):
        while True:
            menu = self._build_menu(user)
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, user: User):
        is_admin = user.role == "Admin"
        items = [MenuItem("1", "Списък с локации", self.show_all)]
        if is_admin:
            items.extend([MenuItem("2", "Добавяне на нова локация", self.add_location),
                          MenuItem("3", "Редактиране на локация", self.edit_location),
                          MenuItem("4", "Изтриване на локация", self.delete_location)])
        items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Управление на складовата мрежа", items)

    def show_all(self, user: User):
        locations = self.location_controller.get_all()
        if not locations:
            print("\n[!] Няма налични локации.")
            return

        columns = ["Код (ID)", "Име на обект", "Зона", "Капацитет"]
        rows = [[loc.location_id[:8], loc.name, loc.zone, loc.capacity] for loc in locations]

        print("\n--- СПИСЪК НА СКЛАДОВЕТЕ И МАГАЗИНИТЕ ---")
        print(format_table(columns, rows))

    def add_location(self, user: User):
        print("\n--- ДОБАВЯНЕ НА НОВА ЛОКАЦИЯ ---")
        name = input("Име на локация (Enter = отказ): ").strip()
        if not name:
            return

        zone = input("Зона/Сектор: ").strip() or ""
        capacity_raw = input("Капацитет (число): ").strip()
        if not capacity_raw: return
        try:
            capacity = LocationValidator.validate_capacity(capacity_raw)
            new_loc = self.location_controller.add(name=name, zone=zone, capacity=capacity)
            print(f"Успех! Локацията е добавена с код: {new_loc.location_id[:8]}")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def edit_location(self, user: User):
        print("\n--- РЕДАКТИРАНЕ НА ЛОКАЦИЯ ---")
        loc_id = input("Въведете Код/ID (пълен или първите 8 знака): ").strip()
        if not loc_id: return


        location = self.location_controller.get_by_id(loc_id)
        if location is None:
            print("Локация с такъв код не съществува.")
            return

        print(f"\nРедактиране на [{location.location_id[:8]}]. Празно = без промяна.")
        new_name = input(f"Ново име ({location.name}): ").strip() or None
        new_zone = input(f"Нова зона ({location.zone}): ").strip() or None
        new_cap_raw = input(f"Нов капацитет ({location.capacity}): ").strip() or None

        try:
            self.location_controller.update(location.location_id, name=new_name, zone=new_zone, capacity=new_cap_raw)
            print(f"Данните за '{location.name}' бяха обновени!")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def delete_location(self, user: User):
        print("\n--- ИЗТРИВАНЕ НА ЛОКАЦИЯ ---")
        loc_id = input("Въведете Код/ID за изтриване: ").strip()
        if not loc_id: return

        location = self.location_controller.get_by_id(loc_id)
        if not location:
            print("Локацията не е намерена.")
            return

        confirm = input(f"Сигурни ли сте, че триете {location.name} [{location.location_id[:8]}]? (y/n): ").lower()
        if confirm == 'y':
            try:
                self.location_controller.remove(location.location_id)
                print(f"Локацията беше премахната успешно.")
            except ValueError as e:
                print(f"[Грешка] {e}")