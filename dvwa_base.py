"""
dvwa_base.py
Shared login + CSRF logic for all DVWA modules.
Subclass DVWABase instead of BaseModule when targeting DVWA.
"""

import re
import requests
from base_module import BaseModule
from utils import colored


class DVWABase(BaseModule):
    """Intermediate base class that adds DVWA session management."""

    # Common DVWA options every subclass will need
    DVWA_OPTIONS = {
        "RHOST":    {"value": "",        "required": True,  "description": "Target DVWA IP or hostname"},
        "RPORT":    {"value": "80",      "required": True,  "description": "Target DVWA port"},
        "USERNAME": {"value": "admin",   "required": True,  "description": "DVWA username"},
        "PASSWORD": {"value": "password","required": True,  "description": "DVWA password"},
    }

    def __init__(self):
        super().__init__()
        # Merge DVWA_OPTIONS into self.options so subclasses only need to add extras
        self.options = {k: dict(v) for k, v in self.DVWA_OPTIONS.items()}
        self.session: requests.Session | None = None
        self.logged_in: bool = False

    # ------------------------------------------------------------------
    # Public helper — call this at the start of run()
    # ------------------------------------------------------------------
    def login(self) -> bool:
        """
        Logs into DVWA and sets security level to Low.
        Returns True on success, False on failure.
        Populates self.session for use by subclass methods.
        """
        rhost = self.options["RHOST"]["value"]
        login_url = f"http://{rhost}/login.php"

        print(colored(f"[*] Connecting to {login_url} ...", "yellow"))
        self.session = requests.Session()

        # --- Fetch login page for CSRF token ---
        try:
            r_get = self.session.get(login_url, timeout=5)
        except Exception as exc:
            print(colored(f"[-] Could not reach login page: {exc}", "red"))
            return False

        token_match = re.search(
            r'name=[\'"]user_token[\'"]\s+value=[\'"]([a-f0-9]+)[\'"]',
            r_get.text, re.IGNORECASE
        )
        if not token_match:
            print(colored("[-] CSRF token not found — is DVWA running?", "red"))
            return False

        user_token = token_match.group(1)
        print(colored(f"  [+] CSRF token: {user_token}", "green"))

        # --- POST login ---
        login_data = {
            "username":   self.options["USERNAME"]["value"],
            "password":   self.options["PASSWORD"]["value"],
            "user_token": user_token,
            "Login":      "Login",
        }
        r_login = self.session.post(login_url, data=login_data, allow_redirects=True)

        if "Logout" not in r_login.text and "Welcome" not in r_login.text:
            print(colored("[-] Login failed — check USERNAME / PASSWORD.", "red"))
            return False

        print(colored("[+] Login successful.", "green"))

        # --- Set security to Low ---
        sec_url = f"http://{rhost}/security.php"
        self.session.post(sec_url, data={"security": "low", "seclev_submit": "Submit"})
        print(colored("[+] Security level set to Low.", "green"))

        self.logged_in = True
        return True

    # ------------------------------------------------------------------
    # Convenience property
    # ------------------------------------------------------------------
    @property
    def base_url(self) -> str:
        return f"http://{self.options['RHOST']['value']}"
