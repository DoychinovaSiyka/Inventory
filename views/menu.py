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

        while True:
            choice = input("Избор (Enter = отказ): ").strip()

            # Enter = отказ
            if choice == "":
                return "0"   # връща към предишното меню

            # не е число
            if not choice.isdigit():
                print("Моля, въведете валидна числова опция от менюто.\n")
                continue

            # число, но не съществува
            if choice not in [item.key for item in self.items]:
                print("Няма такава опция в менюто. Опитайте отново.\n")
                continue

            return choice

    def execute(self, choice, user):
        for item in self.items:
            if item.key == choice:
                return item.action(user)

        print("Невалиден избор.")
        return None


# Menu и MenuItem реализират проста система за навигация.
# MenuItem съдържа ключ, текст и действие, а Menu показва опциите и изпълнява избраната функция.
# Действията се подават отвън, което прави менюто гъвкаво и лесно за разширяване.
