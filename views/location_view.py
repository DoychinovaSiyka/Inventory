from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.location_controller import LocationController
from models.user import User


class LocationView:
    def __init__(self, location_controller: LocationController):
        self.location_controller = location_controller

    def show_menu(self, user: User):
        is_admin = user.role == "Admin"

        menu_items = [MenuItem("1", "Списък с локации", self.show_all)]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на нова локация", self.add_location),
                MenuItem("3", "Редактиране на съществуваща локация", self.edit_location),
                MenuItem("4", "Изтриване на локация", self.delete_location)
            ])

        menu_items.append(MenuItem("0", "Назад към главното меню", lambda u: "break"))
        menu = Menu("Управление на складовата мрежа", menu_items)

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Списък с локации
    def show_all(self, _):
        locations = self.location_controller.get_all()

        if not locations:
            print("\n[!] Няма налични локации в системата.")
            return

        # Променени заглавия за по-добра яснота спрямо логистиката
        columns = ["Код (ID)", "Име на обект", "Зона", "Капацитет"]
        rows = [[loc.location_id, loc.name, loc.zone, loc.capacity] for loc in locations]

        print("\n--- СПИСЪК НА СКЛАДОВЕТЕ И МАГАЗИНИТЕ ---")
        print(format_table(columns, rows))

    # Добавяне
    def add_location(self, _):
        print("\n--- ДОБАВЯНЕ НА НОВА ЛОКАЦИЯ ---")
        name = input("Име на локация (град/склад): ").strip()
        zone = input("Зона/Сектор: ").strip()

        try:
            capacity = int(input("Капацитет (число): "))
        except ValueError:
            print("[Грешка] Капацитетът трябва да бъде цяло число.")
            return

        try:
            # Системата автоматично ще генерира W1, W2 и т.н. чрез контролера
            new_loc = self.location_controller.add(name=name, zone=zone, capacity=capacity)
            print(f"[Успех] Локацията е добавена с автоматичен код: {new_loc.location_id}")
        except ValueError as e:
            print(f"[Грешка] {e}")

    # Редактиране
    def edit_location(self, _):
        print("\n--- РЕДАКТИРАНЕ НА ЛОКАЦИЯ ---")
        loc_id = input("Въведете Код/ID на локацията (напр. W1): ").strip()
        location = self.location_controller.get_by_id(loc_id)

        if not location:
            print(f"[!] Локация с код '{loc_id}' не беше намерена.")
            return

        print("\n* Оставете празно, ако не желаете промяна на текущата стойност.")
        new_name = input(f"Ново име ({location.name}): ").strip()
        new_zone = input(f"Нова зона ({location.zone}): ").strip()

        try:
            new_capacity_input = input(f"Нов капацитет ({location.capacity}): ").strip()
            new_capacity = int(new_capacity_input) if new_capacity_input else location.capacity
        except ValueError:
            print("[Грешка] Капацитетът трябва да бъде число.")
            return

        try:
            self.location_controller.update(
                loc_id,
                name=new_name if new_name else location.name,
                zone=new_zone if new_zone else location.zone,
                capacity=new_capacity
            )
            print(f"[Успех] Данните за '{loc_id}' бяха обновени успешно!")
        except ValueError as e:
            print(f"[Грешка] {e}")

    # Изтриване
    def delete_location(self, _):
        print("\n--- ИЗТРИВАНЕ НА ЛОКАЦИЯ ---")
        loc_id = input("Въведете Код/ID за изтриване (напр. W1): ").strip()

        # Потвърждение преди изтриване
        confirm = input(f"Сигурни ли сте, че искате да изтриете {loc_id}? (y/n): ").lower()
        if confirm != 'y':
            print("Операцията е отказана.")
            return

        try:
            if self.location_controller.remove(loc_id):
                print(f"[Успех] Локация {loc_id} беше премахната от системата.")
            else:
                print(f"[!] Локация с код {loc_id} не съществува.")
        except ValueError as e:
            print(f"[Грешка] {e}")