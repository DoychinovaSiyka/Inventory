class MenuItem:
    def __init__(self, key, text, action):
        self.key = key
        self.text = text
        self.action = action


class Menu:
    def __init__(self, title, items):
        self.title = title
        self.items = items

    def show(self):
        print(f"\n   {self.title}   ")
        for item in self.items:
            print(f"{item.key}. {item.text}")
        return input("Избор: ")

    def execute(self, choice, user):
        for item in self.items:
            if item.key == choice:
                return item.action(user)
        print("Невалиден избор.")
        return None

# Меню системата е реализирана чрез класовете Menu и MenuItem. MenuItem съдържа ключ, текст и действие,
# а Menu показва опциите и извиква съответната функция според
# избора на потребителя. Това е универсален механизъм за навигация в приложението и позволява лесно добавяне на нови менюта и опции.