from views.menu import Menu, MenuItem
from views.password_utils import format_table


class SupplierView:
    def __init__(self, controller):
        self.controller = controller


    def show_menu(self, user):
        while True:
            is_admin = (user and user.role == "Admin")
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
                MenuItem("4", "Изтриване на доставчик", self.delete_supplier)])
        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Доставчици", menu_items)


    def show_suppliers(self, _):
        suppliers = self.controller.get_all()
        if not suppliers:
            print("\nНяма налични доставчици.")
            return
        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = [[s.supplier_id[:8], s.name, s.contact, s.address] for s in suppliers]
        print("\nСПИСЪК С ДОСТАВЧИЦИ")
        print(format_table(columns, rows))



    def add_supplier(self, _):
        print("\nНов доставчик (Enter за отказ)")
        while True:
            name = input("Име: ").strip()
            if not name:
                return

            error = self.controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue

            all_sups = self.controller.get_all()
            duplicate = False
            for s in all_sups:
                if s.name.lower() == name.lower():
                    duplicate = True
                    break
            if duplicate:
                print(f"Доставчик с име '{name}' вече съществува.")
                continue

            break

        while True:
            contact = input("Контакт: ").strip()
            if not contact:
                return
            error = self.controller.validate_field("contact", contact)
            if not error:
                break
            print(f"Грешка: {error}")

        while True:
            address = input("Адрес: ").strip()
            if not address: return
            error = self.controller.validate_field("address", address)
            if not error:
                break
            print(f"Грешка: {error}")

        try:
            new_sup = self.controller.add(name=name, contact=contact, address=address)
            print(f"\nДоставчикът е добавен. ID: {new_sup.supplier_id[:8]}")
        except Exception as e:
            print(f"Грешка при запис: {e}")



    def edit_supplier(self, _):
        print("\nРедактиране на доставчик")
        while True:
            sid = input("Въведете ID за търсене: ").strip()
            if not sid: return
            supplier = self.controller.get_by_id(sid)
            if supplier:
                break
            print("Не е намерен доставчик с такова ID.")

        print(f"\nРедакция на: {supplier.name} (Enter запазва старата стойност)")
        while True:
            new_name = input(f"Ново име [{supplier.name}]: ").strip()
            if new_name == "":
                new_name = supplier.name

            error = self.controller.validate_field("name", new_name)
            if error:
                print(f"Грешка: {error}")
                continue

            all_sups = self.controller.get_all()
            name_taken = False
            for s in all_sups:
                if s.supplier_id == supplier.supplier_id:
                    continue

                if s.name.lower() == new_name.lower():
                    name_taken = True
                    break

            if name_taken:
                print(f"Името '{new_name}' вече се ползва от друг доставчик.")
                continue

            break


        while True:
            new_contact = input(f"Нов контакт [{supplier.contact}]: ").strip() or supplier.contact
            error = self.controller.validate_field("contact", new_contact)
            if not error:
                break
            print(f"Грешка: {error}")

        while True:
            new_address = input(f"Нов адрес [{supplier.address}]: ").strip() or supplier.address
            error = self.controller.validate_field("address", new_address)
            if not error:
                break
            print(f"Грешка: {error}")

        try:
            self.controller.update(supplier_id=supplier.supplier_id, name=new_name,
                                   contact=new_contact, address=new_address)
            print("Данните са обновени успешно.")
        except Exception as e:
            print(f"Проблем при обновяване: {e}")



    def delete_supplier(self, _):
        print("\nИзтриване на доставчик")
        while True:
            sid = input("ID на доставчик за изтриване: ").strip()
            if not sid:
                return
            supplier = self.controller.get_by_id(sid)
            if supplier:
                break
            print("Няма доставчик с такова ID.")

        try:
            self.controller.remove(supplier.supplier_id)
            print("Доставчикът е премахнат от системата.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
