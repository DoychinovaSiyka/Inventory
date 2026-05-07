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
    if not rows:
        return "\n[!] Няма налични данни.\n"

    # Изчисляваме максималната ширина за всяка колона
    col_widths = [len(str(c)) for c in columns]

    # Обхождаме редовете, за да намерим най-дългия елемент във всяка колона
    for row in rows:
        for i, val in enumerate(row):
            val_str = str(val)
            if len(val_str) > col_widths[i]:
                col_widths[i] = len(val_str)

    # Добавяме фиксиран padding от общо 2 интервала (един отляво, един отдясно)
    col_widths = [w + 2 for w in col_widths]
    separator = "+" + "+".join(["-" * w for w in col_widths]) + "+"


    # Центрираме или подравняваме вляво заглавията
    header_parts = []
    for i, col_name in enumerate(columns):
        cell = f" {col_name}".ljust(col_widths[i])
        header_parts.append(cell)
    header_row = "|" + "|".join(header_parts) + "|"

    table_lines = [separator, header_row, separator]

    for row in rows:
        row_parts = []
        for i, cell_val in enumerate(row):
            # Подравняваме съдържанието на всяка клетка спрямо col_widths[i]
            cell_str = f" {cell_val}".ljust(col_widths[i])
            row_parts.append(cell_str)
        table_lines.append("|" + "|".join(row_parts) + "|")


    table_lines.append(separator)
    return "\n" + "\n".join(table_lines) + "\n"



#  Декоратор за защита с парола
def require_password(correct_password):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
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
