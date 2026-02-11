import os
import sys

from utils import print_banner, colored

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


def main():
    print_banner()
    print(colored("[*] Bandito Framework v1.0 - Educational Exploitation Tool", "green"))
    print(colored("[*] Type 'help' for commands\n", "yellow"))

    load_modules()
    current_tool = None

    while True:
        prompt = f"bandito ({current_tool.name if current_tool else 'no tool'}) > "
        cmd = input(prompt).strip()

        if not cmd:
            continue

        low = cmd.lower()

        # If a tool is selected, let the tool handle these first
        # (so submodule selection works: "use cmd_injection", and tool-specific help can exist later)
        if current_tool and (low == "help" or low.startswith("use ") or low == "show options"):
            current_tool.handle_command(cmd)
            continue

        # Global / framework-level commands
        if low in ["exit", "quit"]:
            print(colored("[*] Goodbye!", "red"))
            break

        if low == "help":
            print("\nCommands:")
            print(" use <tool> - Select a tool (e.g. use web_exploit)")
            print(" show tools - List available tools")
            print(" show options - Show current tool options (if applicable)")
            print(" back - Return to main menu")
            print(" exit / quit - Exit framework\n")
            continue

        if low == "show tools":
            print("Available tools:")
            for t in MODULES.keys():
                print(f" - {t}")
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

        # Default: if a tool is selected, pass through; otherwise error
        if current_tool:
            current_tool.handle_command(cmd)
        else:
            print(colored("[-] No tool selected. Use 'use <tool>' first", "red"))

if __name__ == "__main__":
    main()
