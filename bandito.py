import os
import importlib.util
from utils import print_banner, colored, cmatrix_loading
from base_module import BaseModule

MODULES = {}
USER_MODULES = {}  # Tracks user-loaded custom modules

def load_modules():
    global MODULES
    MODULES = {}
    base_path = "modules"  # root for all categories (buffer_overflow, sqli, xss, etc.)

    if not os.path.isdir(base_path):
        print("[-] modules directory not found!")
        return

    def walk_and_load(path, prefix=""):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    rel_path = os.path.relpath(os.path.join(root, file), base_path)
                    module_name = rel_path.replace(os.sep, ".").rstrip(".py")
                    if prefix:
                        module_name = f"{prefix}.{module_name}"
                    full_path = os.path.join(root, file)
                    spec = importlib.util.spec_from_file_location(module_name, full_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for attr in dir(module):
                        obj = getattr(module, attr)
                        if isinstance(obj, type) and issubclass(obj, BaseModule) and obj is not BaseModule:
                            instance = obj()
                            MODULES[module_name] = instance
                            print(colored(f"[+] Loaded module: {module_name}", "green"))

    walk_and_load(base_path)

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
                print("  use <module>          - Select a module (e.g. use buffer_overflow/benjis_snack_vault_bo)")
                print("  show modules          - List all loaded modules")
                print("  browse                - List available categories")
                print("  browse <category>     - List modules in a category")
                print("  load <path>           - Load a single .py file or directory of modules")
                print("  back                  - Return to main menu")
                print("  exit / quit           - Exit framework\n")
                continue

            if low == "show modules":
                print(colored("Available modules:", "yellow"))
                auto_modules = [m for m in sorted(MODULES.keys()) if not m.startswith("custom.")]
                if auto_modules:
                    print(colored("  Auto-loaded:", "yellow"))
                    for m in auto_modules:
                        print(colored(f"    - {m}", "orange"))

                if USER_MODULES:
                    print(colored("\n  User-loaded (custom):", "yellow"))
                    for m in sorted(USER_MODULES.keys()):
                        print(colored(f"    - {m}", "orange"))
                continue

            if low == "browse":
                categories = set(m.split('.')[0] for m in MODULES.keys() if '.' in m)
                print(colored("\nAvailable Categories:", "yellow"))
                for cat in sorted(categories):
                    print(colored(f"  - {cat}", "orange"))
                print(colored("\nType 'browse <category>' to see modules in that category", "yellow"))
                continue

            if low.startswith("browse "):
                cat = cmd.split(maxsplit=1)[1].strip()
                print(colored(f"\nModules in {cat}:", "yellow"))
                found = False
                for m in sorted(MODULES.keys()):
                    if m.startswith(cat + "."):
                        print(colored(f"  - {m}", "orange"))
                        found = True
                if not found:
                    print(colored(f"  No modules found in category '{cat}'", "red"))
                continue

            if low.startswith("load "):
                path = cmd.split(maxsplit=1)[1].strip()
                if not os.path.exists(path):
                    print(colored(f"[-] Path not found: {path}", "red"))
                    continue

                try:
                    count = 0
                    if os.path.isdir(path):
                        # Load directory recursively
                        for root, _, files in os.walk(path):
                            for file in files:
                                if file.endswith(".py") and not file.startswith("__"):
                                    full_path = os.path.join(root, file)
                                    module_name = os.path.splitext(file)[0]
                                    spec = importlib.util.spec_from_file_location(module_name, full_path)
                                    module = importlib.util.module_from_spec(spec)
                                    spec.loader.exec_module(module)

                                    loaded = False
                                    for attr in dir(module):
                                        obj = getattr(module, attr)
                                        if isinstance(obj, type) and issubclass(obj, BaseModule) and obj is not BaseModule:
                                            instance = obj()
                                            key = f"custom.{module_name}"
                                            MODULES[key] = instance
                                            USER_MODULES[key] = instance
                                            print(colored(f"[+] Loaded from path: {key}", "green"))
                                            count += 1
                                            loaded = True
                                    if not loaded:
                                        print(colored(f"[-] No BaseModule found in {full_path}", "red"))
                    else:
                        # Single file
                        module_name = os.path.splitext(os.path.basename(path))[0]
                        spec = importlib.util.spec_from_file_location(module_name, path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        loaded = False
                        for attr in dir(module):
                            obj = getattr(module, attr)
                            if isinstance(obj, type) and issubclass(obj, BaseModule) and obj is not BaseModule:
                                instance = obj()
                                key = f"custom.{module_name}"
                                MODULES[key] = instance
                                USER_MODULES[key] = instance
                                print(colored(f"[+] Loaded custom module: {key}", "green"))
                                loaded = True
                        if not loaded:
                            print(colored(f"[-] No BaseModule found in {path}", "red"))
                except Exception as e:
                    print(colored(f"[-] Failed to load {path}: {e}", "red"))
                continue

            if low.startswith("use "):
                module_name = cmd.split(maxsplit=1)[1].strip()
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
                print(colored("[-] No module selected. Use 'use <module>' or 'browse' first", "red"))

        except KeyboardInterrupt:
            print("\n")
        except Exception as e:
            print(colored(f"[-] Error: {e}", "red"))

if __name__ == "__main__":
    main()