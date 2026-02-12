import os
from utils import print_banner, colored, cmatrix_loading
import sys


# Global modules dictionary
MODULES = {}


def load_modules():
    global MODULES
    MODULES = {}
    tools_dir = "tools"

    print("[DEBUG] Scanning tools directory...")

    if not os.path.isdir(tools_dir):
        print("[-] tools/ directory not found!")
        return

    for tool_name in os.listdir(tools_dir):
        tool_path = os.path.join(tools_dir, tool_name)

        if os.path.isdir(tool_path) and not tool_name.startswith("__"):
            main_file = os.path.join(tool_path, "main.py")

            if os.path.isfile(main_file):
                try:
                    module = __import__(f"tools.{tool_name}.main", fromlist=[""])
                    if hasattr(module, "Tool"):
                        MODULES[tool_name] = module.Tool()
                        print(f"[+] Loaded tool: {tool_name}")
                    else:
                        print(f"[-] {tool_name}/main.py has no 'Tool' class")
                except Exception as e:
                    print(f"[-] Failed to load {tool_name}: {e}")


def load_modules():
    global MODULES
    MODULES = {}
    tools_dir = "tools"

    print("[DEBUG] Scanning tools directory...")

    if not os.path.isdir(tools_dir):
        print("[-] tools/ directory not found!")
        return

    for tool_name in os.listdir(tools_dir):
        tool_path = os.path.join(tools_dir, tool_name)
        if os.path.isdir(tool_path) and not tool_name.startswith("__"):
            main_file = os.path.join(tool_path, "main.py")
            if os.path.isfile(main_file):
                try:
                    module = __import__(f"tools.{tool_name}.main", fromlist=[""])
                    if hasattr(module, "Tool"):
                        MODULES[tool_name] = module.Tool()
                        print(colored(f"[+] Loaded tool: {tool_name}", "green"))
                    else:
                        print(f"[-] {tool_name}/main.py has no 'Tool' class")
                except Exception as e:
                    print(f"[-] Failed to load {tool_name}: {e}")

def main():
    cmatrix_loading()
    print_banner()
    print(colored("[*] Bandito Framework v1.0 - Educational Exploitation Tool", "dark_red"))
    print(colored("[*] Type 'help' for commands\n", "yellow"))

    load_modules()
    current_tool = None

    while True:
        try:
            # Metasploit-style prompt
            prompt = colored(f"bandito ({current_tool.name if current_tool else 'no tool'}) > ", "red")
            cmd = input(prompt).strip()

            if not cmd:
                continue

            low = cmd.lower()

            if current_tool:
                current_tool.handle_command(cmd)
                continue

            if low in ["exit", "quit"]:
                print(colored("[*] Goodbye!", "red"))
                break

            if low == "help":
                print(colored("\nCore Commands:", "yellow"))
                print("  use <tool>       - Select a tool (e.g. use web_exploit)")
                print("  show tools       - List available tools")
                print("  back             - Return to main menu")
                print("  exit / quit      - Exit framework\n")
                continue

            if low == "show tools":
                print(colored("Available tools:", "yellow"))
                for t in MODULES.keys():
                    print(f"  - {t}")
                continue

            if low.startswith("use "):
                tool_name = low.split()[1]
                if tool_name in MODULES:
                    current_tool = MODULES[tool_name]
                    print(colored(f"[+] Tool loaded: {tool_name}", "green"))
                else:
                    print(colored(f"[-] Tool '{tool_name}' not found", "red"))
                continue

            if low == "back":
                current_tool = None
                continue

            print(colored("[-] No tool selected. Use 'use <tool>' first", "red"))

        except KeyboardInterrupt:
            print("\n")
        except Exception as e:
            print(colored(f"[-] Error: {e}", "red"))

if __name__ == "__main__":
    main()