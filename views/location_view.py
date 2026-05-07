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
            items.extend([
                MenuItem("2", "Добавяне на нова локация", self.add_location),
                MenuItem("3", "Редактиране на локация", self.edit_location),
                MenuItem("4", "Изтриване на локация", self.delete_location)])
        items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Управление на локации", items)

    def show_all(self, user: User):
        locations = self.location_controller.get_all()
        if not locations:
            print("\nНяма налични локации.")
            return

        columns = ["Код (ID)", "Име", "Зона", "Капацитет"]
        rows = []
        for loc in locations:
            rows.append([loc.location_id[:8], loc.name, loc.zone, loc.capacity])

        print("\nСписък на локациите")
        print(format_table(columns, rows))

    def add_location(self, user: User):
        print("\nДобавяне на нова локация")
        print("(Напишете 'отказ' за излизане)")

        while True:
            name = input("Име на локация: ").strip()
            if name.lower() == 'отказ':
                return
            if not name:
                print("Името не може да бъде празно.")
                continue
            break

        zone = input("Зона/Сектор: ").strip() or "General"

        while True:
            capacity_raw = input("Капацитет (число): ").strip()
            if capacity_raw.lower() == 'отказ':
                return
            try:
                capacity = LocationValidator.validate_capacity(capacity_raw)
                break
            except ValueError as e:
                print(f"Грешка: {e}. Въведете валидно число.")

        try:
            new_loc = self.location_controller.add(name=name, zone=zone, capacity=capacity)
            print(f"\nЛокацията е добавена. Код: {new_loc.location_id[:8]}")
        except Exception as e:
            print(f"Грешка: {e}")

    def edit_location(self, user: User):
        print("\nРедактиране на локация")

        while True:
            loc_id = input("Въведете ID (или 'отказ'): ").strip()
            if not loc_id or loc_id.lower() == 'отказ':
                return

            location = self.location_controller.get_by_id(loc_id)
            if location:
                break

            print("Локацията не е намерена.")

        print(f"\nРедактиране на {location.name} ({location.location_id[:8]})")
        print("Празно поле запазва старата стойност.")

        new_name = input(f"Ново име ({location.name}): ").strip() or None
        new_zone = input(f"Нова зона ({location.zone}): ").strip() or None

        new_cap = None
        while True:
            new_cap_raw = input(f"Нов капацитет ({location.capacity}): ").strip()
            if not new_cap_raw:
                break
            if new_cap_raw.lower() == 'отказ':
                return
            try:
                new_cap = LocationValidator.validate_capacity(new_cap_raw)
                break
            except ValueError as e:
                print(f"Грешка: {e}")

        try:
            self.location_controller.update(location.location_id, name=new_name, zone=new_zone,
                                            capacity=new_cap)
            print("Данните са обновени.")
        except Exception as e:
            print(f"Грешка: {e}")

    def delete_location(self, user: User):
        print("\nИзтриване на локация")

        while True:
            loc_id = input("Въведете ID (или 'отказ'): ").strip()
            if not loc_id or loc_id.lower() == 'отказ':
                return

            location = self.location_controller.get_by_id(loc_id)
            if location:
                break

            print("Локацията не е намерена.")

        confirm = input(f"Изтриване на {location.name} ({location.location_id[:8]})? (y/n): ").lower()
        if confirm == 'y':
            try:
                self.location_controller.remove(location.location_id)
                print("Локацията е премахната.")
            except Exception as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")
