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


        if code in (10, 13):     # 10 = '\n', 13 = '\r' — извлечени от Windows при натискане на Enter
            print()
            break


        if code == 8:            # 8 = '\x08' — извлечено от Windows при натискане на Backspace
            if password:
                password = password[:-1]
                print("\b \b", end="", flush=True)
            continue

        # Игнориране на специални клавиши
        if code in (0, 224):     # 0 и 224 — първи байт на специални клавиши (стрелки, F-клавиши)
            msvcrt.getch()       # втори байт
            continue


        try:
            char = ch.decode("utf-8")
        except UnicodeDecodeError:
            continue

        password += char
        print("*", end="", flush=True)

    return password



def format_table(columns, rows):
    if not rows:
        return "\nНяма налични данни.\n"


    col_widths = [len(str(c)) for c in columns]

    for row in rows:
        for i, val in enumerate(row):
            val_str = str(val)
            if len(val_str) > col_widths[i]:
                col_widths[i] = len(val_str)


    col_widths = [w + 2 for w in col_widths]

    separator = "+" + "+".join("-" * w for w in col_widths) + "+"


    header_cells = []
    for i, col in enumerate(columns):
        header_cells.append(col.center(col_widths[i]))
    header_row = "|" + "|".join(header_cells) + "|"


    data_lines = []
    for row in rows:
        row_cells = []
        for i, val in enumerate(row):
            val_str = str(val)

            if val_str.replace(".", "", 1).isdigit():
                cell = val_str.rjust(col_widths[i])
            else:
                cell = val_str.ljust(col_widths[i])

            row_cells.append(cell)

        data_lines.append("|" + "|".join(row_cells) + "|")


    return "\n" + "\n".join([separator, header_row, separator] + data_lines + [separator]) + "\n"




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




