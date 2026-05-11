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
        items = [MenuItem("1", "Списък с локации", self.show_all)]
        if is_admin:
            items.extend([
                MenuItem("2", "Добавяне на локация", self.add_location),
                MenuItem("3", "Редактиране на локация", self.edit_location),
                MenuItem("4", "Изтриване на локация", self.delete_location)])
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




    def add_location(self, _):
        print("\nНова локация (Enter за отказ)")
        while True:
            name = input("Име/Код на локация: ").strip()
            if not name:
                print("Името е задължително.")
                continue
            if len(name) < 2:
                print("Името трябва да е поне 2 символа.")
                continue

            try:
                self.controller.validate_field("name", name)

                all_locs = self.controller.get_all()
                duplicate = False
                for l in all_locs:
                    if l.name.lower() == name.lower():
                        duplicate = True
                        break

                if duplicate:
                    print(f"Локация с име '{name}' вече съществува.")
                    continue

                break

            except ValueError as e:
                print(f"Грешка: {e}")


        while True:
            zone = input("Зона/Сектор: ").strip()
            if not zone:
                print("Зоната е задължителна.")
                continue
            if len(zone) < 2:
                print("Зоната трябва да е поне 2 символа.")
                continue

            try:
                self.controller.validate_field("zone", zone)
                break
            except ValueError as e:
                print(f"Грешка: {e}")


        while True:
            capacity_raw = input("Капацитет (цяло число): ").strip()
            if not capacity_raw:
                print("Капацитетът е задължителен.")
                continue

            try:
                self.controller.validate_field("capacity", capacity_raw)
                final_capacity = int(capacity_raw)
                break
            except ValueError as e:
                print(f"Грешка: {e}")


        try:
            new_loc = self.controller.add(name=name, zone=zone, capacity=final_capacity)
            print(f"\nЛокацията е добавена. Код: {new_loc.location_id[:8]}")
        except Exception as e:
            print(f"Грешка при запис: {e}")




    def edit_location(self, _):
        print("\nРедактиране на локация")
        while True:
            loc_id = input("Въведете ID за търсене: ").strip()
            if not loc_id:
                return
            location = self.controller.get_by_id(loc_id)
            if location:
                break
            print("Не е намерена локация с това ID.")

        print(f"\nРедактиране на [{location.name}]. Оставете празно за запазване.")


        while True:
            new_name = input(f"Ново име [{location.name}]: ").strip()
            if not new_name:
                new_name = location.name
                break
            if len(new_name) < 2:
                print("Името трябва да е поне 2 символа.")
                continue

            try:
                self.controller.validate_field("name", new_name)

                all_locs = self.controller.get_all()
                duplicate = False
                for l in all_locs:
                    if l.location_id != location.location_id:
                        if l.name.lower() == new_name.lower():
                            duplicate = True
                            break

                if duplicate:
                    print(f"Името '{new_name}' вече се използва.")
                    continue

                break

            except ValueError as e:
                print(f"Грешка: {e}")


        while True:
            new_zone = input(f"Нова зона [{location.zone}]: ").strip()
            if not new_zone:
                new_zone = location.zone
                break
            if len(new_zone) < 2:
                print("Зоната трябва да е поне 2 символа.")
                continue

            try:
                self.controller.validate_field("zone", new_zone)
                break
            except ValueError as e:
                print(f"Грешка: {e}")


        while True:
            new_cap_raw = input(f"Нов капацитет [{location.capacity}]: ").strip()
            if not new_cap_raw:
                new_cap = location.capacity
                break

            try:
                self.controller.validate_field("capacity", new_cap_raw)
                new_cap = int(new_cap_raw)
                break
            except ValueError as e:
                print(f"Грешка: {e}")

        try:
            self.controller.update(location.location_id, name=new_name, zone=new_zone, capacity=new_cap)
            print("Данните са обновени успешно.")
        except Exception as e:
            print(f"Проблем при обновяване: {e}")


    def delete_location(self, _):
        print("\nИзтриване на локация")
        while True:
            loc_id = input("ID на локация за изтриване: ").strip()
            if not loc_id:
                return
            location = self.controller.get_by_id(loc_id)
            if location:
                break
            print("Не е намерена локация с това ID.")

        try:
            self.controller.remove(location.location_id)
            print("Локацията е изтрита успешно.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
