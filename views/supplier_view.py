from views.menu import Menu, MenuItem
from views.password_utils import format_table


class SupplierView:
    def __init__(self, controller):
        # Контролерът се подава отвън, няма нужда от import SupplierController
        self.controller = controller

    def show_menu(self, user):
        while True:
            # Стандартна проверка за роля без магически функции
            is_admin = False
            if user and hasattr(user, 'role'):
                if user.role == "Admin":
                    is_admin = True

            menu = self._build_menu(is_admin)
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, is_admin):
        menu_items = [MenuItem("1", "Списък с доставчици", self.show_suppliers)]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на доставчик", self.add_supplier),
                MenuItem("3", "Редактиране на доставчик", self.edit_supplier),
                MenuItem("4", "Изтриване на доставчик", self.delete_supplier)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Доставчици", menu_items)

    def show_suppliers(self, _):
        suppliers = self.controller.get_all()
        if not suppliers:
            print("\nНяма налични доставчици.")
            return

        columns = ["ID (кратко)", "Име", "Контакт", "Адрес"]
        rows = []
        for s in suppliers:
            rows.append([s.supplier_id[:8], s.name, s.contact, s.address])

        print("\nСПИСЪК НА ДОСТАВЧИЦИ")
        print(format_table(columns, rows))
        input("\nНатиснете Enter за продължение...")

    def add_supplier(self, _):
        print("\n--- ДОБАВЯНЕ НА ДОСТАВЧИК ---")
        print("(Напишете 'отказ' за изход)")

        # Име
        while True:
            name = input("Име на доставчик: ").strip()
            if name.lower() == "отказ": return
            if not name:
                print("Грешка: Името не може да е празно!")
                continue
            break

        # Контакт
        while True:
            contact = input("Контакт (тел/имейл): ").strip()
            if contact.lower() == "отказ": return
            if not contact:
                print("Грешка: Контактната информация е задължителна!")
                continue
            break

        # Адрес
        while True:
            address = input("Адрес: ").strip()
            if address.lower() == "отказ": return
            if not address:
                print("Грешка: Адресът не може да е празен!")
                continue
            break

        try:
            new_sup = self.controller.add(name=name, contact=contact, address=address)
            print(f"\n[OK] Доставчикът е добавен успешно. ID: {new_sup.supplier_id[:8]}")
        except Exception as e:
            print(f"Грешка при запис: {e}")

    def edit_supplier(self, _):
        print("\n--- РЕДАКТИРАНЕ НА ДОСТАВЧИК ---")

        # Избор на доставчик с проверка
        while True:
            supplier_id_input = input("Въведете ID на доставчик (или 'отказ'): ").strip()
            if not supplier_id_input or supplier_id_input.lower() == 'отказ': return

            supplier = self.controller.get_by_id(supplier_id_input)
            if supplier:
                break
            print("Грешка: Доставчикът не е намерен.")

        print(f"\nРедактирате: {supplier.name}")
        print("(Enter запазва старата стойност, 'отказ' за изход)")

        # Ново име
        while True:
            new_name = input(f"Ново име [{supplier.name}]: ").strip()
            if new_name.lower() == 'отказ': return
            if not new_name:
                new_name = supplier.name
            break

        # Нов контакт
        while True:
            new_contact = input(f"Нов контакт [{supplier.contact}]: ").strip()
            if new_contact.lower() == 'отказ': return
            if not new_contact:
                new_contact = supplier.contact
            break

        # Нов адрес
        while True:
            new_address = input(f"Нов адрес [{supplier.address}]: ").strip()
            if new_address.lower() == 'отказ': return
            if not new_address:
                new_address = supplier.address
            break

        try:
            self.controller.update(supplier_id=supplier.supplier_id, name=new_name,
                                   contact=new_contact, address=new_address)
            print("[OK] Данните са обновени успешно.")
        except Exception as e:
            print(f"Грешка при обновяване: {e}")

    def delete_supplier(self, _):
        print("\n--- ИЗТРИВАНЕ НА ДОСТАВЧИК ---")

        while True:
            supplier_id_input = input("Въведете ID за изтриване (или 'отказ'): ").strip()
            if not supplier_id_input or supplier_id_input.lower() == 'отказ': return

            supplier = self.controller.get_by_id(supplier_id_input)
            if supplier:
                break
            print("Грешка: Доставчикът не е намерен.")

        confirm = input(f"Сигурни ли сте, че триете '{supplier.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.controller.remove(supplier.supplier_id)
                print("[OK] Доставчикът е премахнат.")
            except Exception as e:
                print(f"Грешка при изтриване: {e}")
        else:
            print("Операцията е прекратена.")