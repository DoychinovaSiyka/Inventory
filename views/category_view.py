from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller

    def show_menu(self, user: User):
        is_admin = (user is not None and user.role == "Admin")

        # Добавяме пояснение, че списъкът вече поддържа йерархия
        menu_items = [MenuItem("1", "Списък с категории (Йерархия)", self.show_all)]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на категория", self.add_category),
                MenuItem("3", "Редактиране на категория", self.edit_category),
                MenuItem("4", "Изтриване на категория", self.delete_category)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))

        menu = Menu("Меню Категории", menu_items)

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Списък - Разширен с колона за Родител (Йерархия)
    def show_all(self, _):
        categories = self.controller.get_all()

        if not categories:
            print("Няма категории.")
            return

        # Добавяме "Родител" към колоните
        columns = ["ID", "Име", "Описание", "Родител"]

        rows = []
        for c in categories:
            # Логика за намиране името на родителя
            parent_name = "---"
            if hasattr(c, 'parent_id') and c.parent_id:
                parent = self.controller.get_by_id(c.parent_id)
                parent_name = parent.name if parent else c.parent_id

            rows.append([c.category_id, c.name, c.description, parent_name])

        print("\n" + format_table(columns, rows))

    # Добавяне - Разширено с опция за подкатегория
    def add_category(self, _):
        name = input("Име на категория: ").strip()
        description = input("Описание: ").strip()

        # Добавка за подкатегория
        print("Оставете празно за главна категория или въведете ID на родител.")
        parent_id = input("ID на родител (опционално): ").strip() or None

        try:
            # Проверка дали родителят съществува
            if parent_id and not self.controller.get_by_id(parent_id):
                print(f"Грешка: Родител с ID {parent_id} не съществува.")
                return

            self.controller.add(name=name, description=description, parent_id=parent_id)
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # Редактиране - Разширено с възможност за промяна на родител
    def edit_category(self, _):
        category_id = input("Въведете ID на категория: ").strip()

        category = self.controller.get_by_id(category_id)

        if not category:
            print("Категорията не е намерена.")
            return

        print("\nОставете празно, ако не искате да променяте полето.")
        new_name = input(f"Ново име ({category.name}): ").strip()
        new_desc = input(f"Ново описание ({category.description}): ").strip()

        # Възможност за промяна на Parent ID
        current_p = category.parent_id if hasattr(category, 'parent_id') and category.parent_id else "няма"
        new_parent = input(f"Ново ID на родител (сега: {current_p}): ").strip()

        try:
            if new_name:
                self.controller.update_name(category_id, new_name)
            if new_desc:
                self.controller.update_description(category_id, new_desc)
            if new_parent:
                # "none" премахва родителя и прави категорията главна
                p_id = None if new_parent.lower() == "none" else new_parent

                # Проверка за съществуване на новия родител
                if p_id and not self.controller.get_by_id(p_id):
                    print(f"Грешка: Родител с ID {p_id} не съществува.")
                    return

                if hasattr(self.controller, 'update_parent'):
                    self.controller.update_parent(category_id, p_id)
                else:
                    category.parent_id = p_id
                    # Ако контролерът няма специален метод, променяме обекта директно

            print("Категорията е обновена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # Изтриване - Разширено с проверка за подкатегории
    def delete_category(self, _):
        category_id = input("Въведете ID на категория: ").strip()

        # Проверяваме дали категорията има "деца", за да не ги оставим без родител
        all_cats = self.controller.get_all()
        has_children = any(hasattr(c, 'parent_id') and str(c.parent_id) == str(category_id) for c in all_cats)

        if has_children:
            print("Грешка: Тази категория има подкатегории! Изтрийте или преместете тях първо.")
            return

        if self.controller.remove(category_id):
            print("Категорията е изтрита успешно!")
        else:
            print("Категорията не е намерена.")

