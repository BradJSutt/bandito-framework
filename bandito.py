import os
import importlib.util
from utils import print_banner, colored, cmatrix_loading
from base_module import BaseModule
import sys
import readline  # This is the standard library readline on Linux

# Enable history and arrow keys
readline.parse_and_bind("tab: complete")
readline.set_history_length(1000)  # how many commands to remember

# Optional: Load/save history to a file so it's persistent across runs
history_file = os.path.expanduser("~/.bandito_history")
if os.path.exists(history_file):
    readline.read_history_file(history_file)
import atexit
atexit.register(readline.write_history_file, history_file)

print(colored("[*] Readline enabled: up/down arrows now work for command history", "green"))

MODULES = {}

def load_modules():
    global MODULES
    MODULES = {}
    base_path = "modules"  # ← CHANGED: Now scans the root "modules" folder

    if not os.path.isdir(base_path):
        print("[-] modules directory not found!")
        return

    def walk_and_load(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    # Build dotted module name (e.g., buffer_overflow.benjis_snack_vault_bo)
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
                
                if not MODULES:
                    print(colored("  No modules loaded yet", "red"))
                    continue
                
                modules_list = sorted(MODULES.keys())
                
                # Create a temporary map: number → full module name
                module_map = {}
                idx = 1
                
                for m in modules_list:
                    print(colored(f"  {idx:02d} - {m}", "orange"))
                    module_map[str(idx)] = m
                    idx += 1
                
                print(colored("\nUse 'use <number>' or 'use <full.module.name>'", "yellow"))
                # Optional: Store module_map globally or in session if you want persistence
                # For now, it's per-run (good enough)
                continue

            if low.startswith("use "):
                arg = cmd.split(maxsplit=1)[1].strip()
                
                # Try to interpret as number
                if arg.isdigit() and arg in module_map:
                    module_name = module_map[arg]
                else:
                    module_name = arg
                
                if module_name in MODULES:
                    current_module = MODULES[module_name]
                    print(colored(f"[+] Module loaded: {module_name} ({arg if arg.isdigit() else 'name'})", "green"))
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