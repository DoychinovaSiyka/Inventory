

from menus.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView


class AnonymousMenuView:
    def show_menu(self):
        menu = Menu("Меню за анонимен потребител", [
            MenuItem("1", "Информация за системата", self.show_system_info),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, None)
            if result == "break":
                break

    def show_system_info(self, user):
        SystemInfoView().show_menu()
