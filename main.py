import requests
from datetime import datetime
import os
###################

class Tool:
    def __init__(self):
        self.name = "web_exploit"
        self.description = "DVWA Web Exploitation Tool"
        self.target = "http://192.168.107.129"
        self.user = "admin"
        self.password = "password"
        self.session = None
        self.logged_in = False
        self.sub_modules = {}

    def load_sub_modules(self):
        sub_dir = os.path.join("tools", "web_exploit", "modules")
        for filename in os.listdir(sub_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    module = __import__(f"tools.web_exploit.modules.{module_name}", fromlist=[""])
                    if hasattr(module, "Module"):
                        self.sub_modules[module_name] = module.Module()
                        print(f"[+] Loaded sub-module: {module_name}")
                except Exception as e:
                    print(f"[-] Failed to load sub-module {module_name}: {e}")

    def show_options(self):
        print("\n=== Web Exploit Tool ===")
        print(f"  target       → {self.target}")
        print(f"  user         → {self.user}")
        print(f"  password     → {self.password}\n")
        print("Sub-modules:")
        for m in self.sub_modules.keys():
            print(f"  - {m}")
        print("\nCommands:")
        print("  use <sub-module>     - e.g. use cmd_injection")
        print("  run                  - Login & setup")
        print("  set target <value>")
        print("  back / exit")

    def handle_command(self, cmd_input):
        cmd = cmd_input.strip().lower()

        if cmd == "show options":
            self.show_options()
            return

        if cmd.startswith("set target"):
            value = cmd_input.split(maxsplit=2)[2].strip()
            if not value.startswith(("http://", "https://")):
                value = "http://" + value
            self.target = value.rstrip("/")
            print(f"[+] target → {self.target}")
            return

        if cmd == "run":
            self._login_and_setup()
            return

        if cmd.startswith("use "):
            sub_name = cmd.split()[1]
            if sub_name in self.sub_modules:
                print(f"[+] Using sub-module: {sub_name}")
                self.sub_modules[sub_name].show_options()
            else:
                print(f"[-] Sub-module '{sub_name}' not found")
            return

        if cmd in ["back", "exit"]:
            print("[*] Returning to main Bandito menu...")
            return

        print("Unknown command. Try 'show options'")

    def _login_and_setup(self):
        if self.logged_in:
            print("[+] Already logged in")
            return

        print(f"[*] Logging into {self.target}...")
        self.session = requests.Session()

        login_url = f"{self.target}/login.php"
        r_get = self.session.get(login_url)

        token_marker = "name='user_token' value='"
        token_pos = r_get.text.find(token_marker)
        user_token = ""
        if token_pos != -1:
            start = token_pos + len(token_marker)
            end = r_get.text.find("'", start)
            user_token = r_get.text[start:end]

        login_data = {
            "username": self.user,
            "password": self.password,
            "user_token": user_token,
            "Login": "Login"
        }
        r_login = self.session.post(login_url, data=login_data, allow_redirects=True)

        if "Logout" in r_login.text:
            print("[+] Login successful")
        else:
            print("[-] Login failed")
            return

        sec_url = f"{self.target}/security.php"
        self.session.post(sec_url, data={"security": "low", "seclev_submit": "Submit"})

        self.logged_in = True
        self.load_sub_modules()
        print("[+] Web Exploit ready. Use 'use cmd_injection', 'use file_upload', etc.")