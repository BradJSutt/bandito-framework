import time
import random

def colored(text, color):
    colors = {
        "dark_red": "\033[31m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "orange": "\033[38;5;208m",
        "reset": "\033[0m"
    }
    return colors.get(color, "") + text + colors["reset"]

def print_banner():
    banner = r"""
    _____   _____ __      __  _____ 
   |  __ \ / ____|\ \    / / |  __ \
   | |  | | (___   \ \  / /  | |__) |
   | |  | |\___ \   \ \/ /   |  ___/ 
   | |__| |____) |   \  /    | |     
   |_____/|_____/     \/     |_|      v1.0
    """
    print(colored(banner, "dark_red"))

def cmatrix_loading():
    print("\n" * 4)
    print(colored("Initializing Bandito Framework...", "orange"))
    print("")

    chars = "01█▓▒░"
    width = 90
    height = 18
    columns = [0] * width

    for _ in range(45):
        line = ""
        for i in range(width):
            if columns[i] == 0 and random.random() < 0.1:
                columns[i] = random.randint(5, height)
            if columns[i] > 0:
                line += random.choice(chars)
                columns[i] -= 1
            else:
                line += " "
        print(colored(line, "green"))
        time.sleep(0.04)
        print("\033[F" * height, end="")

    print("\033[0m" + "\n" * 2)
    print("Bandito Framework v1.0 loaded.")
    print("")