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
            name = input("Име: ").strip()
            if not name:
                return

            error = self.controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue

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

        while True:
            zone = input("Зона/Сектор (напр. Сектор А): ").strip()
            error = self.controller.validate_field("zone", zone)
            if not error:
                break
            print(f"Грешка: {error}")


        while True:
            capacity_raw = input("Капацитет (цяло число): ").strip()
            if not capacity_raw: return
            error = self.controller.validate_field("capacity", capacity_raw)
            if not error:
                break
            print(f"Грешка: {error}")

        try:
            new_loc = self.controller.add(name=name, zone=zone, capacity=capacity_raw)
            print(f"\nЛокацията е добавена. Код: {new_loc.location_id[:8]}")
        except Exception as e:
            print(f"Грешка при запис: {e}")

    def edit_location(self, _):
        print("\nРедактиране на локация")
        while True:
            loc_id = input("Въведете ID за търсене: ").strip()
            if not loc_id: return
            location = self.controller.get_by_id(loc_id)
            if location:
                break
            print("Не е намерена локация с това ID.")

        print(f"\nРедакция на {location.name} (Enter запазва старата стойност)")
        while True:
            new_name = input(f"Ново име [{location.name}]: ").strip()
            if new_name == "":
                new_name = location.name

            error = self.controller.validate_field("name", new_name)
            if error:
                print(f"Грешка: {error}")
                continue

            # Проверка дали името вече се използва от друга локация
            all_locs = self.controller.get_all()
            name_taken = False
            for l in all_locs:
                if l.location_id == location.location_id:
                    continue

                if l.name.lower() == new_name.lower():
                    name_taken = True
                    break

            if name_taken:
                print(f"Името '{new_name}' вече е заето от друга локация.")
                continue

            break



        while True:
            new_zone = input(f"Нова зона [{location.zone}]: ").strip() or location.zone
            error = self.controller.validate_field("zone", new_zone)
            if not error:
                break
            print(f"Грешка: {error}")

        while True:
            new_cap_raw = input(f"Нов капацитет [{location.capacity}]: ").strip()
            if not new_cap_raw:
                new_cap = location.capacity
                break
            error = self.controller.validate_field("capacity", new_cap_raw)
            if not error:
                new_cap = new_cap_raw
                break
            print(f"Грешка: {error}")

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
            print("Локацията е изтрита.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
