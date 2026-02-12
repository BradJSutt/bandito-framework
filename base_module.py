import requests
import socket
from utils import colored

class BaseModule:
    def __init__(self):
        self.name = "base"
        self.description = "Base module"
        self.options = {}
        self.session = None
        self.logged_in = False

    def show_options(self):
        print(colored("\nModule options ({self.name}):", "orange"))
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
        print(colored("[-] run() not implemented in this module", "red"))

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"