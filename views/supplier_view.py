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
        items = [MenuItem("1", "Списък с доставчици", self.show_suppliers),
                 MenuItem("2", "Търсене на доставчик", self.search_supplier)]

        if is_admin:
            items.extend([MenuItem("3", "Добавяне на доставчик", self.add_supplier),
                          MenuItem("4", "Редактиране на доставчик", self.edit_supplier),
                          MenuItem("5", "Изтриване на доставчик", self.delete_supplier)])

        items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Доставчици", items)



    def show_suppliers(self, _):
        suppliers = self.controller.get_all()
        if not suppliers:
            print("\nНяма налични доставчици.")
            return

        print("\nСПИСЪК С ДОСТАВЧИЦИ")
        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = [[s.supplier_id[:8], s.name, s.contact, s.address] for s in suppliers]
        print(format_table(columns, rows))




    def search_supplier(self, _):
        print("\nТърсене на доставчик")
        sid = input("Въведете кратко ID (8 символа): ").strip()
        if not sid:
            print("Празно търсене.")
            return

        results = self.controller.search(sid)
        if not results:
            print("Няма доставчик с такова ID.")
            return

        print("\nНамерени доставчици:")
        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = [[s.supplier_id[:8], s.name, s.contact, s.address] for s in results]
        print(format_table(columns, rows))



    def add_supplier(self, _):
        print("\nНов доставчик")

        while True:
            name = input("Име: ").strip()
            if not name:
                print("Името е задължително.")
                continue

            error = self.controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue


            if any(s.name.lower() == name.lower() for s in self.controller.get_all()):
                print(f"Доставчик с име '{name}' вече съществува.")
                continue

            break


        while True:
            contact = input("Контакт: ").strip()
            if not contact:
                print("Контактът е задължителен.")
                continue

            error = self.controller.validate_field("contact", contact)
            if not error:
                break

            print(f"Грешка: {error}")


        while True:
            address = input("Адрес: ").strip()
            if not address:
                print("Адресът е задължителен.")
                continue

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
            sid = input("Въведете кратко ID: ").strip()
            if not sid:
                return

            supplier = self.controller.get_by_id(sid)
            if supplier:
                break

            print("Не е намерен доставчик с такова ID.")

        print(f"\nРедакция на: {supplier.name} (Enter запазва старата стойност)")

        while True:
            new_name = input(f"Ново име [{supplier.name}]: ").strip()

            # Ако е празно → запазваме старото
            if not new_name:
                new_name = supplier.name
                break


            error = self.controller.validate_field("name", new_name)
            if error:
                print(f"Грешка: {error}")
                continue


            exists = False
            for s in self.controller.get_all():
                same_name = s.name.lower() == new_name.lower()
                different_id = s.supplier_id != supplier.supplier_id

                if same_name and different_id:
                    exists = True
                    break

            if exists:
                print(f"Името '{new_name}' вече се използва.")
                continue

            break




        while True:
            new_contact = input(f"Нов контакт [{supplier.contact}]: ").strip()
            if not new_contact:
                new_contact = supplier.contact
                break

            error = self.controller.validate_field("contact", new_contact)
            if not error:
                break

            print(f"Грешка: {error}")


        while True:
            new_address = input(f"Нов адрес [{supplier.address}]: ").strip()
            if not new_address:
                new_address = supplier.address
                break

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
            sid = input("Кратко ID на доставчик: ").strip()
            if not sid:
                return

            supplier = self.controller.get_by_id(sid)
            if supplier:
                break

            print("Няма доставчик с такова ID.")

        try:
            self.controller.remove(supplier.supplier_id[:8])
            print("Доставчикът е премахнат от системата.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
