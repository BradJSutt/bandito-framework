import os
import importlib.util
import sys
import readline
from utils import print_banner, colored, cmatrix_loading
from base_module import BaseModule

# Enable readline for up/down arrows and history (works on Linux/Kali)
readline.parse_and_bind("tab: complete")
readline.set_history_length(1000)
history_file = os.path.expanduser("~/.bandito_history")
if os.path.exists(history_file):
    readline.read_history_file(history_file)
import atexit
atexit.register(readline.write_history_file, history_file)
print(colored("[*] Readline enabled: up/down arrows now work for command history", "green"))

MODULES = {}
module_map = {}  # Global temp map for numbered selection (refreshed on show/browse)

def load_modules():
    global MODULES
    MODULES = {}
    base_path = "modules"  # Scans root 'modules/' and all subfolders

    if not os.path.isdir(base_path):
        print("[-] modules directory not found!")
        return

    def walk_and_load(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    rel_path = os.path.relpath(os.path.join(root, file), base_path)
                    module_name = rel_path.replace(os.sep, ".").rstrip(".py")
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
    global module_map  # We'll refresh this on show/browse

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
                print("  use <module> / use <number>   - Select module (e.g. use buffer_overflow/benjis_snack_vault_bo or use 01)")
                print("  show modules                   - List all modules with numbers")
                print("  browse                         - List categories")
                print("  browse <category>              - List modules in category with numbers")
                print("  load <path>                    - Load single .py or directory")
                print("  back                           - Return to main menu")
                print("  exit / quit                    - Exit framework\n")
                continue

            if low == "show modules":
                print(colored("Available modules:", "yellow"))
                if not MODULES:
                    print(colored("  No modules loaded yet", "red"))
                    continue

                modules_list = sorted(MODULES.keys())
                module_map.clear()  # Reset map
                idx = 1

                for m in modules_list:
                    print(colored(f"  {idx:02d} - {m}", "orange"))
                    module_map[str(idx)] = m
                    idx += 1

                print(colored("\nUse 'use <number>' or 'use <full.name>'", "yellow"))
                continue

            if low == "browse":
                categories = set(m.split('.')[0] for m in MODULES.keys() if '.' in m)
                if not categories:
                    print(colored("  No categories found yet", "red"))
                    continue

                print(colored("\nAvailable Categories:", "yellow"))
                for cat in sorted(categories):
                    print(colored(f"  - {cat}", "orange"))
                print(colored("\nType 'browse <category>' to see modules", "yellow"))
                continue

            if low.startswith("browse "):
                cat = cmd.split(maxsplit=1)[1].strip()
                matching = [m for m in sorted(MODULES.keys()) if m.startswith(cat + ".")]
                if not matching:
                    print(colored(f"  No modules in category '{cat}'", "red"))
                    continue

                print(colored(f"\nModules in {cat}:", "yellow"))
                module_map.clear()  # Reset map
                idx = 1

                for m in matching:
                    print(colored(f"  {idx:02d} - {m}", "orange"))
                    module_map[str(idx)] = m
                    idx += 1

                print(colored("\nUse 'use <number>' or 'use <full.name>'", "yellow"))
                continue

            if low.startswith("load "):
                path = cmd.split(maxsplit=1)[1].strip()
                if not os.path.exists(path):
                    print(colored(f"[-] Path not found: {path}", "red"))
                    continue

                try:
                    count = 0
                    if os.path.isdir(path):
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
                                            print(colored(f"[+] Loaded from path: {key}", "green"))
                                            count += 1
                                            loaded = True
                                    if not loaded:
                                        print(colored(f"[-] No BaseModule in {full_path}", "red"))
                    else:
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
                                print(colored(f"[+] Loaded custom module: {key}", "green"))
                                loaded = True
                        if not loaded:
                            print(colored(f"[-] No BaseModule in {path}", "red"))
                except Exception as e:
                    print(colored(f"[-] Load failed: {e}", "red"))
                continue

            if low.startswith("use "):
                arg = cmd.split(maxsplit=1)[1].strip()

                # Support numbered selection
                if arg.isdigit() and arg in module_map:
                    module_name = module_map[arg]
                else:
                    module_name = arg

                if module_name in MODULES:
                    current_module = MODULES[module_name]
                    print(colored(f"[+] Module loaded: {module_name}", "green"))
                    if hasattr(current_module, 'show_help'):
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
                print(colored("[-] No module selected. Use 'use <module>' / 'use <number>' or 'browse' first", "red"))

        except KeyboardInterrupt:
            print("\n")
        except Exception as e:
            print(colored(f"[-] Error: {e}", "red"))

if __name__ == "__main__":
    main()