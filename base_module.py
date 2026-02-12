from utils import colored

class BaseModule:
    def __init__(self):
        self.name = "base"
        self.description = "Base module"
        self.options = {}

    def show_options(self):
        print(colored(f"\nModule options ({self.name}):", "orange"))

        header = f"{'Name':<15} {'Current Setting':<30} {'Required':<10} {'Description'}"
        print(colored(header, "yellow"))
        print("-" * 80)

        for name, data in self.options.items():
            value = data.get("value", "")
            required = "yes" if data.get("required") else "no"
            desc = data.get("description", "")
            print(f"{name:<15} {colored(value, 'green'):<30} {colored(required, 'red'):<10} {desc}")

    def set_option(self, name, value):
        name = name.upper()
        if name in self.options:
            self.options[name]["value"] = value
            print(colored(f"{name} → {value}", "green"))
        else:
            print(colored(f"Unknown option: {name}", "red"))

    def run(self):
        raise NotImplementedError("Module must implement run() method")

    def handle_command(self, cmd):
        cmd = cmd.strip().lower()
        if cmd.startswith("set "):
            parts = cmd.split(maxsplit=2)
            if len(parts) == 3:
                self.set_option(parts[1], parts[2])
            return
        if cmd in ["options", "show options"]:
            self.show_options()
            return
        if cmd in ["back", "exit", "quit"]:
            return
        print(colored("Unknown command. Type 'help' for options.", "red"))