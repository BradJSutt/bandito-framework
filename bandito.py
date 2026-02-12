import os
from utils import print_banner, colored, cmatrix_loading

MODULES = {}

def load_modules():
    global MODULES
    MODULES = {}
    base_path = "modules/exploits"

    print("[DEBUG] Scanning modules directory...")

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, file), base_path)
                module_name = rel_path.replace(os.sep, ".").replace(".py", "")
                full_import = f"modules.exploits.{module_name}"

                try:
                    module = __import__(full_import, fromlist=[""])
                    for attr in dir(module):
                        obj = getattr(module, attr)
                        if isinstance(obj, type) and issubclass(obj, BaseModule) and obj is not BaseModule:
                            instance = obj()
                            clean_name = module_name.replace(".", "/")
                            MODULES[clean_name] = instance
                            print(colored(f"[+] Loaded module: {clean_name}", "green"))
                except Exception as e:
                    print(f"[-] Failed to load {full_import}: {e}")

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
                print("  use <module>     - Select a module (e.g. use exploits/dvwa/rce)")
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
                module_path = low.split()[1]
                if module_path in MODULES:
                    current_module = MODULES[module_path]
                    print(colored(f"[+] Module loaded: {module_path}", "green"))
                    current_module.show_options()
                else:
                    print(colored(f"[-] Module '{module_path}' not found", "red"))
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