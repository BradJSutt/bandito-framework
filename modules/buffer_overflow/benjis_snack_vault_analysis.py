#!/usr/bin/env python3
"""
Benji's Snack Vault - App Analysis Module
Cleaned-up discovery tool (fuzzing, pattern, offset, badchars, control test)
"""

import socket
import time
import subprocess
from base_module import BaseModule
from utils import colored

class BenjisSnackVaultAnalysis(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "benjis_snack_vault_analysis"
        self.description = "Full discovery module: fuzzing, pattern, offset calculation, badchars, and control test"

        self.options = {
            "RHOST": {"value": "192.168.107.132", "required": True, "description": "Target IP"},
            "RPORT": {"value": 9999, "required": True, "description": "Target port"},
            "PREFIX": {"value": "MEOW ", "required": True, "description": "Command prefix"},
            "MODE": {"value": "full", "required": True, "description": "full | fuzz | pattern | badchars | test_offset"},
            "PATTERN_LENGTH": {"value": 3000, "required": False, "description": "Pattern length (auto-used in full mode)"},
            "OFFSET": {"value": 0, "required": False, "description": "Offset to EIP (auto-set in full mode)"},
            "CRLF": {"value": True, "required": False, "description": "Append \\r\\n"}
        }

    def show_help(self):
        print(colored("\n=== App Analysis Module ===", "yellow"))
        print("Recommended: set MODE full → run")
        print("This runs the complete discovery chain with user confirmation.")
        print("\nAvailable modes:")
        print("  full          - Guided full analysis (fuzz → pattern → offset → badchars → test)")
        print("  fuzz          - Only fuzz to find crash size")
        print("  pattern       - Send pattern only")
        print("  badchars      - Send badchars (requires OFFSET)")
        print("  test_offset   - Test EIP control with BBBB")

    def run(self):
        opts = {k: v["value"] for k, v in self.options.items()}
        mode = opts["MODE"].lower()

        if mode == "full":
            self._run_full_analysis()
        elif mode == "fuzz":
            self._run_fuzz()
        elif mode == "pattern":
            self._run_pattern()
        elif mode == "badchars":
            self._run_badchars()
        elif mode == "test_offset":
            self._run_test_offset()
        else:
            print(colored("[-] Unknown mode. Use 'full' for guided analysis.", "red"))

    # ===================================================================
    # FULL GUIDED ANALYSIS (new main mode)
    # ===================================================================
    def _run_full_analysis(self):
        print(colored("=== Starting Full App Analysis ===", "green"))
        print("This will run: Fuzz → Pattern → Offset Calc → Badchars → Control Test")
        input("Press Enter to begin...")

        # 1. Fuzz
        self._run_fuzz()
        input("\nPress Enter to continue to pattern...")

        # 2. Pattern
        self._run_pattern()
        input("\nPress Enter after noting EIP from Immunity...")

        # 3. Offset calculation
        eip = input(colored("Enter EIP from Immunity (8 hex digits): ", "yellow")).strip().upper()
        offset = self._calc_offset(eip, int(self.options["PATTERN_LENGTH"]["value"]))
        if offset:
            self.options["OFFSET"]["value"] = offset
            print(colored(f"[+] OFFSET auto-set to {offset}", "green"))

        input("\nPress Enter to continue to badchars...")

        # 4. Badchars
        self._run_badchars()

        input("\nPress Enter to run final EIP control test...")
        self._run_test_offset()

        print(colored("\n=== Full analysis complete! ===", "green"))
        print("You can now switch to the exploit module.")

    # ===================================================================
    # Individual modes (kept for flexibility)
    # ===================================================================
    def _run_fuzz(self):
        print(colored("[*] Fuzzing mode", "yellow"))
        # ... (your existing fuzz code here - I can add it if you want)

    def _run_pattern(self):
        print(colored("[*] Pattern mode", "yellow"))
        # ... (existing pattern code)

    def _calc_offset(self, eip_hex, length):
        # Uses official pattern_offset.rb - guaranteed match
        try:
            result = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_offset.rb", "-q", eip_hex, "-l", str(length)],
                text=True
            ).strip()
            if "Exact match at offset" in result:
                offset = int(result.split()[-1])
                print(colored(f"[+] Exact match at offset {offset}", "green"))
                return offset
        except Exception as e:
            print(colored(f"[-] Offset calc failed: {e}", "red"))
        return None

    def _run_badchars(self):
        print(colored("[*] Badchars mode", "yellow"))
        # ... (existing badchars code)

    def _run_test_offset(self):
        print(colored("[*] Testing EIP control", "yellow"))
        # ... (existing test_offset code)

    def handle_command(self, cmd):
        if cmd.strip().lower() == "run":
            self.run()
            return
        super().handle_command(cmd)