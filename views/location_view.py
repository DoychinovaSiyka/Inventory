

from menus.menu import Menu, MenuItem
from storage.password_utils import format_table
from controllers.location_controller import LocationController
from models.user import User


class LocationView:
    def __init__(self, location_controller: LocationController):
        self.location_controller = location_controller

    def show_menu(self, user: User):
        is_admin = user.role == "Admin"

        menu_items = [
            MenuItem("1", "Списък с локации", self.show_all)
        ]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на локация", self.add_location),
                MenuItem("3", "Редактиране на локация", self.edit_location),
                MenuItem("4", "Изтриване на локация", self.delete_location)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))

        menu = Menu("Меню Локации", menu_items)

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # 1. Списък с локации
    def show_all(self, _):
        locations = self.location_controller.get_all()

        if not locations:
            print("Няма налични локации.")
            return

        columns = ["ID", "Име", "Зона", "Капацитет"]
        rows = [
            [loc.location_id, loc.name, loc.zone, loc.capacity]
            for loc in locations
        ]

        print("\n" + format_table(columns, rows))

    # 2. Добавяне
    def add_location(self, _):
        name = input("Име на локация: ").strip()
        zone = input("Зона/Сектор: ").strip()

        try:
            capacity = int(input("Капацитет: "))
        except ValueError:
            print("Капацитетът трябва да е число.")
            return

        try:
            self.location_controller.add(name=name, zone=zone, capacity=capacity)
            print("Локацията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # 3. Редактиране
    def edit_location(self,_):
        loc_id = input("Въведете ID на локация: ").strip()
        location = self.location_controller.get_by_id(loc_id)

        if not location:
            print("Локацията не е намерена.")
            return

        print("\nОставете празно, ако не искате да променяте полето.")
        new_name = input(f"Ново име ({location.name}): ").strip()
        new_zone = input(f"Нова зона ({location.zone}): ").strip()

        try:
            new_capacity_input = input(f"Нов капацитет ({location.capacity}): ").strip()
            new_capacity = int(new_capacity_input) if new_capacity_input else location.capacity
        except ValueError:
            print("Капацитетът трябва да е число.")
            return

        try:
            self.location_controller.update(
                loc_id,
                name=new_name if new_name else location.name,
                zone=new_zone if new_zone else location.zone,
                capacity=new_capacity
            )
            print("Локацията е обновена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # 4. Изтриване
    def delete_location(self, _):
        loc_id = input("Въведете ID на локация: ").strip()

        try:
            if self.location_controller.remove(loc_id):
                print("Локацията е изтрита успешно!")
            else:
                print("Локацията не е намерена.")
        except ValueError as e:
            print("Грешка:", e)
