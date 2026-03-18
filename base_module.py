from utils import colored


class BaseModule:
    """Base class for all Bandito modules."""

    def __init__(self):
        self.name = "base"
        self.description = "Base module"
        self.options: dict = {}

    # ------------------------------------------------------------------
    # Options display  (single implementation — all modules inherit this)
    # ------------------------------------------------------------------
    def show_options(self):
        print(colored(f"\nModule options ({self.name}):", "orange"))

        if not self.options:
            print(colored("  No options defined.", "yellow"))
            return

        rows = [
            (name, str(data.get("value", "")), "yes" if data.get("required") else "no", data.get("description", ""))
            for name, data in self.options.items()
        ]

        name_w  = max(15, max(len(r[0]) for r in rows) + 2)
        val_w   = max(30, max(len(r[1]) for r in rows) + 2)
        req_w   = max(10, max(len(r[2]) for r in rows) + 2)

        header = f"{'Name':<{name_w}} {'Current Setting':<{val_w}} {'Required':<{req_w}} Description"
        print(colored(header, "yellow"))
        print("-" * (name_w + val_w + req_w + 40))

        for name, value, required, desc in rows:
            val_str = (value[:val_w - 3] + "...") if len(value) > val_w - 3 else value
            print(
                f"{name:<{name_w}} "
                f"{colored(val_str, 'green'):<{val_w}} "
                f"{colored(required, 'red'):<{req_w}} "
                f"{desc}"
            )

    # ------------------------------------------------------------------
    # Option setter
    # ------------------------------------------------------------------
    def set_option(self, name: str, value: str):
        key = name.upper()
        if key in self.options:
            self.options[key]["value"] = value
            print(colored(f"{key} → {value}", "green"))
        else:
            print(colored(f"Unknown option: {name}", "red"))

    # ------------------------------------------------------------------
    # Command dispatcher  (subclasses can override or call super())
    # ------------------------------------------------------------------
    def handle_command(self, cmd_input: str):
        cmd = cmd_input.strip()
        low = cmd.lower()

        if low in ["help"]:
            self.show_help()
            return

        if low in ["options", "show options"]:
            self.show_options()
            return

        if low.startswith("set "):
            parts = cmd.split(maxsplit=2)
            if len(parts) == 3:
                self.set_option(parts[1], parts[2])
            else:
                print("Usage: set <option> <value>")
            return

        if low in ["run", "exploit"]:
            self.run()
            return

        if low in ["back", "exit", "quit"]:
            return

        print(colored(f"Unknown command: {cmd}. Type 'help' for options.", "red"))

    # ------------------------------------------------------------------
    # Stubs — subclasses should override
    # ------------------------------------------------------------------
    def show_help(self):
        print(colored(f"\n=== {self.name} ===", "orange"))
        print(self.description)
        print("  run / exploit        - Execute the module")
        print("  set <option> <value> - Set an option")
        print("  show options         - List current settings")
        print("  back / exit          - Return to framework\n")

    def run(self):
        raise NotImplementedError("Module must implement run()")
