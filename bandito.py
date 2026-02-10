import os
from utils import print_banner, colored

# Simple module loader
MODULES = {}

def load_modules():
    global MODULES
    module_dir = "modules"
    for filename in os.listdir(module_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            try:    
                module = __import__(f"modules.{module_name}", fromlist=[""])
                if hasattr(module, "Module"):    
                    MODULES[module_name] = module.Module()   # Every module must have a "Module" class
                    print(f"[+] Loaded module: {module_name}")
                else:
                    print(f"[-] {filename} has no 'Module' class")
            except Exception as e:
                print(f"[-] Failed to load {filename}: {e}")

                
def main():
    print_banner()
    print(colored("[*] Bandito Framework", "green"))
    print(colored("[*] Type 'help' for commands\n", "yellow"))

    load_modules()
    current_module = None

    while True:
        try:
            prompt = f"bandito ({current_module.name if current_module else 'no module'}) > "
            cmd = input(prompt).strip().lower()

            if cmd == "exit" or cmd == "quit":
                print(colored("[*] Goodbye!", "red"))
                break
            elif cmd == "help":
                print("\nCommands:")
                print("  use <module>     - Select a module (e.g. use cmd_injection)")
                print("  show modules     - List available modules")
                print("  show options     - Show current module options")
                print("  set <option> <value> - Set option (e.g. set target http://192.168.x.x)")
                print("  run / exploit    - Run the selected module")
                print("  back             - Unload current module")
                print("  exit / quit      - Exit framework\n")
            elif cmd.startswith("use "):
                module_name = cmd.split()[1]
                if module_name in MODULES:
                    current_module = MODULES[module_name]
                    print(colored(f"[+] Module loaded: {module_name}", "green"))
                else:
                    print(colored(f"[-] Module '{module_name}' not found", "red"))
            elif cmd == "show modules":
                print("Available modules:")
                for m in MODULES.keys():
                    print(f"  - {m}")
            elif cmd == "back":
                current_module = None
            elif current_module:
                current_module.handle_command(cmd)
            else:
                print(colored("[-] No module selected. Use 'use <module>' first", "red"))

        except KeyboardInterrupt:
            print("\n")
        except Exception as e:
            print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()