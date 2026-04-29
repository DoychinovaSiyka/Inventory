from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.location_controller import LocationController
from validators.location_validator import LocationValidator
from models.user import User


class LocationView:
    def __init__(self, location_controller: LocationController):
        self.location_controller = location_controller

    def show_menu(self, user: User):
        """ Основен цикъл на менюто. Динамично генерира опции според ролята. """
        while True:
            menu = self._build_menu(user)
            choice = menu.show()

            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, user: User):
        """ Дефинира правата за достъп (Admin вижда повече). """
        is_admin = user.role == "Admin"
        items = [MenuItem("1", "Списък с локации", self.show_all)]
        if is_admin:
            items.extend([MenuItem("2", "Добавяне на нова локация", self.add_location),
                          MenuItem("3", "Редактиране на съществуваща локация", self.edit_location),
                          MenuItem("4", "Изтриване на локация", self.delete_location)])
        items.append(MenuItem("0", "Назад към главното меню", lambda u: "break"))
        return Menu("Управление на складовата мрежа", items)

    def show_all(self, user: User):
        """ Извежда таблица с всички налични обекти. """
        locations = self.location_controller.get_all()
        if not locations:
            print("\n[!] Няма налични локации в системата.")
            return

        columns = ["Код (ID)", "Име на обект", "Зона", "Капацитет"]
        rows = [[loc.location_id, loc.name, loc.zone, loc.capacity] for loc in locations]

        print("\n--- СПИСЪК НА СКЛАДОВЕТЕ И МАГАЗИНИТЕ ---")
        print(format_table(columns, rows))

    def add_location(self, user: User):
        """ Създава нов обект с валидация на капацитета. """
        print("\n--- ДОБАВЯНЕ НА НОВА ЛОКАЦИЯ ---")
        name = input("Име на локация (Enter = отказ): ").strip()
        if not name:
            print("Операцията е отказана.")
            return
        zone = input("Зона/Сектор (Enter = пропуск): ").strip() or ""
        capacity_raw = input("Капацитет (число, Enter = отказ): ").strip()
        if not capacity_raw:
            print("Операцията е отказана.")
            return
        try:
            capacity = LocationValidator.validate_capacity(capacity_raw)
            new_loc = self.location_controller.add(name=name, zone=zone, capacity=capacity)
            print(f"[Успех] Локацията е добавена с автоматичен код: {new_loc.location_id}")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def edit_location(self, user: User):
        """ Променя съществуваща локация. Позволява частично обновяване. """
        print("\n--- РЕДАКТИРАНЕ НА ЛОКАЦИЯ ---")
        loc_id = input("Въведете Код/ID на локацията (Enter = отказ): ").strip()
        if not loc_id:
            return
        location = self.location_controller.get_by_id(loc_id)
        if location is None:
            print("[Грешка] Локация с такъв ID не съществува.")
            return
        print(f"\nРедактиране на {loc_id}. Оставете празно за запазване на старата стойност.")
        new_name = input(f"Ново име ({location.name}): ").strip() or None
        new_zone = input(f"Нова зона ({location.zone}): ").strip() or None
        new_cap_raw = input(f"Нов капацитет ({location.capacity}): ").strip() or None
        try:
            # Обновявам само ако има подадени нови данни
            self.location_controller.update(loc_id, name=new_name, zone=new_zone, capacity=new_cap_raw)
            print(f"[Успех] Данните за '{loc_id}' бяха обновени успешно!")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def delete_location(self, user: User):
        print("\n--- ИЗТРИВАНЕ НА ЛОКАЦИЯ ---")
        loc_id = input("Въведете Код/ID за изтриване (Enter = отказ): ").strip()
        if not loc_id:
            return
        confirm = input(f"Сигурни ли сте, че искате да изтриете {loc_id}? (y/n): ").lower()
        if confirm != 'y':
            print("Операцията е отказана.")
            return
        try:
            self.location_controller.remove(loc_id)
            print(f"[Успех] Локация {loc_id} беше премахната от системата.")
        except ValueError as e:
            print(f"[Грешка] {e}")
