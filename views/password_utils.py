from functools import wraps
import getpass   # Hides the password input
import msvcrt    # За звездички при въвеждане на парола


def input_password(prompt="Въведете парола: "):
    """Въвежда парола, като показва звездички вместо символи (Windows CMD)."""
    print(prompt, end="", flush=True)
    password = ""

    while True:
        ch = msvcrt.getch()  # getch() връща байт — не буква, а суров код от клавиатурата
        code = ord(ch)       # превръщаме байта в число, за да не пишем хардкоднати \x08, \x00, \xe0

        # Enter
        if code in (10, 13):     # 10 = '\n', 13 = '\r' — извлечени от Windows при натискане на Enter
            print()
            break

        # Backspace
        if code == 8:            # 8 = '\x08' — извлечено от Windows при натискане на Backspace
            if password:
                password = password[:-1]
                print("\b \b", end="", flush=True)
            continue
        # Игнориране на специални клавиши
        if code in (0, 224):     # 0 и 224 — първи байт на специални клавиши (стрелки, F-клавиши)
            msvcrt.getch()       # втори байт
            continue

        # Нормален символ
        try:
            char = ch.decode("utf-8")
        except UnicodeDecodeError:
            continue

        password += char
        print("*", end="", flush=True)

    return password


def format_table(columns, rows):
    """ Форматира таблица в текстов вид.
    Гарантира, че rows винаги е списък, дори ако е None. """
    if rows is None:
        rows = []

    # Ако няма редове – връщаме само заглавна таблица
    if not rows:
        col_widths = [len(col) + 2 for col in columns]
        top_border = "+" + "+".join("-" * w for w in col_widths) + "+"
        header = "|" + "|".join(columns[i].center(col_widths[i]) for i in range(len(columns))) + "|"
        bottom_border = top_border
        return "\n".join([top_border, header, bottom_border])

    all_rows = [columns] + rows
    col_widths = [max(len(str(row[i])) for row in all_rows) + 2 for i in range(len(columns))]

    top_border = "+" + "+".join("-" * w for w in col_widths) + "+"
    header = "|" + "|".join(columns[i].center(col_widths[i]) for i in range(len(columns))) + "|"
    separator = "+" + "+".join("-" * w for w in col_widths) + "+"

    data = []
    for row in rows:
        line = "|"
        for i, cell in enumerate(row):
            cell_str = f"{cell:.2f}" if isinstance(cell, float) else str(cell)
            if isinstance(cell, (int, float)):
                line += cell_str.rjust(col_widths[i]) + "|"
            else:
                line += cell_str.ljust(col_widths[i]) + "|"
        data.append(line)

    bottom_border = top_border
    return "\n".join([top_border, header, separator] + data + [bottom_border])


#  Декоратор за защита с парола
def require_password(correct_password):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # вместо getpass - звездички
                password = input_password("Въведете парола: ")
            except Exception:
                # Ако средата не поддържа - видима парола
                password = input("Въведете парола (видима): ")

            if password == correct_password:
                print("Достъп разрешен!\n")
                return func(*args, **kwargs)
            else:
                print("Достъп отказан! Невалидна парола.\n")
                return None

        return wrapper
    return decorator


@require_password("parola123")  # защита с парола
def show_products_menu(product_controller):
    products = product_controller.get_all()

    if not products:
        print("Няма продукти.")
        return
    
    columns = ["ID", "Име", "Цена", "Количество", "Категории"]
    rows = []
    for p in products:
        categories = ", ".join([c.name for c in p.categories])
        rows.append([p.product_id,
            p.name,p.price,p.quantity,categories])
    print("\n" + format_table(columns, rows))




# Кодовете на специалните клавиши не са ASCII или Unicode.
# Те идват от хардуерните scan codes на клавиатурата.
# Windows Console API ги превежда в два байта – първо \x00 или \xE0, което е сигнал, че клавишът е специален,
# и втори байт, който е конкретният код на клавиша. msvcrt.getch() просто връща тези байтове директно от Windows.
# Конкретните кодове не съм ги измисляла – взела съм ги от стандарта на Windows,
# описан в документацията за keyboard scan codes. Същите кодове могат да се видят и в
# официалната документация за Windows Console Input.
# Освен това мога да ги проверя и сама, като пусна малък тест с getch() и натискам стрелките, за да видя какво връща
