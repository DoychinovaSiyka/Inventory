from views.menu import Menu, MenuItem
from views.password_utils import format_table


class LocationView:
    def __init__(self, location_controller):
        self.controller = location_controller



    def show_menu(self, user):
        while True:
            is_admin = (user and user.role == "Admin")
            menu = self._build_menu(is_admin)
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, is_admin):
        items = [MenuItem("1", "Списък с локации", self.show_all),
                 MenuItem("2", "Търсене на локация", self.search_location)]

        if is_admin:
            items.extend([
                MenuItem("3", "Добавяне на локация", self.add_location),
                MenuItem("4", "Редактиране на локация", self.edit_location),
                MenuItem("5", "Изтриване на локация", self.delete_location)])

        items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Управление на локации", items)



    def show_all(self, _):
        locations = self.controller.get_all()
        if not locations:
            print("\nНяма налични локации.")
            return

        print("\nСПИСЪК С ЛОКАЦИИ")
        columns = ["Код (ID)", "Име", "Зона", "Капацитет"]
        rows = [[loc.location_id[:8], loc.name, loc.zone, loc.capacity] for loc in locations]
        print(format_table(columns, rows))



    def search_location(self, _):
        print("\nТърсене на локация")
        query = input("Въведете ID, име, зона или капацитет: ").strip().lower()
        if not query:
            print("Празно търсене.")
            return

        results = self.controller.search(query)
        if not results:
            print("Няма намерени локации.")
            return

        print("\nНамерени локации:")
        columns = ["Код (ID)", "Име", "Зона", "Капацитет"]
        rows = [[loc.location_id[:8], loc.name, loc.zone, loc.capacity] for loc in results]
        print(format_table(columns, rows))



    def add_location(self, _):
        print("\nНова локация (Остави празно за отказ)")

        try:
            name_raw = input("Име на локация: ").strip()
            if not name_raw:
                return
            name = self.controller.validate_field("name", name_raw)

            zone_raw = input("Зона/Сектор: ").strip()
            if not zone_raw:
                return
            zone = self.controller.validate_field("zone", zone_raw)

            cap_raw = input("Капацитет: ").strip()
            if not cap_raw:
                return
            capacity = self.controller.validate_field("capacity", cap_raw)

            new_loc = self.controller.add(name=name, zone=zone, capacity=capacity)
            print(f"\nЛокацията е добавена. Код: {new_loc.location_id[:8]}")
        except Exception as e:
            print(f"Грешка: {e}")



    def edit_location(self, _):
        print("\nРедактиране на локация")
        loc_id = input("Въведете кратко ID: ").strip()
        if not loc_id:
            return

        location = self.controller.get_by_id(loc_id)
        if not location:
            print("Не е намерена локация с това ID.")
            return

        print(f"\nРедактиране на [{location.name}] (Enter за запазване на старото)")
        try:

            new_name_raw = input(f"Ново име [{location.name}]: ").strip()
            new_name = self.controller.validate_field("name", new_name_raw) if new_name_raw else location.name


            new_zone_raw = input(f"Нова зона [{location.zone}]: ").strip()
            new_zone = self.controller.validate_field("zone", new_zone_raw) if new_zone_raw else location.zone


            new_cap_raw = input(f"Нов капацитет [{location.capacity}]: ").strip()
            new_cap = self.controller.validate_field("capacity", new_cap_raw) if new_cap_raw else location.capacity

            self.controller.update(location.location_id[:8], name=new_name, zone=new_zone, capacity=new_cap)
            print("Данните са обновени успешно.")
        except Exception as e:
            print(f"Грешка при обновяване: {e}")



    def delete_location(self, _):
        print("\nИзтриване на локация")
        loc_id = input("Кратко ID на локация: ").strip()
        if not loc_id:
            return

        location = self.controller.get_by_id(loc_id)
        if not location:
            print("Не е намерена локация с това ID.")
            return

        try:
            if self.controller.remove(location.location_id[:8]):
                print("Локацията е изтрита успешно.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")