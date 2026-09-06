from views.menu import Menu, MenuItem
from views.password_utils import format_table

from controllers.location_controller import LocationController






class LocationView:
    def __init__(self, location_controller: LocationController):
        self.location_controller = location_controller


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
        locations = self.location_controller.get_all()
        if not locations:
            print("\nНяма налични локации.")
            return

        print("\nСПИСЪК С ЛОКАЦИИ")
        columns = ["Код", "Име", "Зона", "Капацитет", "Системно ID"]
        rows = [[loc.code if loc.code else "-", loc.name, loc.zone, loc.capacity, loc.location_id[:8]] for loc in locations]
        print(format_table(columns, rows))





    def search_location(self, _):
        print("\nТърсене на локация")
        query = input("Въведете Код, Име, Зона или ID: ").strip().lower()
        if not query:
            print("Празно търсене.")
            return

        results = self.location_controller.search(query)
        if not results:
            print("Няма намерени локации.")
            return

        print("\nНамерени локации:")
        columns = ["Код", "Име", "Зона", "Капацитет", "Системно ID"]
        rows = [[loc.get("code", "-"), loc["name"], loc["zone"], loc["capacity"], loc["id"]] for loc in results]
        print(format_table(columns, rows))




    def add_location(self, _):
        print("\nНова локация")

        while True:
            code = input("Кратък КОД (напр. W1): ").strip()
            if not code:
                return
            error = self.location_controller.validate_field("code", code)
            if error:
                print(f"Грешка: {error}")
                continue
            break


        while True:
            name = input("Име на локация: ").strip()
            if not name:
                return
            error = self.location_controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue
            break


        while True:
            zone = input("Зона/Сектор: ").strip()
            if not zone:
                return
            error = self.location_controller.validate_field("zone", zone)
            if error:
                print(f"Грешка: {error}")
                continue
            break


        while True:
            cap_raw = input("Капацитет (число): ").strip()
            error = self.location_controller.validate_field("capacity", cap_raw)
            if error:
                print(f"Грешка: {error}")
                continue
            capacity = int(cap_raw)
            break

        try:
            new_loc = self.location_controller.add(name=name, zone=zone, capacity=capacity, code=code)
            print("\nЛокацията е добавена успешно!")
            print(f"Код: {new_loc.code} | Име: {new_loc.name}")
        except Exception as e:
            print(f"Грешка при добавяне: {e}")




    def edit_location(self, _):
        print("\nРедактиране на локация")
        identifier = input("Въведете Код или Системно ID: ").strip()
        if not identifier:
            return

        location = self.location_controller.get_by_id(identifier)
        if not location:
            print("Не е намерена локация.")
            return

        print(f"\nРедактиране на [{location.name}]")


        while True:
            new_code_raw = input(f"Нов КОД [{location.code}]: ").strip()
            new_code = new_code_raw if new_code_raw else location.code
            error = self.location_controller.validate_field("code", new_code)
            if error:
                print(f"Грешка: {error}")
                continue
            break


        while True:
            new_name_raw = input(f"Ново име [{location.name}]: ").strip()
            new_name = new_name_raw if new_name_raw else location.name
            error = self.location_controller.validate_field("name", new_name)
            if error:
                print(f"Грешка: {error}")
                continue
            break


        while True:
            new_zone_raw = input(f"Нова зона [{location.zone}]: ").strip()
            new_zone = new_zone_raw if new_zone_raw else location.zone
            error = self.location_controller.validate_field("zone", new_zone)
            if error:
                print(f"Грешка: {error}")
                continue
            break


        while True:
            new_cap_raw = input(f"Нов капацитет [{location.capacity}]: ").strip()
            new_cap = new_cap_raw if new_cap_raw else location.capacity
            error = self.location_controller.validate_field("capacity", str(new_cap))
            if error:
                print(f"Грешка: {error}")
                continue
            break

        try:
            self.location_controller.update(location.location_id, name=new_name, zone=new_zone, capacity=new_cap, code=new_code)
            print("Данните са обновени успешно.")

        except Exception as e:
            print(f"Грешка при обновяване: {e}")






    def delete_location(self, _):
        print("\nИзтриване на локация")
        identifier = input("Въведете Код или Системно ID: ").strip()
        if not identifier:
            return

        location = self.location_controller.get_by_id(identifier)
        if not location:
            print("Не е намерена локация.")
            return

        try:
            if self.location_controller.remove(location.location_id):
                print(f"Локация {location.code} / {location.name} е изтрита успешно.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
