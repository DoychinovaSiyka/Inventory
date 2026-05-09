from views.menu import Menu, MenuItem
from views.password_utils import format_table


class LocationView:
    def __init__(self, location_controller):
        self.location_controller = location_controller

    def show_menu(self, user):
        while True:
            is_admin = False
            if user and hasattr(user, 'role'):
                if user.role == "Admin":
                    is_admin = True

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
        locations = self.location_controller.get_all()
        if not locations:
            print("\nНяма локации.")
            return

        columns = ["Код (ID)", "Име", "Зона", "Капацитет"]
        rows = []
        for loc in locations:
            rows.append([loc.location_id[:8], loc.name, loc.zone, loc.capacity])

        print("\nСписък с локации")
        print(format_table(columns, rows))
        input("\nEnter за продължение...")

    def add_location(self, _):
        print("\nНова локация")
        print("(Напишете 'отказ' за изход)")

        while True:
            name = input("Име: ").strip()
            if name.lower() == 'отказ':
                return
            if not name:
                print("Името е празно.")
                continue
            break

        zone = input("Зона (Enter за General): ").strip() or "General"

        while True:
            capacity_raw = input("Капацитет: ").strip()
            if capacity_raw.lower() == 'отказ':
                return
            if not capacity_raw:
                print("Въведете капацитет.")
                continue

            try:
                cap = float(capacity_raw)
                if cap < 0:
                    print("Капацитетът не може да е отрицателен.")
                    continue
                break
            except ValueError:
                print("Невалидно число.")
                continue

        try:
            new_loc = self.location_controller.add(name=name, zone=zone, capacity=capacity_raw)
            print(f"\nЛокацията е добавена. Код: {new_loc.location_id[:8]}")
        except Exception as e:
            print(f"Проблем при запис: {e}")

    def edit_location(self, _):
        print("\nРедактиране на локация")

        location = None
        while True:
            loc_id = input("ID или част от него ('отказ' за изход): ").strip()
            if loc_id.lower() == 'отказ' or not loc_id:
                return

            location = self.location_controller.get_by_id(loc_id)
            if location:
                break
            print("Не е намерена такава локация.")

        print(f"\nРедакция на {location.name} (Enter запазва старата стойност)")
        new_name = input(f"Ново име [{location.name}]: ").strip() or location.name
        new_zone = input(f"Нова зона [{location.zone}]: ").strip() or location.zone

        while True:
            new_cap_raw = input(f"Нов капацитет [{location.capacity}]: ").strip()
            if not new_cap_raw:
                new_cap = location.capacity
                break
            if new_cap_raw.lower() == 'отказ':
                return

            try:
                if float(new_cap_raw) < 0:
                    print("Капацитетът не може да е отрицателен.")
                    continue
                new_cap = new_cap_raw
                break
            except ValueError:
                print("Невалидно число.")
                continue

        try:
            self.location_controller.update(location.location_id, name=new_name, zone=new_zone, capacity=new_cap)
            print("Данните са обновени.")
        except Exception as e:
            print(f"Проблем при обновяване: {e}")

    def delete_location(self, _):
        print("\nИзтриване на локация")

        location = None
        while True:
            loc_id = input("ID на локация ('отказ' за изход): ").strip()
            if loc_id.lower() == 'отказ' or not loc_id:
                return

            location = self.location_controller.get_by_id(loc_id)
            if location:
                break
            print("Не е намерена такава локация.")

        confirm = input(f"Искате ли да изтрием '{location.name}'? (y/n): ").lower()
        if confirm == 'y':
            try:
                self.location_controller.remove(location.location_id)
                print("Локацията е изтрита.")
            except Exception as e:
                print(f"Проблем при изтриване: {e}")
        else:
            print("Операцията е прекратена.")
