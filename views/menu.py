class MenuItem:
    def __init__(self, key, text, action):
        self.key = str(key)
        self.text = text
        self.action = action


class Menu:
    def __init__(self, title, items):
        self.title = title
        self.items = items

    def show(self):
        print(f"\n   {self.title.upper()}   ")
        for item in self.items:
            print(f"{item.key}. {item.text}")

        while True:
            choice = input("Избор (Enter за назад): ").strip()
            if choice == "":
                return "0"

            valid_keys = [item.key for item in self.items]
            if choice in valid_keys:
                return choice

            print(f"[!] '{choice}' не е валидна опция. Опитайте отново.\n")

    def execute(self, choice, user):
        for item in self.items:
            if item.key == choice:
                return item.action(user)

        return None


# Menu и MenuItem реализират проста система за навигация.
# MenuItem съдържа ключ, текст и действие, а Menu показва опциите и изпълнява избраната функция.
# Действията се подават отвън, което прави менюто гъвкаво и лесно за разширяване.
