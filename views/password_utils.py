from functools import wraps
import getpass   # Hides the password input
import msvcrt    # За звездички при въвеждане на парола


def input_password(prompt="Въведете парола: "):
    """Въвеждане на парола със звездички (работи в CMD/PowerShell)"""
    print(prompt, end="", flush=True)
    password = ""

    while True:
        ch = msvcrt.getch()

        # Enter
        if ch in {b"\r", b"\n"}:
            print()
            break

        # Backspace
        if ch == b"\x08":
            if password:
                password = password[:-1]
                print("\b \b", end="", flush=True)
            continue

        # Специални клавиши (стрелки, F1 и др.)
        if ch in {b"\x00", b"\xe0"}:
            msvcrt.getch()
            continue

        # Нормален символ
        password += ch.decode("utf-8")
        print("*", end="", flush=True)

    return password


def format_table(columns, rows):
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

            # Опит за скрито въвеждане (идеята на господина, но адаптирана)
            try:
                # вместо getpass → звездички
                password = input_password("Въведете парола: ")
            except Exception:
                # Ако средата не поддържа → видима парола
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
        rows.append([
            p.product_id,
            p.name,
            p.price,
            p.quantity,
            categories
        ])

    print("\n" + format_table(columns, rows))
