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
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, is_admin):
        items = [MenuItem("1", "Списък с локации", self.show_all),
                 MenuItem("2", "Търсене на локация", self.search_location)]

        if is_admin:
            items.extend([MenuItem("3", "Добавяне на локация", self.add_location),
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
        print("\nНова локация (Enter за отказ)")

        while True:
            name = input("Име на локация: ").strip()
            if not name:
                print("Името е задължително.")
                continue
            try:
                name = self.controller.validator.validate_name(name)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            zone = input("Зона/Сектор: ").strip()
            if not zone:
                print("Зоната е задължителна.")
                continue
            try:
                zone = self.controller.validator.validate_zone(zone)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            capacity_raw = input("Капацитет (цяло число): ").strip()
            if not capacity_raw:
                print("Капацитетът е задължителен.")
                continue
            try:
                capacity = self.controller.validator.validate_capacity(capacity_raw)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        try:
            new_loc = self.controller.add(name=name, zone=zone, capacity=capacity)
            print(f"\nЛокацията е добавена. Код: {new_loc.location_id[:8]}")
        except Exception as e:
            print(f"Грешка при запис: {e}")



    def edit_location(self, _):
        print("\nРедактиране на локация")
        while True:
            loc_id = input("Въведете кратко ID: ").strip()
            if not loc_id:
                return

            location = self.controller.get_by_id(loc_id)
            if location:
                break

            print("Не е намерена локация с това ID.")

        print(f"\nРедактиране на [{location.name}]")

        while True:
            new_name = input(f"Ново име [{location.name}]: ").strip()
            if not new_name:
                new_name = location.name
                break
            try:
                new_name = self.controller.validator.validate_name(new_name)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            new_zone = input(f"Нова зона [{location.zone}]: ").strip()
            if not new_zone:
                new_zone = location.zone
                break
            try:
                new_zone = self.controller.validator.validate_zone(new_zone)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            new_cap_raw = input(f"Нов капацитет [{location.capacity}]: ").strip()
            if not new_cap_raw:
                new_cap = location.capacity
                break
            try:
                new_cap = self.controller.validator.validate_capacity(new_cap_raw)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        try:
            self.controller.update(location.location_id[:8], name=new_name, zone=new_zone, capacity=new_cap)
            print("Данните са обновени успешно.")
        except Exception as e:
            print(f"Проблем при обновяване: {e}")



    def delete_location(self, _):
        print("\nИзтриване на локация")

        while True:
            loc_id = input("Кратко ID на локация: ").strip()
            if not loc_id:
                return

            location = self.controller.get_by_id(loc_id)
            if location:
                break

            print("Не е намерена локация с това ID.")

        try:
            self.controller.remove(location.location_id[:8])
            print("Локацията е изтрита успешно.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
