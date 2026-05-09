from views.menu import Menu, MenuItem
from views.password_utils import format_table


class LocationView:
    def __init__(self, location_controller):
        self.location_controller = location_controller

    def show_menu(self, user):
        while True:
            # Използваме стандартна проверка за ролята
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
                MenuItem("2", "Добавяне на нова локация", self.add_location),
                MenuItem("3", "Редактиране на локация", self.edit_location),
                MenuItem("4", "Изтриване на локация", self.delete_location)
            ])

        items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Управление на локации", items)

    def show_all(self, _):
        locations = self.location_controller.get_all()
        if not locations:
            print("\nНяма налични локации.")
            return

        columns = ["Код (ID)", "Име", "Зона", "Капацитет"]
        rows = []
        for loc in locations:
            rows.append([loc.location_id[:8], loc.name, loc.zone, loc.capacity])

        print("\nСПИСЪК НА ЛОКАЦИИТЕ")
        print(format_table(columns, rows))
        input("\nНатиснете Enter за продължение...")

    def add_location(self, _):
        print("\n--- ДОБАВЯНЕ НА ЛОКАЦИЯ ---")
        print("(Напишете 'отказ' за изход)")

        # Валидация за Име
        while True:
            name = input("Име на локация: ").strip()
            if name.lower() == 'отказ': return
            if not name:
                print("Грешка: Името не може да бъде празно!")
                continue
            break

        zone = input("Зона/Сектор (Enter за General): ").strip() or "General"

        # Валидация за Капацитет
        while True:
            capacity_raw = input("Капацитет (число): ").strip()
            if capacity_raw.lower() == 'отказ': return
            if not capacity_raw:
                print("Грешка: Моля, въведете капацитет!")
                continue

            try:
                # Проверка дали е валидно число
                cap = float(capacity_raw)
                if cap < 0:
                    print("Грешка: Капацитетът не може да е отрицателен!")
                    continue
                break
            except ValueError:
                print("Грешка: Въведете валидно число за капацитет!")

        try:
            new_loc = self.location_controller.add(name=name, zone=zone, capacity=capacity_raw)
            print(f"\n[OK] Локацията е добавена успешно с код: {new_loc.location_id[:8]}")
        except Exception as e:
            print(f"Грешка при запис: {e}")

    def edit_location(self, _):
        print("\n--- РЕДАКТИРАНЕ НА ЛОКАЦИЯ ---")

        # Избор на локация с повторение при грешка
        location = None
        while True:
            loc_id = input("Въведете ID (или част от него, 'отказ' за изход): ").strip()
            if loc_id.lower() == 'отказ' or not loc_id: return

            location = self.location_controller.get_by_id(loc_id)
            if location:
                break
            print("Локацията не е намерена. Опитайте отново.")

        print(f"\nРедактирате {location.name} (Enter запазва старата стойност)")

        new_name = input(f"Ново име [{location.name}]: ").strip() or location.name
        new_zone = input(f"Нова зона [{location.zone}]: ").strip() or location.zone

        # Валидация на новия капацитет
        while True:
            new_cap_raw = input(f"Нов капацитет [{location.capacity}]: ").strip()
            if not new_cap_raw:
                new_cap = location.capacity
                break
            if new_cap_raw.lower() == 'отказ': return

            try:
                if float(new_cap_raw) < 0:
                    print("Грешка: Не може да бъде отрицателно число!")
                    continue
                new_cap = new_cap_raw
                break
            except ValueError:
                print("Грешка: Моля, въведете валидно число!")

        try:
            self.location_controller.update(
                location.location_id,
                name=new_name,
                zone=new_zone,
                capacity=new_cap
            )
            print("[OK] Данните са обновени.")
        except Exception as e:
            print(f"Грешка при обновяване: {e}")

    def delete_location(self, _):
        print("\n--- ИЗТРИВАНЕ ---")

        location = None
        while True:
            loc_id = input("Въведете ID на локация ('отказ' за изход): ").strip()
            if loc_id.lower() == 'отказ' or not loc_id: return

            location = self.location_controller.get_by_id(loc_id)
            if location:
                break
            print("Локацията не е намерена.")

        confirm = input(f"Сигурни ли сте, че триете {location.name}? (y/n): ").lower()
        if confirm == 'y':
            try:
                self.location_controller.remove(location.location_id)
                print("[OK] Локацията е премахната.")
            except Exception as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")