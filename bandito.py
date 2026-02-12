import os
import importlib.util
from utils import print_banner, colored, cmatrix_loading
from base_module import BaseModule

MODULES = {}

def load_modules():
    global MODULES
    MODULES = {}
    base_path = "modules/dvwa/exploits"

    if not os.path.isdir(base_path):
        print("[-] modules/dvwa/exploits directory not found!")
        return

    for file in os.listdir(base_path):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = file[:-3]
            full_path = os.path.join(base_path, file)
            spec = importlib.util.spec_from_file_location(module_name, full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseModule) and obj is not BaseModule:
                    instance = obj()
                    MODULES[module_name] = instance
                    print(colored(f"[+] Loaded module: {module_name}", "green"))

def main():
    cmatrix_loading()
    print_banner()
    print(colored("[*] Bandito Framework v1.0 - Educational Exploitation Tool", "dark_red"))
    print(colored("[*] Type 'help' for commands\n", "yellow"))

    load_modules()
    current_module = None

    while True:
        try:
            prompt = colored(f"bandito ({current_module.name if current_module else 'no module'}) > ", "red")
            cmd = input(prompt).strip()

            if not cmd:
                continue

            low = cmd.lower()

            if low in ["exit", "quit"]:
                print(colored("[*] Goodbye!", "red"))
                break

            if low == "help":
                print(colored("\nCore Commands:", "yellow"))
                print("  use <module>     - Select a module (e.g. use rce)")
                print("  show modules     - List available modules")
                print("  back             - Return to main menu")
                print("  exit / quit      - Exit framework\n")
                continue

            if low == "show modules":
                print(colored("Available modules:", "yellow"))
                for m in sorted(MODULES.keys()):
                    print(colored(f"  - {m}", "orange"))
                continue

            if low.startswith("use "):
                module_name = cmd.split()[1]
                if module_name in MODULES:
                    current_module = MODULES[module_name]
                    print(colored(f"[+] Module loaded: {module_name}", "green"))
                    current_module.show_help()
                else:
                    print(colored(f"[-] Module '{module_name}' not found", "red"))
                continue

            if low == "back":
                current_module = None
                continue

            if current_module:
                current_module.handle_command(cmd)
            else:
                print(colored("[-] No module selected. Use 'use <module>' first", "red"))

        except KeyboardInterrupt:
            print("\n")
        except Exception as e:
            print(colored(f"[-] Error: {e}", "red"))

if __name__ == "__main__":
    main()